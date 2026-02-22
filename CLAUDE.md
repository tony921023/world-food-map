# CLAUDE.md

本文件為 Claude Code (claude.ai/code) 在此儲存庫中工作時提供指引。

## 專案概述

World Food Explorer — 全端網頁應用程式，使用者透過互動式 SVG 世界地圖探索各國美食，可進行按讚、留言、搜尋及收藏。

- **前端**: Vue 3 + Vite (JavaScript, Composition API)
- **後端**: Python Flask REST API
- **資料儲存**: `backend/data/` 中的 JSON 檔案（無資料庫）

## 開發指令

### 本機執行（需要兩個終端機）

**後端：**
```bash
cd backend
pip install -r requirements.txt
python app.py
# 執行於 http://127.0.0.1:5000
```

**前端：**
```bash
npm install
npm run dev
# 執行於 http://localhost:5173，透過 vite.config.js 將 /api 和 /static 代理至 Flask
```

### 建置
```bash
npm run build    # 正式環境建置 → dist/
npm run preview  # 預覽正式環境建置
```

### 正式環境後端
```bash
waitress-serve --port 5000 backend:app
```

目前無測試或 lint 設定。

## 架構

### 前端 (`src/`)

**WorldMap.vue** 是主要協調元件 — 透過 `svg-pan-zoom` 載入 SVG 地圖（`public/world.svg`），處理國家選取，並透過 props/emits 協調所有子元件。

元件層級：
- `WorldMap.vue` → `FoodListPanel.vue`（國家美食列表，含標籤篩選） → `FoodDetailModal.vue`（彈窗，含按讚、留言、分享）
- `WorldMap.vue` → `SearchBar.vue`（全域搜尋，含自動完成）
- `WorldMap.vue` → `FavoritesPanel.vue`、`TopFoodsPanel.vue`（側邊欄）

**Composables**（`src/composables/`）：`useFavorites.js`（以 localStorage 儲存的收藏功能）、`useCommentTokens.js`（留言刪除令牌管理）。

狀態存放於元件 refs 中 — 未使用 Vuex/Pinia。URL query params 同步已選取的國家與美食。

### 後端 (`backend/app.py`)

單一檔案 Flask 應用程式，包含所有路由。關鍵模式：
- JSON 檔案持久化，使用 `threading.Lock` 確保原子寫入
- 自動偵測 `foods.json` 檔案修改並重新載入（mtime 檢查）
- 基於 IP 的速率限制（按讚 2 秒、留言 5 秒、留言按讚 2 秒）
- 內容過濾（髒話屏蔽）
- 建立留言時回傳刪除令牌，供匿名刪除使用

### API 路由

| 方法 | 路由 | 用途 |
|------|------|------|
| GET | `/api/foods/<code>` | 取得國家美食列表 |
| GET | `/api/food/<code>/<name>` | 取得美食詳情 |
| GET | `/api/search?q=` | 搜尋（含評分機制） |
| GET | `/api/tags` | 取得所有標籤 |
| POST | `/api/food/<code>/<name>/like` | 美食按讚 |
| POST/GET | `/api/food/<code>/<name>/comments` | 留言 CRUD |
| POST | `/api/food/<code>/<name>/comments/<id>/like` | 留言按讚 |
| GET | `/api/top-foods` | 熱門美食排行 |
| POST | `/api/_reload` | 強制重新載入美食快取 |

### 資料檔案 (`backend/data/`)

- `foods.json` — 美食資料庫，依國家代碼分類
- `likes.json`、`comments.json`、`comment_likes.json` — 使用者互動資料
- `places_cache.json` — 地點快取資料

美食圖片由 `backend/static/foods/` 提供。

## 重要設定

- **vite.config.js**：開發代理將 `/api` 和 `/static` 轉發至 Flask（port 5000）
- 支援國家：日本 (JP)、台灣 (TW)、韓國 (KR)、美國 (US)、加拿大 (CA)
