# BiliNote 终端批量转录 Skill 规范

**版本**: 1.0.0
**创建日期**: 2026-05-15
**目标**: 定义终端批量转录 skill 的边界、参数、返回结构与 CLI 的关系，确保不形成两套不同协议。

---

## 1. 设计原则

### 1.1 核心边界

| 边界原则 | 说明 |
|----------|------|
| skill 只暴露高层参数 | 不重写低层 upload/generate/poll 逻辑 |
| skill 内部调用 CLI | 复用已有的 CLI 实现，不重复实现协议 |
| skill 返回结构化摘要 | 便于后续处理和报告 |
| 服务地址可配置 | 默认 172，但必须保留覆盖能力 |

### 1.2 单一来源原则

**CLI 是唯一协议来源。**

```
+----------------+     +----------------+     +----------------+
|  Skill (高层)   | --> |  CLI (协议层)   | --> |  API (服务层)   |
+----------------+     +----------------+     +----------------+
      参数映射              参数验证/转换          业务逻辑
      结果聚合              流程编排               数据处理
      报告生成              状态管理               存储
```

**禁止**：
- Skill 直接调用 API（绕过 CLI）
- Skill 重新实现 upload/generate/poll 逻辑
- Skill 与 CLI 参数不一致
- Skill 与 CLI 返回格式不一致

---

## 2. Skill 参数定义

### 2.1 输入参数

Skill 接受以下高层参数，内部映射到 CLI 参数：

#### 2.1.1 必填参数

| Skill 参数 | 类型 | CLI 映射 | 说明 |
|------------|------|----------|------|
| `input` | string | `<video_path>` 或 `<input_dir>` | 单文件路径或目录路径 |

#### 2.1.2 可选参数

| Skill 参数 | 类型 | 默认值 | CLI 映射 | 说明 |
|------------|------|--------|----------|------|
| `output_dir` | string | `./bilinote_output` | `--output-dir` | 输出目录 |
| `api_base` | string | `http://10.112.28.172:8483/api` | `--api-base` | API 基地址 |
| `style` | string | `minimal` | `--style` | 笔记风格 |
| `model` | string | (自动获取) | `--model` | LLM 模型名称 |
| `provider_id` | string | (自动获取) | `--provider-id` | LLM 提供商 ID |
| `quality` | string | `medium` | `--quality` | 下载质量 |
| `format` | string[] | `[]` | `--format` | 格式选项 |
| `extras` | string | null | `--extras` | 附加备注 |
| `video_understanding` | boolean | false | `--video-understanding` | 视频理解开关 |
| `video_interval` | int | 0 | `--video-interval` | 视频采样间隔 |
| `grid_size` | int[] | [] | `--grid-size` | 拼图尺寸 |

#### 2.1.3 批量特有参数

仅当 `input` 为目录时生效：

| Skill 参数 | 类型 | 默认值 | CLI 映射 | 说明 |
|------------|------|--------|----------|------|
| `recursive` | boolean | false | `--recursive` | 递归扫描子目录 |
| `pattern` | string | `*.mp4` | `--pattern` | 文件匹配模式 |
| `skip_existing` | boolean | true | `--skip-existing` | 跳过已完成任务 |
| `concurrency` | int | 1 | `--concurrency` | 最大并发任务数 |
| `retries` | int | 3 | `--retries` | 单任务重试次数 |
| `batch_timeout` | int | 0 | `--batch-timeout` | 批次超时（秒），0 表示无限制 |

#### 2.1.4 调试参数

| Skill 参数 | 类型 | 默认值 | CLI 映射 | 说明 |
|------------|------|--------|----------|------|
| `verbose` | boolean | false | `--verbose` | 详细日志 |
| `dry_run` | boolean | false | `--dry-run` | 模拟执行 |
| `save_transcript` | boolean | false | `--save-transcript` | 保存转写文本 |
| `save_json` | boolean | false | `--save-json` | 保存完整 JSON |

### 2.2 参数验证规则

