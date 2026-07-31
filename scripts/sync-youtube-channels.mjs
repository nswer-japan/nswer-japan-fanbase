import { readFile, writeFile, rename, rm } from "node:fs/promises";
import { spawn } from "node:child_process";

const outputPath = process.argv[2] || "data/youtube-channels.json";
const requestedMode = String(process.env.YOUTUBE_SYNC_MODE || "auto").toLowerCase();
const validModes = new Set(["auto", "full", "recent"]);
if (!validModes.has(requestedMode)) {
  throw new Error(`YOUTUBE_SYNC_MODE は auto / full / recent のいずれかです: ${requestedMode}`);
}

const channel = {
  key: "nmixx",
  label: "NMIXX Official",
  handle: "@NMIXXOfficial",
  channelId: "UCnUAyD4t2LkvW68YrDh7fDg",
  url: "https://www.youtube.com/@NMIXXOfficial",
  description: "MV、ビハインド、ライブ、ショートなどNMIXXの公式コンテンツ。",
  feedUrl: "https://www.youtube.com/feeds/videos.xml?channel_id=UCnUAyD4t2LkvW68YrDh7fDg",
};

// Full mode has no playlist limit. Recent mode is used for frequent checks after
// a successful full-history sync and is merged into the stored archive.
const tabs = [
  { path: "videos", type: "video", recentLimit: 180 },
  { path: "shorts", type: "short", recentLimit: 120 },
  { path: "streams", type: "live", recentLimit: 100 },
];

const RUN_TIMEOUT_MS = Number(process.env.YOUTUBE_TAB_TIMEOUT_MS || 20 * 60 * 1000);
const RETRY_COUNT = Math.max(1, Number(process.env.YOUTUBE_TAB_RETRIES || 3));

const run = (command, args, timeoutMs = RUN_TIMEOUT_MS) => new Promise((resolve, reject) => {
  const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
  let stdout = "";
  let stderr = "";
  let settled = false;
  const timer = setTimeout(() => {
    if (settled) return;
    child.kill("SIGTERM");
    setTimeout(() => child.kill("SIGKILL"), 5000).unref();
    settled = true;
    reject(new Error(`${command} timed out after ${Math.round(timeoutMs / 60000)} minutes`));
  }, timeoutMs);

  child.stdout.on("data", (chunk) => { stdout += chunk; });
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  child.on("error", (error) => {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    reject(error);
  });
  child.on("close", (code) => {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    if (code === 0) resolve(stdout);
    else reject(new Error(stderr.trim() || `${command} exited ${code}`));
  });
});

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

const LEGACY_ENTRY_PATTERNS = [
  /rescene/i,
  /リセンヌ/u,
  /리센느/u,
  /\bWONI\b/i,
  /\bLIV\b/i,
  /\bMINAMI\b/i,
  /\bZENA\b/i,
  /scenedrome/i,
  /love\s+attack/i,
  /pretty\s+girl/i,
  /lip\s+bomb/i,
  /busy\s+boy/i,
  /glow\s+up/i,
  /pinball/i,
  /remember\s+a\s+scene/i,
  /scent\s*[·・.]?\s*scene/i,
];

const isLegacyEntry = (item) => {
  const text = JSON.stringify(item || {});
  return LEGACY_ENTRY_PATTERNS.some((pattern) => pattern.test(text));
};

const parseExisting = async () => {
  try {
    const parsed = JSON.parse(await readFile(outputPath, "utf8"));
    const videos = parsed?.channels?.find((item) => item.key === channel.key)?.videos;
    const sourceVideos = Array.isArray(videos) ? videos : [];
    const cleanVideos = sourceVideos.filter((item) => item?.videoId && !isLegacyEntry(item));
    const removedCount = sourceVideos.length - cleanVideos.length;
    if (removedCount > 0) {
      console.log(`旧サイト由来のYouTubeデータを${removedCount}件除外しました。`);
    }
    return {
      payload: parsed,
      videoMap: new Map(cleanVideos.map((item) => [String(item.videoId || ""), item])),
    };
  } catch {
    return { payload: null, videoMap: new Map() };
  }
};

const thumbnailFor = (item, videoId) => {
  const thumbnails = Array.isArray(item.thumbnails) ? item.thumbnails : [];
  return thumbnails.at(-1)?.url || `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
};

const normalizeEntry = (item, fallbackType, previous) => {
  const videoId = String(item?.id || "");
  if (!videoId) return null;
  const duration = Number(item.duration || previous?.duration || 0) || 0;
  const publishedAt = item.timestamp
    ? new Date(item.timestamp * 1000).toISOString()
    : String(item.release_timestamp ? new Date(item.release_timestamp * 1000).toISOString() : previous?.publishedAt || "");
  let videoType = fallbackType;
  if (fallbackType === "video" && duration > 0 && duration <= 61) videoType = "short";
  if (["is_live", "was_live", "is_upcoming"].includes(item.live_status)) videoType = "live";
  return {
    videoId,
    title: String(item.title || previous?.title || ""),
    url: `https://www.youtube.com/watch?v=${videoId}`,
    thumbnail: thumbnailFor(item, videoId) || previous?.thumbnail || "",
    publishedAt,
    videoType,
    duration,
    channelKey: channel.key,
  };
};

