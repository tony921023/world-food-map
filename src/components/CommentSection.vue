<script setup>
import { ref, watch, onUnmounted, computed } from "vue";
import { useCommentTokens } from "../composables/useCommentTokens.js";
import { useAuth } from "../composables/useAuth.js";
import { useToast } from "../composables/useToast.js";
import { apiFetch } from "../utils/api.js";

const props = defineProps({
  code:     { type: String, default: "" },
  foodName: { type: String, default: "" },
});

const { saveCommentToken, getCommentToken, removeCommentToken } = useCommentTokens();
const { isLoggedIn, user } = useAuth();
const { success: toastSuccess, error: toastError } = useToast();

const comments      = ref([]);
const newUser       = ref("");
const newText       = ref("");
const posting       = ref(false);
const commentError  = ref("");

// 排序：newest | most_liked
const sortOrder     = ref("newest");

// 回覆狀態
const replyingTo    = ref(null);   // { id, user } 正在回覆的留言
const replyText     = ref("");
const replyPosting  = ref(false);

// ── 驗證碼 ────────────────────────────────────────────────────────
const captchaQuestion = ref("");
const captchaAnswer   = ref("");
const captchaError    = ref("");

async function fetchCaptcha() {
  try {
    const res = await apiFetch("/api/captcha");
    if (!res.ok) return;
    const data = await res.json();
    captchaQuestion.value = data.question;
    captchaAnswer.value   = "";
    captchaError.value    = "";
  } catch { /* ignore */ }
}

// ── 冷卻計時 ──────────────────────────────────────────────────────
const cooldownSeconds = ref(0);
let _cooldownTimer = null;

function startCooldown(seconds) {
  cooldownSeconds.value = seconds;
  if (_cooldownTimer) clearInterval(_cooldownTimer);
  _cooldownTimer = setInterval(() => {
    if (cooldownSeconds.value > 0) {
      cooldownSeconds.value--;
    } else {
      clearInterval(_cooldownTimer);
      _cooldownTimer = null;
      if (!isLoggedIn.value) fetchCaptcha();
    }
  }, 1000);
}

onUnmounted(() => { if (_cooldownTimer) clearInterval(_cooldownTimer); });

// ── 字數統計 ──────────────────────────────────────────────────────
const MAX_LEN   = 300;
const charCount = computed(() => newText.value.length);
const overLimit = computed(() => charCount.value > MAX_LEN);

// ── 相對時間 ──────────────────────────────────────────────────────
function relativeTime(ts) {
  const now = Math.floor(Date.now() / 1000);
  const diff = now - ts;
  if (diff < 60) return "剛剛";
  if (diff < 3600) return `${Math.floor(diff / 60)}分鐘前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小時前`;
  return `${Math.floor(diff / 86400)}天前`;
}

// ── 頭像色彩 ──────────────────────────────────────────────────────
const AVATAR_COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
];

function avatarColor(name) {
  let hash = 0;
  for (let i = 0; i < (name || "").length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) & 0xffff;
  }
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

function avatarChar(name) {
  return (name || "匿")[0].toUpperCase();
}

// ── 留言排序 ──────────────────────────────────────────────────────
const totalReplies = computed(() =>
  comments.value.reduce((sum, c) => sum + (c.replies?.length || 0), 0)
);

const sortedComments = computed(() => {
  const list = [...comments.value];
  if (sortOrder.value === "most_liked") {
    list.sort((a, b) => (b.likes || 0) - (a.likes || 0));
  } else {
    list.sort((a, b) => (b.id || 0) - (a.id || 0));
  }
  return list;
});

// ── 留言清單 ──────────────────────────────────────────────────────
async function fetchComments() {
  if (!props.code || !props.foodName) return;
  try {
    const r    = await apiFetch(`/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments`);
    const data = await r.json();
    comments.value = data.comments || [];
  } catch {
    comments.value = [];
  }
}

