<script setup>
import { ref, onMounted, nextTick, computed, watch } from "vue";
import svgPanZoom from "svg-pan-zoom";

const svgObj = ref(null);
const panzoom = ref(null);

// === 狀態 ===
const selectedCountryName = ref(null);
const selectedCode = ref(null);

const countryFoods = ref([]);
const loading = ref(false);
const errorMsg = ref("");

const FLAG_BY_CODE = {
  JP: "https://flagcdn.com/w320/jp.png",
  TW: "https://flagcdn.com/w320/tw.png",
  KR: "https://flagcdn.com/w320/kr.png",
  US: "https://flagcdn.com/w320/us.png",
  CA: "https://flagcdn.com/w320/ca.png",
};

const CODE_BY_SVG_ID = {
  Japan: "JP", JPN: "JP", 日本: "JP",
  Taiwan: "TW", TWN: "TW", 臺灣: "TW", 台灣: "TW",
  Korea: "KR", "South Korea": "KR", "Republic of Korea": "KR", KOR: "KR", 韓國: "KR",
  United: "US", "United States": "US", "United States of America": "US", USA: "US", US: "US", America: "US", 美國: "US",
  CA: "CA", CAN: "CA", Canada: "CA", 加拿大: "CA",
};

const COUNTRY_NAMES = {
  JP: "Japan", TW: "Taiwan", KR: "Korea", US: "United States", CA: "Canada",
};

const getFlag = () =>
  FLAG_BY_CODE[selectedCode.value] || "https://flagcdn.com/w320/un.png";
const getFoods = () => countryFoods.value;

// ====== 標籤系統 ======
const allTags = ref([]);
const activeTags = ref([]);

async function fetchAllTags() {
  try {
    const res = await fetch("/api/tags");
    if (!res.ok) return;
    const data = await res.json();
    allTags.value = data.tags || [];
  } catch { /* ignore */ }
}

function toggleTag(tag) {
  const idx = activeTags.value.indexOf(tag);
  if (idx === -1) {
    activeTags.value.push(tag);
  } else {
    activeTags.value.splice(idx, 1);
  }
}

// ====== 搜尋 ======
const searchQuery = ref("");
const searchResults = ref([]);
const searchLoading = ref(false);
const showSearchResults = ref(false);
let _searchTimer = null;

function onSearchInput() {
  clearTimeout(_searchTimer);
  const q = searchQuery.value.trim();
  if (!q) {
    searchResults.value = [];
    showSearchResults.value = false;
    return;
  }
  _searchTimer = setTimeout(() => doSearch(q), 300);
}

async function doSearch(q) {
  if (!q) return;
  searchLoading.value = true;
  showSearchResults.value = true;
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    searchResults.value = data.results || [];
  } catch {
    searchResults.value = [];
  } finally {
    searchLoading.value = false;
  }
}

async function pickSearchResult(item) {
  searchQuery.value = "";
  searchResults.value = [];
  showSearchResults.value = false;

  selectedCode.value = item.code;
  selectedCountryName.value = item.countryName || COUNTRY_NAMES[item.code] || item.code;

  await fetchFoodsByCountry(item.code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) {
    await openFoodDetail(found);
  }
}

function closeSearchDropdown(e) {
  const el = document.querySelector(".search-bar");
  if (el && !el.contains(e.target)) {
    showSearchResults.value = false;
  }
}

// ====== 收藏（localStorage） ======
const FAVORITE_STORAGE_KEY = "worldmap_favorites_v1";
const favorites = ref([]);

function favKey(code, name) {
  return `${code || "??"}::${name}`;
}

function loadFavorites() {
  try {
    const raw = localStorage.getItem(FAVORITE_STORAGE_KEY);
    favorites.value = raw ? JSON.parse(raw) : [];
  } catch {
    favorites.value = [];
  }
}

function saveFavorites() {
  try {
    localStorage.setItem(FAVORITE_STORAGE_KEY, JSON.stringify(favorites.value));
  } catch { /* ignore */ }
}

function isFavorite(code, name) {
  if (!code || !name) return false;
  return favorites.value.includes(favKey(code, name));
}

function toggleFavorite(food) {
  if (!selectedCode.value || !food?.name) return;
  const key = favKey(selectedCode.value, food.name);
  const idx = favorites.value.indexOf(key);
  if (idx === -1) {
    favorites.value.push(key);
  } else {
    favorites.value.splice(idx, 1);
  }
  saveFavorites();
}

