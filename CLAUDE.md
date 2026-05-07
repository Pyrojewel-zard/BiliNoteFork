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
- `app/routers/` — API 路由：`note.py`（生成）、`provider.py`、`model.py`、`config.py`
- `app/services/` — 业务逻辑：`note.py`（NoteGenerator 编排完整流水线）、`task_serial_executor.py`（任务队列）
- `app/downloaders/` — 平台适配器（bilibili、youtube、douyin、kuaishou、local），共享 `base.py` 接口
- `app/transcriber/` — 语音转文字引擎（fast-whisper、groq、bcut、kuaishou、mlx-whisper），工厂在 `transcriber_provider.py`
- `app/gpt/` — LLM 集成，工厂模式 `gpt_factory.py`，提示模板 `prompt.py`/`prompt_builder.py`，长文本分块 `request_chunker.py`
- `app/db/` — SQLite + SQLAlchemy：DAO 模式（`provider_dao.py`、`model_dao.py`、`video_task_dao.py`），模型在 `models/`
- `app/utils/` — `response.py`（ResponseWrapper 统一 JSON）、`video_helper.py`（FFmpeg 截图）、`export.py`（PDF/DOCX）
- `events/` — Blinker 信号系统，用于后处理（如转写完成后清理临时文件）

**前端** (`BillNote_frontend/src/`) — React 19 + Vite + Tailwind + shadcn/ui：
- `pages/HomePage/` — 主界面：`NoteForm.tsx`（输入）、`MarkdownViewer.tsx`（预览）、`MarkmapComponent.tsx`（思维导图）
- `pages/SettingPage/` — LLM 提供商管理、系统监控、转写器配置
- `store/` — Zustand stores：`taskStore`、`modelStore`、`configStore`、`providerStore`
- `services/` — Axios API 客户端，对应后端路由
- `hooks/useTaskPolling.ts` — 每 3 秒轮询任务状态
- `components/ui/` — shadcn/ui（Radix）组件
- 路径别名：`@` → `./src`

**核心流程**：提交 URL → 任务入队 → 下载视频 → FFmpeg 提取音频 → 转写（Whisper/Groq 等）→ LLM 生成笔记 → 前端轮询完成 → 显示 Markdown + 思维导图

## 部署信息

- **生产服务器**：`10.112.28.172`
- **访问地址**：`http://10.112.28.172:3015`

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
