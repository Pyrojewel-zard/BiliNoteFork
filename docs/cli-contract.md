# BiliNote 单文件 CLI 契约

**版本**: 1.0.0
**创建日期**: 2026-05-15
**目标**: 定义终端批量转录单文件的 CLI 接口契约，支撑后续实现与测试。

---

## 1. 命令入口

```bash
bilinote-cli transcribe <video_path> [options]
```

或使用 Python 模块形式：

```bash
python -m bilinote_cli transcribe <video_path> [options]
```

---

## 2. 必填参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `<video_path>` | string | 本地 MP4 视频文件的绝对路径或相对路径 |

**最小调用示例：**

```bash
bilinote-cli transcribe /path/to/video.mp4
```

> **最小参数集触发完整链路**：上传 → 转录 → 生成笔记。默认值覆盖所有必填字段。

---

## 3. 可选参数

### 3.1 服务连接参数

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--api-base` | `-a` | string | `http://10.112.28.172:8483/api` | BiliNote API 基地址 |
| `--poll-interval` | `-i` | int | `3` | 状态轮询间隔（秒） |
| `--timeout` | `-t` | int | `1800` | 任务超时时间（秒），默认 30 分钟 |

### 3.2 输出参数

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--output-dir` | `-o` | string | `./bilinote_output` | 输出目录，存放结果文件 |
| `--save-transcript` | | flag | `false` | 额外保存原始转写文本（`.txt`） |
| `--save-json` | | flag | `false` | 额外保存完整 JSON 结果（`.json`） |

### 3.3 笔记生成参数

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--quality` | `-q` | string | `medium` | 下载质量：`fast` / `medium` / `slow` |
| `--model` | `-m` | string | （从服务获取首个可用） | LLM 模型名称 |
| `--provider-id` | `-p` | string | （从服务获取首个启用） | LLM 提供商 ID |
| `--style` | `-s` | string | `minimal` | 笔记风格（见下方枚举） |
| `--format` | `-f` | string[] | `[]` | 笔记格式选项：`toc`, `link`, `screenshot`, `summary` |

> **CLI 参数格式说明**：`--format` 在 CLI 中接受逗号分隔字符串（如 `--format toc,link`），内部自动转换为数组 `["toc", "link"]` 后发送给 API。

> **CLI 简化设计说明**：API 中 `screenshot` 和 `link` 是独立的布尔字段，CLI 将其合并到 `--format` 选项中（`--format screenshot,link` 等价于 API 中 `screenshot: true, link: true`），简化用户输入。
| `--extras` | `-e` | string | `null` | 附加备注，追加到 Prompt 末尾 |

### 3.4 视频理解参数

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--video-understanding` | | flag | `false` | 启用视频理解（多模态截图分析） |
| `--video-interval` | | int | `0` | 视频采样间隔（秒），1-30，配合 `--video-understanding` |
| `--grid-size` | | string | `[]` | 拼图尺寸 `[列,行]`，如 `"4,3"` |

> **CLI 参数格式说明**：`--grid-size` 在 CLI 中接受逗号分隔字符串（如 `--grid-size "4,3"`），内部自动转换为数组 `[4, 3]` 后发送给 API。

### 3.5 调试参数

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--verbose` | `-v` | flag | `false` | 显示详细日志 |
| `--dry-run` | | flag | `false` | 模拟执行，不提交任务 |
| `--keep-uploaded` | | flag | `false` | 保留服务端上传文件（不自动清理） |

---

## 4. 笔记风格枚举

| 值 | 标签 | 说明 |
|-----|------|------|
| `minimal` | 精简 | 仅记录最重要的内容，简洁明了 |
| `detailed` | 详细 | 包含完整内容和详细讨论 |
| `academic` | 学术 | 适合学术报告，正式且结构化 |
| `tutorial` | 教程 | 详细记录教程，特别是关键点和结论步骤 |
| `xiaohongshu` | 小红书 | 小红书风格，emoji、爆款关键词 |
| `life_journal` | 生活向 | 记录个人生活感悟，情感化表达 |
| `task_oriented` | 任务导向 | 强调任务、目标，适合工作和待办事项 |
| `business` | 商业风格 | 适合商业报告、会议纪要 |
| `meeting_minutes` | 会议纪要 | 适合会议纪要 |
| `rf_course` | 射频课程 | RF/射频课程讲演录，逐页记录 |
| `tech_share` | 技术分享 | 技术分享讲演录，保留完整技术讲解 |
| `rfic_meeting` | RFIC会议 | RFIC组会讲演录，保留分析过程 |

**CLI 默认值**：`minimal`

---

## 5. 终端标准输出规范

### 5.1 输出格式

