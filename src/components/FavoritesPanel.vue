<script setup>
defineProps({
  favorites: { type: Array, default: () => [] },
  myFavorites: { type: Array, default: () => [] },
  show: { type: Boolean, default: false },
  isLoggedIn: { type: Boolean, default: false },
});

const emit = defineEmits(["toggle-panel", "goto", "need-auth"]);

function handleToggle() {
  emit("toggle-panel");
}
</script>

<template>
  <!-- Toggle button -->
  <button class="fav-global-toggle" @click="handleToggle">
    我的收藏（{{ myFavorites.length }}）
  </button>

  <!-- Favorites panel -->
  <div v-if="show" class="fav-global-panel">
    <h3>我的收藏</h3>

    <template v-if="!isLoggedIn">
      <p class="fav-login-hint">
        請先
        <a href="#" @click.prevent="emit('need-auth')">登入</a>
        以使用收藏功能
      </p>
    </template>

    <template v-else>
      <ul class="fav-global-list">
        <li
          v-for="item in myFavorites"
          :key="item.code + '::' + item.name"
          class="fav-global-item"
          @click="emit('goto', item)"
        >
          <span class="fav-dot">❤️</span>
          <span class="fav-name">{{ item.name }}</span>
          <span class="fav-country">{{ item.code }}</span>
        </li>
        <li v-if="!myFavorites.length" class="fav-global-empty">
          還沒有收藏任何料理
        </li>
      </ul>
    </template>
  </div>
</template>

<style scoped>
.fav-global-toggle {
  position: fixed;
  left: 50%;
  bottom: 40px;
  transform: translateX(-50%);
  padding: 8px 18px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  background: #f97316;
  color: #fff;
  font-size: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.18);
  z-index: 30;
}

.fav-global-panel {
  position: fixed;
  left: 50%;
  bottom: 90px;
  transform: translateX(-50%);
  width: 260px;
  background: rgba(255, 255, 255, 0.97);
  border-radius: 18px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.2);
  padding: 10px 14px 12px;
  z-index: 30;
  font-size: 14px;
}
.fav-global-panel h3 {
  margin: 0 0 6px;
  font-size: 15px;
}

.fav-login-hint {
  font-size: 13px;
  color: #6b7280;
  margin: 8px 0;
}
.fav-login-hint a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}

.fav-global-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 220px;
  overflow-y: auto;
}

.fav-global-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 2px;
  border-radius: 8px;
  cursor: pointer;
}
.fav-global-item:hover {
  background: #eff6ff;
}

.fav-dot {
  width: 18px;
  text-align: center;
}
.fav-name {
  flex: 1;
}
.fav-country {
  font-size: 12px;
  color: #6b7280;
}
.fav-global-empty {
  font-size: 13px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .fav-global-panel {
    width: calc(100% - 32px);
  }
}
</style>
