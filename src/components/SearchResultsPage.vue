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
  background: var(--c-hover);
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
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.back-btn {
  border: 1px solid var(--c-border);
  background: var(--c-hover);
  border-radius: var(--r-full);
  padding: 6px 16px;
  font-size: var(--text-sm);
  cursor: pointer;
  font-weight: 600;
  color: var(--c-text-2);
  white-space: nowrap;
  transition: all var(--dur);
}
.back-btn:hover { background: #e2e8f0; box-shadow: var(--shadow-sm); }

.sr-title { font-size: var(--text-md); color: var(--c-text-2); }
.query-label { color: var(--c-text-3); }
.query-text  { font-weight: 700; color: var(--c-text); margin: 0 4px; }
.result-count { color: var(--c-text-3); font-size: var(--text-sm); }

/* Filter bar */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
  padding: 12px 20px;
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  flex-shrink: 0;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-label {
  font-size: var(--text-sm);
  color: var(--c-text-3);
  white-space: nowrap;
}
.pill {
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-full);
  padding: 4px 12px;
  font-size: var(--text-sm);
  cursor: pointer;
  color: var(--c-text-2);
  transition: all var(--dur);
}
.pill:hover  { border-color: var(--c-primary); color: var(--c-primary); }
.pill.active { background: var(--c-primary); color: #fff; border-color: var(--c-primary); }

/* Body / Grid */
.sr-body { flex: 1; overflow-y: auto; padding: 20px; }
.empty-state {
  text-align: center;
  color: var(--c-text-3);
  font-size: var(--text-md);
  padding: 60px 0;
}
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

/* Card */
.result-card {
  background: var(--c-surface);
  border-radius: var(--r-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--c-border);
  cursor: pointer;
  transition: transform var(--dur), box-shadow var(--dur);
}
.result-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.card-img-wrap { position: relative; aspect-ratio: 4/3; overflow: hidden; }
.card-img { width: 100%; height: 100%; object-fit: cover; }

.like-badge {
  position: absolute;
  top: 6px; right: 6px;
  background: rgba(15,23,42,0.6);
  color: #fff;
  font-size: var(--text-xs);
  padding: 2px 7px;
  border-radius: var(--r-full);
  backdrop-filter: blur(4px);
}
.card-body {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.card-name {
  font-weight: 700;
  font-size: var(--text-base);
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-country { font-size: var(--text-sm); color: var(--c-text-3); }
.card-rating  { font-size: var(--text-sm); color: var(--c-text-2); }
.stars-mini   { color: var(--c-warn); }
.rating-count { color: var(--c-text-3); }

.card-tags { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 2px; }
.tag {
  font-size: 10px;
  padding: 1px 6px;
  background: var(--c-primary-light);
  color: var(--c-primary);
  border-radius: var(--r-full);
  font-weight: 600;
}

@media (max-width: 768px) {
  .results-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
  .filter-bar   { gap: 8px 12px; padding: 10px 14px; }
  .sr-body      { padding: 14px; }
}
</style>
