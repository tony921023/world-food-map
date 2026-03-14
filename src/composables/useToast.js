import { ref } from "vue";

const toasts = ref([]);
let _nextId = 0;

export function useToast() {
  function toast(message, type = "success", duration = 3000) {
    const id = ++_nextId;
    toasts.value.push({ id, message, type });
    setTimeout(() => remove(id), duration);
    return id;
  }

  function remove(id) {
    const idx = toasts.value.findIndex((t) => t.id === id);
    if (idx !== -1) toasts.value.splice(idx, 1);
  }

  // Shorthand helpers
  const success = (msg, dur) => toast(msg, "success", dur);
  const error   = (msg, dur) => toast(msg, "error",   dur || 4000);
  const info    = (msg, dur) => toast(msg, "info",    dur);
  const warn    = (msg, dur) => toast(msg, "warn",    dur);

  return { toasts, toast, remove, success, error, info, warn };
}
