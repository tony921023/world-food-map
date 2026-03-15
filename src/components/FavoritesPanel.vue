<script setup>
import { ref, computed } from "vue";
import { useFavorites } from "../composables/useFavorites.js";
import { useToast } from "../composables/useToast.js";

const props = defineProps({
  show: { type: Boolean, default: false },
  isLoggedIn: { type: Boolean, default: false },
});

const emit = defineEmits(["toggle-panel", "goto", "need-auth"]);

const { error: toastError } = useToast();
const {
  myFavorites,
  favoriteLists,
  favsByList,
  createFavoriteList,
  renameFavoriteList,
  deleteFavoriteList,
  moveFavorite,
} = useFavorites();

// Active tab: 'all' | 'uncategorized' | list id (number)
const activeTab = ref("all");

const displayItems = computed(() => {
  return favsByList.value[activeTab.value] || [];
});

// Create list
const showCreateInput = ref(false);
const newListName = ref("");
const createError = ref("");

async function doCreateList() {
  createError.value = "";
  const name = newListName.value.trim();
  if (!name) return;
  try {
    await createFavoriteList(name);
    newListName.value = "";
    showCreateInput.value = false;
  } catch (e) {
    createError.value = e.message;
  }
}

// Rename list
const renamingListId = ref(null);
const renameValue = ref("");

function startRename(list) {
  renamingListId.value = list.id;
  renameValue.value = list.name;
}

async function doRename(listId) {
  const name = renameValue.value.trim();
  if (!name) return;
  try {
    await renameFavoriteList(listId, name);
  } catch (e) {
    toastError(e.message || "重新命名失敗");
  }
  renamingListId.value = null;
}

// Delete list
async function doDeleteList(listId) {
  if (!confirm("刪除清單？清單內的收藏將移回「未分類」")) return;
  try {
    await deleteFavoriteList(listId);
    if (activeTab.value === listId) activeTab.value = "all";
  } catch (e) {
    toastError(e.message || "刪除清單失敗");
  }
}

// Move dropdown
const movingFavId = ref(null);

function toggleMoveMenu(favId) {
  movingFavId.value = movingFavId.value === favId ? null : favId;
}

async function doMove(favId, listId) {
  try {
    await moveFavorite(favId, listId);
  } catch (e) {
    toastError(e.message || "移動失敗");
  }
  movingFavId.value = null;
}

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
      <!-- Tabs -->
      <div class="fav-tabs">
        <button
          class="fav-tab"
          :class="{ active: activeTab === 'all' }"
          @click="activeTab = 'all'"
        >
          全部
        </button>
        <button
          class="fav-tab"
          :class="{ active: activeTab === 'uncategorized' }"
          @click="activeTab = 'uncategorized'"
        >
          未分類
        </button>
        <template v-for="list in favoriteLists" :key="list.id">
          <button
            v-if="renamingListId !== list.id"
            class="fav-tab"
            :class="{ active: activeTab === list.id }"
            @click="activeTab = list.id"
            @dblclick.stop="startRename(list)"
            :title="'雙擊重新命名 / 右鍵刪除'"
            @contextmenu.prevent="doDeleteList(list.id)"
          >
            {{ list.name }}
          </button>
          <div v-else class="fav-tab-rename" @click.stop>
            <input
              v-model="renameValue"
              class="rename-input"
              @keyup.enter="doRename(list.id)"
              @blur="doRename(list.id)"
              @keyup.escape="renamingListId = null"
              ref="renameInput"
              autofocus
            />
          </div>
        </template>
        <button class="fav-tab fav-tab-add" @click="showCreateInput = !showCreateInput">+</button>
      </div>

      <!-- Create list input -->
      <div v-if="showCreateInput" class="fav-create-row" @click.stop>
        <input
          v-model="newListName"
          class="create-input"
          placeholder="新清單名稱"
          @keyup.enter="doCreateList"
          @keyup.escape="showCreateInput = false"
          autofocus
        />
        <button class="create-btn" @click="doCreateList">建立</button>
        <div v-if="createError" class="create-error">{{ createError }}</div>
      </div>

      <!-- Favorites list -->
      <ul class="fav-global-list">
        <li
          v-for="item in displayItems"
          :key="item.id"
          class="fav-global-item"
        >
          <div class="fav-item-main" @click="emit('goto', item)">
            <span class="fav-dot">&#10084;&#65039;</span>
            <span class="fav-name">{{ item.name }}</span>
            <span class="fav-country">{{ item.code }}</span>
          </div>
          <div class="fav-item-actions">
            <button class="move-btn" @click.stop="toggleMoveMenu(item.id)" title="移動到清單">
              &#128193;
            </button>
            <div v-if="movingFavId === item.id" class="move-menu" @click.stop>
              <div class="move-option" @click="doMove(item.id, null)">未分類</div>
              <div
                v-for="list in favoriteLists"
                :key="list.id"
                class="move-option"
                :class="{ current: item.list_id === list.id }"
                @click="doMove(item.id, list.id)"
              >
                {{ list.name }}
              </div>
            </div>
          </div>
        </li>
        <li v-if="!displayItems.length" class="fav-global-empty">
          {{ activeTab === 'all' ? '還沒有收藏任何料理' : '此清單沒有收藏' }}
        </li>
      </ul>
    </template>
  </div>