CLI 采用结构化输出，便于人类阅读和脚本解析。

#### 任务启动

```
[BiliNote] Starting transcription...
  Input: /path/to/video.mp4
  Output: ./bilinote_output/
  Task ID: <uuid>
```

#### 轮询状态

每 `--poll-interval` 秒输出一行状态：

```
[00:03] Status: TRANSCRIBING - 转录中
[00:06] Status: SUMMARIZING - 总结中
```

#### 任务完成

```
[BiliNote] Task completed successfully.
  Task ID: <uuid>
  Duration: 45s
  Output:
    - ./bilinote_output/video.md
    - ./bilinote_output/video.json (if --save-json)
    - ./bilinote_output/video.txt (if --save-transcript)
```

#### 任务失败

```
[BiliNote] Task failed.
  Task ID: <uuid>
  Duration: 12s
  Reason: <错误详情，来自 API 的 msg 字段>
```

#### 超时

```
[BiliNote] Task timeout after 1800s.
  Task ID: <uuid>
  Last Status: TRANSCRIBING
```

### 5.2 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 成功完成 |
| 1 | 参数错误（文件不存在、参数无效等） |
| 2 | 上传失败 |
| 3 | 任务提交失败 |
| 4 | 任务执行失败（服务端返回 FAILED） |
| 5 | 任务超时 |
| 6 | 网络错误 |
| 7 | 服务不可用（API 健康检查失败） |

---

## 6. 本地保存结果命名规则

### 6.1 输出文件命名

以输入文件的 `basename`（不含扩展名）为基础：

| 文件类型 | 文件名 | 说明 |
|----------|--------|------|
| Markdown 笔记 | `<basename>.md` | 始终生成 |
| 完整 JSON | `<basename>.json` | 仅当 `--save-json` |
| 原始转写文本 | `<basename>.txt` | 仅当 `--save-transcript` |
| 任务元数据 | `<basename>.meta.json` | 包含 task_id、状态、耗时等 |

**示例**：

输入 `/data/videos/RF_Lecture_01.mp4`，输出：

```
./bilinote_output/
├── RF_Lecture_01.md           # 笔记（始终生成）
├── RF_Lecture_01.meta.json    # 元数据
├── RF_Lecture_01.json         # 完整结果（--save-json）
└── RF_Lecture_01.txt          # 转写文本（--save-transcript）
```

### 6.2 元数据格式

`<basename>.meta.json` 内容：

```json
{
  "task_id": "uuid-string",
  "input_file": "/absolute/path/to/video.mp4",
  "output_dir": "./bilinote_output",
  "status": "SUCCESS",
  "duration_seconds": 45,
  "created_at": "2026-05-15T10:30:00Z",
  "completed_at": "2026-05-15T10:30:45Z",
  "platform": "local",
  "style": "minimal",
  "model": "gpt-4o",
  "provider_id": "xxx-xxx-xxx"
}
```

### 6.3 文件冲突处理

- 若输出目录已存在同名文件，默认**覆盖**
- 未来可扩展 `--no-clobber` 参数跳过已存在文件

---

## 7. API 调用流程

### 7.1 健康检查

```bash
GET {api_base}/deploy_status
```

失败则返回退出码 7。

### 7.2 上传文件

```bash
POST {api_base}/upload
Content-Type: multipart/form-data

file: <video_file>
```

响应：

```json
{
  "code": 0,
  "data": { "url": "/uploads/<filename>" }
}
```

失败则返回退出码 2。

### 7.3 提交任务

```bash
POST {api_base}/generate_note
Content-Type: application/json

{
  "video_url": "/uploads/<filename>",
  "platform": "local",
  "quality": "<quality>",
  "model_name": "<model>",
  "provider_id": "<provider_id>",
  "style": "<style>",
  "format": <format_array>,
  "extras": "<extras>",
  "video_understanding": <bool>,
  "video_interval": <int>,
  "grid_size": <array>
}
```

响应：

```json
{
  "code": 0,
  "data": { "task_id": "<uuid>" }
}
```

失败则返回退出码 3。

### 7.4 轮询状态

```bash
GET {api_base}/task_status/{task_id}
```

每 `--poll-interval` 秒轮询，直到 `status === "SUCCESS"` 或 `status === "FAILED"`。

### 7.5 获取结果

成功时从 `result` 字段提取：

- `markdown` → 写入 `.md`
- `transcript.full_text` → 写入 `.txt`（如启用）
- 完整 `result` 对象 → 写入 `.json`（如启用）

---

## 8. 默认值解析策略

### 8.1 provider_id 和 model 默认值

若未指定 `--provider-id` 或 `--model`，CLI 自动查询：

