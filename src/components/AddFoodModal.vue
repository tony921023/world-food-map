<script setup>
import { ref, computed, watch } from "vue";
import { apiFetch } from "../utils/api.js";
import { useToast } from "../composables/useToast.js";

const props = defineProps({
  show:        { type: Boolean, default: false },
  code:        { type: String,  default: "" },
  countryName: { type: String,  default: "" },
  allTags:     { type: Array,   default: () => [] },
});

const emit = defineEmits(["close", "added"]);

const { success: toastSuccess, error: toastError } = useToast();

// ── 表單欄位 ────────────────────────────────────────────────────
const name     = ref("");
const desc     = ref("");
const imgUrl   = ref("");
const selTags  = ref([]);   // 已選標籤
const customTag = ref("");  // 自訂標籤輸入
const submitting = ref(false);
const errors     = ref({});

const imgPreviewOk = ref(true);

function resetForm() {
  name.value     = "";
  desc.value     = "";
  imgUrl.value   = "";
  selTags.value  = [];
  customTag.value = "";
  submitting.value = false;
  errors.value   = {};
  imgPreviewOk.value = true;
}

watch(() => props.show, (v) => { if (v) resetForm(); });

// ── 字數統計 ───────────────────────────────────────────────────
const nameLen = computed(() => name.value.length);
const descLen = computed(() => desc.value.length);

// ── 標籤操作 ───────────────────────────────────────────────────
function toggleTag(tag) {
  const i = selTags.value.indexOf(tag);
  if (i === -1) selTags.value.push(tag);
  else selTags.value.splice(i, 1);
}

function addCustomTag() {
  const t = customTag.value.trim();
  if (!t || selTags.value.includes(t)) { customTag.value = ""; return; }
  selTags.value.push(t);
  customTag.value = "";
}

function removeTag(tag) {
  selTags.value = selTags.value.filter((t) => t !== tag);
}

