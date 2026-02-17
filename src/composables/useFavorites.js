import { ref, computed } from "vue";

const STORAGE_KEY = "worldmap_favorites_v1";

// Singleton state shared across all components
const favorites = ref([]);

export function useFavorites() {
  function loadFavorites() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      favorites.value = raw ? JSON.parse(raw) : [];
    } catch {
      favorites.value = [];
    }
  }

  function saveFavorites() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites.value));
    } catch { /* ignore */ }
  }

  function favKey(code, name) {
    return `${code || "??"}::${name}`;
  }

  function isFavorite(code, name) {
    if (!code || !name) return false;
    return favorites.value.includes(favKey(code, name));
  }

  function toggleFavorite(code, name) {
    if (!code || !name) return;
    const key = favKey(code, name);
    const idx = favorites.value.indexOf(key);
    if (idx === -1) {
      favorites.value.push(key);
    } else {
      favorites.value.splice(idx, 1);
    }
    saveFavorites();
  }

  const myFavorites = computed(() =>
    favorites.value.map((k) => {
      const [code, name] = k.split("::");
      return { code, name };
    })
  );

  return {
    favorites,
    myFavorites,
    loadFavorites,
    saveFavorites,
    isFavorite,
    toggleFavorite,
    favKey,
  };
}
