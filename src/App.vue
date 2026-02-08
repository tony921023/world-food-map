<script setup>
import { ref, watch } from 'vue'
import WorldMap from './components/WorldMap.vue'
import CountryFoodGrid from './components/CountryFoodGrid.vue'

const selectedCountry = ref(null)
const countryFoods = ref([])
const loading = ref(false)
const error = ref(null)

// 只要國家代碼改變，就到後端抓該國的料理清單（含 likes）
watch(selectedCountry, async (newCode) => {
  if (!newCode) {
    countryFoods.value = []
    return
  }
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/foods/${newCode.toUpperCase()}`)
    if (!res.ok) {
      const errData = await res.json().catch(() => null)
      const errMsg = errData?.error || res.statusText
      throw new Error(errMsg || '取得料理清單失敗')
    }
    const data = await res.json()

    // ✅ 把後端回來的 likes 一起塞進去
    countryFoods.value = (data.foods || []).map(f => ({
      name : f.name,
      img  : f.img,
      likes: Number.isFinite(f.likes) ? f.likes : 0
    }))
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <h1 class="title">🌍 全球美食探索</h1>

  <!-- 世界地圖：點國家時更新 selectedCountry -->
  <WorldMap @select-country="code => (selectedCountry.value = code)" />

  <!-- 狀態訊息 -->
  <div v-if="loading" class="loading">載入中...</div>
  <div v-if="error" class="error">{{ error }}</div>

  <!-- 左側料理清單（含讚數、可滑動） -->
  <CountryFoodGrid
    v-if="selectedCountry && !loading && !error"
    :foods="countryFoods"
    :code="selectedCountry"
  />
</template>

<style scoped>
.title {
  text-align: center;
  margin: 24px 0 12px;
  font-size: 32px;
}
.loading,
.error {
  margin-top: 12px;
  text-align: center;
}
.error {
  color: #dc2626;
}
</style>
