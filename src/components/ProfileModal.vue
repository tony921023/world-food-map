<script setup>
import { ref, watch, computed } from "vue";
import { useAuth } from "../composables/useAuth.js";
import { useFavorites } from "../composables/useFavorites.js";

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "goto"]);

const { user, authHeaders } = useAuth();
const { myFavorites } = useFavorites();

// ── 分頁 ──────────────────────────────────────────────────────────
const activeTab = ref("account");  // account | comments | favorites

// ── 帳號設定 ──────────────────────────────────────────────────────
const editName     = ref("");
const currentPw    = ref("");
const newPw        = ref("");
const confirmPw    = ref("");
const saveMsg      = ref("");
const saveError    = ref("");
const saving       = ref(false);

function initForm() {
  editName.value  = user.value?.display_name || "";
  currentPw.value = "";
  newPw.value     = "";
  confirmPw.value = "";
  saveMsg.value   = "";
  saveError.value = "";
}

async function saveProfile() {
  saveMsg.value   = "";
  saveError.value = "";

  const body: Record<string, string> = {};
  const trimmedName = editName.value.trim();
  if (trimmedName && trimmedName !== user.value?.display_name) {
    body.display_name = trimmedName;
  }
  if (currentPw.value || newPw.value) {
    if (newPw.value !== confirmPw.value) {
      saveError.value = "新密碼與確認密碼不一致";
      return;
    }
    if (newPw.value.length < 6) {
      saveError.value = "新密碼至少需要 6 個字元";
      return;
    }
    body.current_password = currentPw.value;
    body.new_password     = newPw.value;
  }

  if (!Object.keys(body).length) {
    saveMsg.value = "沒有變更";
    return;
  }

  saving.value = true;
  try {
    const res = await fetch("/api/auth/profile", {
      method:  "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body:    JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      saveError.value = data.error || "儲存失敗";
      return;
    }
    // 更新 user singleton（重新 checkAuth 會自動同步，這裡直接改 display_name）
    if (user.value && data.user?.display_name) {
      user.value.display_name = data.user.display_name;
    }
    saveMsg.value = "儲存成功！";
    currentPw.value = "";
    newPw.value     = "";
    confirmPw.value = "";
  } catch {
    saveError.value = "網路錯誤，請稍後再試";
  } finally {
    saving.value = false;
  }
}

// ── 我的留言 ──────────────────────────────────────────────────────
const myComments = ref([]);
const loadingComments = ref(false);

async function fetchMyComments() {
  loadingComments.value = true;
  try {
    const res = await fetch("/api/auth/my-comments", { headers: authHeaders() });
    if (!res.ok) { myComments.value = []; return; }
    const data = await res.json();
    myComments.value = data.comments || [];
  } catch {
    myComments.value = [];
  } finally {
    loadingComments.value = false;
  }
}

function gotoComment(c) {
  emit("goto", { code: c.country_code, name: c.food_name });
  emit("close");
}

// ── 初始化 ────────────────────────────────────────────────────────
watch(
  () => props.show,
  (val) => {
    if (val) {
      activeTab.value = "account";
      initForm();
    }
  }
);

watch(activeTab, (tab) => {
  if (tab === "comments" && !myComments.value.length) fetchMyComments();
});
</script>

<template>
  <div class="modal-mask" v-if="show" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <button class="close-btn" @click="emit('close')">✕</button>
      <h2>個人資料</h2>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="['tab', { active: activeTab === 'account'   }]" @click="activeTab = 'account'">帳號設定</button>
        <button :class="['tab', { active: activeTab === 'comments'  }]" @click="activeTab = 'comments'">我的留言</button>
        <button :class="['tab', { active: activeTab === 'favorites' }]" @click="activeTab = 'favorites'">我的收藏</button>
      </div>

      <!-- Tab: 帳號設定 -->
      <div v-if="activeTab === 'account'" class="tab-content">
        <div class="info-row">
          <span class="label">Email</span>
          <span class="value">{{ user?.email }}</span>
        </div>

        <div class="section-title">修改顯示名稱</div>
        <input
          v-model="editName"
          class="field-input"
          type="text"
          placeholder="顯示名稱"
          maxlength="30"
        />

        <div class="section-title" style="margin-top: 16px">修改密碼</div>
        <input v-model="currentPw" class="field-input" type="password" placeholder="目前密碼" />
        <input v-model="newPw"     class="field-input" type="password" placeholder="新密碼（至少 6 個字元）" />
        <input v-model="confirmPw" class="field-input" type="password" placeholder="確認新密碼" />

        <div class="save-msg"   v-if="saveMsg">{{ saveMsg }}</div>
        <div class="save-error" v-if="saveError">{{ saveError }}</div>

        <button class="save-btn" :disabled="saving" @click="saveProfile">
          {{ saving ? "儲存中..." : "儲存變更" }}
        </button>
      </div>

      <!-- Tab: 我的留言 -->
      <div v-if="activeTab === 'comments'" class="tab-content">
        <div v-if="loadingComments" class="empty">載入中...</div>
        <div v-else-if="!myComments.length" class="empty">還沒有留言紀錄</div>
        <div v-else class="comment-list">
          <div
            v-for="c in myComments"
            :key="c.id"
            class="comment-item"
            @click="gotoComment(c)"
          >
            <div class="comment-meta">
              <span class="food-name">{{ c.food_name }}</span>
              <span class="country-tag">{{ c.country_code }}</span>
            </div>
            <p class="comment-text">{{ c.text }}</p>
            <div class="comment-time">{{ new Date(c.ts * 1000).toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Tab: 我的收藏 -->
      <div v-if="activeTab === 'favorites'" class="tab-content">
        <div v-if="!myFavorites.length" class="empty">還沒有收藏任何料理</div>
        <div v-else class="fav-list">
          <div
            v-for="f in myFavorites"
            :key="f.id"
            class="fav-item"
            @click="emit('goto', { code: f.code, name: f.name }); emit('close')"
          >
            <span class="fav-name">{{ f.name }}</span>
            <span class="fav-code">{{ f.code }}</span>
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
  background: rgba(15,23,42,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 55;
}
.modal-content {
  width: 460px;
  max-width: calc(100% - 40px);
  max-height: calc(100% - 60px);
  overflow-y: auto;
  background: #fff;
  border-radius: 18px;
  padding: 18px 22px 24px;
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
h2 { margin: 0 0 14px; }

/* Tabs */
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  background: #f3f4f6;
  border-radius: 10px;
  padding: 4px;
}
.tab {
  flex: 1;
  border: none;
  background: transparent;
  border-radius: 8px;
  padding: 7px 0;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}
.tab.active {
  background: #fff;
  color: #2563eb;
  box-shadow: 0 1px 4px rgba(15,23,42,0.1);
}

/* Tab content */
.tab-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 4px;
}
.label { font-size: 13px; color: #6b7280; min-width: 52px; }
.value { font-size: 14px; color: #111827; font-weight: 600; }
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-top: 4px;
}
.field-input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  box-sizing: border-box;
}
.field-input:focus {
  outline: none;
  border-color: #2563eb;
}
.save-msg   { color: #16a34a; font-size: 13px; }
.save-error { color: #dc2626; font-size: 13px; }
.save-btn {
  border: none;
  background: #2563eb;
  color: #fff;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}
.save-btn[disabled] { opacity: 0.6; cursor: not-allowed; }

/* Comments tab */
.empty {
  text-align: center;
  color: #9ca3af;
  padding: 24px 0;
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
.comment-item:hover { background: #eff6ff; }
.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.food-name    { font-weight: 600; font-size: 14px; color: #1e293b; }
.country-tag  { font-size: 11px; color: #6b7280; background: #f3f4f6; padding: 1px 6px; border-radius: 999px; }
.comment-text { margin: 0; font-size: 13px; color: #4b5563; white-space: pre-wrap; line-height: 1.5; }
.comment-time { font-size: 11px; color: #9ca3af; margin-top: 4px; }

/* Favorites tab */
.fav-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.fav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}
.fav-item:hover { background: #eff6ff; }
.fav-name { font-weight: 600; font-size: 14px; color: #1e293b; }
.fav-code { font-size: 11px; color: #6b7280; background: #f3f4f6; padding: 1px 6px; border-radius: 999px; }

@media (max-width: 768px) {
  .modal-content { width: calc(100% - 24px); max-width: calc(100% - 24px); }
}
</style>
