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
  description: "NMIXX公式YouTubeチャンネルの動画、ショート、ライブ配信。",
  feedUrl: "https://www.youtube.com/feeds/videos.xml?channel_id=UCnUAyD4t2LkvW68YrDh7fDg",
};

// YouTubeの各公開タブを別々に取得し、タブを分類の正本にする。
// full は件数上限なし。recent は全履歴取得後の差分確認用。
const tabs = [
  { path: "videos", type: "video", label: "動画", recentLimit: 240 },
  { path: "shorts", type: "short", label: "ショート", recentLimit: 240 },
  { path: "streams", type: "live", label: "ライブ", recentLimit: 180 },
];

const TYPE_PRIORITY = { video: 1, short: 2, live: 3 };
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

const parseExisting = async () => {
  try {
    const parsed = JSON.parse(await readFile(outputPath, "utf8"));
    const currentChannel = Array.isArray(parsed?.channels)
      ? parsed.channels.find((item) => item?.key === channel.key && item?.channelId === channel.channelId)
      : null;
    const videos = Array.isArray(currentChannel?.videos) ? currentChannel.videos : [];
    return {
      payload: parsed,
      videoMap: new Map(videos.filter((item) => item?.videoId).map((item) => [String(item.videoId), item])),
    };
  } catch {
    return { payload: null, videoMap: new Map() };
  }
};

const isoFromSeconds = (value) => {
  const seconds = Number(value || 0);
  if (!Number.isFinite(seconds) || seconds <= 0) return "";
  return new Date(seconds * 1000).toISOString();
};

const isoFromUploadDate = (value) => {
  const text = String(value || "");
  if (!/^\d{8}$/.test(text)) return "";
  const year = text.slice(0, 4);
  const month = text.slice(4, 6);
  const day = text.slice(6, 8);
  return `${year}-${month}-${day}T00:00:00.000Z`;
};

const thumbnailFor = (item, videoId, previous) => {
  const thumbnails = Array.isArray(item?.thumbnails) ? item.thumbnails.filter((entry) => entry?.url) : [];
  return thumbnails.at(-1)?.url
    || String(item?.thumbnail || "")
    || String(previous?.thumbnail || "")
    || `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
};

const normalizeEntry = (item, tab, previous) => {
  const videoId = String(item?.id || "").trim();
  if (!videoId) return null;

  const exactPublishedAt = isoFromSeconds(item?.timestamp) || isoFromSeconds(item?.release_timestamp);
  const approximatePublishedAt = isoFromUploadDate(item?.upload_date);
  const publishedAt = exactPublishedAt || approximatePublishedAt || String(previous?.publishedAt || "");
  const duration = Number(item?.duration ?? previous?.duration ?? 0) || 0;
  const sourceTypes = new Set(Array.isArray(previous?.sourceTypes) ? previous.sourceTypes : []);
  sourceTypes.add(tab.type);

  return {
    videoId,
    title: String(item?.title || previous?.title || ""),
    url: String(item?.webpage_url || `https://www.youtube.com/watch?v=${videoId}`),
    thumbnail: thumbnailFor(item, videoId, previous),
    publishedAt,
    dateAccuracy: exactPublishedAt ? "exact" : (approximatePublishedAt ? "approximate" : (previous?.dateAccuracy || "unknown")),
    videoType: tab.type,
    categoryLabel: tab.label,
    sourceTypes: [...sourceTypes].sort((a, b) => TYPE_PRIORITY[a] - TYPE_PRIORITY[b]),
    duration,
    liveStatus: tab.type === "live" ? String(item?.live_status || previous?.liveStatus || "stream") : "not_live",
    channelKey: channel.key,
    channelId: channel.channelId,
  };
};