| 场景 | 验证规则 | 错误处理 |
|------|----------|----------|
| `input` 为文件 | 检查文件存在且可读 | 返回错误，不执行 |
| `input` 为目录 | 检查目录存在且可读 | 返回错误，不执行 |
| `api_base` 格式 | 检查 URL 格式有效 | 使用默认值并警告 |
| `style` 无效 | 检查是否在枚举列表 | 返回错误，不执行 |
| `concurrency` 过大 | 限制最大值为 4 | 使用最大值并警告 |

---

## 3. Skill 返回结构定义

### 3.1 返回结构

Skill 返回统一的 `SkillResult` 结构：

```python
@dataclass
class SkillResult:
    """Skill 执行结果"""

    # ========== 执行状态 ==========

    # 是否成功完成（无致命错误）
    success: bool

    # 错误信息（失败时）
    error: Optional[str] = None

    # ========== 输入信息 ==========

    # 输入路径（文件或目录）
    input_path: str

    # 输入类型："single" 或 "batch"
    input_type: str

    # ========== 输出信息 ==========

    # 输出目录
    output_dir: str

    # ========== 统计信息 ==========

    # 总文件数（单文件为 1）
    total_files: int = 0

    # 成功数
    success_count: int = 0

    # 失败数
    failed_count: int = 0

    # 跳过数
    skipped_count: int = 0

    # ========== 文件路径 ==========

    # Summary 文件路径（JSON）
    summary_path: Optional[str] = None

    # Summary 文件路径（Markdown）
    summary_md_path: Optional[str] = None

    # ========== 失败清单 ==========

    # 失败任务列表：[{input_file, error_message, retry_count}]
    failed_tasks: List[Dict] = field(default_factory=list)

    # ========== 单文件特有 ==========

    # 单文件 Markdown 输出路径
    markdown_path: Optional[str] = None

    # 单文件元数据路径
    meta_path: Optional[str] = None

    # ========== 执行统计 ==========

    # 总耗时（秒）
    duration_seconds: Optional[float] = None

    # CLI 退出码
    exit_code: int = 0

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "success": self.success,
            "error": self.error,
            "input_path": self.input_path,
            "input_type": self.input_type,
            "output_dir": self.output_dir,
            "statistics": {
                "total_files": self.total_files,
                "success": self.success_count,
                "failed": self.failed_count,
                "skipped": self.skipped_count,
            },
            "paths": {
                "summary": self.summary_path,
                "summary_md": self.summary_md_path,
                "markdown": self.markdown_path,
                "meta": self.meta_path,
            },
            "failed_tasks": self.failed_tasks,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
        }
```

### 3.2 单文件返回示例

```json
{
  "success": true,
  "error": null,
  "input_path": "/data/videos/lecture_01.mp4",
  "input_type": "single",
  "output_dir": "/data/notes",
  "statistics": {
    "total_files": 1,
    "success": 1,
    "failed": 0,
    "skipped": 0
  },
  "paths": {
    "summary": null,
    "summary_md": null,
    "markdown": "/data/notes/lecture_01.md",
    "meta": "/data/notes/lecture_01.meta.json"
  },
  "failed_tasks": [],
  "duration_seconds": 52.3,
  "exit_code": 0
}
```

### 3.3 批量返回示例

```json
{
  "success": true,
  "error": null,
  "input_path": "/data/videos",
  "input_type": "batch",
  "output_dir": "/data/notes",
  "statistics": {
    "total_files": 10,
    "success": 8,
    "failed": 1,
    "skipped": 1
  },
  "paths": {
    "summary": "/data/notes/batch_summary.json",
    "summary_md": "/data/notes/batch_summary.md",
    "markdown": null,
    "meta": null
  },
  "failed_tasks": [
    {
      "input_file": "/data/videos/video_05.mp4",
      "error_message": "Upload timeout after 3 retries",
      "retry_count": 3
    }
  ],
  "duration_seconds": 520.5,
  "exit_code": 0
}
```

### 3.4 错误返回示例

