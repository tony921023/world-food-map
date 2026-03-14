<script setup>
import { useAuth } from "../composables/useAuth.js";

const { user, isLoggedIn, logout } = useAuth();

const emit = defineEmits(["open-auth", "logged-out", "open-my-comments"]);

function handleLogout() {
  logout();
  emit("logged-out");
}
</script>

<template>
  <div class="user-menu">
    <template v-if="isLoggedIn">
      <span class="user-name">{{ user?.display_name }}</span>
      <button class="my-comments-btn" @click="emit('open-my-comments')">我的留言</button>
      <button class="logout-btn" @click="handleLogout">登出</button>
    </template>
    <template v-else>
      <button class="login-btn" @click="emit('open-auth')">登入 / 註冊</button>
    </template>
  </div>
</template>

<style scoped>
.user-menu {
  position: fixed;
  top: 20px;
  right: 140px;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  background: rgba(255, 255, 255, 0.9);
  padding: 6px 12px;
  border-radius: 999px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.login-btn,
.logout-btn,
.my-comments-btn {
  border: none;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 600;
}

.login-btn {
  background: #2563eb;
  color: #fff;
}

.logout-btn {
  background: #e5e7eb;
  color: #374151;
}

.my-comments-btn {
  background: #dbeafe;
  color: #2563eb;
}

@media (max-width: 768px) {
  .user-menu {
    top: 12px;
    right: auto;
    left: 12px;
  }
  .login-btn,
  .logout-btn,
  .my-comments-btn {
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
