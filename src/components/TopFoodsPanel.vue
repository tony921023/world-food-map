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

@media (max-width: 768px) {
  .top-panel {
    display: none;
    position: fixed;
    left: 0;
    right: 0;
    bottom: 60px;
    width: auto;
    border-radius: 18px 18px 0 0;
  }
  .top-panel.show-mobile {
    display: block;
  }
  .top-toggle-mobile {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
