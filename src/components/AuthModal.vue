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
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.auth-box {
  width: 360px;
  max-width: calc(100% - 32px);
  background: #fff;
  border-radius: 18px;
  padding: 24px 28px 28px;
  position: relative;
}

.auth-close {
  position: absolute;
  top: 12px;
  right: 14px;
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

.auth-box h2 {
  margin: 0 0 16px;
  font-size: 22px;
}

.auth-field {
  margin-bottom: 12px;
}
.auth-field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #374151;
}
.auth-field input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}
.auth-field input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

.auth-error {
  color: #dc2626;
  font-size: 13px;
  margin: 8px 0;
}

.auth-submit {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 10px;
  background: #2563eb;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}
.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  margin-top: 14px;
  font-size: 13px;
  color: #6b7280;
}
.auth-switch a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}
</style>
