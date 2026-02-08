<script setup>
import FoodCard from './FoodCard.vue'

const { foods, code } = defineProps({
  foods: { type: Array, default: () => [] }, // [{name,img,likes}]
  code : { type: String, default: '' }
})
</script>

<template>
  <!-- 直向卡片容器：兩張完整 + 第三張露出，滑動可看完整列表 -->
  <div class="cards">
    <FoodCard
      v-for="f in foods"
      :key="f.name"
      :food="f"
      :code="code"
    />
  </div>
</template>

<style scoped>
.cards {
  /* 卡片高度 / 間距 / 露出高度，可以依需求再微調 */
  --card-h: 260px;
  --gap: 16px;
  --peek: 70px; /* 第三張要露出多少 */

  display: flex;
  flex-direction: column;
  gap: var(--gap);

  /* 兩張完整 + 一個間距 + 第三張露出的高度 */
  max-height: calc((var(--card-h) * 2) + var(--gap) + var(--peek));
  overflow-y: auto;
  padding-right: 6px;
  scroll-snap-type: y proximity;
  position: relative;
}

/* 每張卡片在滾動時會微微對齊 */
.cards > * {
  scroll-snap-align: start;
}

/* 底部淡淡的漸層，提示可以往下捲 */
.cards::after {
  content: "";
  position: sticky;
  bottom: 0;
  display: block;
  height: 24px;
  margin-top: -24px;
  background: linear-gradient(to bottom, transparent, rgba(0,0,0,0.06));
  pointer-events: none;
}
</style>
