import { readFile, writeFile, rename, rm } from "node:fs/promises";
import { spawn } from "node:child_process";

const outputPath = process.argv[2] || "data/youtube-channels.json";
const channel = {
  key: "nmixx",
  label: "NMIXX Official",
  handle: "@NMIXXOfficial",
  channelId: "UCnUAyD4t2LkvW68YrDh7fDg",
  url: "https://www.youtube.com/@NMIXXOfficial",
  description: "MV、ビハインド、ライブ、ショートなどNMIXXの公式コンテンツ。",
  feedUrl: "https://www.youtube.com/feeds/videos.xml?channel_id=UCnUAyD4t2LkvW68YrDh7fDg",
};
const tabs = [
  { path: "videos", type: "video", limit: 60 },
  { path: "shorts", type: "short", limit: 40 },
  { path: "streams", type: "live", limit: 30 },
];

const run = (command, args) => new Promise((resolve, reject) => {
  const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (chunk) => { stdout += chunk; });
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  child.on("error", reject);
  child.on("close", (code) => {
    if (code === 0) resolve(stdout);
    else reject(new Error(stderr.trim() || `${command} exited ${code}`));
  });
});

const parseExisting = async () => {
  try {
    const parsed = JSON.parse(await readFile(outputPath, "utf8"));
    const videos = parsed?.channels?.find((item) => item.key === channel.key)?.videos;
    return {
      payload: parsed,
      videoMap: new Map((Array.isArray(videos) ? videos : []).map((item) => [String(item.videoId || ""), item])),
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
  if (item.live_status === "is_live" || item.live_status === "was_live") videoType = "live";
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

const fetchTab = async (tab, existingMap) => {
  const raw = await run("yt-dlp", [
    "--flat-playlist",
    "--dump-single-json",
    "--playlist-end",
    String(tab.limit),
    `${channel.url}/${tab.path}`,
  ]);
  const parsed = JSON.parse(raw);
  const entries = Array.isArray(parsed.entries) ? parsed.entries : [];
  return entries
    .filter(Boolean)
    .map((item) => normalizeEntry(item, tab.type, existingMap.get(String(item.id || ""))))
    .filter(Boolean);
};

const existing = await parseExisting();
const collected = [];
const failures = [];
for (const tab of tabs) {
  try {
    collected.push(...await fetchTab(tab, existing.videoMap));
  } catch (error) {
    failures.push(`${tab.path}: ${error.message}`);
  }
}

try {
  if (!collected.length) throw new Error(`全タブの取得に失敗しました。${failures.join(" / ")}`);

  const merged = new Map();
  for (const video of collected) {
    const previous = merged.get(video.videoId);
    // Prefer the more specific classification when the same item appears in multiple tabs.
    if (!previous || ["live", "short"].includes(video.videoType)) merged.set(video.videoId, { ...previous, ...video });
  }
  const videos = [...merged.values()].sort((a, b) => {
    const timeA = Date.parse(a.publishedAt || "") || 0;
    const timeB = Date.parse(b.publishedAt || "") || 0;
    return timeB - timeA || a.title.localeCompare(b.title, "ja");
  });
  const typeCounts = videos.reduce((counts, item) => {
    counts[item.videoType] = (counts[item.videoType] || 0) + 1;
    return counts;
  }, { video: 0, short: 0, live: 0 });

  const payload = {
    generatedAt: new Date().toISOString(),
    source: "youtube-public",
    collectionMode: "official-channel-public-tabs",
    classificationVersion: 2,
    partialFailures: failures,
    channels: [{ ...channel, totalVideos: videos.length, typeCounts, videos }],
  };
  const temporaryPath = `${outputPath}.tmp`;
  await writeFile(temporaryPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await rename(temporaryPath, outputPath);
  console.log(`YouTubeデータを更新しました: ${videos.length}件${failures.length ? `（一部タブ失敗: ${failures.length}件）` : ""}`);
} catch (error) {
  await rm(`${outputPath}.tmp`, { force: true }).catch(() => {});
  console.error(`YouTube取得に失敗しました。既存データを維持します: ${error.message}`);
  process.exitCode = 2;
}
