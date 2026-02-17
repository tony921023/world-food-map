<script setup>
const props = defineProps({
  code: { type: String, default: "" },
  foodName: { type: String, default: "" },
});

function getShareUrl() {
  if (!props.code || !props.foodName) return window.location.href;
  const params = new URLSearchParams();
  params.set("country", props.code);
  params.set("food", props.foodName);
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
}

async function shareFood() {
  const url = getShareUrl();
  const title = `${props.foodName} - 世界美食地圖`;

  if (navigator.share) {
    try {
      await navigator.share({ title, url });
      return;
    } catch { /* user cancelled or not supported */ }
  }

  try {
    await navigator.clipboard.writeText(url);
    alert("已複製分享連結！");
  } catch {
    prompt("複製這個連結來分享：", url);
  }
}

function shareTo(platform) {
  const url = encodeURIComponent(getShareUrl());
  const title = encodeURIComponent(`${props.foodName} - 世界美食地圖`);
  let shareUrl = "";

  switch (platform) {
    case "facebook":
      shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
      break;
    case "twitter":
      shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
      break;
    case "line":
      shareUrl = `https://social-plugins.line.me/lineit/share?url=${url}`;
      break;
  }
  if (shareUrl) window.open(shareUrl, "_blank", "noopener,noreferrer");
}
</script>

<template>
  <div class="share-row">
    <button class="share-btn" @click.stop="shareFood">📤 分享</button>
    <button class="share-social fb" @click.stop="shareTo('facebook')">Facebook</button>
    <button class="share-social tw" @click.stop="shareTo('twitter')">Twitter</button>
    <button class="share-social line" @click.stop="shareTo('line')">LINE</button>
  </div>
</template>

<style scoped>
.share-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 6px 0 10px;
}

.share-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 14px;
  cursor: pointer;
  background: #6366f1;
  color: #fff;
  font-size: 13px;
}

.share-social {
  border: none;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
  color: #fff;
  font-size: 12px;
}

.share-social.fb {
  background: #1877f2;
}
.share-social.tw {
  background: #1da1f2;
}
.share-social.line {
  background: #06c755;
}

@media (max-width: 768px) {
  .share-btn,
  .share-social {
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
