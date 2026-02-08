<script setup>
import { ref, onMounted, nextTick, computed } from "vue";
import svgPanZoom from "svg-pan-zoom";

const svgObj = ref(null);
const panzoom = ref(null);

// === 狀態 ===
const selectedCountryName = ref(null);  // 顯示用（Japan / Taiwan / Korea）
const selectedCode = ref(null);         // API 用（JP / TW / KR）

const countryFoods = ref([]);           // 後端回來的 food 清單
const loading = ref(false);
const errorMsg = ref("");

// 只負責旗幟
const FLAG_BY_CODE = {
  JP: "https://flagcdn.com/w320/jp.png",
  TW: "https://flagcdn.com/w320/tw.png",
  KR: "https://flagcdn.com/w320/kr.png",
  US: "https://flagcdn.com/w320/us.png", // 美國
  CA: "https://flagcdn.com/w320/ca.png", // 加拿大
};


// SVG 名稱 → 國碼
// SVG 名稱 → 國碼
const CODE_BY_SVG_ID = {
  // 🇯🇵 日本
  Japan: "JP",
  JPN: "JP",
  日本: "JP",

  // 🇹🇼 台灣
  Taiwan: "TW",
  TWN: "TW",
  臺灣: "TW",
  台灣: "TW",

  // 🇰🇷 韓國
  Korea: "KR",
  "South Korea": "KR",
  "Republic of Korea": "KR",
  KOR: "KR",
  韓國: "KR",

  // 🇺🇸 美國（多補幾個可能的名字）
  United: "US",                    // 你的 SVG 現在顯示的就是這個
  "United States": "US",
  "United States of America": "US",
  USA: "US",
  US: "US",
  America: "US",
  美國: "US",

  // 🇨🇦 加拿大
  CA: "CA",
  CAN: "CA",
  Canada: "CA",
  加拿大: "CA",
};


const getFlag = () =>
  FLAG_BY_CODE[selectedCode.value] || "https://flagcdn.com/w320/un.png";
const getFoods = () => countryFoods.value;

// ====== 收藏（localStorage） ======
const FAVORITE_STORAGE_KEY = "worldmap_favorites_v1";

// 只存「國碼::料理名」字串
const favorites = ref([]); // string[]

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
    localStorage.setItem(
      FAVORITE_STORAGE_KEY,
      JSON.stringify(favorites.value)
    );
  } catch {
    // ignore
  }
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

// 「只看收藏」開關 + 清單實際顯示的內容
const showFavoritesOnly = ref(false);
const displayFoods = computed(() => {
  if (!showFavoritesOnly.value) return countryFoods.value;
  return countryFoods.value.filter((f) =>
    isFavorite(selectedCode.value, f.name)
  );
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
  // 國名就直接用 code 對應的英文名就好
  const countryName =
    Object.entries(CODE_BY_SVG_ID).find(([, c]) => c === code)?.[0] || code;
  selectedCountryName.value = countryName;

  await fetchFoodsByCountry(code);
  const found = countryFoods.value.find((f) => f.name === item.name);
  if (found) {
    await openFoodDetail(found);
  }
}

// ====== 清單容器，用來量測高度（讓 3 張卡片剛好出現在畫面內） ======
const listEl = ref(null);
const listMaxHeight = ref(null); // px

function calcListMaxHeight() {
  const el = listEl.value;
  if (!el) return;
  const first = el.querySelector(".food-item");
  if (!first) return;

  const firstH = first.offsetHeight; // 單一卡片實際高度
  const styles = getComputedStyle(el);
  const gap = parseFloat(styles.rowGap || styles.gap || "0"); // 間距

  // 3 張卡片 + 2 個 gap → 剛好完整顯示三張
  listMaxHeight.value = firstH * 3 + gap * 2;
}

// ---------------- 取得料理清單（沒有 code 也會出卡片提示） ----------------
async function fetchFoodsByCountry(code) {
  if (!code) {
    loading.value = false;
    countryFoods.value = [];
    errorMsg.value =
      "這個國家的人們也熱愛美食，但我們還沒新增資料，歡迎之後再來～";
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
        errorMsg.value =
          "目前尚未為這個國家設定代表美食，之後再來看看～";
        return;
      }
      throw new Error("讀取料理清單失敗");
    }
    const data = await res.json();
    countryFoods.value = (data.foods || []).map((f) => ({
      name: f.name,
      img: f.img,
      likes: f.likes ?? 0,
    }));
    if (!countryFoods.value.length) {
      errorMsg.value = "這個國家目前還沒有新增美食資料。";
    }

    // 等 DOM 畫完，再量測高度 → 設定剛好 3 張卡片的 max-height
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
const topFoods = ref([]); // [{code,name,countryName,score,likes,img}]
const topLoading = ref(false);
const topError = ref("");

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

// 從 TOP 5 點選一個料理 → 切換到對應國家、載入清單、打開 modal
async function jumpToTopFood(item) {
  if (!item?.code || !item?.name) return;

  const code = item.code;
  selectedCode.value = code;
  selectedCountryName.value =
    item.countryName ||
    Object.keys(CODE_BY_SVG_ID).find((k) => CODE_BY_SVG_ID[k] === code) ||
    code;

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

  // 初始化收藏 & TOP5
  loadFavorites();
  fetchTopFoods();
});