```bash
GET {api_base}/get_all_providers
```

取返回列表中第一个 `enabled === 1` 的 provider，并查询其可用模型：

```bash
GET {api_base}/model_enable/{provider_id}
```

取第一个模型作为默认值。

**若无可用的 provider/model**：返回错误码 1，提示用户手动指定。

### 8.2 其他默认值

| 参数 | 默认值 | 来源 |
|------|--------|------|
| `--api-base` | `http://10.112.28.172:8483/api` | 硬编码，可配置 |
| `--quality` | `medium` | 硬编码 |
| `--style` | `minimal` | 硬编码 |
| `--poll-interval` | `3` | 参考前端实现 |
| `--timeout` | `1800` | 预估转录+生成最大时长 |

---

## 9. 错误处理

### 9.1 参数校验错误

- 文件不存在：`Error: File not found: /path/to/video.mp4`
- 文件非视频格式：`Error: Unsupported file type: .txt`
- 无效 quality：`Error: Invalid quality 'invalid'. Must be: fast, medium, slow`

### 9.2 网络错误

- 连接失败：`Error: Failed to connect to API at http://10.112.28.172:8483/api`
- 超时：`Error: Request timeout after 30s`

### 9.3 任务错误

来自 API 的 `msg` 字段，直接展示：

```
Error: Task failed - 转写失败：音频格式不支持
```

---

## 10. 环境变量支持

CLI 支持通过环境变量预设默认值：

| 环境变量 | 对应参数 | 说明 |
|----------|----------|------|
| `BILINOTE_API_BASE` | `--api-base` | API 基地址 |
| `BILINOTE_PROVIDER_ID` | `--provider-id` | 默认提供商 ID |
| `BILINOTE_MODEL` | `--model` | 默认模型名称 |
| `BILINOTE_STYLE` | `--style` | 默认笔记风格 |
| `BILINOTE_OUTPUT_DIR` | `--output-dir` | 默认输出目录 |
| `BILINOTE_TIMEOUT` | `--timeout` | 默认超时时间（秒） |
| `BILINOTE_POLL_INTERVAL` | `--poll-interval` | 默认轮询间隔（秒） |

**优先级**：命令行参数 > 环境变量 > 硬编码默认值

---

## 11. 完整调用示例

### 基础调用

```bash
bilinote-cli transcribe /data/videos/lecture.mp4
```

### 指定风格和输出目录

```bash
bilinote-cli transcribe /data/videos/lecture.mp4 \
  --style rf_course \
  --output-dir /data/notes/
```

### 启用视频理解

```bash
bilinote-cli transcribe /data/videos/lecture.mp4 \
  --video-understanding \
  --video-interval 10 \
  --grid-size "4,3"
```

### 完整参数

```bash
bilinote-cli transcribe /data/videos/lecture.mp4 \
  --api-base http://10.112.28.172:8483/api \
  --output-dir ./output \
  --quality medium \
  --model gpt-4o \
  --provider-id xxx-xxx-xxx \
  --style rf_course \
  --format toc,link \
  --extras "重点关注射频电路设计部分" \
  --poll-interval 3 \
  --timeout 1800 \
  --save-json \
  --save-transcript \
  --verbose
```

### 环境变量配置

```bash
export BILINOTE_API_BASE=http://10.112.28.172:8483/api
export BILINOTE_STYLE=rf_course
export BILINOTE_OUTPUT_DIR=/data/notes/

bilinote-cli transcribe /data/videos/lecture.mp4
```

---

## 12. 验收标准

### 12.1 单文件版完成定义（Definition of Done）

单文件版 CLI 视为"完成"需满足以下所有条件：

| 序号 | 验收项 | 验证方式 | 通过标准 |
|------|--------|----------|----------|
| 1 | 成功提交任务 | 执行 `bilinote-cli transcribe <video_path>` 后终端输出 `Task ID: <uuid>` | task_id 为有效 UUID 格式 |
| 2 | 能观察到状态推进 | 轮询期间终端输出状态变更 | 至少观察到 `TRANSCRIBING` → `SUMMARIZING` → `SUCCESS/FAILED` 中的一个状态转换 |
| 3 | 成功拉取结果 | 任务完成后本地生成 `.md` 文件 | 文件非空，包含 Markdown 格式笔记内容 |
| 4 | 本地结果文件可定位 | 输出目录结构与预期一致 | 文件名 = 输入文件 basename，路径 = `--output-dir` 参数指定的目录 |
| 5 | 失败时错误可读 | 任务失败时终端输出错误信息 | 错误信息来自服务端 `msg` 字段，人类可读（非 JSON 报错） |

### 12.2 验收测试用例

#### 用例 1: 最小参数调用