const buildYtDlpArgs = (tab, mode) => {
  const args = [
    "--flat-playlist",
    "--dump-single-json",
    "--ignore-errors",
    "--no-progress",
    "--socket-timeout", "30",
    "--extractor-retries", "5",
    "--retries", "5",
    "--js-runtimes", "node",
  ];
  if (mode === "recent") {
    args.push("--playlist-end", String(tab.recentLimit));
  }
  args.push(`${channel.url}/${tab.path}`);
  return args;
};

const fetchTabOnce = async (tab, mode, existingMap) => {
  const raw = await run("yt-dlp", buildYtDlpArgs(tab, mode));
  const parsed = JSON.parse(raw);
  const entries = Array.isArray(parsed.entries) ? parsed.entries : [];
  return entries
    .filter(Boolean)
    .map((item) => normalizeEntry(item, tab.type, existingMap.get(String(item.id || ""))))
    .filter(Boolean);
};

const fetchTab = async (tab, mode, existingMap) => {
  let lastError;
  for (let attempt = 1; attempt <= RETRY_COUNT; attempt += 1) {
    try {
      const videos = await fetchTabOnce(tab, mode, existingMap);
      if (!videos.length) throw new Error("取得結果が0件でした");
      return videos;
    } catch (error) {
      lastError = error;
      if (attempt < RETRY_COUNT) await sleep(attempt * 5000);
    }
  }
  throw lastError;
};

const existing = await parseExisting();
const existingHistoryComplete = existing.payload?.historyComplete === true;
const mode = requestedMode === "auto" ? (existingHistoryComplete ? "recent" : "full") : requestedMode;
const collected = [];
const failures = [];
const successfulTabs = [];

for (const tab of tabs) {
  try {
    const videos = await fetchTab(tab, mode, existing.videoMap);
    collected.push(...videos);
    successfulTabs.push(tab.path);
    console.log(`${tab.path}: ${videos.length}件取得`);
  } catch (error) {
    failures.push(`${tab.path}: ${error.message}`);
  }
}

try {
  if (!collected.length) throw new Error(`全タブの取得に失敗しました。${failures.join(" / ")}`);

  const merged = new Map();
  const fullSyncSucceeded = mode === "full" && failures.length === 0 && successfulTabs.length === tabs.length;

  // Recent mode always keeps the complete stored archive. A partially failed
  // full sync also preserves the previous archive rather than deleting entries.
  if (mode === "recent" || !fullSyncSucceeded) {
    for (const video of existing.videoMap.values()) {
      if (video?.videoId) merged.set(String(video.videoId), video);
    }
  }

  for (const video of collected) {
    const previous = merged.get(video.videoId);
    // Prefer the more specific classification when an item appears in multiple tabs.
    if (!previous || ["live", "short"].includes(video.videoType)) merged.set(video.videoId, { ...previous, ...video });
    else merged.set(video.videoId, { ...previous, ...video, videoType: previous.videoType || video.videoType });
  }

  const videos = [...merged.values()].sort((a, b) => {
    const timeA = Date.parse(a.publishedAt || "") || 0;
    const timeB = Date.parse(b.publishedAt || "") || 0;
    return timeB - timeA || String(a.title || "").localeCompare(String(b.title || ""), "ja");
  });
  const typeCounts = videos.reduce((counts, item) => {
    const type = ["video", "short", "live"].includes(item.videoType) ? item.videoType : "video";
    counts[type] = (counts[type] || 0) + 1;
    return counts;
  }, { video: 0, short: 0, live: 0 });

  const now = new Date().toISOString();
  const historyComplete = fullSyncSucceeded || existingHistoryComplete;
  const payload = {
    generatedAt: now,
    source: "youtube-public",
    collectionMode: historyComplete ? "official-channel-complete-history" : "official-channel-public-tabs-partial",
    requestedSyncMode: requestedMode,
    effectiveSyncMode: mode,
    historyComplete,
    lastFullSyncAt: fullSyncSucceeded ? now : (existing.payload?.lastFullSyncAt || ""),
    successfulTabs,
    partialFailures: failures,
    classificationVersion: 3,
    channels: [{ ...channel, totalVideos: videos.length, typeCounts, videos }],
  };
  const temporaryPath = `${outputPath}.tmp`;
  await writeFile(temporaryPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await rename(temporaryPath, outputPath);
  console.log(`YouTubeデータを更新しました: ${videos.length}件 / mode=${mode} / historyComplete=${historyComplete}${failures.length ? ` / 一部失敗=${failures.length}` : ""}`);
} catch (error) {
  await rm(`${outputPath}.tmp`, { force: true }).catch(() => {});
  console.error(`YouTube取得に失敗しました。既存データを維持します: ${error.message}`);
  process.exitCode = 2;
}
