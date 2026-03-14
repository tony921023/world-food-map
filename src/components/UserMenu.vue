<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useAuth } from "../composables/useAuth.js";

const { user, isLoggedIn, logout } = useAuth();
const emit = defineEmits(["open-auth", "logged-out", "open-my-comments", "open-profile"]);

const open = ref(false);
const menuRef = ref(null);

function handleLogout() {
  open.value = false;
  logout();
  emit("logged-out");
}

function closeOnOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    open.value = false;
  }
}

onMounted(()  => document.addEventListener("click", closeOnOutside));
onUnmounted(() => document.removeEventListener("click", closeOnOutside));
</script>

<template>
  <!-- 已登入：下拉選單 -->
  <div class="user-dropdown" ref="menuRef" v-if="isLoggedIn">
    <button class="avatar-btn" @click.stop="open = !open">
      <span class="avatar-circle">{{ user?.display_name?.[0]?.toUpperCase() }}</span>
      <span class="user-name-text">{{ user?.display_name }}</span>
      <span class="chevron" :class="{ rotated: open }">▾</span>
    </button>

    <transition name="dropdown-fade">
      <div class="dropdown-panel" v-if="open" @click.stop>
        <div class="dropdown-header">
          <div class="dh-avatar">{{ user?.display_name?.[0]?.toUpperCase() }}</div>
          <div>
            <div class="dh-name">{{ user?.display_name }}</div>
            <div class="dh-email">{{ user?.email }}</div>
          </div>
        </div>
        <div class="dropdown-divider"></div>
        <button class="dd-item" @click="emit('open-profile'); open = false">
          <span class="dd-icon">👤</span> 個人資料
        </button>
        <button class="dd-item" @click="emit('open-my-comments'); open = false">
          <span class="dd-icon">💬</span> 我的留言
        </button>
        <div class="dropdown-divider"></div>
        <button class="dd-item logout-item" @click="handleLogout">
          <span class="dd-icon">🚪</span> 登出
        </button>
      </div>
    </transition>
  </div>

  <!-- 未登入 -->
  <button class="login-btn" v-else @click="emit('open-auth')">
    登入 / 註冊
  </button>
</template>

<style scoped>
/* ── 下拉觸發按鈕 ─────────────────────────────── */
.avatar-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  background: rgba(255,255,255,0.92);
  border: 1px solid var(--c-border);
  border-radius: var(--r-full);
  padding: 5px 12px 5px 6px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: box-shadow var(--dur), background var(--dur);
}
.avatar-btn:hover {
  background: var(--c-surface);
  box-shadow: var(--shadow-md);
}

.avatar-circle {
  width: 30px; height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--c-primary), var(--c-accent));
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.user-name-text {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--c-text);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  font-size: 11px;
  color: var(--c-text-3);
  transition: transform var(--dur);
  line-height: 1;
}
.chevron.rotated { transform: rotate(180deg); }

/* ── 下拉面板 ────────────────────────────────── */
.user-dropdown { position: relative; }

.dropdown-panel {
  position: fixed;
  top: 60px; right: 16px;
  width: 220px;
  background: var(--c-surface);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--c-border);
  overflow: hidden;
  z-index: 200;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 14px 12px;
  background: var(--c-hover-blue);
}
.dh-avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--c-primary), var(--c-accent));
  color: #fff;
  font-size: var(--text-lg);
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.dh-name  { font-size: var(--text-base); font-weight: 700; color: var(--c-text); }
.dh-email { font-size: var(--text-xs); color: var(--c-text-3); margin-top: 1px; }

.dropdown-divider { height: 1px; background: var(--c-hover); margin: 0; }

.dd-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 16px;
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--c-text-2);
  background: transparent;
  border-radius: 0;
  text-align: left;
  transition: background var(--dur);
}
.dd-item:hover { background: var(--c-hover); }
.dd-icon { font-size: var(--text-lg); }

.logout-item { color: var(--c-error); }
.logout-item:hover { background: var(--c-error-light); }

/* ── 未登入按鈕 ──────────────────────────────── */
.login-btn {
  background: linear-gradient(135deg, var(--c-primary), var(--c-primary-hover));
  color: #fff;
  border-radius: var(--r-full);
  padding: 7px 18px;
  font-size: var(--text-sm);
  font-weight: 700;
  border: none;
  box-shadow: 0 2px 8px rgba(37,99,235,0.35);
  transition: all var(--dur);
}
.login-btn:hover {
  background: linear-gradient(135deg, var(--c-primary-hover), #1e40af);
  box-shadow: 0 4px 14px rgba(37,99,235,0.45);
  transform: translateY(-1px);
}

/* ── 動畫 ────────────────────────────────────── */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
  transform-origin: top right;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: scale(0.92) translateY(-6px);
}

/* ── 手機 ────────────────────────────────────── */
@media (max-width: 768px) {
  .user-name-text { display: none; }
  .chevron { display: none; }
  .dropdown-panel { right: 0; }
}
</style>
