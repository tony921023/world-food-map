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
  const key = `${props.code}::${name}`;
  return props.favorites.includes(key);
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

.loading-text,
.error-text {
  margin: 8px 0;
  font-size: 14px;
}
.error-text {
  color: #dc2626;
}

/* Filter row */
.filter-row {
  margin-top: 4px;
  margin-bottom: 6px;
}
.filter-top {
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
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.06));
  pointer-events: none;
}

/* Single food card */
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

.food-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0 10px 6px;
}

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

.no-food {
  font-size: 14px;
  color: #4b5563;
  margin-top: 10px;
}

@media (max-width: 1024px) {
  .food-card {
    width: 220px;
  }
}

@media (max-width: 768px) {
  .food-card {
    position: fixed !important;
    top: auto !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: auto !important;
    max-height: 50vh;
    border-radius: 18px 18px 0 0;
    overflow-y: auto;
    z-index: 25;
  }

  .food-item {
    flex-direction: row;
    align-items: center;
    padding: 8px;
    gap: 10px;
  }
  .food-img-wrap {
    width: 80px;
    flex-shrink: 0;
  }
  .food-img {
    border-radius: 8px;
    aspect-ratio: 1;
    object-fit: cover;
  }
  .food-name-row {
    padding: 0;
  }
  .food-tags {
    padding: 0;
  }

  .fav-filter,
  .fav-icon,
  .tag-chip {
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