```json
{
  "success": false,
  "error": "Service unavailable: http://10.112.28.172:8483/api",
  "input_path": "/data/videos",
  "input_type": "batch",
  "output_dir": "/data/notes",
  "statistics": {
    "total_files": 10,
    "success": 0,
    "failed": 0,
    "skipped": 0
  },
  "paths": {
    "summary": null,
    "summary_md": null,
    "markdown": null,
    "meta": null
  },
  "failed_tasks": [],
  "duration_seconds": 2.1,
  "exit_code": 7
}
```

---

## 4. Skill 与 CLI 的关系

### 4.1 调用关系

Skill 是 CLI 的高层封装，内部通过以下方式调用 CLI：

```
Skill.transcribe(input, options)
    |
    +-- 判断 input 类型（文件/目录）
    |
    +-- 构建 CLI 命令
    |       |
    |       +-- 单文件: bilinote-cli transcribe <video_path> [options]
    |       +-- 批量:   bilinote-cli batch <input_dir> [options]
    |
    +-- 执行 CLI 命令
    |
    +-- 解析 CLI 输出
    |
    +-- 解析生成的文件
    |       |
    |       +-- .meta.json（单文件/每个任务）
    |       +-- batch_summary.json（批量）
    |       +-- batch_summary.md（批量）
    |
    +-- 组装 SkillResult 并返回
```

### 4.2 参数映射实现

```python
# 伪代码：Skill 参数到 CLI 参数的映射
def build_cli_command(input: str, options: dict) -> list[str]:
    """构建 CLI 命令参数列表"""

    cmd = ["bilinote-cli"]

    # 判断模式
    if is_file(input):
        cmd.extend(["transcribe", input])
    else:
        cmd.extend(["batch", input])

    # 通用参数映射
    param_mapping = {
        "output_dir": "--output-dir",
        "api_base": "--api-base",
        "style": "--style",
        "model": "--model",
        "provider_id": "--provider-id",
        "quality": "--quality",
        "extras": "--extras",
    }

    for skill_key, cli_flag in param_mapping.items():
        if options.get(skill_key):
            cmd.extend([cli_flag, str(options[skill_key])])

    # 数组参数
    if options.get("format"):
        cmd.extend(["--format", ",".join(options["format"])])

    if options.get("grid_size"):
        cmd.extend(["--grid-size", ",".join(map(str, options["grid_size"]))])

    # 布尔标志
    if options.get("video_understanding"):
        cmd.append("--video-understanding")

    if options.get("recursive"):
        cmd.append("--recursive")

    if options.get("verbose"):
        cmd.append("--verbose")

    if options.get("dry_run"):
        cmd.append("--dry-run")

    if options.get("save_transcript"):
        cmd.append("--save-transcript")

    if options.get("save_json"):
        cmd.append("--save-json")

    # 数值参数
    if options.get("video_interval"):
        cmd.extend(["--video-interval", str(options["video_interval"])])

    if options.get("concurrency"):
        cmd.extend(["--concurrency", str(options["concurrency"])])

    if options.get("retries"):
        cmd.extend(["--retries", str(options["retries"])])

    if options.get("batch_timeout"):
        cmd.extend(["--batch-timeout", str(options["batch_timeout"])])

    if options.get("pattern"):
        cmd.extend(["--pattern", options["pattern"]])

    # skip_existing 默认为 True，只有显式设为 False 时才添加 --no-skip-existing
    if options.get("skip_existing") == False:
        cmd.append("--no-skip-existing")

    return cmd
```

### 4.3 结果解析实现

