import { ref } from "vue";
import { useAuth } from "./useAuth.js";

// Singleton — 所有元件共享同一份評分快取
const ratingsMap = ref({});  // "CODE|||name" -> { avg, count, myRating }

export function useRatings() {
  const { authHeaders } = useAuth();

  function getRating(code, name) {
    return ratingsMap.value[`${code}|||${name}`] || { avg: 0, count: 0, myRating: 0 };
  }

  async function fetchRating(code, name) {
    try {
      const res = await fetch(
        `/api/food/${code}/${encodeURIComponent(name)}/rating`,
        { headers: authHeaders() }
      );
      if (!res.ok) return;
      const data = await res.json();
      ratingsMap.value[`${code}|||${name}`] = {
        avg:      data.avg      ?? 0,
        count:    data.count    ?? 0,
        myRating: data.my_rating ?? 0,
      };
    } catch { /* ignore */ }
  }

  async function submitRating(code, name, stars) {
    try {
      const res = await fetch(
        `/api/food/${code}/${encodeURIComponent(name)}/rate`,
        {
          method:  "POST",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body:    JSON.stringify({ rating: stars }),
        }
      );
      if (!res.ok) return;
      const data = await res.json();
      ratingsMap.value[`${code}|||${name}`] = {
        avg:      data.avg      ?? 0,
        count:    data.count    ?? 0,
        myRating: data.my_rating ?? stars,
      };
    } catch { /* ignore */ }
  }

  return { getRating, fetchRating, submitRating };
}