**输入**:
```bash
bilinote-cli transcribe /path/to/video.mp4
```

**预期输出**:
- 终端输出 `Task ID: <uuid>`
- 终端输出状态变更序列
- 本地生成 `./bilinote_output/video.md` 和 `./bilinote_output/video.meta.json`
- 退出码 = 0

#### 用例 2: 指定输出目录

**输入**:
```bash
bilinote-cli transcribe /path/to/video.mp4 --output-dir /tmp/test_output
```

**预期输出**:
- 本地生成 `/tmp/test_output/video.md`
- 退出码 = 0

#### 用例 3: 文件不存在

**输入**:
```bash
bilinote-cli transcribe /nonexistent/video.mp4
```

**预期输出**:
- 终端输出 `Error: File not found: /nonexistent/video.mp4`
- 退出码 = 1
- 不创建任何输出文件

#### 用例 4: 服务不可达

**输入**:
```bash
bilinote-cli transcribe /path/to/video.mp4 --api-base http://nonexistent:8483/api
```

**预期输出**:
- 终端输出 `Error: Failed to connect to API at http://nonexistent:8483/api`
- 退出码 = 6 或 7
- 不创建任何输出文件

#### 用例 5: 任务执行失败

**输入**:
```bash
# 假设服务端因某种原因返回 FAILED
bilinote-cli transcribe /path/to/corrupted.mp4
```

**预期输出**:
- 终端输出 `Error: Task failed - <错误详情>`
- 本地生成 `./bilinote_output/corrupted.meta.json`，包含 `error_message` 字段
- 退出码 = 4

### 12.3 非目标边界（Out of Scope for V1）

以下功能明确不在单文件版第一版范围内，避免范围漂移：

| 非目标项 | 原因 | 计划纳入版本 |
|----------|------|--------------|
| 复杂并发控制 | 第一版仅需串行执行，`--concurrency` 参数延后 | V2（批量模式） |
| 断点续跑 | 需要持久化任务状态，增加复杂度 | V2（批量模式） |
| GUI 界面 | 终端版优先，GUI 需要额外技术栈 | 未规划 |
| 进度条显示 | 第一版使用文本状态输出即可 | V2 |
| 配置文件持久化 | 第一版使用环境变量 + 命令行参数 | V2 |
| 批量模式 | 单文件是批量模式的基础 | V2 |
| 纯转录模式（不生成笔记） | 当前后端 API 耦合转录与笔记生成 | 需后端 API 改造 |

### 12.4 范围边界判断原则

当后续工程实现遇到以下情况时，按此原则判断是否超出 V1 范围：

| 情况 | 判断原则 |
|------|----------|
| 新增参数 | 是否影响"最小参数集"原则？若仅增加可选参数且不影响默认行为，可纳入 V1 |
| 性能优化 | 是否改变外部行为？若仅优化内部实现（如更快的 HTTP 客户端），可纳入 V1 |
| 错误处理增强 | 是否让错误更可读？若不影响成功路径，可纳入 V1 |
| 新增输出格式 | 是否符合现有命名规则？若仅需新增解析逻辑，可考虑纳入 V1 |
| 批量处理逻辑 | 明确超出 V1 范围，纳入 V2 |

### 12.5 文档验收清单

- [x] 定义单文件模式输入参数（第 2-4 节）
- [x] 明确最小调用参数集：仅 `<video_path>` 即可触发完整链路（第 2 节）
- [x] 明确终端标准输出内容：任务 ID、当前状态、完成耗时、输出路径、失败原因（第 5 节）
- [x] 明确本地保存结果的命名规则：按输入文件 basename 输出 `.md/.json/.txt/.meta.json`（第 6 节）
- [x] 明确完成定义与验收用例（本节 12.1-12.2）
- [x] 明确非目标边界（本节 12.3）

---

## 13. 后续扩展（Phase 2+）

| 功能 | 说明 |
|------|------|
| 批量模式 | `bilinote-cli transcribe *.mp4` 或从文件列表读取 |
| 断点续传 | 记录已完成的 task_id，支持恢复查询 |
| 并发控制 | `--concurrency N` 控制并发任务数 |
| 进度条 | 使用 rich 库显示进度条 |
| 配置文件 | 支持 `~/.bilinote/config.yaml` 持久化配置 |

---

## 附录 A：任务状态枚举

| 状态 | 说明 |
|------|------|
| `PENDING` | 排队中 |
| `PARSING` | 解析链接 |
| `DOWNLOADING` | 下载中 |
| `TRANSCRIBING` | 转录中 |
| `SUMMARIZING` | 总结中 |
| `FORMATTING` | 格式化中 |
| `SAVING` | 保存中 |
| `SUCCESS` | 完成 |
| `FAILED` | 失败 |

