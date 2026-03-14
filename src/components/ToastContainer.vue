<script setup>
import { useToast } from "../composables/useToast.js";
const { toasts, remove } = useToast();

const ICONS = {
  success: "✓",
  error:   "✕",
  info:    "ℹ",
  warn:    "⚠",
};
</script>

<template>
  <Teleport to="body">
    <div class="toast-wrap">
      <TransitionGroup name="toast" tag="div" class="toast-list">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast"
          :class="t.type"
          @click="remove(t.id)"
        >
          <span class="toast-icon">{{ ICONS[t.type] || "ℹ" }}</span>
          <span class="toast-msg">{{ t.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-wrap {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  pointer-events: none;
}
.toast-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(15,23,42,0.18);
  cursor: pointer;
  pointer-events: auto;
  min-width: 220px;
  max-width: 340px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: all 0.2s;
}
.toast:hover { transform: translateX(-3px); }

.toast.success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.toast.error   { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.toast.info    { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.toast.warn    { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }

.toast-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}
.toast-msg {
  flex: 1;
  line-height: 1.4;
}

/* Transition */
.toast-enter-active { transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1); }
.toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(60px); }
.toast-leave-to     { opacity: 0; transform: translateX(60px); }
.toast-move         { transition: transform 0.3s ease; }

@media (max-width: 768px) {
  .toast-wrap { left: 12px; right: 12px; top: 12px; }
  .toast { min-width: 0; max-width: 100%; }
}
</style>
