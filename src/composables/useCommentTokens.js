const STORAGE_KEY = "worldmap_comment_tokens_v1";

export function useCommentTokens() {
  function loadCommentTokens() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  function saveCommentToken(commentId, token) {
    const tokens = loadCommentTokens();
    tokens[commentId] = token;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
    } catch { /* ignore */ }
  }

  function getCommentToken(commentId) {
    return loadCommentTokens()[commentId] || null;
  }

  function removeCommentToken(commentId) {
    const tokens = loadCommentTokens();
    delete tokens[commentId];
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
    } catch { /* ignore */ }
  }

  return {
    loadCommentTokens,
    saveCommentToken,
    getCommentToken,
    removeCommentToken,
  };
}
