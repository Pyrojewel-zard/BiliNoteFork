# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BiliNote 是 AI 视频笔记生成工具。从视频链接（Bilibili、YouTube、抖音、快手、本地文件）提取内容，用 LLM 生成结构化 Markdown 笔记。全栈应用：FastAPI 后端 + React 前端，可选 Tauri 桌面打包。

## 开发命令

### 后端 (Python 3.11 + FastAPI)
```bash
cd backend
/home/RFRL26/miniconda3/envs/bilinote5090/bin/python -m pip install -r requirements.txt
/home/RFRL26/miniconda3/envs/bilinote5090/bin/python main.py    # 启动于 0.0.0.0:8483
/home/RFRL26/miniconda3/envs/bilinote5090/bin/python -m pytest            # 运行 backend/tests/
/home/RFRL26/miniconda3/envs/bilinote5090/bin/python -m pytest tests/test_request_chunker.py::test_name   # 单个测试
```

### 前端 (React 19 + Vite + TypeScript)
```bash
cd BillNote_frontend
pnpm install
pnpm dev          # 开发服务器端口 3015，代理 /api 到后端
pnpm build        # 生产构建
pnpm lint         # ESLint
```

### Systemd 服务部署（生产环境）
```bash
# 复制服务文件
sudo cp systemd/bilinote-backend.service /etc/systemd/system/
sudo cp systemd/bilinote-frontend.service /etc/systemd/system/

# 启用并启动
sudo systemctl enable --now bilinote-backend
sudo systemctl enable --now bilinote-frontend

# 查看日志
tail -f /tmp/bilinote-backend.log
tail -f /tmp/bilinote-frontend.log
```

### Docker
```bash
docker-compose up -d                             # 标准部署
docker-compose -f docker-compose.gpu.yml up -d   # GPU 加速
```

### 桌面版 (Tauri)
```bash
cd backend && ./build.sh          # PyInstaller 打包后端
cd BillNote_frontend && pnpm tauri build
```

## 架构

**后端** (`backend/`) — FastAPI，入口 `main.py`：
- `app/routers/` — API 路由：`note.py`（生成）、`provider.py`、`model.py`、`config.py`、`chat.py`（基于已生成笔记的 RAG 问答）
- `app/services/` — 业务逻辑：
  - `note.py`（NoteGenerator 编排完整流水线）
  - `task_serial_executor.py`（任务队列）
  - `chat_service.py` + `chat_tools.py` + `vector_store.py` — RAG 问答 + Function Calling，索引转写与视频元数据
  - `cookie_manager.py` — 平台 cookie 存储，注入 yt-dlp（如 Bilibili）
  - `transcriber_config_manager.py` — 转写器持久化配置
- `app/downloaders/` — 平台适配器（bilibili、youtube、douyin、kuaishou、local），共享 `base.py` 接口
- `app/transcriber/` — 语音转文字引擎（fast-whisper、groq、bcut、kuaishou、mlx-whisper），工厂在 `transcriber_provider.py`。YouTube 链路优先使用已有字幕，命中则跳过音频下载。
- `app/gpt/` — LLM 集成，工厂模式 `gpt_factory.py`，提示模板 `prompt.py`/`prompt_builder.py`，长文本分块 `request_chunker.py`
- `app/db/` — SQLite + SQLAlchemy：DAO 模式（`provider_dao.py`、`model_dao.py`、`video_task_dao.py`），模型在 `models/`
- `app/utils/` — `response.py`（ResponseWrapper 统一 JSON）、`video_helper.py`（FFmpeg 截图）、`export.py`（PDF/DOCX）、`ppt_generator.py`、`minio_client.py`
- `app/validators/video_url_validator.py` — URL → 平台识别（扩展端有镜像实现）
- `app/exceptions/` — `BizException` + 处理器，在 `main.py` 通过 `register_exception_handlers` 注册
- `events/` — Blinker 信号系统，用于后处理（如转写完成后清理临时文件）；在 `lifespan` 启动时注册
- `backend/ffmpeg_helper.py` — `ensure_ffmpeg_or_raise` 启动时调用，支持 `FFMPEG_BIN_PATH`

