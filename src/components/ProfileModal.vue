<script setup>
import { ref, watch, computed } from "vue";
import { useAuth } from "../composables/useAuth.js";
import { useFavorites } from "../composables/useFavorites.js";
import { apiFetch } from "../utils/api.js";

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "goto"]);

const { user } = useAuth();
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

  const body = {};
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
    const res = await apiFetch("/api/auth/profile", {
      method:  "PUT",
      headers: { "Content-Type": "application/json" },
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
    const res = await apiFetch("/api/auth/my-comments");
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
  position: fixed; inset: 0;
  background: var(--overlay);
  display: flex; align-items: center; justify-content: center;
  z-index: 60;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}
.modal-content {
  width: 480px;
  max-width: calc(100% - 32px);
  max-height: calc(100vh - 60px);
  overflow-y: auto;
  background: var(--c-surface);
  border-radius: var(--r-xl);
  padding: 28px 26px 28px;
  position: relative;
  box-shadow: var(--shadow-lg);
  animation: popIn 0.25s var(--ease);
}
.close-btn {
  position: absolute; top: 14px; right: 16px;
  background: var(--c-hover); border: none; cursor: pointer;
  width: 30px; height: 30px; border-radius: var(--r-full);
  font-size: 14px; display: flex; align-items: center; justify-content: center;
  padding: 0; color: var(--c-text-2); transition: background var(--dur);
}
.close-btn:hover { background: #e2e8f0; }
h2 { font-size: var(--text-2xl); font-weight: 800; margin: 0 0 18px; letter-spacing: -0.3px; }

.tabs {
  display: flex; gap: 4px; margin-bottom: 18px;
  background: var(--c-hover); border-radius: var(--r-lg); padding: 4px;
}
.tab {
  flex: 1; border: none; background: transparent;
  border-radius: var(--r-md); padding: 8px 0;
  font-size: var(--text-sm); font-weight: 700; color: var(--c-text-3);
  cursor: pointer; transition: all var(--dur);
}
.tab.active {
  background: var(--c-surface); color: var(--c-primary);
  box-shadow: var(--shadow-sm);
}

.tab-content { display: flex; flex-direction: column; gap: 10px; }

.info-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: var(--c-hover);
  border-radius: var(--r-md); margin-bottom: 2px;
}
.label { font-size: var(--text-sm); color: var(--c-text-3); min-width: 52px; font-weight: 600; }
.value { font-size: var(--text-base); color: var(--c-text); font-weight: 700; }

.section-title {
  font-size: var(--text-sm); font-weight: 700; color: var(--c-text-2);
  text-transform: uppercase; letter-spacing: 0.4px; margin-top: 4px;
}
.field-input {
  width: 100%; border: 1.5px solid var(--c-border); border-radius: var(--r-md);
  padding: 9px 13px; font-size: var(--text-base); box-sizing: border-box;
  outline: none; transition: border-color var(--dur), box-shadow var(--dur);
}
.field-input:focus { border-color: var(--c-primary); box-shadow: 0 0 0 3px var(--c-primary-ring); }

.save-msg   { color: var(--c-success); font-size: var(--text-sm); background: #f0fdf4; padding: 8px 12px; border-radius: var(--r-md); }
.save-error { color: var(--c-error);   font-size: var(--text-sm); background: var(--c-error-light); padding: 8px 12px; border-radius: var(--r-md); }

.save-btn {
  border: none; background: var(--c-primary); color: #fff;
  border-radius: var(--r-md); padding: 10px 20px;
  font-size: var(--text-base); font-weight: 700; cursor: pointer; margin-top: 4px;
  transition: background var(--dur), transform 0.1s;
}
.save-btn:hover:not([disabled]) { background: var(--c-primary-hover); transform: translateY(-1px); }
.save-btn[disabled] { opacity: 0.55; cursor: not-allowed; }

.empty {
  text-align: center; color: var(--c-text-3);
  padding: 32px 0; font-size: var(--text-base);
}

.comment-list, .fav-list { display: flex; flex-direction: column; gap: 2px; }

.comment-item {
  padding: 10px 10px; border-radius: var(--r-md);
  cursor: pointer; border-bottom: 1px solid var(--c-hover);
  transition: background var(--dur);
}
.comment-item:hover { background: var(--c-hover-blue); }
.comment-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.food-name   { font-weight: 700; font-size: var(--text-base); color: var(--c-text); }
.country-tag { font-size: var(--text-xs); color: var(--c-text-3); background: var(--c-hover); padding: 2px 7px; border-radius: var(--r-full); }
.comment-text { font-size: var(--text-sm); color: var(--c-text-2); white-space: pre-wrap; line-height: 1.55; }
.comment-time { font-size: var(--text-xs); color: var(--c-text-3); margin-top: 4px; }

.fav-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: var(--r-md);
  cursor: pointer; border-bottom: 1px solid var(--c-hover);
  transition: background var(--dur);
}
.fav-item:hover { background: var(--c-hover-blue); }
.fav-name { font-weight: 700; font-size: var(--text-base); color: var(--c-text); }
.fav-code { font-size: var(--text-xs); color: var(--c-text-3); background: var(--c-hover); padding: 2px 7px; border-radius: var(--r-full); }

@media (max-width: 768px) {
  .modal-content { width: calc(100% - 24px); padding: 22px 18px; }
}
</style>