</template>

<style scoped>
.fav-global-toggle {
  position: fixed;
  left: 28px; bottom: 28px;
  padding: 10px 20px;
  border-radius: var(--r-full);
  border: 1px solid var(--c-border);
  cursor: pointer;
  background: #ffffff;
  color: var(--c-text);
  font-size: var(--text-sm);
  font-weight: 700;
  box-shadow: var(--shadow-md);
  z-index: 30;
  transition: all var(--dur);
}
.fav-global-toggle:hover {
  background: var(--c-surface);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.fav-global-panel {
  position: fixed;
  left: 50%;
  bottom: 90px;
  transform: translateX(-50%);
  width: 320px;
  background: #ffffff;
  border-radius: var(--r-xl);
  box-shadow: 0 8px 32px rgba(15,23,42,0.18);
  padding: 10px 14px 12px;
  z-index: 30;
  font-size: var(--text-base);
}
.fav-global-panel h3 {
  margin: 0 0 6px;
  font-size: var(--text-md);
  font-weight: 800;
  color: var(--c-text);
}

.fav-login-hint {
  font-size: var(--text-sm);
  color: var(--c-text-3);
  margin: 8px 0;
}
.fav-login-hint a {
  color: var(--c-primary);
  text-decoration: none;
  font-weight: 600;
}

/* Tabs */
.fav-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}
.fav-tab {
  border: none;
  background: var(--c-hover);
  border-radius: var(--r-full);
  padding: 3px 10px;
  font-size: var(--text-sm);
  cursor: pointer;
  color: var(--c-text-2);
  white-space: nowrap;
  transition: all var(--dur);
}
.fav-tab:hover { background: #e2e8f0; }
.fav-tab.active {
  background: var(--c-primary);
  color: #fff;
}
.fav-tab-add {
  background: var(--c-primary-light);
  color: var(--c-primary);
  font-weight: 700;
}
.fav-tab-rename {
  display: inline-flex;
}
.rename-input {
  width: 80px;
  border: 1px solid #93c5fd;
  border-radius: var(--r-full);
  padding: 2px 8px;
  font-size: var(--text-sm);
  outline: none;
}

/* Create row */
.fav-create-row {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.create-input {
  flex: 1;
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: 4px 8px;
  font-size: var(--text-sm);
  min-width: 0;
  outline: none;
}
.create-input:focus { border-color: var(--c-primary); }
.create-btn {
  border: none;
  background: var(--c-primary);
  color: #fff;
  border-radius: var(--r-md);
  padding: 4px 10px;
  font-size: var(--text-sm);
  cursor: pointer;
}
.create-btn:hover { background: var(--c-primary-hover); }
.create-error {
  width: 100%;
  color: var(--c-error);
  font-size: var(--text-xs);
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
  gap: 4px;
  padding: 4px 2px;
  border-radius: var(--r-md);
  position: relative;
  transition: background var(--dur);
}
.fav-global-item:hover { background: var(--c-hover-blue); }

.fav-item-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.fav-dot { width: 18px; text-align: center; flex-shrink: 0; }
.fav-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-base);
  color: var(--c-text);
}
.fav-country {
  font-size: var(--text-xs);
  color: var(--c-text-3);
  flex-shrink: 0;
}
.fav-global-empty {
  font-size: var(--text-sm);
  color: var(--c-text-3);
  padding: 6px 2px;
}

.fav-item-actions { position: relative; flex-shrink: 0; }
.move-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--text-base);
  padding: 2px 4px;
  border-radius: var(--r-sm);
  color: var(--c-text-2);
}
.move-btn:hover { background: var(--c-hover); }

.move-menu {
  position: absolute;
  right: 0;
  top: 100%;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-md);
  min-width: 120px;
  z-index: 10;
  padding: 4px 0;
}
.move-option {
  padding: 5px 12px;
  font-size: var(--text-sm);
  cursor: pointer;
  white-space: nowrap;
  color: var(--c-text-2);
  transition: background var(--dur);
}
.move-option:hover { background: var(--c-hover-blue); }
.move-option.current { color: var(--c-primary); font-weight: 600; }

@media (max-width: 768px) {
  .fav-global-panel { width: calc(100% - 32px); }
}
</style>