const buildYtDlpArgs = (tab, mode) => {
  const args = [
    "--flat-playlist",
    "--dump-single-json",
    "--no-progress",
    "--socket-timeout", "30",
    "--extractor-retries", "5",
    "--retries", "5",
    "--js-runtimes", "node",
    "--extractor-args", "youtubetab:approximate_date",
    "--compat-options", "no-youtube-unavailable-videos",
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
  const entries = Array.isArray(parsed?.entries) ? parsed.entries.filter(Boolean) : [];
  if (!entries.length) throw new Error(`${tab.label}タブの取得結果が0件でした`);

  const videos = entries
    .map((item) => normalizeEntry(item, tab, existingMap.get(String(item?.id || ""))))
    .filter(Boolean);

  return {
    videos,
    reportedCount: Number(parsed?.playlist_count || parsed?.n_entries || 0) || null,
  };
};

const fetchTab = async (tab, mode, existingMap) => {
  let lastError;
  for (let attempt = 1; attempt <= RETRY_COUNT; attempt += 1) {
    try {
      return await fetchTabOnce(tab, mode, existingMap);
    } catch (error) {
      lastError = error;
      if (attempt < RETRY_COUNT) await sleep(attempt * 5000);
    }
  }
  throw lastError;
};

const mergeVideo = (current, incoming) => {
  if (!current) return incoming;
  const currentPriority = TYPE_PRIORITY[current.videoType] || 0;
  const incomingPriority = TYPE_PRIORITY[incoming.videoType] || 0;
  const sourceTypes = [...new Set([...(current.sourceTypes || []), ...(incoming.sourceTypes || [])])]
    .sort((a, b) => TYPE_PRIORITY[a] - TYPE_PRIORITY[b]);
  const winner = incomingPriority >= currentPriority ? incoming : current;
  const fallback = winner === incoming ? current : incoming;
  return {
    ...fallback,
    ...winner,
    sourceTypes,
    title: winner.title || fallback.title || "",
    thumbnail: winner.thumbnail || fallback.thumbnail || "",
    publishedAt: winner.publishedAt || fallback.publishedAt || "",
    duration: winner.duration || fallback.duration || 0,
  };
};

const existing = await parseExisting();
const existingHistoryComplete = existing.payload?.historyComplete === true;
let mode;
if (!existingHistoryComplete) mode = "full";
else if (requestedMode === "auto") mode = "recent";
else mode = requestedMode;

const collectedByTab = new Map();
const failures = [];
const successfulTabs = [];
const tabStats = {};

for (const tab of tabs) {
  try {
    const result = await fetchTab(tab, mode, existing.videoMap);
    collectedByTab.set(tab.path, result.videos);
    successfulTabs.push(tab.path);
    tabStats[tab.path] = {
      type: tab.type,
      fetched: result.videos.length,
      reportedCount: result.reportedCount,
      completeRequest: mode === "full",
    };
    console.log(`${tab.path}: ${result.videos.length}件取得${result.reportedCount ? ` / reported=${result.reportedCount}` : ""}`);
  } catch (error) {
    failures.push(`${tab.path}: ${error.message}`);
  }
}

try {
  const collected = [...collectedByTab.values()].flat();
  if (!collected.length) throw new Error(`全タブの取得に失敗しました。${failures.join(" / ")}`);

  const fullSyncSucceeded = mode === "full" && failures.length === 0 && successfulTabs.length === tabs.length;
  const merged = new Map();

  // 差分取得または部分失敗では、既存の完全履歴を失わない。
  if (mode === "recent" || !fullSyncSucceeded) {
    for (const video of existing.videoMap.values()) {
      if (video?.videoId) merged.set(String(video.videoId), video);
    }
  }

  for (const video of collected) {
    merged.set(video.videoId, mergeVideo(merged.get(video.videoId), video));
  }

  const videos = [...merged.values()].sort((a, b) => {
    const timeA = Date.parse(a.publishedAt || "") || 0;
    const timeB = Date.parse(b.publishedAt || "") || 0;
    return timeB - timeA || String(a.title || "").localeCompare(String(b.title || ""), "ja");
  });

  const typeCounts = videos.reduce((counts, item) => {
    const type = Object.hasOwn(TYPE_PRIORITY, item.videoType) ? item.videoType : "video";
    counts[type] += 1;
    return counts;
  }, { video: 0, short: 0, live: 0 });

  const now = new Date().toISOString();
  const historyComplete = fullSyncSucceeded || existingHistoryComplete;
  const payload = {
    generatedAt: now,
    source: "youtube-public-channel-tabs",
    collectionMode: historyComplete ? "complete-public-tab-archive" : "partial-public-tab-archive",
    requestedSyncMode: requestedMode,
    effectiveSyncMode: mode,
    historyComplete,
    lastFullSyncAt: fullSyncSucceeded ? now : String(existing.payload?.lastFullSyncAt || ""),
    successfulTabs,
    partialFailures: failures,
    tabStats,
    classificationVersion: 4,
    classificationRule: "youtube-source-tab-with-live-precedence",
    channels: [{ ...channel, totalVideos: videos.length, typeCounts, videos }],
  };

  const temporaryPath = `${outputPath}.tmp`;
  await writeFile(temporaryPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await rename(temporaryPath, outputPath);
  console.log(`YouTubeデータ更新: 合計${videos.length}件 / 動画${typeCounts.video} / ショート${typeCounts.short} / ライブ${typeCounts.live} / mode=${mode} / historyComplete=${historyComplete}`);
} catch (error) {
  await rm(`${outputPath}.tmp`, { force: true }).catch(() => {});
  console.error(`YouTube取得に失敗しました。既存データを維持します: ${error.message}`);
  process.exitCode = 2;
}