```python
# 伪代码：从 CLI 输出和文件解析 SkillResult
def parse_cli_result(input: str, output_dir: str, exit_code: int, stdout: str) -> SkillResult:
    """解析 CLI 执行结果"""

    input_type = "single" if is_file(input) else "batch"

    result = SkillResult(
        success=(exit_code == 0),
        input_path=input,
        input_type=input_type,
        output_dir=output_dir,
        exit_code=exit_code,
    )

    if input_type == "single":
        # 单文件：解析 .meta.json
        basename = Path(input).stem
        meta_path = Path(output_dir) / f"{basename}.meta.json"

        if meta_path.exists():
            meta = read_json(meta_path)
            result.meta_path = str(meta_path)
            result.total_files = 1

            if meta.get("status") == "SUCCESS":
                result.success_count = 1
                result.markdown_path = str(Path(output_dir) / f"{basename}.md")
            else:
                result.failed_count = 1
                result.failed_tasks = [{
                    "input_file": input,
                    "error_message": meta.get("error_message"),
                    "retry_count": meta.get("retry_count", 0),
                }]

            result.duration_seconds = meta.get("duration_seconds")
    else:
        # 批量：解析 batch_summary.json
        summary_path = Path(output_dir) / "batch_summary.json"

        if summary_path.exists():
            summary = read_json(summary_path)
            result.summary_path = str(summary_path)

            stats = summary.get("statistics", {})
            result.total_files = stats.get("total", 0)
            result.success_count = stats.get("success", 0)
            result.failed_count = stats.get("failed", 0)
            result.skipped_count = stats.get("skipped", 0)

            # 失败任务清单
            result.failed_tasks = [
                {
                    "input_file": task.get("input_file"),
                    "error_message": task.get("error_message"),
                    "retry_count": task.get("retry_count", 0),
                }
                for task in summary.get("tasks", [])
                if task.get("status") == "FAILED"
            ]

            result.duration_seconds = summary.get("duration_seconds")

            # Markdown 报告
            summary_md_path = Path(output_dir) / "batch_summary.md"
            if summary_md_path.exists():
                result.summary_md_path = str(summary_md_path)

    # 错误信息
    if exit_code != 0:
        result.error = extract_error_from_stdout(stdout)

    return result
```

---

## 5. 默认服务地址

### 5.1 默认配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `api_base` | `http://10.112.28.172:8483/api` | 172 服务器后端地址 |
| `poll_interval` | 3 | 轮询间隔（秒） |
| `timeout` | 1800 | 单任务超时（秒） |

### 5.2 地址覆盖

**必须保留覆盖能力**：

```python
# 通过参数覆盖
result = skill.transcribe(
    input="/data/videos",
    api_base="http://custom-server:8483/api",  # 覆盖默认地址
)

# 通过环境变量覆盖
# BILINOTE_API_BASE=http://custom-server:8483/api
result = skill.transcribe(input="/data/videos")
```

### 5.3 地址验证

执行前验证服务可用性：

```python
# 伪代码：服务可用性检查
def check_service_available(api_base: str) -> tuple[bool, str]:
    """检查服务是否可用"""
    try:
        response = http_get(f"{api_base}/deploy_status", timeout=5)
        if response.status_code == 200:
            return True, "Service available"
        else:
            return False, f"Service returned status {response.status_code}"
    except ConnectionError:
        return False, f"Cannot connect to {api_base}"
    except Timeout:
        return False, f"Connection timeout to {api_base}"
```

---

## 6. 错误处理

### 6.1 错误类型

| 错误类型 | 退出码 | 处理方式 |
|----------|--------|----------|
| 参数错误 | 1 | 返回错误，不执行 |
| 服务不可用 | 7 | 返回错误，建议检查服务 |
| 任务执行失败 | 4 | 记录失败任务，继续执行 |
| 任务超时 | 5 | 记录超时任务，继续执行 |
| 网络错误 | 6 | 返回错误，建议检查网络 |
| 用户中断 | 10 | 保留已落地结果，返回部分结果 |
| 批次超时 | 11 | 保留已落地结果，返回部分结果 |

### 6.2 错误信息提取

从 CLI 输出提取错误信息：

```python
# 伪代码：错误信息提取
def extract_error_from_stdout(stdout: str) -> str:
    """从 CLI 输出提取错误信息"""
    # 查找 Error: 开头的行
    for line in stdout.split("\n"):
        if line.startswith("Error:"):
            return line[6:].strip()

    # 查找 Reason: 开头的行
    for line in stdout.split("\n"):
        if "Reason:" in line:
            return line.split("Reason:")[1].strip()

    # 返回最后一行非空内容
    lines = [l for l in stdout.split("\n") if l.strip()]
    return lines[-1] if lines else "Unknown error"
```