**注意**：`PARSING`、`FORMATTING`、`SAVING` 执行时间极短，可能观察不到。

---

## 附录 B：API 响应格式参考

详见 `docs/api-protocol.md`。

---

## 附录 C：单文件执行流程设计

本节定义终端批量转录的单文件执行流程，是 CLI 实现的核心逻辑参考。

### C.1 执行流程概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        单文件执行流程                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  输入: /path/to/video.mp4                                               │
│                                                                         │
│  ┌─────────┐   ┌─────────┐   ┌─────────────┐   ┌─────────────┐         │
│  │ Step 1  │──▶│ Step 2  │──▶│   Step 3    │──▶│   Step 4    │         │
│  │ 文件校验 │   │ 上传文件 │   │ 提交任务    │   │ 轮询状态    │         │
│  └─────────┘   └─────────┘   └─────────────┘   └─────────────┘         │
│       │             │             │                 │                   │
│       ▼             ▼             ▼                 ▼                   │
│   文件存在?     POST /upload   POST /generate    GET /task_status      │
│   格式正确?     获取 URL       获取 task_id      循环直到终态           │
│       │             │             │                 │                   │
│       ▼             ▼             ▼                 ▼                   │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                         Step 5: 保存结果                         │   │
│   │  SUCCESS → 保存 .md + .meta.json (+ .json/.txt 可选)            │   │
│   │  FAILED  → 保存失败摘要到 .meta.json                             │   │
│   │  TIMEOUT → 保存超时信息到 .meta.json                             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  输出: ./bilinote_output/video.md + video.meta.json                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### C.2 详细步骤定义

#### Step 1: 本地文件存在性校验

**目的**: 确保输入文件存在且格式有效，尽早失败。

**校验规则**:

| 校验项 | 规则 | 失败处理 |
|--------|------|----------|
| 文件存在 | `os.path.exists(video_path)` | 退出码 1，打印 "File not found" |
| 是文件非目录 | `os.path.isfile(video_path)` | 退出码 1，打印 "Path is a directory" |
| 扩展名校验 | 支持 `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`, `.wmv` | 退出码 1，打印 "Unsupported file type" |
| 文件大小 | 大于 0 字节 | 退出码 1，打印 "File is empty" |
| 可读权限 | `os.access(video_path, os.R_OK)` | 退出码 1，打印 "File not readable" |

**实现伪代码**:

```
function validate_local_file(video_path):
    if not exists(video_path):
        exit(1, "Error: File not found: {video_path}")

    if is_directory(video_path):
        exit(1, "Error: Path is a directory: {video_path}")

    ext = get_extension(video_path).lower()
    if ext not in SUPPORTED_EXTENSIONS:
        exit(1, "Error: Unsupported file type: {ext}. Supported: mp4, avi, mov, mkv, webm, flv, wmv")

    if file_size(video_path) == 0:
        exit(1, "Error: File is empty: {video_path}")

    if not is_readable(video_path):
        exit(1, "Error: File not readable: {video_path}")

    return True
```

**支持的文件扩展名**:

```python
SUPPORTED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
```

---

#### Step 2: 上传文件到服务端

**目的**: 将本地视频文件上传到 BiliNote 后端，获取服务端可访问的 URL。

**API 调用**:

```http
POST {api_base}/upload
Content-Type: multipart/form-data

file: <video_file>
```

**请求参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `file` | File | 视频文件，保留原始文件名 |

**成功响应**:

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "url": "/uploads/<filename>"
  }
}
```

**失败处理**:

| 场景 | 处理 |
|------|------|
| 网络连接失败 | 退出码 6，打印 "Failed to connect to API" |
| HTTP 错误 (4xx/5xx) | 退出码 2，打印 "Upload failed: {status_code}" |
| 响应 code != 0 | 退出码 2，打印 "Upload failed: {msg}" |
| 超时 | 退出码 6，打印 "Upload timeout after {timeout}s" |

**上传超时计算**:

```
upload_timeout = max(60, file_size_mb * 2)  # 至少 60 秒，每 MB 额外 2 秒
upload_timeout = min(upload_timeout, 600)    # 最大 10 分钟
```

**实现伪代码**:

```
function upload_file(video_path, api_base):
    filename = basename(video_path)
    file_size = get_file_size(video_path)
    timeout = calculate_upload_timeout(file_size)

    try:
        response = http_post_multipart(
            url = "{api_base}/upload",
            file_field = "file",
            file_path = video_path,
            filename = filename,
            timeout = timeout
        )

        if response.code != 0:
            exit(2, "Upload failed: {response.msg}")

        return response.data.url  # 例如 "/uploads/video.mp4"

    except ConnectionError:
        exit(6, "Failed to connect to API at {api_base}")
    except TimeoutError:
        exit(6, "Upload timeout after {timeout}s")
