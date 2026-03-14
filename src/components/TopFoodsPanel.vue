<script setup>
import { ref, onMounted } from "vue";

const emit = defineEmits(["jump"]);

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

onMounted(() => {
  fetchTopFoods();
});
</script>

<template>
  <!-- TOP 5 panel -->
  <div class="top-panel" :class="{ 'show-mobile': showTopPanelMobile }">
    <h3>本週人氣美食 TOP 5</h3>
    <div v-if="topLoading" class="top-status">載入中...</div>
    <div v-else-if="topError" class="top-status top-error">{{ topError }}</div>
    <ul v-else class="top-list">
      <li
        v-for="(item, idx) in topFoods"
        :key="item.code + '_' + item.name"
        class="top-item"
        @click="emit('jump', item)"
      >
        <span class="rank">{{ idx + 1 }}</span>
        <span class="top-name">{{ item.name }}</span>
        <span class="top-country">{{ item.countryName || item.code }}</span>
        <span class="top-score" v-if="item.score != null">
          ★ {{ Number(item.score).toFixed(1) }}
        </span>
      </li>
      <li v-if="!topFoods.length" class="top-status">
        目前還沒有統計資料
      </li>
    </ul>
  </div>

  <!-- Mobile toggle button -->
  <button
    class="top-toggle-mobile"
    @click="showTopPanelMobile = !showTopPanelMobile"
  >
    🏆 TOP5
  </button>
</template>

<style scoped>
.top-panel {
  position: fixed;
  right: 28px; bottom: 28px;
  width: 270px;
  background: #ffffff;
  border-radius: var(--r-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--c-border);
  padding: 16px 16px 12px;
  z-index: 30;
  font-size: var(--text-base);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.top-panel h3 {
  font-size: var(--text-md);
  font-weight: 800;
  color: var(--c-text);
  margin: 0 0 10px;
  letter-spacing: -0.2px;
}

.top-list {
  list-style: none; padding: 0; margin: 0;
  max-height: 260px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 2px;
}

.top-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 8px; border-radius: var(--r-md);
  cursor: pointer; transition: background var(--dur);
}
.top-item:hover { background: var(--c-hover-blue); }

.rank {
  width: 22px; height: 22px; border-radius: var(--r-full);
  background: var(--c-primary-light); color: var(--c-primary);
  font-size: var(--text-xs); font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.top-item:nth-child(1) .rank { background: #fef3c7; color: #d97706; }
.top-item:nth-child(2) .rank { background: #f1f5f9; color: #64748b; }
.top-item:nth-child(3) .rank { background: #fef3c7; color: #b45309; }

.top-name  { flex: 1; font-size: var(--text-base); font-weight: 600; color: var(--c-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.top-country { font-size: var(--text-xs); color: var(--c-text-3); flex-shrink: 0; }
.top-score { font-size: var(--text-xs); color: var(--c-warn); font-weight: 700; flex-shrink: 0; }

.top-status { font-size: var(--text-sm); color: var(--c-text-3); margin-top: 6px; }
.top-error  { color: var(--c-error); }

.top-toggle-mobile {
  display: none;
  position: fixed; right: 14px; bottom: 14px; z-index: 31;
  padding: 0; width: 50px; height: 50px;
  border-radius: var(--r-full); border: none; cursor: pointer;
  background: var(--c-primary); color: #fff;
  font-size: 13px; font-weight: 700;
  box-shadow: 0 4px 16px rgba(37,99,235,0.35);
  align-items: center; justify-content: center;
}

@media (max-width: 768px) {
  .top-panel {
    display: none; position: fixed;
    left: 0; right: 0; bottom: 68px; width: auto;
    border-radius: var(--r-xl) var(--r-xl) 0 0;
  }
  .top-panel.show-mobile { display: block; }
  .top-toggle-mobile { display: flex; }
}
</style>