async function submitComment() {
  if (!props.code || !props.foodName) return;
  commentError.value = "";

  if (overLimit.value) {
    commentError.value = `留言不能超過 ${MAX_LEN} 個字`;
    return;
  }
  if (cooldownSeconds.value > 0) {
    commentError.value = `請等待 ${cooldownSeconds.value} 秒後再留言`;
    return;
  }

  const payload = { text: (newText.value || "").trim() };
  if (!isLoggedIn.value) {
    payload.user = newUser.value || "匿名";
    // 前端驗證碼欄位
    if (!captchaQuestion.value) {
      commentError.value = "請先取得驗證碼";
      await fetchCaptcha();
      return;
    }
    const ans = parseInt(captchaAnswer.value, 10);
    if (isNaN(ans)) {
      commentError.value = "請填寫驗證碼答案";
      return;
    }
    payload.captcha_answer = ans;
  }
  if (!payload.text) return;

  try {
    posting.value = true;
    const r = await apiFetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
    );
    const created = await r.json();

    if (!r.ok) {
      commentError.value = created.error || "留言失敗";
      if (created.retry_after) startCooldown(created.retry_after);
      // 驗證碼錯誤或需要重新取得時重刷
      if (created.need_captcha || r.status === 400) await fetchCaptcha();
      return;
    }

    if (created.delete_token) saveCommentToken(created.id, created.delete_token);
    comments.value.unshift({ ...created, replies: [] });
    newText.value = "";
    toastSuccess("留言送出成功！");
    if (!isLoggedIn.value) await fetchCaptcha();
  } catch {
    commentError.value = "留言失敗，請稍後再試";
    toastError("留言失敗，請稍後再試");
  } finally {
    posting.value = false;
  }
}

function startReply(comment) {
  replyingTo.value = { id: comment.id, user: comment.user };
  replyText.value = "";
}

function cancelReply() {
  replyingTo.value = null;
  replyText.value = "";
}

async function submitReply(parentComment) {
  if (!replyText.value.trim() || replyPosting.value) return;
  replyPosting.value = true;
  try {
    const payload = {
      text: replyText.value.trim(),
      parent_id: parentComment.id,
    };
    if (!isLoggedIn.value) payload.user = newUser.value || "匿名";

    const r = await apiFetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
    );
    const created = await r.json();
    if (!r.ok) {
      toastError(created.error || "回覆失敗");
      return;
    }
    if (!parentComment.replies) parentComment.replies = [];
    parentComment.replies.push(created);
    replyText.value = "";
    replyingTo.value = null;
    toastSuccess("回覆成功！");
  } catch {
    toastError("回覆失敗，請稍後再試");
  } finally {
    replyPosting.value = false;
  }
}

function canDelete(comment) {
  if (isLoggedIn.value && user.value && comment.user_id === user.value.id) return true;
  return !!getCommentToken(comment.id);
}

