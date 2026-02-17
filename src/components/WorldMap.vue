<script setup>
import { ref, onMounted, nextTick, computed } from "vue";
import svgPanZoom from "svg-pan-zoom";
import { useFavorites } from "../composables/useFavorites.js";

import SearchBar from "./SearchBar.vue";
import FoodListPanel from "./FoodListPanel.vue";
import FoodDetailModal from "./FoodDetailModal.vue";
import FavoritesPanel from "./FavoritesPanel.vue";
import TopFoodsPanel from "./TopFoodsPanel.vue";

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
const { favorites, myFavorites, loadFavorites, isFavorite, toggleFavorite } = useFavorites();

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
  if (selectedFood.value) {
    toggleFavorite(selectedCode.value, selectedFood.value.name);
  }
}

function handleToggleFavoriteList(food) {
  toggleFavorite(selectedCode.value, food.name);
}

// === Navigation helpers ===
async function handleSearchPick(item) {
  selectedCode.value = item.code;
  selectedCountryName.value = item.countryName || COUNTRY_NAMES[item.code] || item.code;
  await fetchFoodsByCountry(item.code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) await openFoodDetail(found);
}

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

// === Mount ===
onMounted(() => {
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
  });

  loadFavorites();
  fetchAllTags();
  parseUrlAndNavigate();
});
</script>

<template>
  <div class="world-page">
    <SearchBar @pick="handleSearchPick" />

    <button class="reset-btn" @click="resetMap">返回地圖</button>

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
      :favorites="favorites"
      :my-favorites="myFavorites"
      :show="showFavPanel"
      @toggle-panel="showFavPanel = !showFavPanel"
      @goto="gotoFavorite"
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
      @close="closeFoodDetail"
      @like="doLike"
      @toggle-favorite="handleToggleFavoriteModal"
    />
  </div>
</template>

<style>
.world-page {
  position: relative;
}

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

.reset-btn {
  position: fixed;
  top: 20px;
  right: 40px;
  z-index: 50;
}

@media (max-width: 768px) {
  .reset-btn {
    top: 12px;
    right: 12px;
    font-size: 14px;
    padding: 8px 12px;
    min-width: 44px;
    min-height: 44px;
  }
}
</style>
