# 纯终端批量转录与 Skill 封装 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 复用当前前端到后端的调用链，先做一版“纯终端请求”的单文件/批量 MP4 转录入口，再将其封装为可直接调用的 skill，并最终支持对部署在 `10.112.28.172` 的 BiliFork 服务进行批量转录。

**Architecture:** 保持现有 FastAPI 后端与前端调用协议不变，先抽取“前端请求协议 + 任务轮询 + 结果回收”的最小闭环，形成 CLI/终端入口；随后在 CLI 之上增加目录扫描、批量调度、结果汇总；最后由 skill 作为薄封装入口调用 CLI。整体遵循“先复用、后抽象；先单文件、后批量；先 CLI、后 skill”的路线。

**Tech Stack:** React + Axios 前端调用层、FastAPI 后端、后台任务/状态文件机制、已有 uploads/note_results 目录约定、未来新增 CLI/skill 封装。

---

## 0. 已确认的仓库现状（用于计划边界） 

### 当前前端调用链
- `BillNote_frontend/src/utils/request.ts`
  - 统一 Axios 实例
  - `baseURL = VITE_API_BASE_URL || /api`
  - 请求超时 10 分钟
- `BillNote_frontend/src/services/upload.ts`
  - `POST /upload`
  - `multipart/form-data`
- `BillNote_frontend/src/services/note.ts`
  - `POST /generate_note`
  - `GET /task_status/{task_id}`
  - `POST /delete_task`
- `BillNote_frontend/src/pages/HomePage/components/NoteForm.tsx`
  - 本地文件先上传，再以返回的 `/uploads/...` 作为 `video_url` 提交生成任务
- `BillNote_frontend/src/store/taskStore/index.ts`
  - 前端任务状态模型、重试逻辑、任务 ID 复用逻辑

### 当前后端接口与行为
- `backend/app/routers/note.py`
  - `POST /upload`：保存文件到 `backend/uploads`，返回 `/uploads/<filename>`
  - `POST /generate_note`：提交任务，写入 `PENDING` 状态，后台执行 `run_note_task`
  - `GET /task_status/{task_id}`：读取 `note_results/<task_id>.status.json` 与结果 JSON
- `backend/main.py`
  - 挂载 `/uploads` 静态目录
- `backend/app/services/note.py`
  - 任务实际执行、状态推进、结果产出
- 当前产物目录
  - 上传目录：`backend/uploads`
  - 结果目录：`backend/note_results`

### 关键事实
- 当前“本地视频”并不是直接把本地绝对路径传给后端，而是：
  1. 前端先 `POST /upload`
  2. 后端返回 `/uploads/<file>`
  3. 前端再把这个 URL 作为 `video_url` 调用 `POST /generate_note`
- 因此终端版优先应该复用“上传 + 生成 + 轮询”三段式，而不是自己重新发明协议。

---

## 1. 建议的目标拆分

### 子目标 A：前端协议复用版 CLI（单文件）
输出一个纯终端入口，能完整执行：
- 输入本地 MP4
- 上传到服务
- 提交生成任务
- 轮询任务状态
- 拉取成功结果
- 保存到指定输出目录

### 子目标 B：批量 CLI
在单文件 CLI 基础上增加：
- 扫描目录中的 MP4
- 顺序/有限并发处理
- 跳过已有结果
- 失败重试
- 汇总 summary

### 子目标 C：Skill 封装
将批量 CLI 封装成 skill：
- skill 只负责参数接收与结果汇总
- 复杂请求逻辑保持在 CLI/适配层

---

## 2. 推荐文件结构（规划层，不是最终强制）

### 已有文件（应尽量复用）
- `BillNote_frontend/src/utils/request.ts`
- `BillNote_frontend/src/services/upload.ts`
- `BillNote_frontend/src/services/note.ts`
- `BillNote_frontend/src/pages/HomePage/components/NoteForm.tsx`
- `BillNote_frontend/src/store/taskStore/index.ts`
- `backend/app/routers/note.py`
- `backend/app/services/note.py`

### 建议新增的后续实现位置
> 下列是建议，不代表本轮要写代码。

- CLI 入口层
  - `backend/app/cli/` 或 `backend/scripts/`
  - 负责终端调用入口
- 服务协议适配层
  - `backend/app/clients/` 或 `backend/app/services/terminal_transcribe_*.py`
  - 负责 upload / generate_note / poll status / result normalize
