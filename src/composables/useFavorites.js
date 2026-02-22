import { ref, computed } from "vue";
import { useAuth } from "./useAuth.js";

const OLD_STORAGE_KEY = "worldmap_favorites_v1";

// Singleton state shared across all components
const favorites = ref([]);

export function useFavorites() {
  const { isLoggedIn, authHeaders } = useAuth();

  function favKey(code, name) {
    return `${code || "??"}::${name}`;
  }

  function isFavorite(code, name) {
    if (!code || !name) return false;
    return favorites.value.includes(favKey(code, name));
  }

  async function loadFavorites() {
    if (!isLoggedIn.value) {
      favorites.value = [];
      return;
    }
    try {
      const res = await fetch("/api/favorites", { headers: authHeaders() });
      if (!res.ok) {
        favorites.value = [];
        return;
      }
      const data = await res.json();
      favorites.value = (data.favorites || []).map(
        (f) => favKey(f.country_code, f.food_name)
      );
    } catch {
      favorites.value = [];
    }
  }

  async function toggleFavorite(code, name) {
    if (!code || !name || !isLoggedIn.value) return;
    const key = favKey(code, name);
    const wasFav = favorites.value.includes(key);

    // Optimistic update
    if (wasFav) {
      favorites.value = favorites.value.filter((k) => k !== key);
    } else {
      favorites.value = [...favorites.value, key];
    }

    try {
      const res = await fetch("/api/favorites", {
        method: wasFav ? "DELETE" : "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ country_code: code, food_name: name }),
      });
      if (!res.ok) {
        // Revert on failure
        await loadFavorites();
      }
    } catch {
      await loadFavorites();
    }
  }

  async function migrateLocalStorage() {
    if (!isLoggedIn.value) return;
    try {
      const raw = localStorage.getItem(OLD_STORAGE_KEY);
      if (!raw) return;
      const oldFavs = JSON.parse(raw);
      if (!Array.isArray(oldFavs) || !oldFavs.length) return;

      const items = oldFavs
        .map((k) => {
          const [code, name] = k.split("::");
          return code && name ? { country_code: code, food_name: name } : null;
        })
        .filter(Boolean);

      if (!items.length) return;

      const res = await fetch("/api/favorites/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ items }),
      });

      if (res.ok) {
        localStorage.removeItem(OLD_STORAGE_KEY);
        await loadFavorites();
      }
    } catch {
      // Silently ignore migration errors
    }
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
    isFavorite,
    toggleFavorite,
    migrateLocalStorage,
    favKey,
  };
}