```

---

#### Step 3: 组装请求参数并提交任务

**目的**: 将上传获得的 URL 作为 `video_url`，组装完整请求参数提交给 `/generate_note`。

**请求参数组装**:

| 字段 | 值来源 | 说明 |
|------|--------|------|
| `video_url` | Step 2 返回的 URL | 例如 `/uploads/video.mp4` |
| `platform` | 固定值 `"local"` | 本地文件平台标识 |
| `quality` | CLI 参数或默认 `"medium"` | 下载质量 |
| `model_name` | CLI 参数或自动查询 | LLM 模型名称 |
| `provider_id` | CLI 参数或自动查询 | LLM 提供商 ID |
| `style` | CLI 参数或默认 `"minimal"` | 笔记风格 |
| `format` | CLI 参数或默认 `[]` | 格式选项数组 |
| `screenshot` | 从 `format` 推断 | `"screenshot" in format` |
| `link` | 从 `format` 推断 | `"link" in format` |
| `extras` | CLI 参数或 `null` | 附加备注 |
| `video_understanding` | CLI 参数或 `false` | 视频理解开关 |
| `video_interval` | CLI 参数或 `0` | 采样间隔 |
| `grid_size` | CLI 参数或 `[]` | 拼图尺寸 |

**API 调用**:

```http
POST {api_base}/generate_note
Content-Type: application/json

{
  "video_url": "/uploads/video.mp4",
  "platform": "local",
  "quality": "medium",
  "model_name": "gpt-4o",
  "provider_id": "xxx-xxx-xxx",
  "style": "minimal",
  "format": [],
  "screenshot": false,
  "link": false
}
```

> **注**: `screenshot` 和 `link` 字段是从 `format` 数组推断的。示例中同时显示两者是为了完整性展示请求体结构，实际实现应根据 `format` 数组内容自动计算这两个布尔值（见下方伪代码）。

**成功响应**:

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "uuid-string"
  }
}
```

**失败处理**:

| 场景 | 处理 |
|------|------|
| 网络错误 | 退出码 6 |
| HTTP 400 | 退出码 3，打印参数错误详情 |
| HTTP 500 | 退出码 3，打印服务器错误 |
| 响应 code != 0 | 退出码 3，打印错误信息 |

**自动获取 provider_id 和 model 默认值**:

若未通过 CLI 参数指定，执行以下查询:

```http
GET {api_base}/get_all_providers
```

取第一个 `enabled == 1` 的 provider，记录其 `id` 和默认模型。

```http
GET {api_base}/model_enable/{provider_id}
```

取第一个可用模型作为默认值。

若无可用的 provider/model，退出码 1，提示用户手动指定。

**实现伪代码**:

```
# api_base: 后端 API 基础路径，已包含 /api 前缀
# 例如: http://localhost:8483/api
function submit_task(video_url, options, api_base):
    # 自动获取默认值
    if not options.provider_id or not options.model:
        provider, model = get_default_provider_and_model(api_base)
        if not provider:
            exit(1, "No enabled provider found. Please specify --provider-id and --model")

        options.provider_id = options.provider_id or provider.id
        options.model = options.model or model

    # 推断 screenshot 和 link
    screenshot = "screenshot" in options.format
    link = "link" in options.format

    request_body = {
        "video_url": video_url,
        "platform": "local",
        "quality": options.quality,
        "model_name": options.model,
        "provider_id": options.provider_id,
        "style": options.style,
        "format": options.format,
        "screenshot": screenshot,
        "link": link,
        "extras": options.extras,
        "video_understanding": options.video_understanding,
        "video_interval": options.video_interval,
        "grid_size": options.grid_size
    }

    response = http_post("{api_base}/generate_note", json=request_body)

    if response.code != 0:
        exit(3, "Task submission failed: {response.msg}")

    return response.data.task_id
```

---

#### Step 4: 轮询任务状态

**目的**: 周期性查询任务状态，直到任务完成（成功/失败）或超时。

**轮询逻辑**:

```
状态终态: SUCCESS, FAILED
状态进行中: PENDING, PARSING, DOWNLOADING, TRANSCRIBING, SUMMARIZING, SAVING
```

**轮询参数**:

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `poll_interval` | 3 秒 | 轮询间隔 |
| `timeout` | 1800 秒 (30 分钟) | 最大等待时间 |

**API 调用**:

```http
GET {api_base}/task_status/{task_id}
```

**响应格式**:

**进行中**:

```json
{
  "code": 0,
  "data": {
    "status": "TRANSCRIBING",
    "message": "转录中",
    "task_id": "uuid-string"
  }
}
```

**成功**:

```json
{
  "code": 0,
  "data": {
    "status": "SUCCESS",
    "message": "完成",
    "task_id": "uuid-string",
    "result": {
      "markdown": "...",
      "transcript": {
        "full_text": "...",
        "segments": [...]
      },
      "audio_meta": {...}
    }
  }
}
```

**失败**:

```json
{
  "code": 500,
  "msg": "错误详情信息"
}
```

**终端输出格式**:

轮询过程中输出状态变更:

```
[00:00] Status: PENDING - 排队中
[00:03] Status: DOWNLOADING - 下载中
[00:15] Status: TRANSCRIBING - 转录中
[00:45] Status: SUMMARIZING - 总结中
[01:30] Status: SUCCESS - 完成
```

**超时处理**:

```
[BiliNote] Task timeout after 1800s.
  Task ID: <uuid>
  Last Status: TRANSCRIBING
```

**实现伪代码**:

```
function poll_task_status(task_id, api_base, poll_interval, timeout):
    start_time = now()
    last_status = None

    while elapsed_seconds(start_time) < timeout:
        response = http_get("{api_base}/task_status/{task_id}")

        # 处理失败响应
        if response.code != 0:
            return {
                "status": "FAILED",
                "message": response.msg,
                "result": None
            }

        current_status = response.data.status

        # 输出状态变更
        if current_status != last_status:
            print_status(elapsed_seconds, current_status, response.data.message)
            last_status = current_status

        # 检查终态
        if current_status == "SUCCESS":
            return {
                "status": "SUCCESS",
                "message": response.data.message,
                "result": response.data.result,
                "duration": elapsed_seconds(start_time)
            }

        if current_status == "FAILED":
            return {
                "status": "FAILED",
                "message": response.data.message or "任务失败",
                "result": None,
                "duration": elapsed_seconds(start_time)
            }

        sleep(poll_interval)

    # 超时
    return {
        "status": "TIMEOUT",
        "message": "任务超时",
        "last_status": last_status,
        "result": None,
        "duration": timeout
    }
```

---

#### Step 5: 保存结果到本地

**目的**: 将任务结果保存到本地输出目录，生成标准格式的输出文件。

**输出文件**:

| 文件名 | 生成条件 | 内容 |
|--------|----------|------|
| `<basename>.md` | 始终 | Markdown 笔记 |
| `<basename>.meta.json` | 始终 | 任务元数据 |
| `<basename>.json` | `--save-json` | 完整 JSON 结果 |
| `<basename>.txt` | `--save-transcript` | 原始转写文本 |

**basename 计算规则**:

```
basename = stem(video_path)  # 不含扩展名的文件名
# 例如: /data/videos/RF_Lecture_01.mp4 -> basename = "RF_Lecture_01"
```

**文件冲突处理**:

- 默认覆盖同名文件
- 后续可扩展 `--no-clobber` 参数跳过已存在文件

**元数据格式 (`<basename>.meta.json`)**:

```json
{
  "task_id": "uuid-string",
  "input_file": "/absolute/path/to/video.mp4",
  "output_dir": "./bilinote_output",
  "status": "SUCCESS",
  "duration_seconds": 45,
  "created_at": "2026-05-15T10:30:00Z",
  "completed_at": "2026-05-15T10:30:45Z",
  "platform": "local",
  "style": "minimal",
  "model": "gpt-4o",
  "provider_id": "xxx-xxx-xxx",
  "error_message": null
}
```

**失败时元数据**:

```json
{
  "task_id": "uuid-string",
  "input_file": "/absolute/path/to/video.mp4",
  "output_dir": "./bilinote_output",
  "status": "FAILED",
  "duration_seconds": 12,
  "created_at": "2026-05-15T10:30:00Z",
  "completed_at": "2026-05-15T10:30:12Z",
  "platform": "local",
  "style": "minimal",
  "model": "gpt-4o",
  "provider_id": "xxx-xxx-xxx",
  "error_message": "转写失败：音频格式不支持"
}
```

**实现伪代码**:

```
function save_results(result, video_path, output_dir, options):
    basename = stem(video_path)
    ensure_directory(output_dir)

    # 元数据
    meta = {
        "task_id": result.task_id,
        "input_file": absolute_path(video_path),
        "output_dir": output_dir,
        "status": result.status,
        "duration_seconds": result.duration,
        "created_at": result.start_time,
        "completed_at": result.end_time,
        "platform": "local",
        "style": options.style,
        "model": options.model,
        "provider_id": options.provider_id,
        "error_message": result.message if result.status == "FAILED" else null
    }

    write_file("{output_dir}/{basename}.meta.json", json_dumps(meta))

    if result.status == "SUCCESS":
        # Markdown 笔记
        write_file("{output_dir}/{basename}.md", result.result.markdown)

        # 可选: 完整 JSON
        if options.save_json:
            write_file("{output_dir}/{basename}.json", json_dumps(result.result))

        # 可选: 转写文本
        if options.save_transcript:
            write_file("{output_dir}/{basename}.txt", result.result.transcript.full_text)

    # 失败时不生成 .md/.json/.txt，仅保留 .meta.json
```

---

### C.3 完整执行流程伪代码

```
function transcribe_single_file(video_path, options):
    # ==================== Step 1: 文件校验 ====================
    validate_local_file(video_path)

    # 打印启动信息
    print("[BiliNote] Starting transcription...")
    print("  Input: {video_path}")
    print("  Output: {options.output_dir}/")

    # ==================== Step 2: 上传文件 ====================
    print("Uploading file...")
    uploaded_url = upload_file(video_path, options.api_base)
    print("  Uploaded to: {uploaded_url}")

    # ==================== Step 3: 提交任务 ====================
    print("Submitting task...")
    task_id = submit_task(uploaded_url, options, options.api_base)
    print("  Task ID: {task_id}")

    # ==================== Step 4: 轮询状态 ====================
    result = poll_task_status(
        task_id,
        options.api_base,
        options.poll_interval,
        options.timeout
    )

    # ==================== Step 5: 保存结果 ====================
    save_results(result, video_path, options.output_dir, options)

    # ==================== Step 6: 输出结果摘要 ====================
    if result.status == "SUCCESS":
        print("[BiliNote] Task completed successfully.")
        print("  Task ID: {task_id}")
        print("  Duration: {result.duration_seconds}s")
        print("  Output:")
        print("    - {output_dir}/{basename}.md")
        exit(0)

    elif result.status == "FAILED":
        print("[BiliNote] Task failed.")
        print("  Task ID: {task_id}")
        print("  Duration: {result.duration_seconds}s")
        print("  Reason: {result.message}")
        exit(4)

    elif result.status == "TIMEOUT":
        print("[BiliNote] Task timeout after {options.timeout}s.")
        print("  Task ID: {task_id}")
        print("  Last Status: {result.last_status}")
        exit(5)
```

---

### C.4 错误处理矩阵

| 错误类型 | 退出码 | 输出信息 | 本地产物 |
|----------|--------|----------|----------|
| 文件不存在 | 1 | `Error: File not found: /path/to/video.mp4` | 无 |
| 文件格式不支持 | 1 | `Error: Unsupported file type: .txt` | 无 |
| 上传失败（网络） | 6 | `Error: Failed to connect to API at ...` | 无 |
| 上传失败（HTTP） | 2 | `Error: Upload failed: 500 Internal Server Error` | 无 |
| 任务提交失败 | 3 | `Error: Task submission failed: ...` | 无 |
| 任务执行失败 | 4 | `Error: Task failed - 转写失败：音频格式不支持` | `.meta.json` (含 error_message) |
| 任务超时 | 5 | `Error: Task timeout after 1800s. Last Status: TRANSCRIBING` | `.meta.json` (含 last_status) |

---

### C.5 输出目录结构示例

执行以下命令:

```bash
bilinote-cli transcribe /data/videos/RF_Lecture_01.mp4 --save-json --save-transcript
```

输出目录 `./bilinote_output/` 结构:

```
./bilinote_output/
├── RF_Lecture_01.md           # Markdown 笔记（始终生成）
├── RF_Lecture_01.meta.json    # 任务元数据（始终生成）
├── RF_Lecture_01.json         # 完整 JSON 结果（--save-json）
└── RF_Lecture_01.txt          # 转写文本（--save-transcript）
```

---

### C.6 验收清单

- [x] Step 1: 本地文件存在性校验（文件存在、格式正确、可读）
- [x] Step 2: 调用 `/upload` 上传 MP4，获取 `/uploads/<filename>` URL
- [x] Step 3: 组装请求参数，调用 `/generate_note`，获取 `task_id`
- [x] Step 4: 轮询 `/task_status/{task_id}`，直到 SUCCESS/FAILED/超时
- [x] Step 5: 保存结果到本地（`.md` + `.meta.json` + 可选 `.json/.txt`）
- [x] Step 6: 失败时保留服务端返回 message 与本地失败摘要
- [x] 定义退出码语义
- [x] 定义终端输出格式
- [x] 单文件终端流程在设计上闭环，无需前端页面参与