// 「只看收藏」開關 + tag 篩選 + 清單實際顯示的內容
const showFavoritesOnly = ref(false);
const displayFoods = computed(() => {
  let list = countryFoods.value;
  if (showFavoritesOnly.value) {
    list = list.filter((f) => isFavorite(selectedCode.value, f.name));
  }
  if (activeTags.value.length > 0) {
    list = list.filter((f) =>
      activeTags.value.some((t) => (f.tags || []).includes(t))
    );
  }
  return list;
});

// ====== 全域「我的收藏」面板 ======
const showFavPanel = ref(false);
const myFavorites = computed(() =>
  favorites.value.map((k) => {
    const [code, name] = k.split("::");
    return { code, name };
  })
);

async function gotoFavorite(item) {
  if (!item?.code || !item?.name) return;
  const code = item.code;

  selectedCode.value = code;
  selectedCountryName.value = COUNTRY_NAMES[code] || code;

  await fetchFoodsByCountry(code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) {
    await openFoodDetail(found);
  }
}

// ====== 清單容器高度量測 ======
const listEl = ref(null);
const listMaxHeight = ref(null);

function calcListMaxHeight() {
  const el = listEl.value;
  if (!el) return;
  const first = el.querySelector(".food-item");
  if (!first) return;

  const firstH = first.offsetHeight;
  const styles = getComputedStyle(el);
  const gap = parseFloat(styles.rowGap || styles.gap || "0");
  listMaxHeight.value = firstH * 3 + gap * 2;
}

// ====== URL 同步 ======
function updateUrl(code, food) {
  const params = new URLSearchParams();
  if (code) params.set("country", code);
  if (food) params.set("food", food);
  const qs = params.toString();
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  history.replaceState(null, "", url);
}

async function parseUrlAndNavigate() {
  const params = new URLSearchParams(window.location.search);
  const country = params.get("country");
  const food = params.get("food");
  if (!country) return;

  selectedCode.value = country.toUpperCase();
  selectedCountryName.value = COUNTRY_NAMES[selectedCode.value] || selectedCode.value;

  await fetchFoodsByCountry(selectedCode.value);

  if (food) {
    const decoded = decodeURIComponent(food);
    const found = countryFoods.value.find((f) => f.name === decoded);
    if (found) {
      await openFoodDetail(found);
    }
  }
}

// ====== 取得料理清單 ======
async function fetchFoodsByCountry(code) {
  if (!code) {
    loading.value = false;
    countryFoods.value = [];
    errorMsg.value = "這個國家的人們也熱愛美食，但我們還沒新增資料，歡迎之後再來～";
    listMaxHeight.value = null;
    return;
  }

  loading.value = true;
  errorMsg.value = "";
  countryFoods.value = [];
  listMaxHeight.value = null;

  try {
    const res = await fetch(`/api/foods/${code}`);
    if (!res.ok) {
      if (res.status === 404) {
        errorMsg.value = "目前尚未為這個國家設定代表美食，之後再來看看～";
        return;
      }
      throw new Error("讀取料理清單失敗");
    }
    const data = await res.json();
    countryFoods.value = (data.foods || []).map((f) => ({
      name: f.name,
      img: f.img,
      likes: f.likes ?? 0,
      tags: f.tags || [],
    }));
    if (!countryFoods.value.length) {
      errorMsg.value = "這個國家目前還沒有新增美食資料。";
    }

    await nextTick();
    calcListMaxHeight();
  } catch (e) {
    console.error(e);
    errorMsg.value = e.message || "資料載入失敗";
  } finally {
    loading.value = false;
  }
}

// ====== TOP 5 人氣美食 ======
const topFoods = ref([]);
const topLoading = ref(false);
const topError = ref("");
const showTopPanelMobile = ref(false);

async function fetchTopFoods() {
  try {
    topLoading.value = true;
    topError.value = "";
    const res = await fetch("/api/top-foods");
    if (!res.ok) throw new Error("讀取人氣美食失敗");
    const data = await res.json();
    topFoods.value = data.foods || [];
  } catch (e) {
    console.error(e);
    topError.value = e.message || "讀取人氣美食失敗";
  } finally {
    topLoading.value = false;
  }
}

async function jumpToTopFood(item) {
  if (!item?.code || !item?.name) return;

  const code = item.code;
  selectedCode.value = code;
  selectedCountryName.value = item.countryName || COUNTRY_NAMES[code] || code;

  await fetchFoodsByCountry(code);

  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) {
    await openFoodDetail(found);
  }
}