---

## 7. 验收标准

### 7.1 边界验收

| 序号 | 验收项 | 验证方式 |
|------|--------|----------|
| 1 | Skill 不直接调用 API | 代码审查：无直接的 HTTP 请求到后端 |
| 2 | Skill 不重写 upload/generate/poll | 代码审查：这些逻辑在 CLI 中 |
| 3 | Skill 与 CLI 参数一致 | 对比文档：参数名称和语义相同 |
| 4 | Skill 与 CLI 返回格式一致 | 对比文档：元数据格式相同 |

### 7.2 参数验收

| 序号 | 验收项 | 验证方式 |
|------|--------|----------|
| 1 | 默认服务地址正确 | 调用时不传 api_base，验证使用默认值 |
| 2 | 服务地址可覆盖 | 传入自定义 api_base，验证生效 |
| 3 | 参数验证正确 | 传入无效参数，返回错误而非执行 |

### 7.3 返回结构验收

| 序号 | 验收项 | 验证方式 |
|------|--------|----------|
| 1 | 单文件成功返回正确结构 | 执行单文件任务，检查返回结构 |
| 2 | 单文件失败返回正确结构 | 使用损坏文件，检查失败结构 |
| 3 | 批量成功返回正确结构 | 执行批量任务，检查返回结构 |
| 4 | 批量部分失败返回正确结构 | 混合文件，检查失败清单 |
| 5 | 服务不可用返回错误 | 停止服务，检查错误返回 |

### 7.4 协议一致性验收

| 序号 | 验收项 | 验证方式 |
|------|--------|----------|
| 1 | 终端工具与 skill 不出现两套协议 | 对比 CLI 文档与 Skill 文档，确认一致 |
| 2 | 不形成双维护 | 修改 CLI 参数时，skill 无需独立修改 |

---

## 8. 文件命名约定

### 8.1 Skill 文件位置

```
/home/holmes/.cc-switch/skills/bilinote-transcribe/
├── SKILL.md              # Skill 定义（本文档的精简版）
├── references/
│   ├── cli-contract.md   # CLI 契约引用
│   └── batch-model.md    # 批量模型引用
└── scripts/
    └── bilinote-cli      # CLI 入口（可选）
```

### 8.2 文档关系

```
docs/
├── cli-contract.md       # CLI 契约（Source of Truth）
├── batch-model.md        # 批量任务模型
├── deployment-172.md     # 部署配置
└── skill-spec.md         # Skill 规范（本文档）
```

---

## 9. 后续扩展

| 扩展项 | 说明 |
|--------|------|
| 进度回调 | Skill 支持进度回调函数 |
| 事件钩子 | 任务开始/完成/失败时触发回调 |
| 结果校验 | 校验输出文件完整性 |
| 异步支持 | 支持异步调用 |

---

## 10. 用户使用指南

本节面向终端用户，定义 skill 的使用方式、高级选项和失败反馈机制。

### 10.1 最小调用方式

**核心原则**：指定输入目录即可运行，所有其他参数均有合理默认值。

#### 10.1.1 单文件转录

```bash
bilinote-cli transcribe /path/to/video.mp4
```

**执行结果**：
- 自动上传到 172 服务器
- 自动选择首个可用 LLM 模型
- 自动生成 Markdown 笔记
- 输出到 `./bilinote_output/video.md`

**默认配置**：
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 服务地址 | `http://10.112.28.172:8483/api` | 172 服务器后端 |
| 输出目录 | `./bilinote_output` | 当前目录下 |
| 笔记风格 | `minimal` | 精简风格 |
| 模型 | 自动获取 | 首个可用模型 |
| 超时 | 1800s | 30 分钟 |

#### 10.1.2 批量转录

```bash
bilinote-cli batch /path/to/videos
```

**执行结果**：
- 扫描目录下所有 `.mp4` 文件
- 逐个转录生成笔记
- 跳过已完成的文件（断点续传）
- 生成批量报告

