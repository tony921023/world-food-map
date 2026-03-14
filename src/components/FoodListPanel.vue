<script setup>
import { ref, watch, nextTick } from "vue";

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
  listMaxHeight: { type: Number, default: null },
});

const emit = defineEmits([
  "toggle-fav-filter",
  "toggle-tag",
  "toggle-favorite",
  "open-food",
  "update:list-max-height",
]);

const listEl = ref(null);

function isFav(name) {
  if (!props.code || !name) return false;
  return props.favorites.some(
    (f) => f.country_code === props.code.toUpperCase() && f.food_name === name
  );
}

function calcListMaxHeight() {
  const el = listEl.value;
  if (!el) return;
  const first = el.querySelector(".food-item");
  if (!first) return;
  const firstH = first.offsetHeight;
  const styles = getComputedStyle(el);
  const gap = parseFloat(styles.rowGap || styles.gap || "0");
  emit("update:list-max-height", firstH * 3 + gap * 2);
}

watch(
  () => props.allFoods.length,
  async () => {
    await nextTick();
    calcListMaxHeight();
  }
);
</script>

<template>
  <div class="food-card">
    <div class="food-header">
      <img class="flag" :src="flagUrl" />
      <h2>{{ countryName }}</h2>
    </div>

    <h3 class="section-title">代表料理</h3>

    <div v-if="loading" class="loading-text">資料載入中...</div>
    <div v-else-if="errorMsg" class="error-text">{{ errorMsg }}</div>

    <!-- Filter row -->
    <div class="filter-row" v-else-if="allFoods.length">
      <div class="filter-top">
        <button
          class="fav-filter"
          :class="{ active: showFavoritesOnly }"
          @click="emit('toggle-fav-filter')"
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
          @click="emit('toggle-tag', tag)"
        >
          {{ tag }}
        </button>
      </div>
    </div>

    <!-- Food list -->
    <div
      class="food-list"
      v-if="allFoods.length"
      ref="listEl"
      :style="listMaxHeight ? { maxHeight: listMaxHeight + 'px' } : {}"
    >
      <div
        class="food-item"
        v-for="f in foods"
        :key="f.name"
        @click="emit('open-food', f)"
      >
        <div class="food-img-wrap">
          <img class="food-img" :src="f.img" :alt="f.name" loading="lazy" />
          <div class="food-like-badge" title="讚數">
            👍 {{ (f.likes ?? 0).toLocaleString() }}
          </div>
        </div>
        <div class="food-name-row">
          <p class="food-name">{{ f.name }}</p>
          <button
            v-if="isLoggedIn"
            class="fav-icon"
            :class="{ active: isFav(f.name) }"
            @click.stop="emit('toggle-favorite', f)"
          >
            {{ isFav(f.name) ? "❤️" : "🤍" }}
          </button>
        </div>
        <div class="food-tags" v-if="f.tags && f.tags.length">
          <span class="tag-badge" v-for="t in f.tags" :key="t">{{ t }}</span>
        </div>
      </div>
    </div>

    <p v-else class="no-food">這個國家目前還沒有新增美食資料。</p>
  </div>
</template>

<style scoped>
.food-card {
  position: absolute;
  top: 46px; left: 40px;
  width: 260px;
  max-height: calc(100vh - 120px);
  overflow: hidden;
  padding: 14px 18px 20px;
  background: rgba(255,255,255,0.97);
  border-radius: var(--r-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--c-border);
  z-index: 20;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.food-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}
.food-header h2 {
  margin: 0;
  font-size: var(--text-2xl);
  color: var(--c-text);
}

.section-title {
  margin: 4px 0 6px;
  font-size: var(--text-lg);
  color: var(--c-text-2);
  font-weight: 700;
}

.flag {
  width: 32px; height: 24px;
  border-radius: var(--r-sm);
  box-shadow: var(--shadow-sm);
}

.loading-text, .error-text {
  margin: 8px 0;
  font-size: var(--text-base);
  color: var(--c-text-3);
}
.error-text { color: var(--c-error); }

/* Filter row */
.filter-row { margin-top: 4px; margin-bottom: 6px; }
.filter-top { display: flex; justify-content: flex-end; }

.fav-filter {
  border: none;
  padding: 4px 10px;
  border-radius: var(--r-full);
  font-size: var(--text-sm);
  cursor: pointer;
  background: var(--c-hover);
  color: var(--c-text-2);
  transition: all var(--dur);
}
.fav-filter.active { background: #fee2e2; color: #dc2626; }

.tag-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.tag-chip {
  border: none;
  padding: 3px 10px;
  border-radius: var(--r-full);
  font-size: var(--text-xs);
  cursor: pointer;
  background: var(--c-hover);
  color: var(--c-text-2);
  transition: all var(--dur);
}
.tag-chip.active { background: var(--c-primary); color: #fff; }
.tag-chip:hover:not(.active) { background: #e2e8f0; }

/* Food list */
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
  background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.8));
  pointer-events: none;
}

/* Single food card */
.food-item {
  scroll-snap-align: start;
  background: var(--c-surface);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  overflow: visible;
  padding-bottom: 6px;
  transition: box-shadow var(--dur), transform var(--dur);
}
.food-item:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }

.food-img-wrap { position: relative; width: 100%; }
.food-img { width: 100%; height: auto; display: block; border-radius: var(--r-md) var(--r-md) 0 0; }

.food-like-badge {
  position: absolute;
  top: 8px; right: 8px;
  padding: 3px 8px;
  border-radius: var(--r-full);
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: var(--text-xs);
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
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--c-text);
}

.fav-icon {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--text-lg);
  padding: 0;
  opacity: 0.8;
  transition: opacity var(--dur), transform var(--dur);
}
.fav-icon:hover { opacity: 1; transform: scale(1.1); }
.fav-icon.active { opacity: 1; }

.food-tags { display: flex; flex-wrap: wrap; gap: 4px; padding: 0 10px 6px; }

.tag-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--r-full);
  background: var(--c-primary-light);
  color: var(--c-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.4;
}

.no-food {
  font-size: var(--text-base);
  color: var(--c-text-3);
  margin-top: 10px;
}

@media (max-width: 1024px) {
  .food-card { width: 220px; }
}

@media (max-width: 768px) {
  .food-card {
    position: fixed !important;
    top: auto !important; left: 0 !important;
    right: 0 !important; bottom: 0 !important;
    width: auto !important;
    max-height: 50vh;
    border-radius: var(--r-xl) var(--r-xl) 0 0;
    overflow-y: auto;
    z-index: 25;
  }
  .food-item { flex-direction: row; align-items: center; padding: 8px; gap: 10px; }
  .food-img-wrap { width: 80px; flex-shrink: 0; }
  .food-img { border-radius: var(--r-md); aspect-ratio: 1; object-fit: cover; }
  .food-name-row { padding: 0; }
  .food-tags { padding: 0; }
  .fav-filter, .fav-icon, .tag-chip {
    min-width: 44px; min-height: 44px;
    display: inline-flex; align-items: center; justify-content: center;
  }
}
</style>
