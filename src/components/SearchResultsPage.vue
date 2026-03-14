<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  show:           { type: Boolean, default: false },
  initialQuery:   { type: String,  default: "" },
  initialResults: { type: Array,   default: () => [] },
});

const emit = defineEmits(["close", "pick"]);

const allResults     = ref([]);
const filterCountry  = ref("");
const filterMinRating = ref(0);
const sortBy         = ref("likes");
const loading        = ref(false);

const COUNTRY_NAMES = {
  JP: "日本", TW: "台灣", KR: "韓國", US: "美國", CA: "加拿大",
};

// 每次開啟時用 initialResults 初始化，並重新 fetch 以確保資料完整
watch(
  () => props.show,
  async (val) => {
    if (val) {
      allResults.value = props.initialResults || [];
      if (props.initialQuery) await doSearch(props.initialQuery);
    }
  }
);

async function doSearch(q) {
  if (!q) return;
  loading.value = true;
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    allResults.value = data.results || [];
  } catch {
    // 保留 initialResults
  } finally {
    loading.value = false;
  }
}

const filteredResults = computed(() => {
  let list = allResults.value;
  if (filterCountry.value) {
    list = list.filter((r) => r.code === filterCountry.value);
  }
  if (filterMinRating.value > 0) {
    list = list.filter((r) => r.avg_rating >= filterMinRating.value);
  }
  if (sortBy.value === "rating") {
    list = [...list].sort((a, b) => b.avg_rating - a.avg_rating || b.likes - a.likes);
  } else if (sortBy.value === "name") {
    list = [...list].sort((a, b) => a.name.localeCompare(b.name, "zh-TW"));
  } else {
    list = [...list].sort((a, b) => b.likes - a.likes || b.avg_rating - a.avg_rating);
  }
  return list;
});

function pickItem(item) {
  emit("pick", item);
  emit("close");
}
</script>

<template>
  <div class="sr-overlay" v-if="show">
    <!-- Header -->
    <div class="sr-header">
      <button class="back-btn" @click="emit('close')">← 返回</button>
      <div class="sr-title">
        <span class="query-label">搜尋：</span>
        <span class="query-text">{{ initialQuery }}</span>
        <span class="result-count" v-if="!loading">（{{ filteredResults.length }} 筆結果）</span>
        <span class="result-count" v-else>搜尋中...</span>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">國家：</span>
        <button
          class="pill"
          :class="{ active: filterCountry === '' }"
          @click="filterCountry = ''"
        >全部</button>
        <button
          v-for="(label, code) in COUNTRY_NAMES"
          :key="code"
          class="pill"
          :class="{ active: filterCountry === code }"
          @click="filterCountry = filterCountry === code ? '' : code"
        >{{ label }}</button>
      </div>

      <div class="filter-group">
        <span class="filter-label">最低評分：</span>
        <button class="pill" :class="{ active: filterMinRating === 0 }" @click="filterMinRating = 0">不限</button>
        <button class="pill" :class="{ active: filterMinRating === 3 }" @click="filterMinRating = 3">3★+</button>
        <button class="pill" :class="{ active: filterMinRating === 4 }" @click="filterMinRating = 4">4★+</button>
      </div>

      <div class="filter-group">
        <span class="filter-label">排序：</span>
        <button class="pill" :class="{ active: sortBy === 'likes'  }" @click="sortBy = 'likes'">最多讚</button>
        <button class="pill" :class="{ active: sortBy === 'rating' }" @click="sortBy = 'rating'">最高分</button>
        <button class="pill" :class="{ active: sortBy === 'name'   }" @click="sortBy = 'name'">名稱</button>
      </div>
    </div>

    <!-- Results grid -->
    <div class="sr-body">
      <div v-if="loading" class="empty-state">搜尋中...</div>

      <div v-else-if="filteredResults.length === 0" class="empty-state">
        沒有找到符合條件的料理
      </div>

      <div v-else class="results-grid">
        <div
          class="result-card"
          v-for="item in filteredResults"
          :key="item.code + '_' + item.name"
          @click="pickItem(item)"
        >
          <div class="card-img-wrap">
            <img :src="item.img" :alt="item.name" class="card-img" />
            <span class="like-badge" v-if="item.likes > 0">👍 {{ item.likes }}</span>
          </div>
          <div class="card-body">
            <div class="card-name">{{ item.name }}</div>
            <div class="card-country">{{ item.countryName }}</div>
            <div class="card-rating" v-if="item.rating_count > 0">
              <span class="stars-mini">★</span>
              {{ item.avg_rating.toFixed(1) }}
              <span class="rating-count">（{{ item.rating_count }}）</span>
            </div>
            <div class="card-tags" v-if="item.tags?.length">
              <span class="tag" v-for="t in item.tags.slice(0, 3)" :key="t">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sr-overlay {
  position: fixed;
  inset: 0;
  background: #f8fafc;
  z-index: 60;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.sr-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.back-btn {
  border: none;
  background: #e2e8f0;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 14px;
  cursor: pointer;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}
.back-btn:hover { background: #cbd5e1; }
.sr-title {
  font-size: 15px;
  color: #374151;
}
.query-label { color: #6b7280; }
.query-text  { font-weight: 700; color: #111827; margin: 0 4px; }
.result-count{ color: #9ca3af; font-size: 13px; }

/* Filter bar */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-label {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}
.pill {
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
  cursor: pointer;
  color: #374151;
  transition: all 0.15s;
}
.pill:hover  { border-color: #2563eb; color: #2563eb; }
.pill.active { background: #2563eb; color: #fff; border-color: #2563eb; }

/* Body / Grid */
.sr-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.empty-state {
  text-align: center;
  color: #9ca3af;
  font-size: 15px;
  padding: 60px 0;
}
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

/* Card */
.result-card {
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(15,23,42,0.08);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.result-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(15,23,42,0.14);
}
.card-img-wrap {
  position: relative;
  aspect-ratio: 4/3;
  overflow: hidden;
}
.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.like-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(15,23,42,0.6);
  color: #fff;
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 999px;
}
.card-body {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.card-name {
  font-weight: 700;
  font-size: 14px;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-country {
  font-size: 12px;
  color: #6b7280;
}
.card-rating {
  font-size: 12px;
  color: #4b5563;
}
.stars-mini { color: #f59e0b; }
.rating-count { color: #9ca3af; }
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 2px;
}
.tag {
  font-size: 10px;
  padding: 1px 6px;
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 999px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .results-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
  .filter-bar   { gap: 8px 12px; padding: 10px 14px; }
  .sr-body      { padding: 14px; }
}
</style>