- 批量调度层
  - `backend/app/services/batch_transcription_*.py`
  - 负责扫描、跳过、重试、summary
- Skill 文件
  - 推荐后续放到 skill 目录体系中，作为薄封装入口，内部调用 CLI
- 文档
  - `docs/superpowers/plans/2026-05-15-terminal-transcription-skill-plan.md`（本文件）
  - 后续补 `docs/` 下的调用说明、部署说明、172 服务说明

---

## 3. 实施原则

- [ ] **原则 1：不先改协议，先复用现有协议**
  - 第一版不要先设计新后端 API。
  - 先严格复用前端现有 `/upload` → `/generate_note` → `/task_status/{task_id}`。

- [ ] **原则 2：先单文件打通，再上批量**
  - 单文件成功是所有后续工作的基础验收门槛。

- [ ] **原则 3：Skill 不直接承载底层复杂逻辑**
  - Skill 只做参数入口和结果输出。
  - 上传、轮询、重试、批量调度留在 CLI/服务层。

- [ ] **原则 4：尽量让 10.112.28.172 成为稳定服务节点**
  - 若当前仓库未来部署到 `10.112.28.172`，则终端版/skill 版都以该服务地址为默认目标。
  - 如果 172 已有现成 BiliFork 服务，则应先确认其 base URL、端口、路径前缀、鉴权与可达性。

---

## 4. Phase 1：前端调用链逆向与 172 服务协议确认

### Task 1: 固化当前前端协议表

**Files:**
- Read: `BillNote_frontend/src/utils/request.ts`
- Read: `BillNote_frontend/src/services/upload.ts`
- Read: `BillNote_frontend/src/services/note.ts`
- Read: `BillNote_frontend/src/pages/HomePage/components/NoteForm.tsx`
- Read: `BillNote_frontend/src/store/taskStore/index.ts`
- Output Doc: `docs/` 下后续补充的接口说明文档

- [ ] 记录 `baseURL` 解析方式与环境变量依赖。
- [ ] 明确终端版默认应接受的服务根地址格式，例如：`http://10.112.28.172:PORT/api` 或 `http://10.112.28.172:PORT`。
- [ ] 记录 `/upload` 的字段名、返回字段名、文件保存路径约定。
- [ ] 记录 `/generate_note` 的完整请求体字段及哪些字段是最小必填。
- [ ] 记录 `/task_status/{task_id}` 的成功、处理中、失败返回差异。
- [ ] 明确前端“本地视频任务”的真实链路就是“上传后再提交 URL”，并把这条链路写入文档。

**验收标准：**
- 能得到一张结构化协议表，至少包括 URL、method、headers、body 字段、返回字段、错误语义。

---

### Task 2: 核查后端 172 部署前提

**Files:**
- Read: `backend/main.py`
- Read: `backend/app/routers/note.py`
- Read: `backend/app/services/note.py`
- Read: `.env` / `backend/.env.example`
- Read: `docker-compose.yml`
- Read: `docker-compose.gpu.yml`
- Read: `systemd/bilinote-backend.service`
- Read: `docs/deploy-handover-rfrlserver5-2026-04-26.md`

- [ ] 确认后端是否默认暴露 `/api` 前缀，或由 nginx/前端代理补足。
- [ ] 确认 `uploads` 与 `note_results` 在服务端的真实落盘位置。
- [ ] 确认单个任务是后台执行还是阻塞执行；当前看是 `BackgroundTasks + 串行执行器`，需要在文档中明确。
- [ ] 确认 172 上是否存在额外鉴权、反向代理、路径前缀、跨机访问限制。
- [ ] 确认 172 上 whisper / ffmpeg / GPU / 模型依赖是否已经可用。

**验收标准：**
- 可以回答“终端从另一台机器请求 172 服务时，应该打到哪个 base URL、是否要认证、结果写在哪”。

---

## 5. Phase 2：终端单文件版方案

### Task 3: 定义单文件 CLI 契约

**Files:**
- Create: 后续 CLI 设计文档（建议 `docs/` 下单独补充）
- Future code location: `backend/app/cli/` or `backend/scripts/`

- [ ] 定义单文件模式输入参数：
  - 本地 MP4 路径
  - 输出目录
  - 服务地址（默认 172）
  - 轮询间隔
  - 超时时间
  - 可选质量/模型/provider/style/format 等
