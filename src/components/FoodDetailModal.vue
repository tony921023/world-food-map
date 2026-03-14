<script setup>
import { computed, watch } from "vue";
import ShareButtons from "./ShareButtons.vue";
import CommentSection from "./CommentSection.vue";
import StarRating from "./StarRating.vue";
import { useRatings } from "../composables/useRatings.js";

const props = defineProps({
  show: { type: Boolean, default: false },
  food: { type: Object, default: null },
  code: { type: String, default: "" },
  countryName: { type: String, default: "" },
  likesCount: { type: Number, default: 0 },
  hasLiked: { type: Boolean, default: false },
  likeLoading: { type: Boolean, default: false },
  isFavorite: { type: Boolean, default: false },
  isLoggedIn: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "like", "toggle-favorite", "need-auth"]);

const { getRating, fetchRating, submitRating } = useRatings();

watch(
  () => [props.show, props.food?.name],
  ([show, name]) => {
    if (show && props.code && name) {
      fetchRating(props.code, name);
    }
  },
  { immediate: true }
);

const currentRating = computed(() =>
  props.code && props.food?.name
    ? getRating(props.code, props.food.name)
    : { avg: 0, count: 0, myRating: 0 }
);

async function handleRate(stars) {
  if (props.code && props.food?.name) {
    await submitRating(props.code, props.food.name, stars);
  }
}

const googleMapUrl = computed(() => {
  if (!props.food) return "https://www.google.com/maps";
  const qCountry = props.countryName || props.code || "";
  const q = encodeURIComponent(`${qCountry} ${props.food.name} 美食`);
  return `https://www.google.com/maps/search/${q}`;
});

function handleFavClick() {
  if (!props.isLoggedIn) {
    emit("need-auth");
    return;
  }
  emit("toggle-favorite");
}
</script>

<template>
  <div class="modal-mask" v-if="show" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <button class="close-btn" @click="emit('close')">✕</button>
      <img class="modal-food-img" :src="food?.img" />
      <h2>{{ food?.name }}</h2>

      <!-- Tags -->
      <div class="modal-tags" v-if="food?.tags?.length">
        <span class="tag-badge" v-for="t in food.tags" :key="t">{{ t }}</span>
      </div>

      <!-- Star Rating -->
      <StarRating
        :avg="currentRating.avg"
        :count="currentRating.count"
        :my-rating="currentRating.myRating"
        @rate="handleRate"
      />

      <p class="food-desc">
        {{ food?.desc || "這道料理還沒有詳細介紹。" }}
      </p>

      <!-- Like / Favorite -->
      <div class="like-row">
        <div class="like-main">
          <button
            class="like-btn"
            :class="{ liked: hasLiked }"
            :disabled="likeLoading"
            @click.stop="emit('like')"
          >
            {{ hasLiked ? '👍 已按讚' : '👍 按讚' }}
          </button>
          <span class="likes">{{ likesCount }} 個讚</span>
          <button
            class="fav-btn"
            :class="{ active: isFavorite }"
            @click.stop="handleFavClick"
          >
            {{ !isLoggedIn ? '🤍 收藏' : isFavorite ? '❤️ 已收藏' : '🤍 收藏' }}
          </button>
        </div>

        <a
          class="map-link"
          :href="googleMapUrl"
          target="_blank"
          rel="noopener"
          @click.stop
        >
          在附近找這道料理
        </a>
      </div>

      <!-- Share -->
      <ShareButtons :code="code" :food-name="food?.name || ''" />

      <!-- Comments -->
      <CommentSection :code="code" :food-name="food?.name || ''" />
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}

.modal-content {
  width: 480px;
  max-width: calc(100% - 40px);
  max-height: calc(100% - 40px);
  overflow-y: auto;
  background: var(--c-surface);
  border-radius: var(--r-xl);
  padding: 18px 22px 22px;
  position: relative;
  box-shadow: var(--shadow-lg);
  animation: popIn 0.25s var(--ease);
}

.close-btn {
  position: absolute;
  top: 10px; right: 12px;
  border: none;
  background: var(--c-hover);
  color: var(--c-text-2);
  font-size: 14px;
  cursor: pointer;
  width: 30px; height: 30px;
  border-radius: var(--r-full);
  display: flex; align-items: center; justify-content: center;
  padding: 0;
  transition: background var(--dur);
}
.close-btn:hover { background: #e2e8f0; }

.modal-food-img {
  width: 100%;
  max-height: 260px;
  object-fit: cover;
  border-radius: var(--r-lg);
  margin-bottom: 12px;
}

.modal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 4px 0 8px;
}

.food-desc {
  margin: 8px 0 6px;
  line-height: 1.6;
  color: var(--c-text-2);
  font-size: var(--text-base);
}

.like-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 8px 0 6px;
}
.like-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.like-btn {
  border: 2px solid var(--c-primary);
  border-radius: var(--r-full);
  padding: 7px 18px;
  cursor: pointer;
  background: var(--c-surface);
  color: var(--c-primary);
  font-size: var(--text-base);
  font-weight: 600;
  transition: all var(--dur);
}
.like-btn:hover:not([disabled]) { background: var(--c-hover-blue); }
.like-btn.liked { background: var(--c-primary); color: #fff; }
.like-btn.liked:hover:not([disabled]) { background: var(--c-primary-hover); }
.like-btn[disabled] { opacity: 0.6; cursor: not-allowed; }

.likes {
  font-size: var(--text-base);
  color: var(--c-text);
  font-weight: 600;
}

.fav-btn {
  border: 1px solid var(--c-border);
  border-radius: var(--r-full);
  padding: 6px 14px;
  cursor: pointer;
  background: var(--c-hover);
  color: var(--c-text-2);
  font-size: var(--text-sm);
  font-weight: 600;
  transition: all var(--dur);
}
.fav-btn:hover { background: #e2e8f0; }
.fav-btn.active { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

.map-link {
  display: inline-flex;
  width: 100%;
  justify-content: center;
  margin-top: 2px;
  font-size: var(--text-sm);
  font-weight: 600;
  padding: 8px 10px;
  border-radius: var(--r-full);
  text-decoration: none;
  background: #10b981;
  color: #fff;
  box-sizing: border-box;
  transition: background var(--dur);
}
.map-link:hover { background: #059669; }

@media (max-width: 1024px) {
  .modal-content { width: 420px; }
}

@media (max-width: 768px) {
  .modal-content {
    width: calc(100% - 24px);
    max-width: calc(100% - 24px);
  }
  .like-btn, .fav-btn {
    min-width: 44px; min-height: 44px;
    display: inline-flex; align-items: center; justify-content: center;
  }
}
</style>
