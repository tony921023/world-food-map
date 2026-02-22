import { ref, computed } from "vue";

const TOKEN_KEY = "worldmap_jwt";

// Singleton state
const token = ref(localStorage.getItem(TOKEN_KEY) || "");
const user = ref(null);

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value);

  function _setToken(t) {
    token.value = t;
    if (t) {
      localStorage.setItem(TOKEN_KEY, t);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  function authHeaders() {
    return token.value
      ? { Authorization: `Bearer ${token.value}` }
      : {};
  }

  async function register(email, password, displayName) {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "註冊失敗");
    _setToken(data.token);
    user.value = data.user;
    return data;
  }

  async function login(email, password) {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "登入失敗");
    _setToken(data.token);
    user.value = data.user;
    return data;
  }

  function logout() {
    _setToken("");
    user.value = null;
  }

  async function checkAuth() {
    if (!token.value) return false;
    try {
      const res = await fetch("/api/auth/me", {
        headers: authHeaders(),
      });
      if (!res.ok) {
        logout();
        return false;
      }
      const data = await res.json();
      user.value = data.user;
      return true;
    } catch {
      logout();
      return false;
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    authHeaders,
    register,
    login,
    logout,
    checkAuth,
  };
}
