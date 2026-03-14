import { ref, computed } from "vue";
import { useAuth } from "./useAuth.js";

const OLD_STORAGE_KEY = "worldmap_favorites_v1";

// Singleton state shared across all components
const favorites = ref([]);       // [{id, country_code, food_name, list_id}, ...]
const favoriteLists = ref([]);   // [{id, name}, ...]

export function useFavorites() {
  const { isLoggedIn, authHeaders } = useAuth();

  function favKey(code, name) {
    return `${code || "??"}::${name}`;
  }

  function isFavorite(code, name) {
    if (!code || !name) return false;
    return favorites.value.some(
      (f) => f.country_code === code.toUpperCase() && f.food_name === name
    );
  }

  function getFavoriteId(code, name) {
    const f = favorites.value.find(
      (f) => f.country_code === code.toUpperCase() && f.food_name === name
    );
    return f ? f.id : null;
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
      favorites.value = data.favorites || [];
    } catch {
      favorites.value = [];
    }
  }

  async function toggleFavorite(code, name) {
    console.log("[Fav] toggleFavorite called", { code, name, isLoggedIn: isLoggedIn.value });
    if (!code || !name || !isLoggedIn.value) {
      console.warn("[Fav] 跳出：", { code, name, loggedIn: isLoggedIn.value });
      return;
    }
    const wasFav = isFavorite(code, name);
    console.log("[Fav] wasFav =", wasFav);

    // Optimistic update
    if (wasFav) {
      favorites.value = favorites.value.filter(
        (f) => !(f.country_code === code.toUpperCase() && f.food_name === name)
      );
    } else {
      favorites.value = [
        ...favorites.value,
        { id: 0, country_code: code.toUpperCase(), food_name: name, list_id: null },
      ];
    }

    try {
      const res = await fetch("/api/favorites", {
        method: wasFav ? "DELETE" : "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ country_code: code, food_name: name }),
      });
      const data = await res.json().catch(() => ({}));
      console.log("[Fav] API 回應", res.status, data);
      if (!res.ok) {
        console.error("[Fav] API 失敗，重新載入");
        await loadFavorites();
      } else if (!wasFav) {
        await loadFavorites();
      }
    } catch (e) {
      console.error("[Fav] 網路錯誤", e);
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
    favorites.value.map((f) => ({
      id: f.id,
      code: f.country_code,
      name: f.food_name,
      list_id: f.list_id,
    }))
  );

  // ---- Favorite Lists ----
  async function loadFavoriteLists() {
    if (!isLoggedIn.value) {
      favoriteLists.value = [];
      return;
    }
    try {
      const res = await fetch("/api/favorite-lists", { headers: authHeaders() });
      if (!res.ok) {
        favoriteLists.value = [];
        return;
      }
      const data = await res.json();
      favoriteLists.value = data.lists || [];
    } catch {
      favoriteLists.value = [];
    }
  }

  async function createFavoriteList(name) {
    const res = await fetch("/api/favorite-lists", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ name }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "建立失敗");
    favoriteLists.value = [...favoriteLists.value, data];
    return data;
  }

  async function renameFavoriteList(listId, name) {
    const res = await fetch(`/api/favorite-lists/${listId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ name }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "重新命名失敗");
    favoriteLists.value = favoriteLists.value.map((l) =>
      l.id === listId ? { ...l, name: data.name } : l
    );
  }

  async function deleteFavoriteList(listId) {
    const res = await fetch(`/api/favorite-lists/${listId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || "刪除失敗");
    }
    favoriteLists.value = favoriteLists.value.filter((l) => l.id !== listId);
    // Move favorites back to uncategorized locally
    favorites.value = favorites.value.map((f) =>
      f.list_id === listId ? { ...f, list_id: null } : f
    );
  }

  async function moveFavorite(favoriteId, listId) {
    const res = await fetch("/api/favorites/move", {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ favorite_id: favoriteId, list_id: listId }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || "移動失敗");
    }
    favorites.value = favorites.value.map((f) =>
      f.id === favoriteId ? { ...f, list_id: listId } : f
    );
  }

  const favsByList = computed(() => {
    const map = { all: myFavorites.value, uncategorized: [] };
    for (const fl of favoriteLists.value) {
      map[fl.id] = [];
    }
    for (const f of myFavorites.value) {
      if (f.list_id && map[f.list_id]) {
        map[f.list_id].push(f);
      } else {
        map.uncategorized.push(f);
      }
    }
    return map;
  });

  return {
    favorites,
    myFavorites,
    favoriteLists,
    favsByList,
    loadFavorites,
    loadFavoriteLists,
    isFavorite,
    getFavoriteId,
    toggleFavorite,
    migrateLocalStorage,
    favKey,
    createFavoriteList,
    renameFavoriteList,
    deleteFavoriteList,
    moveFavorite,
  };
}
