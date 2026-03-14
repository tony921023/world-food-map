<script setup>
import { ref, watch } from "vue";
import { useCommentTokens } from "../composables/useCommentTokens.js";
import { useAuth } from "../composables/useAuth.js";

const props = defineProps({
  code: { type: String, default: "" },
  foodName: { type: String, default: "" },
});

const { saveCommentToken, getCommentToken, removeCommentToken } = useCommentTokens();
const { isLoggedIn, user, authHeaders } = useAuth();

const comments = ref([]);
const newUser = ref("");
const newText = ref("");
const posting = ref(false);
const commentError = ref("");

async function fetchComments() {
  if (!props.code || !props.foodName) return;
  try {
    const r = await fetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments`
    );
    const data = await r.json();
    comments.value = data.comments || [];
  } catch {
    comments.value = [];
  }
}

async function submitComment() {
  if (!props.code || !props.foodName) return;
  commentError.value = "";
  const payload = {
    text: (newText.value || "").trim(),
  };
  if (!isLoggedIn.value) {
    payload.user = newUser.value || "匿名";
  }
  if (!payload.text) return;
  try {
    posting.value = true;
    const headers = { "Content-Type": "application/json" };
    if (isLoggedIn.value) {
      Object.assign(headers, authHeaders());
    }
    const r = await fetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments`,
      {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      }
    );
    const created = await r.json();
    if (!r.ok) {
      commentError.value = created.error || "留言失敗";
      return;
    }
    if (created.delete_token) {
      saveCommentToken(created.id, created.delete_token);
    }
    comments.value.unshift(created);
    newText.value = "";
  } catch {
    commentError.value = "留言失敗，請稍後再試";
  } finally {
    posting.value = false;
  }
}

function canDelete(comment) {
  // Logged-in user can delete their own comments
  if (isLoggedIn.value && user.value && comment.user_id === user.value.id) {
    return true;
  }
  // Or has delete token
  return !!getCommentToken(comment.id);
}

async function deleteComment(comment) {
  if (!props.code || !props.foodName) return;
  if (!confirm("確定要刪除這則留言嗎？")) return;

  try {
    const headers = { "Content-Type": "application/json" };
    const body = {};

    if (isLoggedIn.value && user.value && comment.user_id === user.value.id) {
      // Use auth header for own comments
      Object.assign(headers, authHeaders());
    } else {
      const token = getCommentToken(comment.id);
      if (!token) return;
      body.token = token;
    }

    const r = await fetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments/${comment.id}`,
      {
        method: "DELETE",
        headers,
        body: JSON.stringify(body),
      }
    );
    if (r.ok) {
      comments.value = comments.value.filter((c) => c.id !== comment.id);
      removeCommentToken(comment.id);
    }
  } catch { /* ignore */ }
}

async function likeComment(comment) {
  if (!props.code || !props.foodName) return;
  try {
    const r = await fetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments/${comment.id}/like`,
      { method: "POST" }
    );
    const data = await r.json();
    if (Number.isFinite(data.likes)) {
      comment.likes = data.likes;
    }
  } catch { /* ignore */ }
}

// Fetch comments when code/foodName changes
watch(
  () => [props.code, props.foodName],
  ([c, f]) => {
    if (c && f) fetchComments();
  },
  { immediate: true }
);
</script>

<template>
  <div class="comment-section">
    <div class="comment-editor" @click.stop>
      <!-- Show name input only for anonymous users -->
      <template v-if="isLoggedIn && user">
        <div class="comment-as">
          以 <strong>{{ user.display_name }}</strong> 的身分留言
        </div>
      </template>
      <template v-else>
        <input
          v-model="newUser"
          class="comment-input name"
          type="text"
          placeholder="你的名字（可留空，預設匿名）"
        />
      </template>
      <textarea
        v-model="newText"
        class="comment-input text"
        rows="3"
        placeholder="寫下你的看法..."
      ></textarea>
      <div class="comment-error" v-if="commentError">{{ commentError }}</div>
      <button class="submit-btn" :disabled="posting" @click="submitComment">
        送出留言
      </button>
    </div>

    <div class="comment-list" v-if="comments.length">
      <h3 style="margin: 10px 0 6px">留言</h3>
      <div class="comment-item" v-for="c in comments" :key="c.id">
        <div class="meta">
          <strong>{{ c.user || "匿名" }}</strong>
          <span> · {{ new Date(c.ts * 1000).toLocaleString() }}</span>
        </div>
        <p class="text">{{ c.text }}</p>
        <div class="comment-actions">
          <button class="comment-like-btn" @click.stop="likeComment(c)">
            &#128077; {{ c.likes || 0 }}
          </button>
          <button
            class="comment-delete-btn"
            v-if="canDelete(c)"
            @click.stop="deleteComment(c)"
          >
            刪除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comment-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 10px 0 16px;
}

.comment-as {
  font-size: 13px;
  color: #4b5563;
  padding: 6px 10px;
  background: #f0fdf4;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
}

.comment-input {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
  box-sizing: border-box;
}

.comment-error {
  color: #dc2626;
  font-size: 13px;
}

.submit-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
  background: #2563eb;
  color: #fff;
  font-size: 14px;
}
.submit-btn[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

.comment-list .comment-item {
  padding: 10px 0;
  border-top: 1px dashed #e5e7eb;
}
.comment-list .comment-item .meta {
  font-size: 13px;
  color: #6b7280;
}
.comment-list .comment-item .text {
  margin: 4px 0 0;
  white-space: pre-wrap;
}

.comment-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

.comment-like-btn {
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  font-size: 12px;
  color: #374151;
  min-height: 28px;
}
.comment-like-btn:hover {
  background: #e5e7eb;
}

.comment-delete-btn {
  border: none;
  background: #fee2e2;
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  font-size: 12px;
  color: #dc2626;
  min-height: 28px;
}
.comment-delete-btn:hover {
  background: #fecaca;
}

@media (max-width: 768px) {
  .submit-btn,
  .comment-like-btn,
  .comment-delete-btn {
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