onMounted(() => {
  // 地圖載入 + svgPanZoom
  if (!svgObj.value) return;

  svgObj.value.addEventListener("load", () => {
    const svgDoc = svgObj.value.contentDocument;
    if (!svgDoc) return;
    const svgEl = svgDoc.querySelector("svg");
    if (!svgEl) return;

    panzoom.value = svgPanZoom(svgEl, {
      zoomEnabled: true,
      controlIconsEnabled: false,
      panEnabled: true,
      minZoom: 1,
      maxZoom: 10,
      fit: true,
      center: true,
    });

    const countries = svgDoc.querySelectorAll("path");

    countries.forEach((p) => {
      p.style.cursor = "pointer";

      p.addEventListener("mouseenter", () => {
        p.style.fill = "#88b7deff";
      });
      p.addEventListener("mouseleave", () => {
        p.style.fill = "#ececec";
      });

      p.addEventListener("click", async () => {
        const countryNameRaw =
          p.getAttribute("name") ||
          p.getAttribute("id") ||
          (p.getAttribute("class")?.split(" ")[0]) ||
          "Unknown";

        selectedCountryName.value = countryNameRaw;
        const code = CODE_BY_SVG_ID[countryNameRaw] || null;
        selectedCode.value = code;

        updateUrl(code, null);
        await fetchFoodsByCountry(code);

        const bbox = p.getBBox();
        const cx = bbox.x + bbox.width / 2;
        const cy = bbox.y + bbox.height / 2;

        panzoom.value.zoomAtPoint(4, { x: cx, y: cy });
        panzoom.value.center();
        panzoom.value.pan({ x: -(cx * 3), y: -(cy * 3) });
      });
    });
  });

  // 初始化收藏 & TOP5 & Tags
  loadFavorites();
  fetchTopFoods();
  fetchAllTags();

  // 解析 URL 參數自動導航
  parseUrlAndNavigate();

  // 點擊空白處關閉搜尋下拉
  document.addEventListener("click", closeSearchDropdown);
});

// ====== 留言 token localStorage ======
const COMMENT_TOKEN_KEY = "worldmap_comment_tokens_v1";

