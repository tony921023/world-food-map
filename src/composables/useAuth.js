import { ref, computed } from "vue";
import { apiFetch } from "../utils/api.js";

// Singleton state
const user = ref(null);

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value);

  // Kept for backward compatibility - cookies are now sent automatically
  function authHeaders() {
    return {};
  }

  async function register(email, password, displayName) {
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "註冊失敗");
    user.value = data.user;
    return data;
  }

  async function login(email, password) {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "登入失敗");
    user.value = data.user;
    return data;
  }

  async function logout() {
    await apiFetch("/api/auth/logout", { method: "POST" }).catch(() => {});
    user.value = null;
  }

  async function checkAuth() {
    try {
      const res = await apiFetch("/api/auth/me");
      if (!res.ok) {
        user.value = null;
        return false;
      }
      const data = await res.json();
      user.value = data.user;
      return true;
    } catch {
      user.value = null;
      return false;
    }
  }

  return {
    user,
    isLoggedIn,
    authHeaders,
    register,
    login,
    logout,
    checkAuth,
  };
}
