<script setup>
import { computed } from "vue";

const props = defineProps({
  countryName: { type: String, default: "" },
  code: { type: String, default: "" },
  flagUrl: { type: String, default: "" },
  foods: { type: Array, default: () => [] },
  allFoods: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  errorMsg: { type: String, default: "" },
  allTags: { type: Array, default: () => [] },
  activeTags: { type: Array, default: () => [] },
  showFavoritesOnly: { type: Boolean, default: false },
  favorites: { type: Array, default: () => [] },
  isLoggedIn: { type: Boolean, default: false },
});

const emit = defineEmits([
  "back",
  "toggle-fav-filter",
  "toggle-tag",
  "toggle-favorite",
  "open-food",
]);

function isFav(name) {
  if (!props.code || !name) return false;
  return props.favorites.some(
    (f) => f.country_code === props.code.toUpperCase() && f.food_name === name
  );
}

const COUNTRY_LABELS = {
  JP: "日本", TW: "台灣", KR: "韓國", US: "美國", CA: "加拿大",
};

const countryLabel = computed(() =>
  COUNTRY_LABELS[props.code] || props.countryName
);
</script>

<template>
  <div class="country-page">
    <!-- Hero 標題區 -->
    <div class="hero">
      <button class="back-btn" @click="emit('back')">
        <span class="back-arrow">←</span> 返回地圖
      </button>

      <div class="hero-content">
        <img class="hero-flag" :src="flagUrl" :alt="countryName" />
        <div class="hero-text">
          <h1 class="hero-title">{{ countryLabel }}</h1>
          <p class="hero-sub">{{ countryName }} · 代表料理</p>
        </div>
      </div>
    </div>

    <!-- 篩選列 -->
    <div class="filter-bar" v-if="!loading && !errorMsg && allFoods.length">
      <div class="filter-inner">
        <button
          class="fav-filter-btn"
          :class="{ active: showFavoritesOnly }"
          @click="emit('toggle-fav-filter')"
          v-if="isLoggedIn"
        >
          ❤️ 只看收藏
        </button>
        <div class="tag-chips" v-if="allTags.length">
          <button
            class="tag-chip"
            v-for="tag in allTags"
            :key="tag"
            :class="{ active: activeTags.includes(tag) }"
            @click="emit('toggle-tag', tag)"
          >{{ tag }}</button>
        </div>
      </div>
    </div>

    <!-- 內容區 -->
    <div class="content">
      <div v-if="loading" class="state-msg">
        <div class="spinner"></div>
        <p>資料載入中...</p>
      </div>

      <div v-else-if="errorMsg" class="state-msg error">
        <span class="state-icon">🍽️</span>
        <p>{{ errorMsg }}</p>
      </div>

      <div v-else-if="!foods.length && allFoods.length" class="state-msg">
        <span class="state-icon">🔍</span>
        <p>沒有符合條件的料理</p>
      </div>

      <!-- 食物格線 -->
      <div class="food-grid" v-else-if="foods.length">
        <div
          class="food-card"
          v-for="f in foods"
          :key="f.name"
          @click="emit('open-food', f)"
        >
          <div class="card-img-wrap">
            <img class="card-img" :src="f.img" :alt="f.name" loading="lazy" />
            <div class="like-badge">👍 {{ (f.likes ?? 0).toLocaleString() }}</div>
            <button
              v-if="isLoggedIn"
              class="fav-btn"
              :class="{ active: isFav(f.name) }"
              @click.stop="emit('toggle-favorite', f)"
            >{{ isFav(f.name) ? "❤️" : "🤍" }}</button>
          </div>
          <div class="card-body">
            <p class="card-name">{{ f.name }}</p>
            <div class="card-tags" v-if="f.tags && f.tags.length">
              <span class="tag" v-for="t in f.tags" :key="t">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.country-page {
  min-height: 100vh;
  background: var(--c-bg);
  display: flex;
  flex-direction: column;
}