function loadCommentTokens() {
  try {
    const raw = localStorage.getItem(COMMENT_TOKEN_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveCommentToken(commentId, token) {
  const tokens = loadCommentTokens();
  tokens[commentId] = token;
  try {
    localStorage.setItem(COMMENT_TOKEN_KEY, JSON.stringify(tokens));
  } catch { /* ignore */ }
}

function getCommentToken(commentId) {
  return loadCommentTokens()[commentId] || null;
}

function removeCommentToken(commentId) {
  const tokens = loadCommentTokens();
  delete tokens[commentId];
  try {
    localStorage.setItem(COMMENT_TOKEN_KEY, JSON.stringify(tokens));
  } catch { /* ignore */ }
}

// 地圖歸位
const resetMap = () => {
  if (panzoom.value) panzoom.value.reset();
  selectedCountryName.value = null;
  selectedCode.value = null;
  countryFoods.value = [];
  errorMsg.value = "";
  listMaxHeight.value = null;
  showFavoritesOnly.value = false;
  activeTags.value = [];
  updateUrl(null, null);
};

// ===== 食物介紹 Modal =====
const selectedFood = ref(null);
const showFoodModal = ref(false);

// Like & Comment 狀態
const likesCount = ref(0);
const likeLoading = ref(false);
const comments = ref([]);
const posting = ref(false);
const newUser = ref("");
const newText = ref("");
const commentError = ref("");

const isCurrentFoodFav = computed(() => {
  if (!selectedFood.value || !selectedCode.value) return false;
  return isFavorite(selectedCode.value, selectedFood.value.name);
});

const googleMapUrl = computed(() => {
  if (!selectedFood.value) return "https://www.google.com/maps";
  const qCountry = selectedCountryName.value || selectedCode.value || "";
  const q = encodeURIComponent(`${qCountry} ${selectedFood.value.name} 美食`);
  return `https://www.google.com/maps/search/${q}`;
});

function syncListLikes() {
  if (!selectedFood.value) return;
  const idx = countryFoods.value.findIndex(
    (f) => f.name === selectedFood.value.name
  );
  if (idx !== -1) {
    countryFoods.value[idx] = {
      ...countryFoods.value[idx],
      likes: likesCount.value,
    };
  }
}

async function fetchLikes() {
  if (!selectedCode.value || !selectedFood.value) return;
  const r = await fetch(
    `/api/food/${selectedCode.value}/${encodeURIComponent(selectedFood.value.name)}/likes`
  );
  const data = await r.json();
  likesCount.value = data.likes ?? 0;
  syncListLikes();
}

async function doLike() {
  if (!selectedCode.value || !selectedFood.value || likeLoading.value) return;
  likeLoading.value = true;
  try {
    const r = await fetch(
      `/api/food/${selectedCode.value}/${encodeURIComponent(selectedFood.value.name)}/like`,
      { method: "POST" }
    );
    const data = await r.json();
    if (Number.isFinite(data.likes)) {
      likesCount.value = data.likes;
      syncListLikes();
    }
  } finally {
    likeLoading.value = false;
  }
}

async function fetchComments() {
  if (!selectedCode.value || !selectedFood.value) return;
  const r = await fetch(
    `/api/food/${selectedCode.value}/${encodeURIComponent(selectedFood.value.name)}/comments`
  );
  const data = await r.json();
  comments.value = data.comments || [];
}

async function submitComment() {
  if (!selectedCode.value || !selectedFood.value) return;
  commentError.value = "";
  const payload = {
    user: newUser.value || "匿名",
    text: (newText.value || "").trim(),
  };
  if (!payload.text) return;
  try {
    posting.value = true;
    const r = await fetch(
      `/api/food/${selectedCode.value}/${encodeURIComponent(selectedFood.value.name)}/comments`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    const created = await r.json();
    if (!r.ok) {
      commentError.value = created.error || "留言失敗";
      return;
    }
    // Save delete token
    if (created.delete_token) {
      saveCommentToken(created.id, created.delete_token);
    }
    comments.value.unshift(created);
    newText.value = "";
  } catch {
    commentError.value = "留言失敗，請稍後再試";
  } finally {
    posting.value = false;
  }
}

async function deleteComment(comment) {
  if (!selectedCode.value || !selectedFood.value) return;
  const token = getCommentToken(comment.id);
  if (!token) return;
  if (!confirm("確定要刪除這則留言嗎？")) return;

  try {
    const r = await fetch(
      `/api/food/${selectedCode.value}/${encodeURIComponent(selectedFood.value.name)}/comments/${comment.id}`,
      {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      }
    );
    if (r.ok) {
      comments.value = comments.value.filter((c) => c.id !== comment.id);
      removeCommentToken(comment.id);
    }
  } catch { /* ignore */ }
}

async function likeComment(comment) {
  if (!selectedCode.value || !selectedFood.value) return;
  try {
    const r = await fetch(
      `/api/food/${selectedCode.value}/${encodeURIComponent(selectedFood.value.name)}/comments/${comment.id}/like`,
      { method: "POST" }
    );
    const data = await r.json();
    if (Number.isFinite(data.likes)) {
      comment.likes = data.likes;
    }
  } catch { /* ignore */ }
}

async function openFoodDetail(food) {
  if (!selectedCode.value) return;

  try {
    const res = await fetch(
      `/api/food/${selectedCode.value}/${encodeURIComponent(food.name)}`
    );
    if (!res.ok) throw new Error("讀取料理介紹失敗");
    const detail = await res.json();
    selectedFood.value = {
      name: detail.name,
      img: detail.img,
      desc: detail.desc || "這道料理還沒有詳細介紹。",
      tags: detail.tags || [],
    };
  } catch (e) {
    console.error(e);
    selectedFood.value = { ...food, desc: "這道料理還沒有詳細介紹。" };
  }

  updateUrl(selectedCode.value, food.name);
  commentError.value = "";
  await Promise.all([fetchLikes(), fetchComments()]);
  showFoodModal.value = true;
}

const closeFoodDetail = () => {
  showFoodModal.value = false;
  updateUrl(selectedCode.value, null);
};

// ====== 分享功能 ======
function getShareUrl() {
  if (!selectedCode.value || !selectedFood.value) return window.location.href;
  const params = new URLSearchParams();
  params.set("country", selectedCode.value);
  params.set("food", selectedFood.value.name);
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
}

async function shareFood() {
  const url = getShareUrl();
  const title = `${selectedFood.value?.name} - 世界美食地圖`;

  if (navigator.share) {
    try {
      await navigator.share({ title, url });
      return;
    } catch { /* user cancelled or not supported */ }
  }

  // Fallback: copy to clipboard
  try {
    await navigator.clipboard.writeText(url);
    alert("已複製分享連結！");
  } catch {
    // Final fallback
    prompt("複製這個連結來分享：", url);
  }
}

function shareTo(platform) {
  const url = encodeURIComponent(getShareUrl());
  const title = encodeURIComponent(`${selectedFood.value?.name} - 世界美食地圖`);
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
  <div class="world-page" @click="showSearchResults = false">
    <!-- 搜尋列 -->
    <div class="search-bar" @click.stop>
      <input
        type="text"
        class="search-input"
        placeholder="搜尋料理、標籤..."
        v-model="searchQuery"
        @input="onSearchInput"
        @focus="if (searchResults.length) showSearchResults = true"
      />
      <div class="search-dropdown" v-if="showSearchResults">
        <div v-if="searchLoading" class="search-status">搜尋中...</div>
        <div v-else-if="!searchResults.length" class="search-status">沒有找到結果</div>
        <div
          v-else
          class="search-result-item"
          v-for="item in searchResults"
          :key="item.code + '_' + item.name"
          @click="pickSearchResult(item)"
        >
          <img class="search-thumb" :src="item.img" :alt="item.name" />
          <div class="search-info">
            <span class="search-name">{{ item.name }}</span>
            <span class="search-country">{{ item.countryName }}</span>
            <div class="search-tags" v-if="item.tags && item.tags.length">
              <span class="tag-badge small" v-for="t in item.tags" :key="t">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <button class="reset-btn" @click="resetMap">返回地圖</button>

    <!-- 地圖 + 左側浮動卡片 -->
    <div class="map-stage">
      <object
        ref="svgObj"
        data="/world.svg"
        type="image/svg+xml"
        class="world-map"
      />

      <!-- 左側美食清單卡片 -->
      <transition name="slide">
        <div class="food-card" v-if="selectedCountryName">
          <div class="food-header">
            <img class="flag" :src="getFlag()" />
            <h2>{{ selectedCountryName }}</h2>
          </div>

          <h3 class="section-title">代表料理</h3>

          <div v-if="loading" class="loading-text">資料載入中...</div>
          <div v-else-if="errorMsg" class="error-text">
            {{ errorMsg }}
          </div>

          <!-- 收藏篩選 + Tag chips -->
          <div
            class="filter-row"
            v-else-if="getFoods().length"
          >
            <div class="filter-top">
              <button
                class="fav-filter"
                :class="{ active: showFavoritesOnly }"
                @click="showFavoritesOnly = !showFavoritesOnly"
              >
                只看收藏
              </button>
            </div>
            <div class="tag-chips" v-if="allTags.length">
              <button
                class="tag-chip"
                v-for="tag in allTags"
                :key="tag"
                :class="{ active: activeTags.includes(tag) }"
                @click="toggleTag(tag)"
              >
                {{ tag }}
              </button>
            </div>
          </div>

          <!-- 清單 -->
          <div
            class="food-list"
            v-if="getFoods().length"
            ref="listEl"
            :style="listMaxHeight ? { maxHeight: listMaxHeight + 'px' } : {}"
          >
            <div
              class="food-item"
              v-for="f in displayFoods"
              :key="f.name"
              @click="openFoodDetail(f)"
            >
              <div class="food-img-wrap">
                <img
                  class="food-img"
                  :src="f.img"
                  :alt="f.name"
                  loading="lazy"
                />
                <div class="food-like-badge" title="讚數">
                  👍 {{ (f.likes ?? 0).toLocaleString() }}
                </div>
              </div>

              <div class="food-name-row">
                <p class="food-name">{{ f.name }}</p>
                <button
                  class="fav-icon"
                  :class="{ active: isFavorite(selectedCode, f.name) }"
                  @click.stop="toggleFavorite(f)"
                >
                  {{ isFavorite(selectedCode, f.name) ? "❤️" : "🤍" }}
                </button>
              </div>

              <!-- Tag badges on card -->
              <div class="food-tags" v-if="f.tags && f.tags.length">
                <span class="tag-badge" v-for="t in f.tags" :key="t">{{ t }}</span>
              </div>
            </div>
          </div>

          <p v-else class="no-food">
            這個國家目前還沒有新增美食資料。
          </p>
        </div>
      </transition>
    </div>

    <!-- 右上角：我的收藏 toggle -->
    <button
      class="fav-global-toggle"
      @click="showFavPanel = !showFavPanel"
    >
      我的收藏（{{ myFavorites.length }}）
    </button>

    <!-- 右側：我的收藏列表 -->
    <div v-if="showFavPanel" class="fav-global-panel">
      <h3>我的收藏</h3>
      <ul class="fav-global-list">
        <li
          v-for="item in myFavorites"
          :key="item.code + '::' + item.name"
          class="fav-global-item"
          @click="gotoFavorite(item)"
        >
          <span class="fav-dot">❤️</span>
          <span class="fav-name">{{ item.name }}</span>
          <span class="fav-country">{{ item.code }}</span>
        </li>
        <li v-if="!myFavorites.length" class="fav-global-empty">
          還沒有收藏任何料理
        </li>
      </ul>
    </div>

    <!-- 右下角：本週人氣美食 TOP 5 -->
    <div class="top-panel" :class="{ 'show-mobile': showTopPanelMobile }">
      <h3>本週人氣美食 TOP 5</h3>
      <div v-if="topLoading" class="top-status">載入中...</div>
      <div v-else-if="topError" class="top-status top-error">
        {{ topError }}
      </div>
      <ul v-else class="top-list">
        <li
          v-for="(item, idx) in topFoods"
          :key="item.code + '_' + item.name"
          class="top-item"
          @click="jumpToTopFood(item)"
        >
          <span class="rank">{{ idx + 1 }}</span>
          <span class="top-name">{{ item.name }}</span>
          <span class="top-country">
            {{ item.countryName || item.code }}
          </span>
          <span class="top-score" v-if="item.score != null">
            ★ {{ Number(item.score).toFixed(1) }}
          </span>
        </li>
        <li v-if="!topFoods.length" class="top-status">
          目前還沒有統計資料
        </li>
      </ul>
    </div>

    <!-- 手機版 TOP5 toggle 按鈕 -->
    <button
      class="top-toggle-mobile"
      @click="showTopPanelMobile = !showTopPanelMobile"
    >
      🏆 TOP5
    </button>

    <!-- 食物介紹 Modal -->
    <div class="modal-mask" v-if="showFoodModal" @click="closeFoodDetail">
      <div class="modal-content" @click.stop>
        <button class="close-btn" @click="closeFoodDetail">✕</button>
        <img class="modal-food-img" :src="selectedFood?.img" />
        <h2>{{ selectedFood?.name }}</h2>

        <!-- Modal tag badges -->
        <div class="modal-tags" v-if="selectedFood?.tags?.length">
          <span class="tag-badge" v-for="t in selectedFood.tags" :key="t">{{ t }}</span>
        </div>

        <p class="food-desc">
          {{ selectedFood?.desc || "這道料理還沒有詳細介紹。" }}
        </p>

        <!-- 按讚 / 收藏 -->
        <div class="like-row">
          <div class="like-main">
            <button
              class="like-btn"
              :disabled="likeLoading"
              @click.stop="doLike"
            >
              👍 按讚
            </button>
            <span class="likes">已獲得 {{ likesCount }} 個讚</span>

            <button
              class="fav-btn"
              :class="{ active: isCurrentFoodFav }"
              @click.stop="toggleFavorite(selectedFood)"
            >
              {{ isCurrentFoodFav ? "❤️ 已收藏" : "🤍 收藏" }}
            </button>
          </div>

          <!-- Google Map 連結 -->
          <a
            class="map-link"
            :href="googleMapUrl"
            target="_blank"
            rel="noopener"
            @click.stop
          >
            在附近找這道料理
          </a>
        </div>

        <!-- 分享列 -->
        <div class="share-row">
          <button class="share-btn" @click.stop="shareFood">📤 分享</button>
          <button class="share-social fb" @click.stop="shareTo('facebook')">Facebook</button>
          <button class="share-social tw" @click.stop="shareTo('twitter')">Twitter</button>
          <button class="share-social line" @click.stop="shareTo('line')">LINE</button>
        </div>

        <div class="comment-editor" @click.stop>
          <input
            v-model="newUser"
            class="comment-input name"
            type="text"
            placeholder="你的名字（可留空，預設匿名）"
          />
          <textarea
            v-model="newText"
            class="comment-input text"
            rows="3"
            placeholder="寫下你的看法..."
          ></textarea>
          <div class="comment-error" v-if="commentError">{{ commentError }}</div>
          <button class="submit-btn" :disabled="posting" @click="submitComment">
            送出留言
          </button>
        </div>

        <div class="comment-list" v-if="comments.length">
          <h3 style="margin: 10px 0 6px">留言</h3>
          <div class="comment-item" v-for="c in comments" :key="c.id">
            <div class="meta">
              <strong>{{ c.user || "匿名" }}</strong>
              <span> · {{ new Date(c.ts * 1000).toLocaleString() }}</span>
            </div>
            <p class="text">{{ c.text }}</p>
            <div class="comment-actions">
              <button class="comment-like-btn" @click.stop="likeComment(c)">
                👍 {{ c.likes || 0 }}
              </button>
              <button
                class="comment-delete-btn"
                v-if="getCommentToken(c.id)"
                @click.stop="deleteComment(c)"
              >
                刪除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.world-page {
  position: relative;
}

/* ===== 搜尋列 ===== */
.search-bar {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: 340px;
  z-index: 55;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
  outline: none;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #2563eb;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
  max-height: 320px;
  overflow-y: auto;
  padding: 6px 0;
}

.search-status {
  padding: 12px 16px;
  font-size: 13px;
  color: #6b7280;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  cursor: pointer;
}

.search-result-item:hover {
  background: #eff6ff;
}

.search-thumb {
  width: 48px;
  height: 36px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.search-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.search-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.search-country {
  font-size: 12px;
  color: #6b7280;
}

.search-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

/* ===== Tag badge ===== */
.tag-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
}

.tag-badge.small {
  padding: 1px 6px;
  font-size: 10px;
}

/* ===== Tag chips (filter) ===== */
.tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.tag-chip {
  border: none;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  cursor: pointer;
  background: #f3f4f6;
  color: #374151;
}

.tag-chip.active {
  background: #2563eb;
  color: #fff;
}

/* Food card tags */
.food-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0 10px 6px;
}

/* Modal tags */
.modal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 4px 0 8px;
}

/* ===== Filter row ===== */
.filter-row {
  margin-top: 4px;
  margin-bottom: 6px;
}

.filter-top {
  display: flex;
  justify-content: flex-end;
}

/* 地圖區 */
.map-stage {
  position: relative;
  width: 100%;
  max-width: 2000px;
  margin: 0 auto;
}

.world-map {
  width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}

/* 左上角的返回地圖按鈕 */
.reset-btn {
  position: fixed;
  top: 20px;
  right: 40px;
  z-index: 50;
}

/* 左側整個卡片容器 */
.food-card {
  position: absolute;
  top: 46px;
  left: 40px;
  width: 260px;
  max-height: calc(100vh - 120px);
  overflow: hidden;

  padding: 14px 18px 20px;
  background: #fff;
  color: #000;
  border-radius: 16px;
  box-shadow: 0 0 20px rgba(15, 23, 42, 0.2);
  z-index: 20;
}

.food-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}

.food-header h2 {
  margin: 0;
  font-size: 22px;
}

.section-title {
  margin: 4px 0 6px;
  font-size: 16px;
}

.flag {
  width: 32px;
  height: 24px;
  border-radius: 4px;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.1);
}

/* loading / error */
.loading-text,
.error-text {
  margin: 8px 0;
  font-size: 14px;
}
.error-text {
  color: #dc2626;
}

/* 收藏篩選 */
.fav-filter {
  border: none;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  cursor: pointer;
  background: #e5e7eb;
  color: #374151;
}
.fav-filter.active {
  background: #f97316;
  color: #fff;
}

/* ===== 清單 ===== */
.food-list {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  row-gap: 16px;

  overflow-y: auto;
  padding-right: 6px;
  scroll-snap-type: y proximity;
  position: relative;
}

.food-list::after {
  content: "";
  position: sticky;
  bottom: 0;
  height: 18px;
  margin-top: -18px;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.06));
  pointer-events: none;
}

