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
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(148,163,184,0.35);
  border-radius: 999px;
  padding: 5px 12px 5px 6px;
  box-shadow: 0 1px 6px rgba(15,23,42,0.09);
  cursor: pointer;
  transition: box-shadow 0.2s, background 0.2s;
}
.avatar-btn:hover {
  background: #fff;
  box-shadow: 0 3px 10px rgba(15,23,42,0.14);
}

.avatar-circle {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-name-text {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  font-size: 11px;
  color: #64748b;
  transition: transform 0.2s;
  line-height: 1;
}
.chevron.rotated { transform: rotate(180deg); }

/* ── 下拉面板 ────────────────────────────────── */
.user-dropdown {
  position: relative;
}

.dropdown-panel {
  position: fixed;
  top: 60px;
  right: 16px;
  width: 220px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 8px 30px rgba(15,23,42,0.16);
  border: 1px solid rgba(148,163,184,0.2);
  overflow: hidden;
  z-index: 200;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 14px 12px;
  background: linear-gradient(135deg, #eff6ff, #f0f9ff);
}
.dh-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.dh-name  { font-size: 14px; font-weight: 700; color: #1e293b; }
.dh-email { font-size: 11px; color: #64748b; margin-top: 1px; }

.dropdown-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 0;
}

.dd-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  background: transparent;
  border-radius: 0;
  text-align: left;
  transition: background 0.12s;
}
.dd-item:hover { background: #f8fafc; }
.dd-icon { font-size: 16px; }

.logout-item { color: #ef4444; }
.logout-item:hover { background: #fff5f5; }

/* ── 未登入按鈕 ──────────────────────────────── */
.login-btn {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  border-radius: 999px;
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  box-shadow: 0 2px 8px rgba(37,99,235,0.35);
  transition: all 0.2s;
}
.login-btn:hover {
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
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
