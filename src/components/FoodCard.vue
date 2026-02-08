<script setup>
import { ref, computed } from 'vue'

const { food, code } = defineProps({
  // food 會有 { name, img, likes? }
  food: { type: Object, required: true },
  code: { type: String, required: true }   // JP / TW / KR
})

const detail = ref(null)
const loading = ref(false)
const error = ref(null)

// 初始先用後端帶來的 likes
const likesCount = ref(food.likes ?? 0)
const likeLoading = ref(false)

const comments = ref([])
const posting = ref(false)
const newUser = ref('')
const newText = ref('')

// 右上角徽章用的讚數（detail 打開／按讚後會更新）
const badgeLikes = computed(() => likesCount.value ?? (food.likes ?? 0))

// 取得料理介紹 + 互動資料
async function loadDetail() {
  if (loading.value) return
  loading.value = true
  error.value = null
  try {
    // 第一次點才抓介紹，之後只更新 likes / comments
    if (!detail.value) {
      const res = await fetch(`/api/food/${code.toUpperCase()}/${encodeURIComponent(food.name)}`)
      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        const errMsg = errData?.error || res.statusText
        throw new Error(errMsg || '取得料理介紹失敗')
      }
      detail.value = await res.json()
    }
    await Promise.all([fetchLikes(), fetchComments()])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// 取得讚數
async function fetchLikes() {
  const r = await fetch(`/api/food/${code.toUpperCase()}/${encodeURIComponent(food.name)}/likes`)
  const data = await r.json().catch(() => ({}))
  if (Number.isFinite(data.likes)) {
    likesCount.value = data.likes
  }
}

// 按讚
async function doLike() {
  if (likeLoading.value) return
  likeLoading.value = true
  try {
    const r = await fetch(
      `/api/food/${code.toUpperCase()}/${encodeURIComponent(food.name)}/like`,
      { method: 'POST' }
    )
    const data = await r.json().catch(() => ({}))
    if (Number.isFinite(data.likes)) {
      likesCount.value = data.likes
    }
  } finally {
    likeLoading.value = false
  }
}

// 取得留言
async function fetchComments() {
  const r = await fetch(`/api/food/${code.toUpperCase()}/${encodeURIComponent(food.name)}/comments`)
  const data = await r.json().catch(() => ({}))
  comments.value = Array.isArray(data.comments) ? data.comments : []
}

// 送出留言
async function submitComment() {
  const payload = {
    user: newUser.value || '匿名',
    text: (newText.value || '').trim()
  }
  if (!payload.text) return
  try {
    posting.value = true
    const r = await fetch(
      `/api/food/${code.toUpperCase()}/${encodeURIComponent(food.name)}/comments`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    )
    if (!r.ok) throw new Error('留言失敗')
    const created = await r.json()
    comments.value.unshift(created)
    newText.value = ''
  } catch (e) {
    alert(e.message || '留言失敗，請稍後再試')
  } finally {
    posting.value = false
  }
}
</script>

<template>
  <div class="card" @click="loadDetail">
    <div class="img-wrap">
      <img :src="food.img" class="card-img" :alt="food.name" loading="lazy" />
      <!-- 👍 右上角讚數徽章 -->
      <div class="likes-badge" title="讚數">
        👍 {{ badgeLikes.toLocaleString() }}
      </div>
    </div>

    <h3 class="name">{{ food.name }}</h3>

    <p v-if="loading" class="sub loading">載入中...</p>
    <p v-else-if="error" class="sub error">{{ error }}</p>

    <!-- 展開後才顯示介紹 + 互動 -->
    <div v-else-if="detail" class="detail" @click.stop>
      <p class="desc">{{ detail.desc || '這道料理還沒有詳細介紹。' }}</p>

      <div class="like-row">
        <button class="like-btn" :disabled="likeLoading" @click.stop="doLike">
          👍 按讚
        </button>
        <span class="likes">已獲得 {{ likesCount }} 個讚</span>
      </div>

      <div class="comment-editor">
        <input
          v-model="newUser"
          class="comment-input name"
          type="text"
          placeholder="你的名字（可留空，預設匿名）"
          @click.stop
        />
        <textarea
          v-model="newText"
          class="comment-input text"
          rows="3"
          placeholder="寫下你的看法..."
          @click.stop
        ></textarea>
        <button class="submit-btn" :disabled="posting" @click.stop="submitComment">
          送出留言
        </button>
      </div>

      <div class="comment-list" v-if="comments.length">
        <h4 class="c-title">留言</h4>
        <div class="comment-item" v-for="c in comments" :key="c.id">
          <div class="meta">
            <strong>{{ c.user || '匿名' }}</strong>
            <span> · {{ new Date(c.ts * 1000).toLocaleString() }}</span>
          </div>
          <p class="text">{{ c.text }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  height: var(--card-h, 260px);
  padding: 0 0 10px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.img-wrap {
  position: relative;
  width: 100%;
  height: 62%;
  overflow: hidden;
}
.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 右上角讚數徽章 */
.likes-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  backdrop-filter: blur(2px);
}

.name {
  margin: 10px 12px 0;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.detail { margin: 6px 12px 0; }

/* 雙行截斷 */
.desc {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.4;
  margin-bottom: 6px;
  overflow: hidden;
  line-clamp: 2;                 /* 標準 */
  display: -webkit-box;          /* WebKit */
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.like-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0 12px;
}
.like-btn,
.submit-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
  background: #2563eb;
  color: #fff;
  font-size: 14px;
}
.like-btn[disabled],
.submit-btn[disabled] {
  opacity: .6;
  cursor: not-allowed;
}
.likes { font-size: 14px; color: #333; }

.comment-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 10px 0 16px;
}
.comment-input {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
}
.comment-list .c-title { margin: 10px 0 6px; }
.comment-list .comment-item {
  padding: 10px 0;
  border-top: 1px dashed #e5e7eb;
}
.comment-list .comment-item .meta { font-size: 13px; color: #6b7280; }
.comment-list .comment-item .text {
  margin: 4px 0 0;
  white-space: pre-wrap;
}

.sub { margin: 6px 12px 0; font-size: 14px; }
.loading { color: #6b7280; }
.error { color: #dc2626; }
</style>