/* 單一卡片 */
.food-item {
  scroll-snap-align: start;
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  overflow: visible;
  padding-bottom: 6px;
}

/* 圖片 + 讚數徽章 */
.food-img-wrap {
  position: relative;
  width: 100%;
}
.food-img {
  width: 100%;
  height: auto;
  display: block;
}
.food-like-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  backdrop-filter: blur(2px);
}

.food-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px 4px 10px;
}

.food-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.fav-icon {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  opacity: 0.8;
}
.fav-icon.active {
  opacity: 1;
}

.no-food {
  font-size: 14px;
  color: #4b5563;
  margin-top: 10px;
}

/* ===== 全域「我的收藏」按鈕 / 面板 ===== */
.fav-global-toggle {
  position: fixed;
  left: 50%;
  bottom: 40px;
  transform: translateX(-50%);
  padding: 8px 18px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  background: #f97316;
  color: #fff;
  font-size: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.18);
  z-index: 30;
}

.fav-global-panel {
  position: fixed;
  left: 50%;
  bottom: 90px;
  transform: translateX(-50%);
  width: 260px;
  background: rgba(255, 255, 255, 0.97);
  border-radius: 18px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.2);
  padding: 10px 14px 12px;
  z-index: 30;
  font-size: 14px;
}
.fav-global-panel h3 {
  margin: 0 0 6px;
  font-size: 15px;
}
.fav-global-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 220px;
  overflow-y: auto;
}
.fav-global-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 2px;
  border-radius: 8px;
  cursor: pointer;
}
.fav-global-item:hover {
  background: #eff6ff;
}
.fav-dot {
  width: 18px;
  text-align: center;
}
.fav-name {
  flex: 1;
}
.fav-country {
  font-size: 12px;
  color: #6b7280;
}
.fav-global-empty {
  font-size: 13px;
  color: #6b7280;
}

