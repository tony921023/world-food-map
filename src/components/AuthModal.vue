<script setup>
import { ref } from "vue";
import { useAuth } from "../composables/useAuth.js";

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "authed"]);

const { register, login } = useAuth();

const mode = ref("login"); // 'login' | 'register'
const email = ref("");
const password = ref("");
const displayName = ref("");
const error = ref("");
const submitting = ref(false);

function resetForm() {
  email.value = "";
  password.value = "";
  displayName.value = "";
  error.value = "";
}

function switchMode() {
  mode.value = mode.value === "login" ? "register" : "login";
  error.value = "";
}

async function handleSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    if (mode.value === "register") {
      await register(email.value, password.value, displayName.value);
    } else {
      await login(email.value, password.value);
    }
    resetForm();
    emit("authed");
    emit("close");
  } catch (e) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}

function handleClose() {
  resetForm();
  emit("close");
}
</script>

<template>
  <div class="auth-mask" v-if="show" @click="handleClose">
    <div class="auth-box" @click.stop>
      <button class="auth-close" @click="handleClose">✕</button>

      <h2>{{ mode === "login" ? "登入" : "註冊" }}</h2>

      <form @submit.prevent="handleSubmit">
        <div class="auth-field" v-if="mode === 'register'">
          <label>顯示名稱</label>
          <input
            v-model="displayName"
            type="text"
            placeholder="你的名稱"
            maxlength="50"
            required
          />
        </div>

        <div class="auth-field">
          <label>Email</label>
          <input
            v-model="email"
            type="email"
            placeholder="your@email.com"
            required
          />
        </div>

        <div class="auth-field">
          <label>密碼</label>
          <input
            v-model="password"
            type="password"
            placeholder="至少 6 個字元"
            minlength="6"
            required
          />
        </div>

        <p class="auth-error" v-if="error">{{ error }}</p>

        <button class="auth-submit" type="submit" :disabled="submitting">
          {{ submitting ? "處理中..." : mode === "login" ? "登入" : "註冊" }}
        </button>
      </form>

      <p class="auth-switch">
        {{ mode === "login" ? "還沒有帳號？" : "已有帳號？" }}
        <a href="#" @click.prevent="switchMode">
          {{ mode === "login" ? "前往註冊" : "前往登入" }}
        </a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-mask {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 60;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}

.auth-box {
  width: 380px;
  max-width: calc(100% - 32px);
  background: var(--c-surface);
  border-radius: var(--r-xl);
  padding: 32px 30px;
  position: relative;
  box-shadow: var(--shadow-lg);
  animation: popIn 0.25s var(--ease);
}

.auth-close {
  position: absolute;
  top: 14px; right: 16px;
  border: none;
  background: var(--c-hover);
  color: var(--c-text-2);
  font-size: 15px;
  cursor: pointer;
  width: 30px; height: 30px;
  border-radius: var(--r-full);
  display: flex; align-items: center; justify-content: center;
  padding: 0;
  transition: background var(--dur);
}
.auth-close:hover { background: #e2e8f0; }

.auth-box h2 {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--c-text);
  margin: 0 0 20px;
  letter-spacing: -0.3px;
}

.auth-field { margin-bottom: 14px; }
.auth-field label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 700;
  margin-bottom: 5px;
  color: var(--c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.auth-field input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--c-border);
  border-radius: var(--r-md);
  font-size: var(--text-base);
  box-sizing: border-box;
  transition: border-color var(--dur), box-shadow var(--dur);
  outline: none;
  color: var(--c-text);
}
.auth-field input:focus {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px var(--c-primary-ring);
}

.auth-error {
  color: var(--c-error);
  font-size: var(--text-sm);
  background: var(--c-error-light);
  border-radius: var(--r-md);
  padding: 8px 12px;
  margin: 6px 0;
}

.auth-submit {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: var(--r-md);
  background: var(--c-primary);
  color: #fff;
  font-size: var(--text-md);
  font-weight: 700;
  cursor: pointer;
  margin-top: 6px;
  transition: background var(--dur), transform 0.1s;
}
.auth-submit:hover:not(:disabled) {
  background: var(--c-primary-hover);
  transform: translateY(-1px);
}
.auth-submit:disabled { opacity: 0.55; cursor: not-allowed; }

.auth-switch {
  text-align: center;
  margin-top: 16px;
  font-size: var(--text-sm);
  color: var(--c-text-3);
}
</style>
