<script setup>
import { ref, onMounted, nextTick, computed } from "vue";
import svgPanZoom from "svg-pan-zoom";
import { useFavorites } from "../composables/useFavorites.js";
import { useAuth } from "../composables/useAuth.js";

import SearchBar from "./SearchBar.vue";
import FoodListPanel from "./FoodListPanel.vue";
import FoodDetailModal from "./FoodDetailModal.vue";
import FavoritesPanel from "./FavoritesPanel.vue";
import TopFoodsPanel from "./TopFoodsPanel.vue";
import AuthModal from "./AuthModal.vue";
import UserMenu from "./UserMenu.vue";
import MyCommentsModal from "./MyCommentsModal.vue";
import ProfileModal from "./ProfileModal.vue";
import SearchResultsPage from "./SearchResultsPage.vue";

// === Auth ===
const { isLoggedIn, checkAuth } = useAuth();
const showAuthModal   = ref(false);
const showMyComments  = ref(false);
const showProfile     = ref(false);

// === Search Results ===
const showSearchResults  = ref(false);
const searchResultsQuery = ref("");
const searchResultsData  = ref([]);

function handleSearchOpen({ query, results }) {
  searchResultsQuery.value = query;
  searchResultsData.value  = results || [];
  showSearchResults.value  = true;
}

async function handleSearchPick(item) {
  selectedCode.value = item.code;
  selectedCountryName.value = item.countryName || COUNTRY_NAMES[item.code] || item.code;
  await fetchFoodsByCountry(item.code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) await openFoodDetail(found);
}

// === SVG map refs ===
const svgObj = ref(null);
const panzoom = ref(null);

// === Core state ===
const selectedCountryName = ref(null);
const selectedCode = ref(null);
const countryFoods = ref([]);
const loading = ref(false);
const errorMsg = ref("");
const listMaxHeight = ref(null);

// === Constants ===
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

// === Tag system ===
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
  if (idx === -1) activeTags.value.push(tag);
  else activeTags.value.splice(idx, 1);
}

// === Favorites composable ===
const { favorites, myFavorites, loadFavorites, loadFavoriteLists, isFavorite, toggleFavorite, migrateLocalStorage } = useFavorites();

const showFavoritesOnly = ref(false);
const showFavPanel = ref(false);

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

// === Auth events ===
async function handleAuthed() {
  await migrateLocalStorage();
  await loadFavorites();
  await loadFavoriteLists();
}

async function handleLoggedOut() {
  favorites.value = [];
  showFavPanel.value = false;
  showMyComments.value = false;
}

function handleNeedAuth() {
  showAuthModal.value = true;
}

// === URL sync ===
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
    if (found) await openFoodDetail(found);
  }
}

// === Fetch foods ===
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
  } catch (e) {
    console.error(e);
    errorMsg.value = e.message || "資料載入失敗";
  } finally {
    loading.value = false;
  }
}

// === Food detail modal ===
const selectedFood = ref(null);
const showFoodModal = ref(false);
const likesCount = ref(0);
const likeLoading = ref(false);