**默认配置**：
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 文件模式 | `*.mp4` | 仅匹配 MP4 |
| 递归扫描 | `false` | 不递归子目录 |
| 跳过已完成 | `true` | 自动断点续传 |
| 并发数 | `1` | 串行执行 |
| 重试次数 | `3` | 失败最多重试 3 次 |

---

### 10.2 高级选项

#### 10.2.1 输出与格式选项

| 选项 | 短参数 | 默认值 | 说明 |
|------|--------|--------|------|
| `--output-dir` | `-o` | `./bilinote_output` | 指定输出目录 |
| `--style` | `-s` | `minimal` | 笔记风格（见下方枚举） |
| `--format` | `-f` | `[]` | 格式选项：`toc,link,screenshot,summary` |
| `--save-transcript` | | `false` | 保存原始转写文本（`.txt`） |
| `--save-json` | | `false` | 保存完整 JSON 结果（`.json`） |

**笔记风格枚举**：

| 风格 | 适用场景 |
|------|----------|
| `minimal` | 精简笔记，仅记录核心内容 |
| `detailed` | 详细笔记，完整记录讨论 |
| `academic` | 学术风格，适合论文/讲座 |
| `tutorial` | 教程风格，强调步骤和关键点 |
| `rf_course` | 射频课程讲演录 |
| `tech_share` | 技术分享讲演录 |
| `meeting_minutes` | 会议纪要 |

**示例**：

```bash
# 射频课程讲座，带目录和链接
bilinote-cli transcribe /data/RF_Lecture_01.mp4 \
  --style rf_course \
  --format toc,link

# 保存转写文本和完整 JSON
bilinote-cli batch /data/videos \
  --save-transcript \
  --save-json
```

#### 10.2.2 批量处理选项

| 选项 | 短参数 | 默认值 | 说明 |
|------|--------|--------|------|
| `--recursive` | `-r` | `false` | 递归扫描子目录 |
| `--pattern` | | `*.mp4` | 文件匹配模式（glob 语法） |
| `--skip-existing` | | `true` | 跳过已完成任务 |
| `--no-skip-existing` | | | 强制重新处理所有文件 |
| `--concurrency` | `-c` | `1` | 最大并发任务数（建议 1-4） |
| `--retries` | | `3` | 单任务失败重试次数 |
| `--batch-timeout` | | `0` | 批次总超时（秒），0 表示无限制 |

**示例**：

```bash
# 递归扫描所有子目录
bilinote-cli batch /data/videos --recursive

# 匹配多种视频格式
bilinote-cli batch /data/videos --pattern "*.mp4,*.avi"

# 并发处理（2 个任务同时进行）
bilinote-cli batch /data/videos --concurrency 2

# 强制重新处理所有文件
bilinote-cli batch /data/videos --no-skip-existing
```

#### 10.2.3 服务连接选项

| 选项 | 短参数 | 默认值 | 说明 |
|------|--------|--------|------|
| `--api-base` | `-a` | `http://10.112.28.172:8483/api` | API 服务地址 |
| `--poll-interval` | `-i` | `3` | 状态轮询间隔（秒） |
| `--timeout` | `-t` | `1800` | 单任务超时（秒） |

**环境变量覆盖**：

```bash
# 通过环境变量配置
export BILINOTE_API_BASE=http://custom-server:8483/api
export BILINOTE_STYLE=rf_course
export BILINOTE_OUTPUT_DIR=/data/notes

bilinote-cli batch /data/videos
```

#### 10.2.4 调试选项

| 选项 | 短参数 | 默认值 | 说明 |
|------|--------|--------|------|
| `--verbose` | `-v` | `false` | 显示详细日志 |
| `--dry-run` | | `false` | 模拟执行，不提交任务 |

**示例**：

```bash
# 查看会执行哪些文件，但不实际执行
bilinote-cli batch /data/videos --dry-run

# 详细日志，用于排查问题
bilinote-cli transcribe /data/video.mp4 --verbose
```

---

### 10.3 失败反馈机制

