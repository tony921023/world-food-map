/**
 * Wrapper around fetch that always includes credentials (cookies).
 * This enables httpOnly cookie-based JWT authentication.
 */
export function apiFetch(url, options = {}) {
  return fetch(url, { ...options, credentials: "include" });
}
