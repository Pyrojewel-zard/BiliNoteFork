# BiliNote 批量任务模型定义

**版本**: 1.0.0
**创建日期**: 2026-05-15
**目标**: 定义终端批量转录的任务数据模型，实现与前端 store 解耦，提供稳定的数据契约。

---

## 1. 设计原则

### 1.1 核心原则

| 原则 | 说明 |
|------|------|
| 一个 MP4 = 一个任务对象 | 每个输入文件对应一个独立的任务实例 |
| 状态可持久化 | 任务状态可序列化为 JSON，支持断点续传 |
| 与前端 store 解耦 | 终端版有独立模型，不依赖 Zustand store 结构 |
| 最小必要字段 | 仅保留批量转录必需的字段，避免冗余 |

### 1.2 模型边界

**包含**:
- 单文件任务生命周期管理
- 批量任务聚合统计
- 错误与重试信息

**不包含**:
- 前端 UI 状态（如 currentTaskId）
- 笔记版本历史（Markdown 版本数组）
- 音频元信息的复杂嵌套结构

---

## 2. 单文件任务模型 (BatchTask)

### 2.1 数据结构定义

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class BatchTaskStatus(str, Enum):
    """批量任务状态枚举"""
    PENDING = "PENDING"           # 待处理
    UPLOADING = "UPLOADING"       # 上传中
    QUEUED = "QUEUED"             # 已提交，排队中
    PROCESSING = "PROCESSING"     # 服务端处理中
    SUCCESS = "SUCCESS"           # 成功完成
    FAILED = "FAILED"             # 执行失败
    SKIPPED = "SKIPPED"           # 跳过（如已存在结果）
    TIMEOUT = "TIMEOUT"           # 超时