/* ===== TOP 5 人氣美食 ===== */
.top-panel {
  position: fixed;
  right: 40px;
  bottom: 40px;
  width: 260px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 18px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
  padding: 12px 14px;
  z-index: 30;
  font-size: 14px;
}

.top-panel h3 {
  font-size: 15px;
  margin-bottom: 6px;
}

.top-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 260px;
  overflow-y: auto;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 2px;
  border-radius: 8px;
  cursor: pointer;
}
.top-item:hover {
  background: #eff6ff;
}

.rank {
  width: 18px;
  text-align: center;
  font-weight: 700;
  color: #2563eb;
}

.top-name {
  flex: 1;
}

.top-country {
  font-size: 12px;
  color: #6b7280;
}

.top-score {
  font-size: 12px;
  color: #f97316;
}

.top-status {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
.top-error {
  color: #dc2626;
}

/* 手機版 TOP5 toggle 按鈕 — 桌面版隱藏 */
.top-toggle-mobile {
  display: none;
  position: fixed;
  right: 12px;
  bottom: 12px;
  z-index: 31;
  padding: 10px 16px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  background: #2563eb;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.2);
  min-width: 44px;
  min-height: 44px;
}

/* ===== Modal ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
}

.modal-content {
  width: 480px;
  max-width: calc(100% - 40px);
  max-height: calc(100% - 40px);
  overflow-y: auto;
  background: #fff;
  border-radius: 18px;
  padding: 18px 22px 22px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 12px;
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

.modal-food-img {
  width: 100%;
  max-height: 260px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 12px;
}

.food-desc {
  margin: 8px 0 6px;
  line-height: 1.6;
  color: #4b5563;
}

/* 按讚 + 收藏同一行；Google Map 另外一行 */
.like-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 8px 0 6px;
}
.like-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.like-btn,
.submit-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
  background: #2563eb;
  color: #fff;
  font-size: 14px;
}
.like-btn[disabled],
.submit-btn[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}
.likes {
  font-size: 14px;
  color: #333;
}

