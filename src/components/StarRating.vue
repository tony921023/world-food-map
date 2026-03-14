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
.stars { display: flex; gap: 1px; }
.star {
  font-size: 24px;
  color: var(--c-border);
  line-height: 1;
  transition: color var(--dur), transform var(--dur);
  user-select: none;
}
.star.filled { color: var(--c-warn); }
.stars.interactive .star { cursor: pointer; }
.stars.interactive .star:hover { color: var(--c-warn); transform: scale(1.15); }
.rating-info { font-size: var(--text-sm); color: var(--c-text-2); }
.rating-info.muted { color: var(--c-text-3); font-size: var(--text-xs); }
</style>