- [ ] 明确最小调用参数集：确保即使不做“笔记生成全功能”，也能复用现有接口成功触发转录主链路。
- [ ] 明确终端标准输出内容：任务 ID、当前状态、完成耗时、输出路径、失败原因。
- [ ] 明确本地保存结果的命名规则：按输入文件 basename 输出 `.json/.md/.txt` 等。

**验收标准：**
- 有一份不依赖 UI 的 CLI 契约说明，足够支撑后续实现与测试。

---

### Task 4: 设计单文件执行流程

**Files:**
- Read: `backend/app/routers/note.py`
- Read: `backend/app/services/note.py`
- Future code location: CLI / client / service 层

- [ ] 固化步骤 1：本地文件存在性校验。
- [ ] 固化步骤 2：调用 `/upload` 上传 MP4。
- [ ] 固化步骤 3：取回 `/uploads/<filename>` 并组装成 `generate_note` 的 `video_url`。
- [ ] 固化步骤 4：调用 `/generate_note`，拿到 `task_id`。
- [ ] 固化步骤 5：轮询 `/task_status/{task_id}`，直到 `SUCCESS` / `FAILED` / 超时。
- [ ] 固化步骤 6：把 `result` 保存为本地标准结果文件。
- [ ] 固化步骤 7：如果失败，保留远端返回 message 与本地失败摘要。

**验收标准：**
- 单文件终端流程在设计上闭环，无需前端页面参与。

---

### Task 5: 单文件验收口径

**Files:**
- `docs/cli-contract.md`（已更新，第 12 节验收标准）

- [x] 明确单文件版的”完成定义”：
  - 成功提交任务
  - 能观察到状态推进
  - 成功拉取结果
  - 本地结果文件可定位
  - 失败时错误可读
- [x] 明确”非目标”：
  - 第一版不做复杂并发
  - 第一版不做断点续跑
  - 第一版不立即做 GUI

**验收标准：**
- 后续工程实现时，所有人都用同一组验收标准，不再反复争论范围。

---

## 6. Phase 3：批量 CLI 方案

### Task 6: 定义批量任务模型

**Files:**
- Future code location: `backend/app/services/batch_transcription_*.py`
- Future docs: 批量模式说明

- [ ] 规定“一个 MP4 = 一个任务对象”。
- [ ] 每个任务至少记录：
  - 输入文件路径
  - 远端上传 URL
  - 远端 task_id
  - 本地输出路径
  - 当前状态
  - 重试次数
  - 错误信息
- [ ] 定义批量总状态：总数、成功、失败、跳过、进行中。

**验收标准：**
- 后续实现批量调度时不再依赖前端 store 结构，终端版有独立稳定的任务模型。

---

### Task 7: 定义批量输入与扫描规则

**Files:**
- Future CLI docs

- [ ] 定义批量输入参数：
  - 输入目录
  - 输出目录
  - 是否递归
  - 匹配模式（默认 `*.mp4`）
  - 跳过已完成开关
  - 最大并发数
  - 重试次数
- [ ] 明确如何判断“已完成”：建议依据本地输出产物或 summary 记录，而不是只依赖远端状态。
- [ ] 明确文件名冲突策略：同名不同目录文件如何输出不冲突。

**验收标准：**
- 批量扫描规则稳定且可预测，不会因为目录结构变化而覆盖结果。

---

### Task 8: 定义批量执行策略

**Files:**
- Future batch scheduler docs

- [ ] 第一版默认顺序执行。
- [ ] 第二版再开放有限并发，并发值默认保守。
- [ ] 失败重试只对单文件任务生效，不影响全局批次继续执行。
- [ ] 每个文件完成后立即落地结果与状态，避免批次中断导致所有结果丢失。
- [ ] 设计 summary 文件格式，建议同时输出机器可读（JSON）与人可读（Markdown/文本）版本。

**验收标准：**
- 即使批量中途失败，也能知道已经完成了哪些文件、哪些失败、哪些未开始。

---

## 7. Phase 4：Skill 封装方案

### Task 9: 定义 skill 的边界

**Files:**
- Future skill files
- Future skill docs