// 地圖歸位
const resetMap = () => {
  if (panzoom.value) panzoom.value.reset();
  selectedCountryName.value = null;
  selectedCode.value = null;
  countryFoods.value = [];
  errorMsg.value = "";
  listMaxHeight.value = null;
  showFavoritesOnly.value = false;
};

// ===== 食物介紹 Modal（點清單卡片） =====
const selectedFood = ref(null);
const showFoodModal = ref(false);

// Like & Comment 狀態
const likesCount = ref(0);
const likeLoading = ref(false);
const comments = ref([]);
const posting = ref(false);
const newUser = ref("");
const newText = ref("");

// 目前 modal 這道料理是不是已收藏
const isCurrentFoodFav = computed(() => {
  if (!selectedFood.value || !selectedCode.value) return false;
  return isFavorite(selectedCode.value, selectedFood.value.name);
});

// Google Map 查附近這道料理
const googleMapUrl = computed(() => {
  if (!selectedFood.value) return "https://www.google.com/maps";
  const qCountry = selectedCountryName.value || selectedCode.value || "";
  const q = encodeURIComponent(`${qCountry} ${selectedFood.value.name} 美食`);
  return `https://www.google.com/maps/search/${q}`;
});

// 更新左側清單上的 likes
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
    `/api/food/${selectedCode.value}/${encodeURIComponent(
      selectedFood.value.name
    )}/likes`
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
      `/api/food/${selectedCode.value}/${encodeURIComponent(
        selectedFood.value.name
      )}/like`,
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
    `/api/food/${selectedCode.value}/${encodeURIComponent(
      selectedFood.value.name
    )}/comments`
  );
  const data = await r.json();
  comments.value = data.comments || [];
}

async function submitComment() {
  if (!selectedCode.value || !selectedFood.value) return;
  const payload = {
    user: newUser.value || "匿名",
    text: (newText.value || "").trim(),
  };
  if (!payload.text) return;
  try {
    posting.value = true;
    const r = await fetch(
      `/api/food/${selectedCode.value}/${encodeURIComponent(
        selectedFood.value.name
      )}/comments`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    if (!r.ok) throw new Error("留言失敗");
    const created = await r.json();
    comments.value.unshift(created);
    newText.value = "";
  } finally {
    posting.value = false;
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
    };
  } catch (e) {
    console.error(e);
    selectedFood.value = { ...food, desc: "這道料理還沒有詳細介紹。" };
  }

  await Promise.all([fetchLikes(), fetchComments()]);
  showFoodModal.value = true;
}

const closeFoodDetail = () => {
  showFoodModal.value = false;
};
</script>

<template>
  <div class="world-page">
    <button class="reset-btn" @click="resetMap">返回地圖</button>

    <!-- 地圖 + 左側浮動卡片 -->
    <div class="map-stage">
      <object
        ref="svgObj"
        data="/world.svg"
        type="image/svg+xml"
        class="world-map"
      />

      <!-- 左側美食清單卡片（浮在地圖上方，位置比較高） -->
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

          <!-- 收藏篩選 -->
          <div
            class="fav-filter-row"
            v-else-if="getFoods().length"
          >
            <button
              class="fav-filter"
              :class="{ active: showFavoritesOnly }"
              @click="showFavoritesOnly = !showFavoritesOnly"
            >
              只看收藏
            </button>
          </div>

          <!-- 清單：3 張完整卡片，可滾動 -->
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
    <div class="top-panel">
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

    <!-- 食物介紹 Modal -->
    <div class="modal-mask" v-if="showFoodModal" @click="closeFoodDetail">
      <div class="modal-content" @click.stop>
        <button class="close-btn" @click="closeFoodDetail">✕</button>
        <img class="modal-food-img" :src="selectedFood?.img" />
        <h2>{{ selectedFood?.name }}</h2>
        <p class="food-desc">
          {{ selectedFood?.desc || "這道料理還沒有詳細介紹。" }}
        </p>

        <!-- 第一行：按讚 / 已獲得 / 收藏 -->
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

          <!-- 第二行：Google Map 連結 -->
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

/* 地圖區，讓卡片可以絕對定位在裡面 */
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
.fav-filter-row {
  margin-top: 4px;
  margin-bottom: 6px;
  display: flex;
  justify-content: flex-end;
}

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

/* ===== 清單：3 張完整卡片 + 滾輪 ===== */
.food-list {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  row-gap: 16px;   /* 卡片間距 */

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

  /* 這裡改成 visible + 多留一點內距，文字就不會被裁掉 */
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
  padding: 6px 8px 4px 10px;  /* 和圖片、下緣都多留一點距離 */
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

/* ===== Modal 互動區塊樣式 ===== */
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

/* Google Map 連結：獨立一行置中 */
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
}

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
</style>