/* 收藏按鈕（modal） */
.fav-btn {
  border: none;
  border-radius: 999px;
  padding: 6px 10px;
  cursor: pointer;
  background: #e5e7eb;
  color: #111827;
  font-size: 13px;
}
.fav-btn.active {
  background: #f97316;
  color: #fff;
}

/* Google Map 連結 */
.map-link {
  display: inline-flex;
  width: 100%;
  justify-content: center;
  margin-top: 2px;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 999px;
  text-decoration: none;
  background: #10b981;
  color: #fff;
  box-sizing: border-box;
}

/* ===== 分享列 ===== */
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

/* ===== Comment ===== */
.comment-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 10px 0 16px;
}
.comment-input {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
  box-sizing: border-box;
}

.comment-error {
  color: #dc2626;
  font-size: 13px;
}

.comment-list .comment-item {
  padding: 10px 0;
  border-top: 1px dashed #e5e7eb;
}
.comment-list .comment-item .meta {
  font-size: 13px;
  color: #6b7280;
}
.comment-list .comment-item .text {
  margin: 4px 0 0;
  white-space: pre-wrap;
}

.comment-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

.comment-like-btn {
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  font-size: 12px;
  color: #374151;
  min-height: 28px;
}

.comment-like-btn:hover {
  background: #e5e7eb;
}

.comment-delete-btn {
  border: none;
  background: #fee2e2;
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  font-size: 12px;
  color: #dc2626;
  min-height: 28px;
}

.comment-delete-btn:hover {
  background: #fecaca;
}
</style>