- [ ] skill 只暴露高层参数，不重写低层 upload/generate/poll 逻辑。
- [ ] skill 内部调用批量 CLI 或其等价服务层。
- [ ] skill 返回结构化摘要：
  - 输入路径
  - 输出目录
  - 总文件数
  - 成功/失败/跳过数
  - summary 文件路径
  - 失败清单
- [ ] skill 允许把 `10.112.28.172` 作为默认服务地址，但必须保留覆盖能力。

**验收标准：**
- 终端工具与 skill 不出现两套不同协议，不形成双维护。

---

### Task 10: 定义 skill 的用户体验

**Files:**
- Future skill README / usage doc

- [ ] 明确 skill 的最小调用方式：指定输入目录即可运行。
- [ ] 明确高级选项：递归、输出目录、并发、跳过、重试、语言/模型配置。
- [ ] 明确失败反馈：如果 172 服务不可达、上传失败、轮询超时、结果为空，skill 应返回明确诊断。
- [ ] 明确后续扩展能力：字幕导出、纯转录模式、仅上传不转录、仅拉取结果等。

**验收标准：**
- 用户能把它当作“批量转录服务入口”理解，而不是一个需要读源码才能用的开发工具。

---

## 8. 风险清单与缓解策略

### 风险 1：172 服务访问地址与前端代理不一致
- [ ] 缓解：在 Phase 1 明确 base URL、端口、是否经过 nginx、是否需要 `/api` 前缀。

### 风险 2：终端环境与前端环境的鉴权方式不同
- [ ] 缓解：尽量改成 token/header 或内网免鉴权；若依赖 cookie，必须先抽象出终端可用认证方案。

### 风险 3：本地上传大文件耗时长或不稳定
- [ ] 缓解：单文件先验证大文件上传体验；必要时补充进度、重试、超时控制。

### 风险 4：后端实际不仅做转录，还做完整“笔记生成”
- [ ] 缓解：先接受现状复用整条链路；如果后续要拆“纯转录 API”，再单独立项，不影响第一版 CLI/skill 落地。

### 风险 5：批量模式下串行执行器吞吐有限
- [ ] 缓解：先顺序跑通并测出真实速度；是否提升并发交给后续性能阶段，不在 MVP 一开始解决。

### 风险 6：远端结果与本地输出不一致
- [ ] 缓解：优先保存远端原始 `result`，本地衍生文件（如 txt）作为附加产物而不是唯一真相源。

---

## 9. 推荐执行顺序

### Task 11: 先做协议与部署确认
- [ ] 完成前端协议表
- [ ] 完成 172 base URL / 代理 / 鉴权确认
- [ ] 完成上传目录、结果目录、服务能力确认

### Task 12: 再做单文件 CLI
- [ ] 打通 upload → generate_note → task_status
- [ ] 固化本地输出规范
- [ ] 固化错误输出规范

### Task 13: 再扩批量
- [ ] 目录扫描
- [ ] 顺序执行
- [ ] summary
- [ ] 跳过/重试

### Task 14: 最后封 skill
- [ ] skill 参数契约
- [ ] skill 调 CLI
- [ ] skill 结果摘要
- [ ] 使用文档

---

## 10. 计划边界（避免范围漂移）

### 本计划包含
- 复用当前前端协议
- 终端版单文件/批量链路
- 对 `10.112.28.172` 的服务调用方案
- skill 封装边界设计

### 本计划暂不包含
- 重写前后端架构
- 新建独立 Web UI
- Whisper/模型底层大改
- 高性能并行集群调度
- 复杂权限系统

---

## 11. 最终交付定义

当以下四项都成立时，可认为这条路线完成：

- [ ] 能从纯终端对 `10.112.28.172` 的 BiliFork 服务提交单个 MP4 并拿回结果。
- [ ] 能对一个目录的 MP4 做批量转录，并输出清晰 summary。
- [ ] 终端版对失败、超时、重试、跳过有明确行为。
- [ ] 用户可通过一个 skill 直接调用这套批量转录能力。

---

## 12. 后续建议

- [ ] 在正式实现前，先补一份“接口协议与部署确认记录”。
- [ ] 若发现 `generate_note` 耦合过重，可在 CLI 第一版中先容忍其“转录+笔记生成”行为，后续再拆“纯转录 API”。
- [ ] 若 172 环境已稳定，建议把它作为默认服务端；若还不稳定，应先补健康检查与 deploy status 查询能力。