@dataclass
class BatchTask:
    """
    单文件批量任务模型

    核心契约：一个 MP4 文件 = 一个 BatchTask 实例
    """

    # ========== 必填字段 ==========

    # 本地输入文件路径（绝对路径）
    input_file: str

    # 本地输出目录（绝对路径）
    output_dir: str

    # ========== 自动生成字段 ==========

    # 任务唯一标识（UUID4 字符串）
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 创建时间（ISO 8601 格式）
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    # ========== 远端状态字段 ==========

    # 上传后服务端返回的 URL（如 /uploads/video.mp4）
    remote_upload_url: Optional[str] = None

    # 服务端任务 ID（与 task_id 可能不同，由服务端生成）
    remote_task_id: Optional[str] = None

    # ========== 执行状态字段 ==========

    # 当前状态
    status: BatchTaskStatus = BatchTaskStatus.PENDING

    # 重试次数
    retry_count: int = 0

    # 最大重试次数
    max_retries: int = 3

    # 错误信息（失败时记录）
    error_message: Optional[str] = None

    # 最后一次状态更新时间
    updated_at: Optional[str] = None

    # ========== 时间统计字段 ==========

    # 上传开始时间
    upload_started_at: Optional[str] = None

    # 上传完成时间
    upload_completed_at: Optional[str] = None

    # 处理开始时间（服务端开始处理）
    processing_started_at: Optional[str] = None

    # 处理完成时间
    completed_at: Optional[str] = None

    # 总耗时（秒）
    duration_seconds: Optional[float] = None

    # ========== 输出文件字段 ==========

    # Markdown 输出路径
    markdown_path: Optional[str] = None

    # 元数据输出路径
    meta_path: Optional[str] = None

    # 转写文本输出路径（可选）
    transcript_path: Optional[str] = None

    # 完整 JSON 输出路径（可选）
    json_path: Optional[str] = None

    # ========== 请求参数字段 ==========

    # 笔记风格
    style: str = "minimal"

    # LLM 模型名称
    model_name: Optional[str] = None

    # 提供商 ID
    provider_id: Optional[str] = None

    # 下载质量
    quality: str = "medium"

    def update_status(self, new_status: BatchTaskStatus) -> None:
        """更新任务状态并记录时间戳"""
        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat() + "Z"

    def mark_upload_started(self) -> None:
        """标记上传开始"""
        self.upload_started_at = datetime.utcnow().isoformat() + "Z"
        self.update_status(BatchTaskStatus.UPLOADING)

    def mark_upload_completed(self, remote_url: str) -> None:
        """标记上传完成"""
        self.remote_upload_url = remote_url
        self.upload_completed_at = datetime.utcnow().isoformat() + "Z"

    def mark_queued(self, remote_task_id: str) -> None:
        """标记任务已入队"""
        self.remote_task_id = remote_task_id
        self.update_status(BatchTaskStatus.QUEUED)

    def mark_processing(self) -> None:
        """标记服务端开始处理"""
        self.processing_started_at = datetime.utcnow().isoformat() + "Z"
        self.update_status(BatchTaskStatus.PROCESSING)

    def mark_success(self, markdown_path: str, meta_path: str) -> None:
        """标记任务成功"""
        self.markdown_path = markdown_path
        self.meta_path = meta_path
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        if self.upload_started_at:
            start = datetime.fromisoformat(self.upload_started_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
            self.duration_seconds = (end - start).total_seconds()
        self.update_status(BatchTaskStatus.SUCCESS)

    def mark_failed(self, error_message: str) -> None:
        """标记任务失败"""
        self.error_message = error_message
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.update_status(BatchTaskStatus.FAILED)

    def mark_timeout(self) -> None:
        """标记任务超时"""
        self.error_message = "Task timeout"
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.update_status(BatchTaskStatus.TIMEOUT)

    def mark_skipped(self, reason: str = "Result already exists") -> None:
        """标记任务跳过"""
        self.error_message = reason
        self.update_status(BatchTaskStatus.SKIPPED)

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries and self.status in [
            BatchTaskStatus.FAILED,
            BatchTaskStatus.TIMEOUT,
        ]

    def increment_retry(self) -> None:
        """增加重试计数"""
        self.retry_count += 1
        self.status = BatchTaskStatus.PENDING
        self.error_message = None
        self.updated_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "task_id": self.task_id,
            "input_file": self.input_file,
            "output_dir": self.output_dir,
            "remote_upload_url": self.remote_upload_url,
            "remote_task_id": self.remote_task_id,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "upload_started_at": self.upload_started_at,
            "upload_completed_at": self.upload_completed_at,
            "processing_started_at": self.processing_started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "markdown_path": self.markdown_path,
            "meta_path": self.meta_path,
            "transcript_path": self.transcript_path,
            "json_path": self.json_path,
            "style": self.style,
            "model_name": self.model_name,
            "provider_id": self.provider_id,
            "quality": self.quality,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatchTask":
        """从字典反序列化"""
        data["status"] = BatchTaskStatus(data.get("status", "PENDING"))
        return cls(**data)
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_file` | string | **是** | 本地 MP4 文件绝对路径 |
| `output_dir` | string | **是** | 输出目录绝对路径 |
| `task_id` | string | 自动 | 任务唯一标识（UUID4） |
| `created_at` | string | 自动 | 创建时间（ISO 8601） |
| `remote_upload_url` | string? | 否 | 服务端上传 URL（如 `/uploads/video.mp4`） |
| `remote_task_id` | string? | 否 | 服务端返回的任务 ID |
| `status` | enum | 自动 | 当前状态，默认 `PENDING` |
| `retry_count` | int | 自动 | 重试次数，默认 0 |
| `max_retries` | int | 自动 | 最大重试次数，默认 3 |
| `error_message` | string? | 否 | 失败时的错误信息 |
| `updated_at` | string? | 否 | 最后更新时间 |
| `duration_seconds` | float? | 否 | 总耗时（秒） |
| `markdown_path` | string? | 否 | Markdown 输出路径 |
| `meta_path` | string? | 否 | 元数据输出路径 |

### 2.3 状态枚举说明

| 状态 | 说明 | 后续状态 |
|------|------|----------|
| `PENDING` | 待处理，等待开始 | `UPLOADING` |
| `UPLOADING` | 正在上传文件 | `QUEUED`, `FAILED` |
| `QUEUED` | 已提交服务端，排队中 | `PROCESSING`, `FAILED` |
| `PROCESSING` | 服务端正在处理 | `SUCCESS`, `FAILED`, `TIMEOUT` |
| `SUCCESS` | 成功完成 | 终态 |
| `FAILED` | 执行失败 | `PENDING`（重试）, 终态 |
| `SKIPPED` | 跳过处理 | 终态 |
| `TIMEOUT` | 执行超时 | `PENDING`（重试）, 终态 |

### 2.4 状态转换图

```
PENDING ──► UPLOADING ──► QUEUED ──► PROCESSING ──► SUCCESS
    │            │           │            │
    │            │           │            ├──► FAILED ──► PENDING (retry)
    │            │           │            │
    │            │           │            └──► TIMEOUT ──► PENDING (retry)
    │            │           │
    │            │           └──► FAILED
    │            │
    │            └──► FAILED
    │
    └──► SKIPPED (结果已存在)
```

---

## 3. 批量任务总状态 (BatchSummary)

### 3.1 数据结构定义

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class BatchSummary:
    """
    批量任务汇总状态

    用于跟踪一批任务的总体进度，支持增量更新
    """

    # ========== 批次标识 ==========

    # 批次唯一标识
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 批次创建时间
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    # ========== 任务统计 ==========

    # 总任务数
    total: int = 0

    # 成功数
    success: int = 0

    # 失败数
    failed: int = 0

    # 跳过数
    skipped: int = 0

    # 进行中数
    in_progress: int = 0

    # 待处理数
    pending: int = 0

    # ========== 时间统计 ==========

    # 批次开始时间
    started_at: Optional[str] = None

    # 批次完成时间
    completed_at: Optional[str] = None

    # 批次总耗时（秒）
    duration_seconds: Optional[float] = None

    # ========== 配置信息 ==========

    # 输入目录
    input_dir: Optional[str] = None

    # 输出目录
    output_dir: Optional[str] = None

    # 是否递归扫描
    recursive: bool = False

    # 文件匹配模式
    file_pattern: str = "*.mp4"

    # 最大并发数
    concurrency: int = 1

    # ========== 任务清单 ==========

    # 任务 ID 列表（按顺序）
    task_ids: List[str] = field(default_factory=list)

    # 失败任务清单：task_id -> error_message
    failed_tasks: Dict[str, str] = field(default_factory=dict)

    # 跳过任务清单：task_id -> reason
    skipped_tasks: Dict[str, str] = field(default_factory=dict)

    def add_task(self, task_id: str) -> None:
        """添加任务到批次"""
        self.task_ids.append(task_id)
        self.total = len(self.task_ids)
        self.pending = self.total

    def update_from_tasks(self, tasks: List[BatchTask]) -> None:
        """根据任务列表更新统计"""
        self.total = len(tasks)
        self.success = sum(1 for t in tasks if t.status == BatchTaskStatus.SUCCESS)
        self.failed = sum(1 for t in tasks if t.status == BatchTaskStatus.FAILED)
        self.skipped = sum(1 for t in tasks if t.status == BatchTaskStatus.SKIPPED)
        self.in_progress = sum(
            1 for t in tasks
            if t.status in [BatchTaskStatus.UPLOADING, BatchTaskStatus.QUEUED, BatchTaskStatus.PROCESSING]
        )
        self.pending = sum(1 for t in tasks if t.status == BatchTaskStatus.PENDING)

        # 更新失败清单
        self.failed_tasks = {
            t.task_id: t.error_message or "Unknown error"
            for t in tasks
            if t.status == BatchTaskStatus.FAILED
        }

        # 更新跳过清单
        self.skipped_tasks = {
            t.task_id: t.error_message or "Skipped"
            for t in tasks
            if t.status == BatchTaskStatus.SKIPPED
        }

    def mark_started(self) -> None:
        """标记批次开始"""
        self.started_at = datetime.utcnow().isoformat() + "Z"

    def mark_completed(self) -> None:
        """标记批次完成"""
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        if self.started_at:
            start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
            self.duration_seconds = (end - start).total_seconds()

    def is_complete(self) -> bool:
        """检查批次是否完成"""
        return (self.success + self.failed + self.skipped) == self.total

    def get_progress_percentage(self) -> float:
        """获取完成百分比"""
        if self.total == 0:
            return 0.0
        return round((self.success + self.failed + self.skipped) / self.total * 100, 1)

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "skipped": self.skipped,
            "in_progress": self.in_progress,
            "pending": self.pending,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "recursive": self.recursive,
            "file_pattern": self.file_pattern,
            "concurrency": self.concurrency,
            "task_ids": self.task_ids,
            "failed_tasks": self.failed_tasks,
            "skipped_tasks": self.skipped_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatchSummary":
        """从字典反序列化"""
        return cls(**data)
```

### 3.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `batch_id` | string | 批次唯一标识 |
| `total` | int | 总任务数 |
| `success` | int | 成功完成的任务数 |
| `failed` | int | 失败的任务数 |
| `skipped` | int | 跳过的任务数 |
| `in_progress` | int | 正在处理的任务数 |
| `pending` | int | 待处理的任务数 |
| `failed_tasks` | dict | 失败任务详情：task_id -> error_message |
| `skipped_tasks` | dict | 跳过任务详情：task_id -> reason |

### 3.3 状态不变量

以下不变量必须始终成立：

```
total = success + failed + skipped + in_progress + pending
```

---

## 4. 持久化格式

### 4.1 单任务元数据文件

路径：`<output_dir>/<basename>.meta.json`

```json
{
  "task_id": "uuid-string",
  "input_file": "/absolute/path/to/video.mp4",
  "output_dir": "/absolute/path/to/output",
  "remote_upload_url": "/uploads/video.mp4",
  "remote_task_id": "server-task-id",
  "status": "SUCCESS",
  "retry_count": 0,
  "max_retries": 3,
  "error_message": null,
  "created_at": "2026-05-15T10:30:00Z",
  "updated_at": "2026-05-15T10:31:00Z",
  "upload_started_at": "2026-05-15T10:30:05Z",
  "upload_completed_at": "2026-05-15T10:30:20Z",
  "processing_started_at": "2026-05-15T10:30:21Z",
  "completed_at": "2026-05-15T10:31:00Z",
  "duration_seconds": 55.0,
  "markdown_path": "/output/video.md",
  "meta_path": "/output/video.meta.json",
  "style": "minimal",
  "model_name": "gpt-4o",
  "provider_id": "xxx-xxx-xxx",
  "quality": "medium"
}
```

### 4.2 批次摘要文件

路径：`<output_dir>/batch_summary.json`

```json
{
  "batch_id": "batch-uuid",
  "created_at": "2026-05-15T10:00:00Z",
  "total": 10,
  "success": 8,
  "failed": 1,
  "skipped": 1,
  "in_progress": 0,
  "pending": 0,
  "started_at": "2026-05-15T10:00:05Z",
  "completed_at": "2026-05-15T10:45:00Z",
  "duration_seconds": 2695.0,
  "input_dir": "/data/videos",
  "output_dir": "/data/notes",
  "recursive": true,
  "file_pattern": "*.mp4",
  "concurrency": 1,
  "task_ids": ["task-uuid-1", "task-uuid-2", "..."],
  "failed_tasks": {
    "task-uuid-failed": "Upload timeout"
  },
  "skipped_tasks": {
    "task-uuid-skipped": "Result already exists"
  }
}
```

### 4.3 批次摘要 Markdown 报告

路径：`<output_dir>/batch_summary.md`

```markdown
# BiliNote 批量转录报告

**批次 ID**: batch-uuid
**执行时间**: 2026-05-15 10:00:05 - 10:45:00 (约 45 分钟)

## 统计摘要

| 指标 | 数量 |
|------|------|
| 总任务数 | 10 |
| 成功 | 8 |
| 失败 | 1 |
| 跳过 | 1 |

## 失败任务

| 文件名 | 错误信息 |
|--------|----------|
| video_05.mp4 | Upload timeout |

## 跳过任务

| 文件名 | 原因 |
|--------|------|
| video_10.mp4 | Result already exists |

## 成功任务

| 文件名 | 输出路径 | 耗时 |
|--------|----------|------|
| video_01.mp4 | /data/notes/video_01.md | 52s |
| video_02.mp4 | /data/notes/video_02.md | 48s |
| ... | ... | ... |
```

---

## 5. 使用示例

### 5.1 创建单任务

```python
# 从本地文件创建任务
task = BatchTask(
    input_file="/data/videos/lecture_01.mp4",
    output_dir="/data/notes",
    style="rf_course",
    model_name="gpt-4o",
)

# 标记上传开始
task.mark_upload_started()

# 上传完成，获得服务端 URL
task.mark_upload_completed("/uploads/lecture_01.mp4")

# 任务入队
task.mark_queued("server-task-uuid")

# 处理中
task.mark_processing()

# 成功完成
task.mark_success(
    markdown_path="/data/notes/lecture_01.md",
    meta_path="/data/notes/lecture_01.meta.json"
)

# 保存元数据
import json
with open(task.meta_path, "w") as f:
    json.dump(task.to_dict(), f, indent=2)
```

### 5.2 创建批量任务

```python
from pathlib import Path

# 扫描目录
input_dir = Path("/data/videos")
video_files = list(input_dir.glob("*.mp4"))

# 创建批次摘要
summary = BatchSummary(
    input_dir=str(input_dir),
    output_dir="/data/notes",
    recursive=False,
)
summary.mark_started()

# 创建任务列表
tasks = []
for video_file in video_files:
    task = BatchTask(
        input_file=str(video_file),
        output_dir="/data/notes",
    )
    tasks.append(task)
    summary.add_task(task.task_id)

# 执行任务（伪代码）
for task in tasks:
    execute_task(task)  # 执行单任务
    summary.update_from_tasks(tasks)

# 标记批次完成
summary.mark_completed()

# 保存摘要
with open("/data/notes/batch_summary.json", "w") as f:
    json.dump(summary.to_dict(), f, indent=2)
```

### 5.3 断点续传

```python
import json
from pathlib import Path

def load_existing_tasks(output_dir: str) -> dict[str, BatchTask]:
    """加载已存在的任务元数据"""
    tasks = {}
    output_path = Path(output_dir)

    for meta_file in output_path.glob("*.meta.json"):
        with open(meta_file) as f:
            data = json.load(f)
            task = BatchTask.from_dict(data)
            tasks[task.input_file] = task

    return tasks

def should_skip_task(input_file: str, existing_tasks: dict) -> bool:
    """判断是否跳过任务"""
    if input_file in existing_tasks:
        task = existing_tasks[input_file]
        return task.status == BatchTaskStatus.SUCCESS
    return False

# 断点续传示例
existing = load_existing_tasks("/data/notes")

for video_file in video_files:
    input_file = str(video_file)

    if should_skip_task(input_file, existing):
        # 跳过已成功的任务
        task = existing[input_file]
        task.mark_skipped("Result already exists")
    else:
        # 创建新任务或重试失败任务
        if input_file in existing:
            task = existing[input_file]
            if task.can_retry():
                task.increment_retry()
        else:
            task = BatchTask(input_file=input_file, output_dir="/data/notes")
```

---

## 6. 与前端 store 的差异

| 特性 | 前端 TaskStore | 终端 BatchTask |
|------|---------------|----------------|
| 状态持久化 | localStorage | JSON 文件 |
| 任务标识 | 前端生成 UUID | 本地生成 UUID |
| 版本历史 | Markdown 版本数组 | 仅最新版本 |
| UI 状态 | currentTaskId | 无 |
| 音频元信息 | 嵌套 AudioMeta | 扁平化字段 |
| 重试逻辑 | 前端重发请求 | 计数器 + 状态转换 |

---

## 7. 验收清单

- [x] 定义 BatchTask 数据结构
- [x] 定义 BatchTaskStatus 状态枚举
- [x] 定义 BatchSummary 汇总结构
- [x] 规定"一个 MP4 = 一个任务对象"原则
- [x] 每个任务记录：输入文件路径、远端上传 URL、远端 task_id、本地输出路径、当前状态、重试次数、错误信息
- [x] 批量总状态：总数、成功、失败、跳过、进行中
- [x] 定义持久化格式（JSON）
- [x] 定义断点续传机制
- [x] 与前端 store 解耦，终端版有独立模型

---

## 8. 批量输入参数定义

### 8.1 CLI 批量命令入口

```bash
bilinote-cli batch <input_dir> [options]
```

或使用 Python 模块形式：

```bash
python -m bilinote_cli batch <input_dir> [options]
```

### 8.2 必填参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `<input_dir>` | string | 扫描目录的绝对路径或相对路径 |

**最小调用示例：**

```bash
bilinote-cli batch /data/videos
```

### 8.3 批量特有参数

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--output-dir` | `-o` | string | `./bilinote_output` | 输出目录，存放所有结果文件 |
| `--recursive` | `-r` | flag | `false` | 是否递归扫描子目录 |
| `--pattern` | | string | `*.mp4` | 文件匹配模式（glob 语法） |
| `--skip-existing` | | flag | `true` | 跳过已完成任务 |
| `--concurrency` | `-c` | int | `1` | 最大并发任务数 |
| `--retries` | | int | `3` | 单任务失败重试次数 |

### 8.4 继承自单文件模式的参数

批量模式自动继承单文件模式的所有参数，应用于批量中的每个任务：

| 参数 | 说明 |
|------|------|
| `--api-base` | 服务地址 |
| `--poll-interval` | 轮询间隔 |
| `--timeout` | 单任务超时时间 |
| `--quality` | 下载质量 |
| `--model` | LLM 模型名称 |
| `--provider-id` | LLM 提供商 ID |
| `--style` | 笔记风格 |
| `--format` | 笔记格式选项 |
| `--save-transcript` | 保存转写文本 |
| `--save-json` | 保存完整 JSON |
| `--verbose` | 详细日志 |

### 8.5 环境变量支持

批量模式支持以下额外环境变量：

| 环境变量 | 对应参数 | 说明 |
|----------|----------|------|
| `BILINOTE_BATCH_RECURSIVE` | `--recursive` | 默认递归扫描 |
| `BILINOTE_BATCH_PATTERN` | `--pattern` | 默认匹配模式 |
| `BILINOTE_BATCH_SKIP_EXISTING` | `--skip-existing` | 默认跳过已完成 |
| `BILINOTE_BATCH_CONCURRENCY` | `--concurrency` | 默认并发数 |
| `BILINOTE_BATCH_RETRIES` | `--retries` | 默认重试次数 |

---

## 9. 文件扫描规则

### 9.1 扫描流程

```
输入目录 → glob 匹配 → 文件校验 → 去重 → 输出文件列表
```

### 9.2 glob 模式匹配

支持标准 glob 语法：

| 模式 | 说明 | 示例匹配 |
|------|------|----------|
| `*.mp4` | 当前目录所有 MP4 | `video.mp4` |
| `**/*.mp4` | 递归所有 MP4（需配合 `--recursive`） | `subdir/video.mp4` |
| `*.mp4,*.avi` | 多模式（逗号分隔） | `video.mp4`, `video.avi` |
| `video_*.mp4` | 前缀匹配 | `video_01.mp4` |

**实现伪代码：**

```python
function scan_video_files(input_dir: str, pattern: str, recursive: bool) -> list[str]:
    input_path = Path(input_dir)

    if recursive:
        # 使用 ** 通配符
        effective_pattern = f"**/{pattern}"
    else:
        effective_pattern = pattern

    # 支持多模式（逗号分隔）
    patterns = [p.strip() for p in pattern.split(",")]
    video_files = set()

    for p in patterns:
        if recursive:
            matched = input_path.rglob(p)
        else:
            matched = input_path.glob(p)
        video_files.update(str(f.absolute()) for f in matched)

    return sorted(video_files)  # 按路径排序，确保顺序稳定
```

### 9.3 文件校验规则

扫描阶段对每个文件执行校验：

| 校验项 | 规则 | 处理 |
|--------|------|------|
| 文件存在 | `os.path.exists(path)` | 排除并记录警告 |
| 是文件非目录 | `os.path.isfile(path)` | 排除并记录警告 |
| 扩展名校验 | 支持的视频格式 | 排除并记录警告 |
| 文件大小 | 大于 0 字节 | 排除并记录警告 |
| 可读权限 | `os.access(path, os.R_OK)` | 排除并记录警告 |

**支持的视频格式：**

```python
SUPPORTED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
```

### 9.4 扫描结果输出

扫描完成后输出摘要：

```
[BiliNote] Scanning directory: /data/videos
  Pattern: *.mp4
  Recursive: false
  Found: 15 files
  Valid: 14 files
  Skipped (invalid): 1 files
```

---

## 10. 已完成判断规则

### 10.1 判断原则

**核心原则**：依据本地输出产物判断，不依赖远端状态。

理由：
1. 远端状态可能因服务重启、缓存清理等不可靠
2. 本地产物是最终交付物，更值得信任
3. 支持离线断点续传场景

### 10.2 判断逻辑

一个任务视为"已完成"，当且仅当：

1. **元数据文件存在**：`<output_dir>/<basename>.meta.json`
2. **状态为成功**：`meta.status === "SUCCESS"`
3. **Markdown 文件存在**：`<output_dir>/<basename>.md`
4. **Markdown 文件非空**：文件大小 > 0 字节

**实现伪代码：**

```python
function is_task_completed(input_file: str, output_dir: str) -> tuple[bool, str]:
    basename = Path(input_file).stem
    meta_path = Path(output_dir) / f"{basename}.meta.json"
    md_path = Path(output_dir) / f"{basename}.md"

    # 检查元数据文件
    if not meta_path.exists():
        return False, "No meta file found"

    try:
        with open(meta_path) as f:
            meta = json.load(f)
    except json.JSONDecodeError:
        return False, "Meta file is corrupted"

    # 检查状态
    if meta.get("status") != "SUCCESS":
        return False, f"Status is {meta.get('status')}, not SUCCESS"

    # 检查 Markdown 文件
    if not md_path.exists():
        return False, "No markdown file found"

    if md_path.stat().st_size == 0:
        return False, "Markdown file is empty"

    return True, "Completed"
```

### 10.3 跳过逻辑

当 `--skip-existing` 启用时：

```python
function filter_pending_tasks(video_files: list[str], output_dir: str) -> list[dict]:
    pending = []
    skipped = []

    for video_file in video_files:
        completed, reason = is_task_completed(video_file, output_dir)

        if completed:
            skipped.append({
                "input_file": video_file,
                "reason": reason,
                "action": "skip"
            })
        else:
            pending.append({
                "input_file": video_file,
                "action": "process"
            })

    return pending, skipped
```

### 10.4 失败任务重试

对于已存在但状态非 SUCCESS 的任务：

| 状态 | 处理 |
|------|------|
| `FAILED` | 检查重试次数，若未达上限则重试 |
| `TIMEOUT` | 检查重试次数，若未达上限则重试 |
| `PENDING`/`UPLOADING`/`QUEUED`/`PROCESSING` | 视为中断，重新处理 |

**重试判断伪代码：**

```python
function should_retry_task(input_file: str, output_dir: str, max_retries: int) -> bool:
    basename = Path(input_file).stem
    meta_path = Path(output_dir) / f"{basename}.meta.json"

    if not meta_path.exists():
        return True  # 无元数据，需处理

    with open(meta_path) as f:
        meta = json.load(f)

    status = meta.get("status")

    if status == "SUCCESS":
        return False  # 已成功，跳过

    if status in ["FAILED", "TIMEOUT"]:
        retry_count = meta.get("retry_count", 0)
        return retry_count < max_retries

    # 其他状态视为中断，需重新处理
    return True
```

---

## 11. 文件名冲突策略

### 11.1 问题场景

当递归扫描或多个输入目录时，可能出现同名文件：

```
/data/videos/
├── lecture_01.mp4
└── subdir/
    └── lecture_01.mp4    # 同名不同目录
```

### 11.2 冲突处理策略

**策略 A（推荐）：路径哈希后缀**

在输出文件名后追加源路径的哈希后缀：

```
lecture_01.md           # 第一个同名文件
lecture_01_a3f2c1.md    # 第二个同名文件（带哈希后缀）
```

哈希计算规则：

```python
function resolve_output_basename(input_file: str, all_inputs: list[str]) -> str:
    stem = Path(input_file).stem

    # 统计同名文件数量
    same_stem_files = [f for f in all_inputs if Path(f).stem == stem]

    if len(same_stem_files) == 1:
        return stem  # 无冲突

    # 有冲突，计算哈希后缀
    # 使用相对路径或绝对路径的短哈希
    hash_suffix = hashlib.md5(input_file.encode()).hexdigest()[:6]

    return f"{stem}_{hash_suffix}"
```

**策略 B（备选）：保留目录结构**

在输出目录中保留输入目录的相对路径结构：

```
output_dir/
├── lecture_01.md              # /data/videos/lecture_01.mp4
└── subdir/
    └── lecture_01.md          # /data/videos/subdir/lecture_01.mp4
```

此策略需配合 `--preserve-structure` 参数使用。

### 11.3 推荐策略

**默认采用策略 A**，理由：

1. 输出目录扁平，便于批量管理
2. 哈希后缀稳定，同一输入文件多次运行生成相同后缀
3. 避免目录结构嵌套过深

### 11.4 冲突检测输出

扫描阶段输出冲突警告：

```
[BiliNote] Warning: Duplicate filename detected
  lecture_01.mp4 appears 2 times
    - /data/videos/lecture_01.mp4 → lecture_01.md
    - /data/videos/subdir/lecture_01.mp4 → lecture_01_a3f2c1.md
```

### 11.5 输出文件命名示例

输入：

```
/data/videos/
├── RF_Lecture_01.mp4
├── RF_Lecture_02.mp4
└── archive/
    └── RF_Lecture_01.mp4    # 同名
```

输出：

```
./bilinote_output/
├── RF_Lecture_01.md
├── RF_Lecture_01.meta.json
├── RF_Lecture_01_7b2d8f.md        # 带哈希后缀
├── RF_Lecture_01_7b2d8f.meta.json
├── RF_Lecture_02.md
├── RF_Lecture_02.meta.json
└── batch_summary.json
```

---

## 12. 批量执行顺序

### 12.1 文件排序

为确保执行顺序稳定可预测：

1. 按文件路径字典序排序
2. 同名文件按完整路径排序

```python
function sort_video_files(video_files: list[str]) -> list[str]:
    return sorted(video_files, key=lambda f: (Path(f).stem, f))
```

### 12.2 并发控制

| 参数值 | 行为 |
|--------|------|
| `--concurrency 1` | 串行执行（默认） |
| `--concurrency N` | 最多 N 个任务同时处理 |

**串行模式（concurrency=1）：**

```
Task 1: UPLOAD → PROCESS → SUCCESS
Task 2: UPLOAD → PROCESS → SUCCESS
Task 3: UPLOAD → PROCESS → SUCCESS
...
```

**并发模式（concurrency=N）：**

```
Task 1: UPLOAD → PROCESS → SUCCESS
Task 2:    UPLOAD → PROCESS → SUCCESS
Task 3:       UPLOAD → PROCESS → SUCCESS
...
（最多 N 个同时处于 PROCESS 状态）
```

### 12.3 进度输出

批量执行过程中实时输出进度：

```
[BiliNote] Batch transcription started
  Total: 14 files
  Output: ./bilinote_output/

[01/14] RF_Lecture_01.mp4 - UPLOADING
[01/14] RF_Lecture_01.mp4 - PROCESSING
[01/14] RF_Lecture_01.mp4 - SUCCESS (52s)
[02/14] RF_Lecture_02.mp4 - UPLOADING
...
[14/14] RF_Lecture_14.mp4 - SUCCESS (48s)

[BiliNote] Batch completed
  Success: 13
  Failed: 1
  Skipped: 0
  Total time: 12m 35s
  Summary: ./bilinote_output/batch_summary.json
```

---

## 13. 验收清单

- [x] 定义批量输入参数（第 8 节）
- [x] 定义文件扫描规则（第 9 节）
- [x] 定义已完成判断规则（第 10 节）
- [x] 定义文件名冲突策略（第 11 节）
- [x] 定义批量执行顺序（第 12 节）
- [x] 批量扫描规则稳定且可预测，不会因目录结构变化而覆盖结果
- [x] 已完成判断基于本地输出产物，不依赖远端状态
- [x] 同名文件冲突有明确处理策略（哈希后缀）

## 13.5 批量执行策略验收清单（第 14 节）

- [x] 定义 V1 顺序执行策略（默认并发=1）
- [x] 定义 V2 有限并发策略（默认并发=2，最大=4）
- [x] 定义失败重试策略（单任务级，不影响批次继续）
- [x] 定义重试触发条件和指数退避
- [x] 定义结果即时落地策略（每个任务完成后立即保存）
- [x] 定义增量批次摘要更新
- [x] 定义断点续传机制
- [x] 定义 JSON Summary 格式（机器可读）
- [x] 定义 Markdown Summary 格式（人类可读）
- [x] 即使批量中途失败，也能知道已完成的文件、失败的文件、未开始的文件

---

## 14. 批量执行策略

本节定义批量任务的执行策略，确保批次执行的可靠性、可恢复性和可观测性。

### 14.1 版本演进策略

#### 14.1.1 V1：顺序执行（默认）

**设计原则**：简单可靠，优先保证正确性。

| 配置项 | V1 默认值 | 说明 |
|--------|----------|------|
| `--concurrency` | 1 | 串行执行，一个任务完成后再启动下一个 |
| 失败处理 | 继续执行 | 单任务失败不影响后续任务 |
| 重试策略 | 单任务级 | 失败任务在批次结束后统一重试 |

**执行流程**：

```
Task 1: PENDING → UPLOADING → PROCESSING → SUCCESS/FAILED
                                                          ↓ (完成后立即落地)
Task 2: PENDING → UPLOADING → PROCESSING → SUCCESS/FAILED
                                                          ↓ (完成后立即落地)
Task 3: PENDING → UPLOADING → PROCESSING → SUCCESS/FAILED
                                                          ↓ (完成后立即落地)
...

最后：生成 batch_summary.json + batch_summary.md
```

**优点**：
- 实现简单，易于调试
- 资源占用可控
- 失败定位清晰
- 不存在并发冲突

**适用场景**：
- 首次部署验证
- 任务数量较少（< 50）
- 服务端资源有限
- 网络带宽受限

#### 14.1.2 V2：有限并发（扩展）

**设计原则**：保守起步，按需调优。

| 配置项 | V2 默认值 | 说明 |
|--------|----------|------|
| `--concurrency` | 2 | 默认并发数，建议范围 1-4 |
| 最大并发 | 4 | 硬上限，避免过载 |
| 失败处理 | 继续执行 | 单任务失败不影响其他并发任务 |
| 重试策略 | 延迟重试 | 失败任务放入重试队列，批次结束后重试 |

**执行流程**：

```
         ┌─ Task 1: SUCCESS ──────────────────────┐
         │                                         │
时间线 ──┼─ Task 2: SUCCESS ──────────────────────┼──→ 完成
         │                                         │
         └─ Task 3: FAILED (重试队列) ────────────┘

重试队列: [Task 3] → 重试 → SUCCESS/最终失败
```

**并发控制实现**：

```python
# 伪代码：并发控制
function execute_batch_concurrent(tasks, concurrency):
    semaphore = Semaphore(concurrency)
    results = []

    async def run_task(task):
        async with semaphore:
            return await execute_single_task(task)

    # 启动所有任务，由信号量控制并发
    results = await asyncio.gather(*[run_task(t) for t in tasks])

    return results
```

**并发数推荐**：

| 服务端配置 | 推荐并发数 | 说明 |
|-----------|-----------|------|
| 单核 / 2GB | 1 | 资源受限，串行为佳 |
| 2核 / 4GB | 1-2 | 轻度并发 |
| 4核 / 8GB | 2-3 | 中等并发 |
| 8核+ / 16GB+ | 3-4 | 可充分利用 |

**注意**：并发数过高可能导致：
- 服务端 OOM（内存溢出）
- API 限流
- 上传带宽饱和
- 任务失败率上升

---

### 14.2 失败重试策略

#### 14.2.1 重试范围

**原则**：重试仅对单文件任务生效，不影响全局批次继续执行。

| 场景 | 重试行为 | 批次行为 |
|------|----------|----------|
| 单任务上传失败 | 计入重试队列 | 继续执行下一个任务 |
| 单任务处理失败 | 计入重试队列 | 继续执行下一个任务 |
| 单任务超时 | 计入重试队列 | 继续执行下一个任务 |
| 批次整体超时 | 停止所有进行中任务 | 生成部分结果摘要 |
| 网络完全中断 | 视为批次级失败 | 保存已落地结果 |

#### 14.2.2 重试配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--retries` | 3 | 单任务最大重试次数 |
| 重试延迟 | 指数退避 | 避免瞬时压力 |

**指数退避策略**：

```python
# 重试延迟计算
retry_delay = min(base_delay * (2 ** retry_count), max_delay)

# 示例：base=5s, max=60s
# 第 1 次重试: 5s
# 第 2 次重试: 10s
# 第 3 次重试: 20s
```

#### 14.2.3 重试触发条件

| 错误类型 | 是否重试 | 原因 |
|----------|----------|------|
| 网络超时 | 是 | 临时性问题 |
| 服务端 5xx | 是 | 服务端临时故障 |
| 上传失败 | 是 | 可能是临时网络问题 |
| 服务端 4xx（除 429） | 否 | 参数错误，重试无意义 |
| 文件损坏 | 否 | 源文件问题，需人工介入 |
| 格式不支持 | 否 | 源文件问题，需人工介入 |
| API 限流 (429) | 是 | 等待后重试 |

#### 14.2.4 重试队列处理

**V1 实现**（批次结束后统一重试）：

```python
# 伪代码：V1 重试队列
function execute_batch_v1(tasks):
    pending_tasks = list(tasks)
    retry_queue = []
    completed_tasks = []

    # 第一轮：顺序执行
    for task in pending_tasks:
        result = execute_single_task(task)
        save_task_result(task, result)  # 立即落地

        if result.status == "FAILED" and task.can_retry():
            retry_queue.append(task)
        else:
            completed_tasks.append(task)

    # 第二轮：重试失败任务
    for task in retry_queue:
        task.increment_retry()
        result = execute_single_task(task)
        save_task_result(task, result)  # 立即落地
        completed_tasks.append(task)

    # 生成批次摘要
    save_batch_summary(completed_tasks)
```

**V2 实现**（延迟重试，支持并发）：

```python
# 伪代码：V2 重试队列
function execute_batch_v2(tasks, concurrency):
    pending_tasks = list(tasks)
    retry_queue = []
    max_retry_rounds = 3

    for retry_round in range(max_retry_rounds):
        if not pending_tasks:
            break

        # 并发执行
        results = execute_concurrent(pending_tasks, concurrency)

        # 分类结果
        retry_queue = []
        for task, result in results:
            save_task_result(task, result)  # 立即落地

            if result.status == "FAILED" and task.can_retry():
                task.increment_retry()
                retry_queue.append(task)

        # 下一轮重试
        pending_tasks = retry_queue

    # 最终仍失败的任务
    for task in retry_queue:
        task.mark_failed("Exceeded max retries")

    # 生成批次摘要
    save_batch_summary(all_tasks)
```

---

### 14.3 结果即时落地策略

#### 14.3.1 核心原则

**每个文件完成后立即落地结果与状态，避免批次中断导致所有结果丢失。**

#### 14.3.2 落地时机

| 任务状态 | 落地内容 | 落地时机 |
|----------|----------|----------|
| `UPLOADING` | `.meta.json`（含 remote_upload_url） | 上传完成后 |
| `QUEUED` | `.meta.json`（含 remote_task_id） | 任务入队后 |
| `PROCESSING` | `.meta.json`（状态更新） | 状态变更时 |
| `SUCCESS` | `.md` + `.meta.json` (+ 可选 `.json/.txt`) | 任务成功后 |
| `FAILED` | `.meta.json`（含 error_message） | 任务失败后 |
| `TIMEOUT` | `.meta.json`（含 last_status） | 任务超时后 |
| `SKIPPED` | `.meta.json`（含 reason） | 判断跳过后 |

#### 14.3.3 落地实现

```python
# 伪代码：即时落地
function save_task_result(task, result):
    meta_path = Path(task.output_dir) / f"{task.basename}.meta.json"

    # 原子写入：先写临时文件，再重命名
    temp_path = meta_path.with_suffix(".tmp")
    write_json(temp_path, task.to_dict())
    rename(temp_path, meta_path)

    # 成功时写入 Markdown
    if result.status == "SUCCESS":
        md_path = Path(task.output_dir) / f"{task.basename}.md"
        write_file(md_path, result.markdown)

        # 可选文件
        if task.save_json:
            write_json(md_path.with_suffix(".json"), result.full_result)
        if task.save_transcript:
            write_file(md_path.with_suffix(".txt"), result.transcript)

    # 更新批次摘要（增量）
    update_batch_summary_incremental(task)
```

#### 14.3.4 增量批次摘要

每次任务完成后，增量更新 `batch_summary.json`：

```python
# 伪代码：增量更新批次摘要
function update_batch_summary_incremental(completed_task):
    summary_path = Path(output_dir) / "batch_summary.json"

    # 读取现有摘要
    if summary_path.exists():
        summary = read_json(summary_path)
    else:
        summary = create_empty_summary()

    # 更新统计
    if completed_task.status == "SUCCESS":
        summary["success"] += 1
    elif completed_task.status == "FAILED":
        summary["failed"] += 1
        summary["failed_tasks"][completed_task.task_id] = completed_task.error_message
    elif completed_task.status == "SKIPPED":
        summary["skipped"] += 1
        summary["skipped_tasks"][completed_task.task_id] = completed_task.error_message

    summary["in_progress"] -= 1
    summary["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # 原子写入
    write_json_atomic(summary_path, summary)
```

#### 14.3.5 中断恢复能力

**场景**：批次执行过程中被中断（Ctrl+C、进程终止、系统重启）。

**恢复策略**：

1. **重新运行相同命令**：
   - 扫描输出目录，加载已存在的 `.meta.json`
   - 根据状态判断：SUCCESS 跳过，FAILED/TIMEOUT 重试，其他状态重新执行
   - 合并现有结果与新任务

2. **断点续传实现**：

```python
# 伪代码：断点续传
function resume_batch(input_dir, output_dir):
    # 加载已有任务
    existing_tasks = load_existing_tasks(output_dir)

    # 扫描输入文件
    video_files = scan_video_files(input_dir)

    pending_tasks = []
    for video_file in video_files:
        if video_file in existing_tasks:
            task = existing_tasks[video_file]

            # 已成功：跳过
            if task.status == "SUCCESS":
                task.mark_skipped("Already completed")
                continue

            # 可重试：加入重试
            if task.can_retry():
                task.increment_retry()
                pending_tasks.append(task)
            else:
                # 超过重试次数：标记失败
                task.mark_failed("Exceeded max retries after resume")
        else:
            # 新任务
            task = BatchTask(input_file=video_file, output_dir=output_dir)
            pending_tasks.append(task)

    return pending_tasks
```

---

### 14.4 Summary 文件格式

#### 14.4.1 设计原则

1. **机器可读**：JSON 格式，支持程序解析和后续处理
2. **人类可读**：Markdown 格式，便于快速浏览和存档
3. **完整信息**：包含所有任务的最终状态和路径
4. **可追溯**：记录批次配置和执行时间

#### 14.4.2 JSON Summary 格式

**文件路径**：`<output_dir>/batch_summary.json`

```json
{
  "version": "1.0.0",
  "batch_id": "uuid-string",
  "created_at": "2026-05-15T10:00:00Z",
  "updated_at": "2026-05-15T10:45:00Z",
  "started_at": "2026-05-15T10:00:05Z",
  "completed_at": "2026-05-15T10:45:00Z",
  "duration_seconds": 2695.0,

  "statistics": {
    "total": 10,
    "success": 8,
    "failed": 1,
    "skipped": 1,
    "retried": 2
  },

  "configuration": {
    "input_dir": "/data/videos",
    "output_dir": "/data/notes",
    "recursive": true,
    "file_pattern": "*.mp4",
    "concurrency": 1,
    "max_retries": 3,
    "style": "minimal",
    "model": "gpt-4o",
    "provider_id": "xxx-xxx-xxx"
  },

  "tasks": [
    {
      "task_id": "uuid-1",
      "input_file": "/data/videos/video_01.mp4",
      "output_basename": "video_01",
      "status": "SUCCESS",
      "retry_count": 0,
      "duration_seconds": 52.3,
      "markdown_path": "/data/notes/video_01.md",
      "meta_path": "/data/notes/video_01.meta.json"
    },
    {
      "task_id": "uuid-2",
      "input_file": "/data/videos/video_02.mp4",
      "output_basename": "video_02",
      "status": "FAILED",
      "retry_count": 3,
      "duration_seconds": 12.5,
      "error_message": "Upload timeout after 3 retries",
      "meta_path": "/data/notes/video_02.meta.json"
    }
  ],

  "failed_tasks": {
    "uuid-2": "Upload timeout after 3 retries"
  },

  "skipped_tasks": {
    "uuid-10": "Result already exists"
  }
}
```

#### 14.4.3 Markdown Summary 格式

**文件路径**：`<output_dir>/batch_summary.md`

```markdown
# BiliNote 批量转录报告

**批次 ID**: `batch-uuid-xxx`
**执行时间**: 2026-05-15 10:00:05 ~ 10:45:00 (约 45 分钟)
**命令**: `bilinote-cli batch /data/videos --recursive --style minimal`

---

## 统计摘要

| 指标 | 数量 | 百分比 |
|------|------|--------|
| 总任务数 | 10 | 100% |
| ✅ 成功 | 8 | 80% |
| ❌ 失败 | 1 | 10% |
| ⏭️ 跳过 | 1 | 10% |
| 🔄 已重试 | 2 | - |

---

## 执行配置

| 配置项 | 值 |
|--------|-----|
| 输入目录 | `/data/videos` |
| 输出目录 | `/data/notes` |
| 递归扫描 | 是 |
| 文件模式 | `*.mp4` |
| 并发数 | 1 |
| 最大重试 | 3 |
| 笔记风格 | minimal |
| LLM 模型 | gpt-4o |

---

## ❌ 失败任务 (1)

| 文件名 | 错误信息 | 重试次数 |
|--------|----------|----------|
| video_02.mp4 | Upload timeout after 3 retries | 3 |

---

## ⏭️ 跳过任务 (1)

| 文件名 | 原因 |
|--------|------|
| video_10.mp4 | Result already exists |

---

## ✅ 成功任务 (8)

| 文件名 | 输出路径 | 耗时 |
|--------|----------|------|
| video_01.mp4 | `/data/notes/video_01.md` | 52s |
| video_03.mp4 | `/data/notes/video_03.md` | 48s |
| video_04.mp4 | `/data/notes/video_04.md` | 55s |
| video_05.mp4 | `/data/notes/video_05.md` | 50s |
| video_06.mp4 | `/data/notes/video_06.md` | 47s |
| video_07.mp4 | `/data/notes/video_07.md` | 51s |
| video_08.mp4 | `/data/notes/video_08.md` | 49s |
| video_09.mp4 | `/data/notes/video_09.md` | 53s |

---

## 执行日志

```
[10:00:05] [BiliNote] Batch transcription started
[10:00:05]   Total: 10 files
[10:00:05]   Output: /data/notes/
[10:00:06] [01/10] video_01.mp4 - UPLOADING
[10:00:15] [01/10] video_01.mp4 - PROCESSING
[10:00:58] [01/10] video_01.mp4 - SUCCESS (52s)
...
[10:45:00] [BiliNote] Batch completed
[10:45:00]   Success: 8
[10:45:00]   Failed: 1
[10:45:00]   Skipped: 1
```

---

*报告生成时间: 2026-05-15 10:45:00*
```

#### 14.4.4 Summary 生成时机

| 时机 | 操作 | 内容 |
|------|------|------|
| 批次开始 | 创建 `batch_summary.json` | 初始化配置和任务列表 |
| 每个任务完成 | 增量更新 JSON | 更新统计和任务状态 |
| 批次完成 | 生成 Markdown | 完整报告 |
| 批次中断 | 保留现有 JSON | 支持断点续传 |

---

### 14.5 验收标准

#### 14.5.1 核心验收点

| 序号 | 验收项 | 验证方式 |
|------|--------|----------|
| 1 | 顺序执行正常 | 执行 3 个任务，验证按顺序逐个完成 |
| 2 | 单任务失败不影响批次 | 手动制造失败，验证后续任务继续执行 |
| 3 | 结果即时落地 | 任务完成后立即检查 `.meta.json` 和 `.md` |
| 4 | 中断恢复 | 执行中途 Ctrl+C，重新运行验证断点续传 |
| 5 | Summary 完整 | 检查 `batch_summary.json` 和 `.md` 包含所有任务 |
| 6 | 失败任务可追溯 | 验证 `failed_tasks` 包含错误信息和重试次数 |

#### 14.5.2 验收测试用例

**用例 1: 正常批量执行**

```bash
bilinote-cli batch /data/test_videos --output-dir /tmp/test_output
```

**预期**:
- 所有任务顺序完成
- 每个任务生成 `.md` 和 `.meta.json`
- 生成 `batch_summary.json` 和 `batch_summary.md`
- `batch_summary.json` 统计正确

**用例 2: 部分失败**

```bash
# 准备：包含一个损坏的视频文件
bilinote-cli batch /data/mixed_videos --output-dir /tmp/test_output
```

**预期**:
- 损坏文件任务失败，记录错误信息
- 其他任务正常完成
- `batch_summary.json` 中 `failed_tasks` 包含失败任务
- 退出码 = 0（批次完成，即使有失败）

**用例 3: 中断恢复**

```bash
# 第一次运行（中途 Ctrl+C）
bilinote-cli batch /data/videos --output-dir /tmp/test_output
# 执行 3/10 时中断

# 第二次运行（断点续传）
bilinote-cli batch /data/videos --output-dir /tmp/test_output
```

**预期**:
- 第二次运行跳过已成功的 3 个任务
- 继续执行剩余 7 个任务
- 最终 `batch_summary.json` 包含全部 10 个任务

**用例 4: 重试生效**

```bash
# 模拟：服务端临时不可用
bilinote-cli batch /data/videos --retries 2
```

**预期**:
- 失败任务重试最多 2 次
- `.meta.json` 记录 `retry_count`
- 重试成功后状态更新为 SUCCESS

---

### 14.6 设计决策记录

| 决策 | 理由 |
|------|------|
| V1 默认并发=1 | 简单可靠，降低出错风险 |
| 重试在批次结束后 | 简化实现，避免复杂状态管理 |
| 即时落地而非批量保存 | 最大化数据保留，支持断点续传 |
| 双格式 Summary | JSON 供程序解析，Markdown 供人工查阅 |
| 批次退出码=0 即使有失败 | 批次"完成"与"全成功"分离，失败信息在 Summary 中 |

---

## 15. 后续扩展

| 扩展项 | 说明 |
|--------|------|
| 并发控制 | 增加 `--concurrency` 参数和并发调度 |
| 进度回调 | 支持 progress callback 报告进度 |
| 事件钩子 | 任务开始/完成/失败时触发钩子 |
| 结果校验 | 校验输出文件完整性 |

---

**文档结束**