#### 10.3.1 错误类型与诊断信息

| 错误类型 | 退出码 | 终端输出 | 诊断建议 |
|----------|--------|----------|----------|
| 参数错误 | 1 | `Error: File not found: /path/to/video.mp4` | 检查文件路径是否正确 |
| 服务不可达 | 7 | `Error: Cannot connect to API at http://...` | 检查网络连接或服务状态 |
| 上传失败 | 2 | `Error: Upload failed: <详情>` | 检查文件大小、网络带宽 |
| 任务提交失败 | 3 | `Error: Task submission failed: <详情>` | 检查 LLM 提供商配置 |
| 任务执行失败 | 4 | `Error: Task failed - <服务端返回的错误>` | 查看服务端日志 |
| 任务超时 | 5 | `Error: Task timeout after 1800s. Last Status: TRANSCRIBING` | 增加 `--timeout` 或检查视频长度 |
| 网络错误 | 6 | `Error: Network error: <详情>` | 检查网络连接 |
| 用户中断 | 10 | `[BiliNote] Batch interrupted by user. Partial results saved.` | 可重新运行以断点续传 |
| 批次超时 | 11 | `[BiliNote] Batch timeout. Partial results saved.` | 增加 `--batch-timeout` |

#### 10.3.2 服务可用性检查

执行前自动检查服务可用性：

```
[BiliNote] Checking service availability...
  API: http://10.112.28.172:8483/api
  Status: OK (response time: 23ms)
  Default model: gpt-4o
  Provider: openai-xxx
```

**服务不可用时**：

```
[BiliNote] Service unavailable
  API: http://10.112.28.172:8483/api
  Error: Connection refused

  Diagnostic suggestions:
  1. Check if the server is running: curl http://10.112.28.172:8483/api/deploy_status
  2. Check network connectivity: ping 10.112.28.172
  3. Try an alternative server: --api-base http://backup-server:8483/api
```

#### 10.3.3 批量任务失败详情

批量任务完成后，失败详情记录在 `batch_summary.json` 和 `batch_summary.md` 中：

**终端输出**：

```
[BiliNote] Batch completed
  Total: 10 files
  Success: 8
  Failed: 1
  Skipped: 1
  Duration: 12m 35s

  Failed tasks:
    - video_05.mp4: Upload timeout after 3 retries

  Summary saved to:
    - ./bilinote_output/batch_summary.json
    - ./bilinote_output/batch_summary.md
```

**JSON 摘要（失败任务）**：

```json
{
  "failed_tasks": [
    {
      "input_file": "/data/videos/video_05.mp4",
      "error_message": "Upload timeout after 3 retries",
      "retry_count": 3
    }
  ]
}
```

#### 10.3.4 结果为空检测

当任务成功但结果为空时：

```
[BiliNote] Warning: Empty result detected
  Task ID: uuid-xxx
  Markdown file is empty or contains only whitespace

  Possible causes:
  1. Video has no audio track
  2. Audio is silent or in unsupported language
  3. LLM returned empty response

  Action: Check video file and re-run with --verbose for details
```

---

### 10.4 后续扩展能力

#### 10.4.1 计划中的扩展功能

| 功能 | 说明 | 预计版本 |
|------|------|----------|
| **字幕导出** | 支持导出 SRT/VTT 字幕文件 | V2 |
| **纯转录模式** | 仅转录不生成笔记，节省成本 | V2 |
| **仅上传不转录** | 上传文件获取 URL，供其他工具使用 | V2 |
| **仅拉取结果** | 根据 task_id 拉取已完成的任务结果 | V2 |
| **并发控制增强** | 支持 `--concurrency` 并发处理 | V2 |
| **进度条显示** | 使用 rich 库显示进度条 | V2 |
| **配置文件** | 支持 `~/.bilinote/config.yaml` 持久化配置 | V2 |

#### 10.4.2 扩展使用示例（V2 规划）

**字幕导出**：

```bash
# 导出 SRT 字幕
bilinote-cli transcribe /data/video.mp4 --export-srt

# 导出 VTT 字幕
bilinote-cli transcribe /data/video.mp4 --export-vtt
```

