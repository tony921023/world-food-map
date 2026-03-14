<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const emit = defineEmits(["pick", "search"]);

const searchQuery = ref("");
const searchResults = ref([]);
const searchLoading = ref(false);
const showSearchResults = ref(false);
let _searchTimer = null;

function onSearchInput() {
  clearTimeout(_searchTimer);
  const q = searchQuery.value.trim();
  if (!q) {
    searchResults.value = [];
    showSearchResults.value = false;
    return;
  }
  _searchTimer = setTimeout(() => doSearch(q), 300);
}

async function doSearch(q) {
  if (!q) return;
  searchLoading.value = true;
  showSearchResults.value = true;
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    searchResults.value = data.results || [];
  } catch {
    searchResults.value = [];
  } finally {
    searchLoading.value = false;
  }
}

function pickResult(item) {
  searchQuery.value = "";
  searchResults.value = [];
  showSearchResults.value = false;
  emit("pick", item);
}

function openSearchPage() {
  const q = searchQuery.value.trim();
  if (!q) return;
  showSearchResults.value = false;
  emit("search", { query: q, results: searchResults.value });
}

function onKeydown(e) {
  if (e.key === "Enter") openSearchPage();
}

function closeDropdown(e) {
  const el = document.querySelector(".search-bar");
  if (el && !el.contains(e.target)) {
    showSearchResults.value = false;
  }
}

onMounted(() => {
  document.addEventListener("click", closeDropdown);
});

onUnmounted(() => {
  document.removeEventListener("click", closeDropdown);
});
</script>

<template>
  <div class="search-bar" @click.stop>
    <input
      type="text"
      class="search-input"
      placeholder="搜尋料理、標籤..."
      v-model="searchQuery"
      @input="onSearchInput"
      @keydown="onKeydown"
      @focus="searchResults.length && (showSearchResults = true)"
    />
    <div class="search-dropdown" v-if="showSearchResults">
      <div v-if="searchLoading" class="search-status">搜尋中...</div>
      <div v-else-if="!searchResults.length" class="search-status">沒有找到結果</div>
      <div
        v-else
        class="search-result-item"
        v-for="item in searchResults"
        :key="item.code + '_' + item.name"
        @click="pickResult(item)"
      >
        <img class="search-thumb" :src="item.img" :alt="item.name" />
        <div class="search-info">
          <span class="search-name">{{ item.name }}</span>
          <span class="search-country">{{ item.countryName }}</span>
          <div class="search-tags" v-if="item.tags && item.tags.length">
            <span class="tag-badge small" v-for="t in item.tags" :key="t">{{ t }}</span>
          </div>
        </div>
      </div>
      <div class="show-all-btn" v-if="searchResults.length" @click="openSearchPage">
        查看所有結果 →
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 8px 16px;
  border: 1.5px solid var(--c-border);
  border-radius: var(--r-full);
  font-size: var(--text-base);
  background: rgba(255,255,255,0.95);
  box-shadow: var(--shadow-sm);
  outline: none;
  box-sizing: border-box;
  transition: border-color var(--dur), box-shadow var(--dur);
  color: var(--c-text);
}
.search-input:focus {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px var(--c-primary-ring);
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0; right: 0;
  z-index: 200;
  background: var(--c-surface);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--c-border);
  max-height: 320px;
  overflow-y: auto;
  padding: 6px 0;
}

.search-status {
  padding: 12px 16px;
  font-size: var(--text-sm);
  color: var(--c-text-3);
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background var(--dur);
}
.search-result-item:hover { background: var(--c-hover-blue); }

.search-thumb {
  width: 48px; height: 36px;
  object-fit: cover;
  border-radius: var(--r-sm);
  flex-shrink: 0;
}

.search-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.search-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--c-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-country {
  font-size: var(--text-sm);
  color: var(--c-text-3);
}
.search-tags { display: flex; flex-wrap: wrap; gap: 3px; }

.tag-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--r-full);
  background: var(--c-primary-light);
  color: var(--c-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.4;
}
.tag-badge.small { padding: 1px 6px; font-size: 10px; }

.show-all-btn {
  padding: 10px 16px;
  font-size: var(--text-sm);
  color: var(--c-primary);
  cursor: pointer;
  border-top: 1px solid var(--c-hover);
  text-align: center;
  font-weight: 600;
  transition: background var(--dur);
}
.show-all-btn:hover { background: var(--c-hover-blue); }
</style>