const isCurrentFoodFav = computed(() => {
  if (!selectedFood.value || !selectedCode.value) return false;
  return isFavorite(selectedCode.value, selectedFood.value.name);
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
  await fetchLikes();
  showFoodModal.value = true;
}

function closeFoodDetail() {
  showFoodModal.value = false;
  updateUrl(selectedCode.value, null);
}

function handleToggleFavoriteModal() {
  if (!isLoggedIn.value) {
    showAuthModal.value = true;
    return;
  }
  if (selectedFood.value) {
    toggleFavorite(selectedCode.value, selectedFood.value.name);
  }
}

function handleToggleFavoriteList(food) {
  if (!isLoggedIn.value) {
    showAuthModal.value = true;
    return;
  }
  toggleFavorite(selectedCode.value, food.name);
}

// === Navigation helpers ===
async function gotoFavorite(item) {
  if (!item?.code || !item?.name) return;
  selectedCode.value = item.code;
  selectedCountryName.value = COUNTRY_NAMES[item.code] || item.code;
  await fetchFoodsByCountry(item.code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) await openFoodDetail(found);
}

async function jumpToTopFood(item) {
  if (!item?.code || !item?.name) return;
  selectedCode.value = item.code;
  selectedCountryName.value = item.countryName || COUNTRY_NAMES[item.code] || item.code;
  await fetchFoodsByCountry(item.code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) await openFoodDetail(found);
}

// === Reset map ===
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

// === SVG 初始化（獨立函式，避免非同步競態） ===
function setupSvg() {
  const svgDoc = svgObj.value?.contentDocument;
  if (!svgDoc) return;
  const svgEl = svgDoc.querySelector("svg");
  if (!svgEl) return;

  // 避免重複初始化
  if (panzoom.value) return;

  panzoom.value = svgPanZoom(svgEl, {
    zoomEnabled: true,
    controlIconsEnabled: false,
    panEnabled: true,
    minZoom: 1,
    maxZoom: 10,
    fit: true,
    center: true,
  });

  svgDoc.querySelectorAll("path").forEach((p) => {
    p.style.cursor = "pointer";
    p.addEventListener("mouseenter", () => { p.style.fill = "#88b7deff"; });
    p.addEventListener("mouseleave", () => { p.style.fill = "#ececec"; });

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
}

// === Mount ===
onMounted(async () => {
  // ★ 先同步附上 SVG load 監聽器，避免 await 期間 SVG 已載完而錯過事件
  if (svgObj.value) {
    svgObj.value.addEventListener("load", setupSvg);
    // 若 SVG 已從快取載入完成，直接執行
    if (svgObj.value.contentDocument?.querySelector?.("svg")) {
      setupSvg();
    }
  }

  // 再做非同步 auth 操作
  const authed = await checkAuth();
  if (authed) {
    await migrateLocalStorage();
    await loadFavorites();
    await loadFavoriteLists();
  }

  fetchAllTags();
  parseUrlAndNavigate();
});
</script>

<template>
  <div class="world-page">
    <!-- 頂部導覽列 -->
    <div class="top-bar">
      <div class="top-bar-left">
        <span class="app-logo">🌍</span>
        <span class="app-title">World Food Explorer</span>
      </div>
      <div class="top-bar-center">
        <SearchBar @pick="handleSearchPick" @search="handleSearchOpen" />
      </div>
      <div class="top-bar-right">
        <button class="reset-btn" @click="resetMap">↩ 返回</button>
        <UserMenu
          @open-auth="showAuthModal = true"
          @logged-out="handleLoggedOut"
          @open-my-comments="showMyComments = true"
          @open-profile="showProfile = true"
        />
      </div>
    </div>

    <div class="map-stage">
      <object
        ref="svgObj"
        data="/world.svg"
        type="image/svg+xml"
        class="world-map"
      />

      <transition name="slide">
        <FoodListPanel
          v-if="selectedCountryName"
          :country-name="selectedCountryName"
          :code="selectedCode"
          :flag-url="getFlag()"
          :foods="displayFoods"
          :all-foods="countryFoods"
          :loading="loading"
          :error-msg="errorMsg"
          :all-tags="allTags"
          :active-tags="activeTags"
          :show-favorites-only="showFavoritesOnly"
          :favorites="favorites"
          :is-logged-in="isLoggedIn"
          :list-max-height="listMaxHeight"
          @toggle-fav-filter="showFavoritesOnly = !showFavoritesOnly"
          @toggle-tag="toggleTag"
          @toggle-favorite="handleToggleFavoriteList"
          @open-food="openFoodDetail"
          @update:list-max-height="(v) => (listMaxHeight = v)"
        />
      </transition>
    </div>

    <FavoritesPanel
      :show="showFavPanel"
      :is-logged-in="isLoggedIn"
      @toggle-panel="showFavPanel = !showFavPanel"
      @goto="gotoFavorite"
      @need-auth="handleNeedAuth"
    />

    <TopFoodsPanel @jump="jumpToTopFood" />

    <FoodDetailModal
      :show="showFoodModal"
      :food="selectedFood"
      :code="selectedCode"
      :country-name="selectedCountryName"
      :likes-count="likesCount"
      :like-loading="likeLoading"
      :is-favorite="isCurrentFoodFav"
      :is-logged-in="isLoggedIn"
      @close="closeFoodDetail"
      @like="doLike"
      @toggle-favorite="handleToggleFavoriteModal"
      @need-auth="handleNeedAuth"
    />

    <AuthModal
      :show="showAuthModal"
      @close="showAuthModal = false"
      @authed="handleAuthed"
    />

    <MyCommentsModal
      :show="showMyComments"
      @close="showMyComments = false"
      @goto="gotoFavorite"
    />

    <ProfileModal
      :show="showProfile"
      @close="showProfile = false"
      @goto="gotoFavorite"
    />

    <SearchResultsPage
      :show="showSearchResults"
      :initial-query="searchResultsQuery"
      :initial-results="searchResultsData"
      @close="showSearchResults = false"
      @pick="handleSearchPick"
    />
  </div>
</template>

<style>
/* WorldMap 的全域 style 已移至 src/style.css 的 top-bar / world-page */
</style>