**纯转录模式**：

```bash
# 仅转录，不调用 LLM 生成笔记
bilinote-cli transcribe /data/video.mp4 --transcribe-only

# 输出: video.txt（转写文本）+ video.meta.json
```

**仅上传模式**：

```bash
# 上传文件，获取服务端 URL
bilinote-cli upload /data/video.mp4
# 输出: {"upload_url": "/uploads/video.mp4", "expires_at": "..."}
```

**仅拉取结果**：

```bash
# 根据任务 ID 拉取结果
bilinote-cli fetch --task-id uuid-xxx --output-dir ./output
```

#### 10.4.3 扩展参数预留

为未来扩展预留的参数命名空间：

| 参数 | 类型 | 说明 |
|------|------|------|
| `--export-srt` | flag | 导出 SRT 字幕 |
| `--export-vtt` | flag | 导出 VTT 字幕 |
| `--transcribe-only` | flag | 仅转录不生成笔记 |
| `--upload-only` | flag | 仅上传不处理 |
| `--task-id` | string | 指定任务 ID 拉取结果 |
| `--config` | string | 指定配置文件路径 |

---

### 10.5 使用场景示例

#### 10.5.1 日常使用

```bash
# 快速转录单个视频
bilinote-cli transcribe ~/Downloads/lecture.mp4

# 批量处理课程视频
bilinote-cli batch ~/Videos/RF_Course --style rf_course --format toc

# 断点续传（中断后继续）
bilinote-cli batch ~/Videos/RF_Course  # 自动跳过已完成的
```

#### 10.5.2 生产环境

```bash
# 服务器部署后批量处理
ssh RFRL26@RFRLSERVER5 'cd /data/bilinote && bilinote-cli batch /data/videos --output-dir /data/notes --recursive'

# 使用自定义服务器
bilinote-cli batch /data/videos --api-base http://custom-server:8483/api

# 高并发处理（服务端资源充足时）
bilinote-cli batch /data/videos --concurrency 3
```

#### 10.5.3 脚本集成

```bash
#!/bin/bash
# 批量转录并检查失败任务

bilinote-cli batch /data/videos --output-dir /data/notes

# 检查退出码
if [ $? -eq 0 ]; then
    # 检查是否有失败任务
    failed=$(jq '.statistics.failed' /data/notes/batch_summary.json)
    if [ "$failed" -gt 0 ]; then
        echo "Warning: $failed tasks failed"
        # 发送通知或重试失败任务
    fi
elif [ $? -eq 10 ]; then
    echo "Batch interrupted, re-run to resume"
elif [ $? -eq 7 ]; then
    echo "Service unavailable, check server status"
fi
```

---

### 10.6 常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `Service unavailable` | 172 服务器未启动或网络不通 | 检查服务状态或使用备用服务器 |
| `No enabled provider found` | 未配置 LLM 提供商 | 在 Web UI 配置 API Key 或通过 `--model` 指定 |
| `Task timeout` | 视频过长或服务端处理慢 | 增加 `--timeout` 参数 |
| `Upload failed` | 文件过大或网络不稳定 | 检查网络或使用 `--verbose` 查看详情 |
| 结果为空 | 视频无音轨或音频格式不支持 | 检查视频文件，确保有有效音轨 |
| 批量中断后部分完成 | 用户 Ctrl+C 或进程被终止 | 重新运行相同命令，自动断点续传 |

---

### 10.7 验收标准

用户能将此 skill 当作"批量转录服务入口"理解，而非需要读源码才能使用的开发工具：

| 验收项 | 验证方式 |
|--------|----------|
| 最小调用方式明确 | 用户只需指定输入路径即可运行 |
| 高级选项有文档 | 所有参数均有帮助信息（`--help`） |
| 失败反馈清晰 | 错误信息包含原因和解决建议 |
| 后续扩展透明 | 用户知道未来会有哪些功能 |
| 无需读源码 | 用户仅凭终端输出即可完成所有操作 |

---

**文档结束**