/* ── Hero ─────────────────────────────────────────────── */
.hero {
  position: relative;
  padding: 28px 32px 24px;
  background: linear-gradient(135deg, rgba(37,99,235,0.08) 0%, rgba(124,58,237,0.06) 100%);
  border-bottom: 1px solid var(--c-border);
  backdrop-filter: blur(4px);
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.9);
  border: 1px solid var(--c-border);
  border-radius: var(--r-full);
  padding: 8px 18px;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--c-text-2);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all var(--dur);
  margin-bottom: 20px;
}
.back-btn:hover {
  background: var(--c-surface);
  box-shadow: var(--shadow-md);
  transform: translateX(-3px);
}
.back-arrow { font-size: var(--text-lg); }

.hero-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.hero-flag {
  width: 80px;
  height: 56px;
  object-fit: cover;
  border-radius: var(--r-md);
  box-shadow: var(--shadow-md);
}

.hero-title {
  font-size: 36px;
  font-weight: 800;
  color: var(--c-text);
  letter-spacing: -0.5px;
  margin: 0;
}
.hero-sub {
  font-size: var(--text-md);
  color: var(--c-text-2);
  margin: 4px 0 0;
}

/* ── Filter bar ───────────────────────────────────────── */
.filter-bar {
  padding: 12px 32px;
  background: rgba(255,255,255,0.7);
  border-bottom: 1px solid var(--c-border);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.filter-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  max-width: 1280px;
  margin: 0 auto;
}

.fav-filter-btn {
  background: var(--c-hover);
  color: var(--c-text-2);
  border: 1px solid var(--c-border);
  border-radius: var(--r-full);
  padding: 5px 14px;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur);
  white-space: nowrap;
}
.fav-filter-btn.active { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

.tag-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-chip {
  background: rgba(255,255,255,0.85);
  border: 1px solid var(--c-border);
  border-radius: var(--r-full);
  padding: 4px 13px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all var(--dur);
}
.tag-chip.active { background: var(--c-primary); color: #fff; border-color: var(--c-primary); }
.tag-chip:hover:not(.active) { background: var(--c-hover-blue); border-color: #93c5fd; }

/* ── Content ──────────────────────────────────────────── */
.content {
  flex: 1;
  padding: 32px;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 200px;
  color: var(--c-text-3);
  font-size: var(--text-md);
}
.state-msg.error { color: var(--c-error); }
.state-icon { font-size: 48px; }

.spinner {
  width: 40px; height: 40px;
  border: 3px solid var(--c-hover);
  border-top-color: var(--c-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Food grid ────────────────────────────────────────── */
.food-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
}

.food-card {
  background: #ffffff;
  border-radius: var(--r-xl);
  box-shadow: 0 4px 20px rgba(15,23,42,0.14);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--dur), box-shadow var(--dur);
}
.food-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 36px rgba(15,23,42,0.2);
}

.card-img-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  overflow: hidden;
}
.card-img {
  width: 100%; height: 100%;
  object-fit: cover; display: block;
  transition: transform 0.3s;
}
.food-card:hover .card-img { transform: scale(1.04); }

.like-badge {
  position: absolute;
  bottom: 8px; left: 8px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: var(--text-xs);
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--r-full);
  backdrop-filter: blur(4px);
}

.fav-btn {
  position: absolute;
  top: 8px; right: 8px;
  background: rgba(255,255,255,0.9);
  border: none;
  border-radius: 50%;
  width: 34px; height: 34px;
  font-size: var(--text-lg);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow-sm);
  transition: transform var(--dur);
  padding: 0;
  backdrop-filter: blur(4px);
}
.fav-btn:hover { transform: scale(1.15); background: var(--c-surface); }

.card-body { padding: 12px 14px 14px; }
.card-name {
  margin: 0 0 8px;
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--c-text);
  line-height: 1.3;
}

.card-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.tag {
  background: var(--c-primary-light);
  color: var(--c-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 9px;
  border-radius: var(--r-full);
}

/* ── RWD ──────────────────────────────────────────────── */
@media (max-width: 768px) {
  .hero { padding: 20px 16px 16px; }
  .hero-title { font-size: 26px; }
  .hero-flag { width: 56px; height: 40px; }
  .filter-bar { padding: 10px 16px; }
  .content { padding: 20px 16px; }
  .food-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 16px; }
  .back-btn { padding: 7px 14px; font-size: var(--text-sm); }
}
</style>