async function deleteComment(comment) {
  if (!props.code || !props.foodName) return;
  if (!confirm("確定要刪除這則留言嗎？")) return;
  try {
    const headers = { "Content-Type": "application/json" };
    const body = {};
    if (!isLoggedIn.value || !user.value || comment.user_id !== user.value.id) {
      const token = getCommentToken(comment.id);
      if (!token) return;
      body.token = token;
    }
    const r = await apiFetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments/${comment.id}`,
      { method: "DELETE", headers, body: JSON.stringify(body) }
    );
    if (r.ok) {
      comments.value = comments.value.filter((c) => c.id !== comment.id);
      removeCommentToken(comment.id);
      toastSuccess("留言已刪除");
    } else {
      const data = await r.json().catch(() => ({}));
      toastError(data.error || "刪除失敗");
    }
  } catch {
    toastError("刪除失敗，請稍後再試");
  }
}

async function likeComment(comment) {
  if (!props.code || !props.foodName) return;
  try {
    const r = await apiFetch(
      `/api/food/${props.code}/${encodeURIComponent(props.foodName)}/comments/${comment.id}/like`,
      { method: "POST" }
    );
    const data = await r.json();
    if (!r.ok) {
      toastError(data.error || "按讚失敗");
      return;
    }
    if (Number.isFinite(data.likes)) comment.likes = data.likes;
  } catch {
    toastError("操作失敗，請稍後再試");
  }
}

watch(
  () => [props.code, props.foodName],
  ([c, f]) => {
    if (c && f) {
      fetchComments();
      if (!isLoggedIn.value) fetchCaptcha();
    }
  },
  { immediate: true }
);
</script>

<template>
  <div class="comment-section">
    <div class="comment-editor" @click.stop>
      <!-- 登入狀態顯示名稱 -->
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
        :class="{ 'over-limit': overLimit }"
        rows="3"
        placeholder="寫下你的看法..."
      ></textarea>

      <!-- 字數統計 -->
      <div class="char-count" :class="{ warn: charCount > MAX_LEN * 0.9, over: overLimit }">
        {{ charCount }} / {{ MAX_LEN }}
      </div>

      <!-- 驗證碼（僅匿名用戶） -->
      <div class="captcha-row" v-if="!isLoggedIn">
        <span class="captcha-label" v-if="captchaQuestion">{{ captchaQuestion }}</span>
        <span class="captcha-label muted" v-else>載入驗證碼中...</span>
        <input
          v-model="captchaAnswer"
          class="captcha-input"
          type="number"
          placeholder="答案"
          @focus="!captchaQuestion && fetchCaptcha()"
        />
        <button class="refresh-btn" @click="fetchCaptcha" title="重新取得驗證碼">↺</button>
      </div>

      <!-- 冷卻提示 -->
      <div class="cooldown-msg" v-if="cooldownSeconds > 0">
        請等待 {{ cooldownSeconds }} 秒後再留言
      </div>

      <div class="comment-error" v-if="commentError">{{ commentError }}</div>

      <button
        class="submit-btn"
        :disabled="posting || overLimit || cooldownSeconds > 0"
        @click="submitComment"
      >
        {{ posting ? "送出中..." : "送出留言" }}
      </button>
    </div>

    <div class="comment-list" v-if="comments.length">
      <div class="comment-list-header">
        <h3>
          留言（{{ comments.length }} 條<template v-if="totalReplies > 0">，含 {{ totalReplies }} 則回覆</template>）
        </h3>
        <div class="sort-toggle">
          <button
            class="sort-btn"
            :class="{ active: sortOrder === 'newest' }"
            @click="sortOrder = 'newest'"
          >最新</button>
          <button
            class="sort-btn"
            :class="{ active: sortOrder === 'most_liked' }"
            @click="sortOrder = 'most_liked'"
          >最多讚</button>
        </div>
      </div>

      <div class="comment-item" v-for="c in sortedComments" :key="c.id">
        <div class="meta">
          <span
            class="avatar"
            :style="{ background: avatarColor(c.user || '匿名') }"
          >{{ avatarChar(c.user || '匿名') }}</span>
          <strong class="meta-user">{{ c.user || "匿名" }}</strong>
          <span class="meta-time"> · {{ relativeTime(c.ts) }}</span>
        </div>
        <p class="text">{{ c.text }}</p>
        <div class="comment-actions">
          <button class="comment-like-btn" @click.stop="likeComment(c)">
            👍 {{ c.likes || 0 }}
          </button>
          <button class="reply-btn" @click.stop="startReply(c)">
            💬 回覆
          </button>
          <button
            class="comment-delete-btn"
            v-if="canDelete(c)"
            @click.stop="deleteComment(c)"
          >
            刪除
          </button>
        </div>

        <!-- 回覆輸入框 -->
        <div class="reply-editor" v-if="replyingTo?.id === c.id" @click.stop>
          <div class="reply-hint">回覆 <strong>{{ c.user }}</strong></div>
          <textarea
            v-model="replyText"
            class="comment-input text reply-input"
            rows="2"
            placeholder="寫下回覆..."
            autofocus
          ></textarea>
          <div class="reply-actions">
            <button class="submit-btn reply-submit-btn" :disabled="replyPosting || !replyText.trim()" @click="submitReply(c)">
              {{ replyPosting ? "送出中..." : "送出回覆" }}
            </button>
            <button class="cancel-reply-btn" @click="cancelReply">取消</button>
          </div>
        </div>

        <!-- 巢狀回覆 -->
        <div class="replies" v-if="c.replies && c.replies.length">
          <div class="reply-item" v-for="r in c.replies" :key="r.id">
            <div class="meta">
              <span
                class="avatar avatar-sm"
                :style="{ background: avatarColor(r.user || '匿名') }"
              >{{ avatarChar(r.user || '匿名') }}</span>
              <strong class="meta-user">{{ r.user || "匿名" }}</strong>
              <span class="meta-time"> · {{ relativeTime(r.ts) }}</span>
            </div>
            <p class="text">{{ r.text }}</p>
            <div class="comment-actions">
              <button class="comment-like-btn" @click.stop="likeComment(r)">
                👍 {{ r.likes || 0 }}
              </button>
              <button
                class="comment-delete-btn"
                v-if="canDelete(r)"
                @click.stop="deleteComment(r)"
              >
                刪除
              </button>
            </div>
          </div>
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
  font-size: var(--text-sm);
  color: var(--c-success);
  padding: 6px 10px;
  background: #f0fdf4;
  border-radius: var(--r-md);
  border: 1px solid #bbf7d0;
}
.comment-input {
  width: 100%;
  border: 1.5px solid var(--c-border);
  border-radius: var(--r-md);
  padding: 8px 10px;
  font-size: var(--text-base);
  box-sizing: border-box;
  outline: none;
  transition: border-color var(--dur);
  font-family: inherit;
  color: var(--c-text);
}
.comment-input:focus { border-color: var(--c-primary); }
.comment-input.over-limit { border-color: var(--c-error); }

.char-count {
  font-size: var(--text-xs);
  color: var(--c-text-3);
  text-align: right;
}
.char-count.warn { color: var(--c-warn); }
.char-count.over { color: var(--c-error); font-weight: 600; }

.captcha-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--c-hover);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: 8px 10px;
}
.captcha-label {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--c-text);
  white-space: nowrap;
}
.captcha-label.muted { color: var(--c-text-3); font-weight: 400; }
.captcha-input {
  width: 72px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  padding: 4px 8px;
  font-size: var(--text-base);
  text-align: center;
  outline: none;
}
.captcha-input:focus { border-color: var(--c-primary); }

.refresh-btn {
  border: none;
  background: var(--c-hover);
  border-radius: var(--r-sm);
  padding: 4px 8px;
  cursor: pointer;
  font-size: var(--text-md);
  color: var(--c-text-2);
  transition: background var(--dur);
}
.refresh-btn:hover { background: #cbd5e1; }

.cooldown-msg {
  font-size: var(--text-sm);
  color: #92400e;
  padding: 6px 10px;
  background: #fffbeb;
  border-radius: var(--r-md);
  border: 1px solid #fde68a;
  text-align: center;
}
.comment-error { color: var(--c-error); font-size: var(--text-sm); }

.submit-btn {
  border: none;
  border-radius: var(--r-md);
  padding: 8px 16px;
  cursor: pointer;
  background: var(--c-primary);
  color: #fff;
  font-size: var(--text-base);
  font-weight: 600;
  transition: background var(--dur);
}
.submit-btn:hover:not([disabled]) { background: var(--c-primary-hover); }
.submit-btn[disabled] { opacity: 0.6; cursor: not-allowed; }

/* Comment list header with sort toggle */
.comment-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 10px 0 6px;
}
.comment-list-header h3 {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--c-text);
}
.sort-toggle {
  display: flex;
  gap: 4px;
}
.sort-btn {
  border: 1px solid var(--c-border);
  background: var(--c-surface);
  border-radius: var(--r-full);
  padding: 3px 10px;
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  color: var(--c-text-3);
  transition: all var(--dur);
}
.sort-btn:hover { border-color: var(--c-primary); color: var(--c-primary); }
.sort-btn.active { background: var(--c-primary); color: #fff; border-color: var(--c-primary); }

/* Avatar */
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  margin-right: 2px;
}
.avatar-sm {
  width: 20px;
  height: 20px;
  font-size: 10px;
}

.comment-list .comment-item {
  padding: 10px 0;
  border-top: 1px solid var(--c-hover);
}
.comment-list .comment-item .meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-sm);
  color: var(--c-text-3);
}
.comment-list .comment-item .text {
  margin: 4px 0 0;
  white-space: pre-wrap;
  font-size: var(--text-base);
  color: var(--c-text-2);
  line-height: 1.55;
}
.comment-actions { display: flex; gap: 8px; margin-top: 6px; }

.comment-like-btn {
  border: none;
  background: var(--c-hover);
  border-radius: var(--r-sm);
  padding: 3px 10px;
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--c-text-2);
  min-height: 28px;
  transition: background var(--dur);
}
.comment-like-btn:hover { background: #e2e8f0; }

.comment-delete-btn {
  border: none;
  background: var(--c-error-light);
  border-radius: var(--r-sm);
  padding: 3px 10px;
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--c-error);
  min-height: 28px;
  transition: background var(--dur);
}
.comment-delete-btn:hover { background: #fecaca; }

.meta-user { color: var(--c-text); font-size: var(--text-base); }
.meta-time  { color: var(--c-text-3); font-size: var(--text-xs); }

.reply-btn {
  border: none;
  background: transparent;
  color: var(--c-primary);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 3px 8px;
  border-radius: var(--r-sm);
  transition: background var(--dur);
}
.reply-btn:hover { background: var(--c-hover-blue); }

.reply-editor {
  margin-top: 8px;
  padding: 10px 12px;
  background: var(--c-hover);
  border-radius: var(--r-md);
  border-left: 3px solid var(--c-primary);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.reply-hint {
  font-size: var(--text-sm);
  color: var(--c-text-3);
}
.reply-input { resize: none; }
.reply-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.reply-submit-btn {
  padding: 5px 14px;
  font-size: var(--text-sm);
}
.cancel-reply-btn {
  border: none;
  background: transparent;
  color: var(--c-text-3);
  font-size: var(--text-sm);
  cursor: pointer;
  padding: 5px 10px;
  border-radius: var(--r-sm);
}
.cancel-reply-btn:hover { color: var(--c-text-2); background: var(--c-hover); }

/* 巢狀回覆區 */
.replies {
  margin-top: 8px;
  margin-left: 16px;
  border-left: 2px solid var(--c-border);
  padding-left: 12px;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.reply-item {
  padding: 8px 0;
  border-top: 1px solid var(--c-hover);
}
.reply-item:first-child { border-top: none; }

@media (max-width: 768px) {
  .submit-btn, .comment-like-btn, .comment-delete-btn {
    min-width: 44px; min-height: 44px;
    display: inline-flex; align-items: center; justify-content: center;
  }
}
</style>
