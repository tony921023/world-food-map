<script setup>
import { ref, watch } from "vue";
import { useAuth } from "../composables/useAuth.js";

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "goto"]);

const { authHeaders } = useAuth();
const comments = ref([]);
const loading = ref(false);

async function fetchMyComments() {
  loading.value = true;
  try {
    const res = await fetch("/api/auth/my-comments", {
      headers: authHeaders(),
    });
    if (!res.ok) {
      comments.value = [];
      return;
    }
    const data = await res.json();
    comments.value = data.comments || [];
  } catch {
    comments.value = [];
  } finally {
    loading.value = false;
  }
}

function handleGoto(c) {
  emit("goto", { code: c.country_code, name: c.food_name });
  emit("close");
}

watch(
  () => props.show,
  (val) => {
    if (val) fetchMyComments();
  }
);
</script>

<template>
  <div class="modal-mask" v-if="show" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <button class="close-btn" @click="emit('close')">&#10005;</button>
      <h2>我的留言</h2>

      <div v-if="loading" class="loading">載入中...</div>

      <div v-else-if="!comments.length" class="empty">
        還沒有留言紀錄
      </div>

      <div v-else class="comment-list">
        <div
          v-for="c in comments"
          :key="c.id"
          class="comment-item"
          @click="handleGoto(c)"
        >
          <div class="comment-food">
            <span class="food-name">{{ c.food_name }}</span>
            <span class="food-country">{{ c.country_code }}</span>
          </div>
          <p class="comment-text">{{ c.text }}</p>
          <div class="comment-time">
            {{ new Date(c.ts * 1000).toLocaleString() }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-content {
  width: 440px;
  max-width: calc(100% - 40px);
  max-height: calc(100% - 40px);
  overflow-y: auto;
  background: #fff;
  border-radius: 18px;
  padding: 18px 22px 22px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 12px;
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

h2 {
  margin: 0 0 12px;
}

.loading,
.empty {
  text-align: center;
  color: #6b7280;
  padding: 20px 0;
  font-size: 14px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.comment-item {
  padding: 10px 8px;
  border-radius: 10px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}
.comment-item:hover {
  background: #eff6ff;
}

.comment-food {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.food-name {
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}

.food-country {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 1px 6px;
  border-radius: 999px;
}

.comment-text {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  white-space: pre-wrap;
  line-height: 1.5;
}

.comment-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .modal-content {
    width: calc(100% - 24px);
    max-width: calc(100% - 24px);
  }
}
</style>