// ── 提交 ───────────────────────────────────────────────────────
async function submit() {
  errors.value = {};
  const n = name.value.trim();
  if (!n) { errors.value.name = "請填寫食物名稱"; return; }
  if (n.length > 100) { errors.value.name = "名稱過長（最多 100 字）"; return; }
  if (desc.value.length > 500) { errors.value.desc = "描述過長（最多 500 字）"; return; }

  submitting.value = true;
  try {
    const res = await apiFetch(`/api/foods/${props.code}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name:  n,
        desc:  desc.value.trim(),
        img:   imgUrl.value.trim(),
        tags:  selTags.value,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      errors.value.general = data.error || "新增失敗";
      return;
    }
    toastSuccess(`「${n}」已新增到 ${props.countryName}！`);
    emit("added", data);
    emit("close");
  } catch {
    errors.value.general = "網路錯誤，請稍後再試";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="modal-mask" v-if="show" @click="emit('close')">
    <div class="modal-box" @click.stop>
      <button class="close-btn" @click="emit('close')">✕</button>

      <h2 class="modal-title">
        ＋ 新增美食
        <span class="country-badge">{{ countryName }}</span>
      </h2>

      <!-- 食物名稱 -->
      <div class="field">
        <label class="label">食物名稱 <span class="req">*</span></label>
        <div class="input-wrap">
          <input
            v-model="name"
            class="input"
            :class="{ error: errors.name }"
            type="text"
            placeholder="例：壽司、泡菜鍋..."
            maxlength="100"
          />
          <span class="char-count" :class="{ warn: nameLen > 80 }">{{ nameLen }}/100</span>
        </div>
        <p class="field-error" v-if="errors.name">{{ errors.name }}</p>
      </div>

      <!-- 簡介 -->
      <div class="field">
        <label class="label">簡介描述</label>
        <div class="input-wrap">
          <textarea
            v-model="desc"
            class="input textarea"
            placeholder="介紹這道食物的特色、口感或文化背景..."
            rows="3"
            maxlength="500"
          />
          <span class="char-count" :class="{ warn: descLen > 400 }">{{ descLen }}/500</span>
        </div>
        <p class="field-error" v-if="errors.desc">{{ errors.desc }}</p>
      </div>

      <!-- 圖片 URL -->
      <div class="field">
        <label class="label">圖片 URL</label>
        <input
          v-model="imgUrl"
          class="input"
          type="url"
          placeholder="https://example.com/food.jpg"
        />
        <div class="img-preview" v-if="imgUrl">
          <img
            :src="imgUrl"
            alt="預覽"
            class="preview-img"
            @load="imgPreviewOk = true"
            @error="imgPreviewOk = false"
          />
          <p class="preview-fail" v-if="!imgPreviewOk">⚠️ 無法載入圖片，請確認 URL 是否正確</p>
        </div>
      </div>

      <!-- 標籤 -->
      <div class="field">
        <label class="label">標籤</label>

        <!-- 已選標籤 -->
        <div class="selected-tags" v-if="selTags.length">
          <span class="sel-tag" v-for="t in selTags" :key="t">
            {{ t }}
            <button class="rm-tag" @click="removeTag(t)">×</button>
          </span>
        </div>

        <!-- 現有標籤建議 -->
        <div class="tag-suggest" v-if="allTags.length">
          <span class="suggest-label">建議標籤：</span>
          <button
            v-for="t in allTags"
            :key="t"
            class="tag-pill"
            :class="{ active: selTags.includes(t) }"
            @click="toggleTag(t)"
          >{{ t }}</button>
        </div>

        <!-- 自訂標籤 -->
        <div class="custom-tag-row">
          <input
            v-model="customTag"
            class="input custom-input"
            type="text"
            placeholder="自訂標籤..."
            @keyup.enter="addCustomTag"
            @keyup.comma="addCustomTag"
          />
          <button class="add-tag-btn" @click="addCustomTag">新增</button>
        </div>
      </div>

      <!-- 全域錯誤 -->
      <p class="general-error" v-if="errors.general">{{ errors.general }}</p>

      <!-- 按鈕列 -->
      <div class="actions">
        <button class="cancel-btn" @click="emit('close')">取消</button>
        <button
          class="submit-btn"
          :disabled="submitting || !name.trim()"
          @click="submit"
        >
          {{ submitting ? "新增中..." : "確認新增" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-box {
  width: 520px;
  max-width: calc(100% - 32px);
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  background: #fff;
  border-radius: var(--r-xl);
  padding: 24px 28px 28px;
  position: relative;
  box-shadow: 0 20px 60px rgba(15,23,42,0.3);
  animation: popIn 0.22s var(--ease);
}

@keyframes popIn {
  from { opacity: 0; transform: scale(0.95) translateY(8px); }
  to   { opacity: 1; transform: scale(1)    translateY(0);   }
}

.close-btn {
  position: absolute;
  top: 12px; right: 14px;
  border: none;
  background: var(--c-hover);
  color: var(--c-text-2);
  width: 30px; height: 30px;
  border-radius: var(--r-full);
  font-size: 14px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background var(--dur);
}
.close-btn:hover { background: #e2e8f0; }

.modal-title {
  font-size: var(--text-xl);
  font-weight: 800;
  color: var(--c-text);
  margin: 0 0 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.country-badge {
  font-size: var(--text-sm);
  font-weight: 600;
  background: var(--c-primary-light);
  color: var(--c-primary);
  padding: 3px 10px;
  border-radius: var(--r-full);
}

/* Fields */
.field { margin-bottom: 16px; }
.label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--c-text-2);
  margin-bottom: 5px;
}
.req { color: var(--c-error); }

.input-wrap { position: relative; }
.char-count {
  position: absolute;
  right: 8px; bottom: 8px;
  font-size: 11px;
  color: var(--c-text-3);
  pointer-events: none;
}
.char-count.warn { color: var(--c-warn); }

.input {
  width: 100%;
  border: 1.5px solid var(--c-border);
  border-radius: var(--r-md);
  padding: 9px 12px;
  font-size: var(--text-base);
  color: var(--c-text);
  box-sizing: border-box;
  outline: none;
  transition: border-color var(--dur);
  font-family: inherit;
}
.input:focus { border-color: var(--c-primary); }
.input.error { border-color: var(--c-error); }
.textarea { resize: vertical; min-height: 80px; padding-bottom: 24px; }

.field-error {
  font-size: var(--text-xs);
  color: var(--c-error);
  margin: 4px 0 0;
}

/* Image preview */
.img-preview {
  margin-top: 8px;
  border-radius: var(--r-md);
  overflow: hidden;
  border: 1px solid var(--c-border);
  max-height: 180px;
}
.preview-img {
  width: 100%;
  max-height: 180px;
  object-fit: cover;
  display: block;
}
.preview-fail {
  font-size: var(--text-sm);
  color: var(--c-warn);
  padding: 8px 12px;
  margin: 0;
}

/* Tags */
.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.sel-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--c-primary);
  color: #fff;
  padding: 3px 10px;
  border-radius: var(--r-full);
  font-size: var(--text-sm);
  font-weight: 600;
}
.rm-tag {
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.8);
  cursor: pointer;
  font-size: 15px;
  line-height: 1;
  padding: 0;
  display: flex; align-items: center;
}
.rm-tag:hover { color: #fff; }

.tag-suggest {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.suggest-label {
  font-size: var(--text-xs);
  color: var(--c-text-3);
  white-space: nowrap;
}
.tag-pill {
  border: 1px solid var(--c-border);
  background: var(--c-hover);
  border-radius: var(--r-full);
  padding: 3px 10px;
  font-size: var(--text-sm);
  cursor: pointer;
  color: var(--c-text-2);
  transition: all var(--dur);
}
.tag-pill:hover { border-color: var(--c-primary); color: var(--c-primary); }
.tag-pill.active { background: var(--c-primary); color: #fff; border-color: var(--c-primary); }

.custom-tag-row {
  display: flex;
  gap: 8px;
}
.custom-input { flex: 1; }
.add-tag-btn {
  border: 1px solid var(--c-primary);
  background: var(--c-primary-light);
  color: var(--c-primary);
  border-radius: var(--r-md);
  padding: 8px 14px;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--dur);
}
.add-tag-btn:hover { background: var(--c-primary); color: #fff; }

/* Actions */
.general-error {
  color: var(--c-error);
  font-size: var(--text-sm);
  margin: 0 0 12px;
  padding: 8px 12px;
  background: var(--c-error-light);
  border-radius: var(--r-md);
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}
.cancel-btn {
  border: 1px solid var(--c-border);
  background: var(--c-hover);
  color: var(--c-text-2);
  border-radius: var(--r-md);
  padding: 9px 20px;
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur);
}
.cancel-btn:hover { background: #e2e8f0; }
.submit-btn {
  border: none;
  background: var(--c-primary);
  color: #fff;
  border-radius: var(--r-md);
  padding: 9px 24px;
  font-size: var(--text-base);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--dur);
}
.submit-btn:hover:not([disabled]) { background: var(--c-primary-hover); }
.submit-btn[disabled] { opacity: 0.55; cursor: not-allowed; }

@media (max-width: 600px) {
  .modal-box { padding: 18px 16px 22px; }
}
</style>
