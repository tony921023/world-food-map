<script setup>
import { ref } from "vue";

const props = defineProps({
  avg:      { type: Number, default: 0 },
  count:    { type: Number, default: 0 },
  myRating: { type: Number, default: 0 },
  readonly: { type: Boolean, default: false },
});

const emit = defineEmits(["rate"]);
const hovered = ref(0);

function starClass(i) {
  const active = hovered.value || props.myRating;
  return active >= i ? "star filled" : "star";
}
</script>

<template>
  <div class="star-rating">
    <div class="stars" :class="{ interactive: !readonly }">
      <span
        v-for="i in 5"
        :key="i"
        :class="starClass(i)"
        @mouseenter="!readonly && (hovered = i)"
        @mouseleave="!readonly && (hovered = 0)"
        @click="!readonly && emit('rate', i)"
      >★</span>
    </div>
    <span class="rating-info" v-if="count > 0">
      {{ avg.toFixed(1) }} ★（{{ count }} 人評分）
    </span>
    <span class="rating-info muted" v-else-if="!readonly">
      點擊星星來評分
    </span>
  </div>
</template>

<style scoped>
.star-rating {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0;
}
.stars {
  display: flex;
  gap: 1px;
}
.star {
  font-size: 24px;
  color: #d1d5db;
  line-height: 1;
  transition: color 0.1s;
  user-select: none;
}
.star.filled {
  color: #f59e0b;
}
.stars.interactive .star {
  cursor: pointer;
}
.stars.interactive .star:hover {
  color: #f59e0b;
  transform: scale(1.15);
}
.rating-info {
  font-size: 13px;
  color: #4b5563;
}
.rating-info.muted {
  color: #9ca3af;
  font-size: 12px;
}
</style>