**前端** (`BillNote_frontend/src/`) — React 19 + Vite + Tailwind + shadcn/ui：
- `pages/HomePage/` — 主界面：`NoteForm.tsx`（输入）、`MarkdownViewer.tsx`（预览）、`MarkmapComponent.tsx`（思维导图）
- `pages/SettingPage/` — LLM 提供商管理、系统监控、转写器配置
- `store/` — Zustand stores：`taskStore`、`modelStore`、`configStore`、`providerStore`，持久化到 IndexedDB
- `services/` — Axios API 客户端，对应后端路由
- `hooks/useTaskPolling.ts` — 每 3 秒轮询任务状态
- `components/ui/` — shadcn/ui（Radix）组件
- `i18n/` — `react-i18next`，locale JSON 在 `i18n/locales/`，通过 `components/LanguageSwitcher.tsx` 切换
- 路径别名：`@` → `./src`

### 浏览器扩展 (Vue 3 + vitesse-webext, MV3)
```bash
cd BillNote_extension
pnpm install
pnpm dev          # watch 模式 → ./extension/
pnpm build        # 生产构建 → ./extension/
pnpm typecheck
pnpm test         # Vitest 单元测试
pnpm test:e2e     # Playwright e2e
```
在 `chrome://extensions/` 加载已解压扩展 → 选 `BillNote_extension/extension/`。与后端通信 `http://localhost:8483`（可在 options 页配置）。`backend/main.py` 的 CORS 已通过正则接受 `chrome-extension://` 和 `moz-extension://`。

**扩展架构** (`BillNote_extension/`) — Vue 3 + Vite + UnoCSS + webextension-polyfill, MV3：
- `src/popup/Popup.vue` — 主入口：从活动标签页 URL 识别平台，驱动生成流程，展示进度 + markdown
- `src/options/Options.vue` — 设置：后端 URL、默认 provider/model、画质、截图/链接开关、风格
- `src/logic/api.ts` — 后端 API 客户端（用 `settings.backendUrl`，解包 `ResponseWrapper`，把 `/static/screenshots/...` 图片路径绝对化）
- `src/logic/storage.ts` — 基于 `chrome.storage.local` 的类 Pinia 状态（设置 + 最近 30 个任务）
- `src/logic/platform.ts` — URL → 平台识别，镜像 `backend/app/validators/video_url_validator.py`
- `src/sidepanel/`、`src/contentScripts/` — P2/P3 占位（浮按钮、侧边栏思维导图、RAG chat），MVP 未接入
- `src/manifest.ts` — MV3 manifest，popup 为默认 action；`host_permissions: *://*/*`
- 轮询在 popup 客户端进行（打开时 3s 间隔）；MV3 service worker 在 P1 刻意保持精简

**核心流程**：提交 URL → 任务入队 → 下载视频 → FFmpeg 提取音频 → 转写（Whisper/Groq 等）→ LLM 生成笔记 → 前端轮询完成 → 显示 Markdown + 思维导图

## 部署信息

- **生产服务器**：`10.112.28.172`
- **访问地址**：`http://10.112.28.172:3015`
- **CORS**：`backend/main.py` 使用正则 (`CORS_ORIGIN_REGEX`)，允许 localhost、`tauri.localhost`、`chrome-extension://` / `moz-extension://` 来源 —— 桌面应用与浏览器扩展必需。

## 关键配置

- **端口**：后端 8483，前端开发 3015，Docker 映射 3015→80
- **环境变量**：根目录 `.env`（从 `.env.example` 复制）。LLM API 密钥通过 UI 配置，不走 env。
- **数据库**：SQLite 位于 `backend/app/db/bili_note.db`，首次运行自动初始化
- **FFmpeg**：系统依赖，用于视频/音频处理
- **Whisper 模型**：存储于 `backend/models/whisper/whisper-{size}/`，首次使用时从 ModelScope 自动下载
- **Vite 代理**：开发服务器代理 `/api` 和 `/static` 到后端（`vite.config.ts`）

## 转写器配置

通过环境变量或 UI 配置：
- `TRANSCRIBER_TYPE`：fast-whisper / bcut / kuaishou / mlx-whisper（仅 Apple）/ groq
- `WHISPER_MODEL_SIZE`：tiny / base / small / medium / large-v1 / large-v2 / large-v3 / large-v3-turbo

## 代码风格

- **前端**：ESLint + Prettier（2 空格、单引号、100 字符宽度、Tailwind 插件）。TypeScript strict 模式。
- **后端**：Python 类型注解。无配置 linter。使用 Pydantic 模型验证。
- **注意**：前端目录名为 `BillNote_frontend`（不是 "Bili"）。
