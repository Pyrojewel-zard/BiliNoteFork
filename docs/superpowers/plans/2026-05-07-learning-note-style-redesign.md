# Learning-Oriented Note Style Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the three learning-heavy note styles with a shared lightweight two-layer prompt structure that preserves teaching progression and adds a short retrieval recap.

**Architecture:** Keep the first version prompt-only. Refactor `backend/app/gpt/prompt_builder.py` so `rf_course`, `tech_share`, and `rfic_meeting` share one common learning-note skeleton and inject concise style-specific priorities. Add direct unit coverage for the generated prompt text so future edits do not silently regress the structure.

**Tech Stack:** Python, unittest, existing backend prompt builder

---

## File Structure

- Modify: `backend/app/gpt/prompt_builder.py`
  - Add one helper that returns the shared lightweight two-layer prompt skeleton.
  - Rewrite `rf_course`, `tech_share`, and `rfic_meeting` to call the shared helper with different priority bullets.
- Create: `backend/tests/test_prompt_builder.py`
  - Add direct tests for `get_style_format()` and `generate_base_prompt()` for the three learning-heavy styles.

This plan intentionally avoids frontend changes, schema changes, and transcription changes because the spec keeps scope to prompt organization only.

### Task 1: Add Regression Tests For Learning-Oriented Prompt Structure

**Files:**
- Create: `backend/tests/test_prompt_builder.py`
- Test: `backend/tests/test_prompt_builder.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_prompt_builder.py` with this content:

```python
import importlib.util
import pathlib
import unittest


def _load_prompt_builder_module():
    root = pathlib.Path(__file__).resolve().parents[1]
    module_path = root / "app" / "gpt" / "prompt_builder.py"
    spec = importlib.util.spec_from_file_location("prompt_builder", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("prompt_builder module spec not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prompt_builder = _load_prompt_builder_module()


class TestPromptBuilderLearningStyles(unittest.TestCase):
    def test_rf_course_uses_shared_two_layer_structure(self):
        prompt = prompt_builder.get_style_format("rf_course")
        self.assertIn("时间脉络主笔记", prompt)
        self.assertIn("主题回顾", prompt)
        self.assertIn("按讲解推进分段", prompt)
        self.assertIn("推导顺序", prompt)
        self.assertIn("公式的物理意义", prompt)

    def test_tech_share_uses_shared_two_layer_structure(self):
        prompt = prompt_builder.get_style_format("tech_share")
        self.assertIn("时间脉络主笔记", prompt)
        self.assertIn("主题回顾", prompt)
        self.assertIn("问题动机", prompt)
        self.assertIn("方案演进", prompt)
        self.assertIn("踩坑和修正", prompt)

    def test_rfic_meeting_uses_shared_two_layer_structure(self):
        prompt = prompt_builder.get_style_format("rfic_meeting")
        self.assertIn("时间脉络主笔记", prompt)
        self.assertIn("主题回顾", prompt)
        self.assertIn("决策理由", prompt)
        self.assertIn("行动项", prompt)
        self.assertIn("未决问题", prompt)

    def test_generate_base_prompt_keeps_base_and_appends_style(self):
        prompt_builder.BASE_PROMPT = "标题:{video_title}\\n正文:{segment_text}\\n标签:{tags}"
        prompt = prompt_builder.generate_base_prompt(
            title="RF Lesson",
            segment_text="segment text",
            tags="rf,course",
            style="rf_course",
        )
        self.assertIn("标题:RF Lesson", prompt)
        self.assertIn("正文:segment text", prompt)
        self.assertIn("标签:rf,course", prompt)
        self.assertIn("时间脉络主笔记", prompt)
        self.assertIn("主题回顾", prompt)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest backend/tests/test_prompt_builder.py -q
```

Expected: FAIL because the current style text does not contain the new shared two-layer structure assertions.

- [ ] **Step 3: Commit the failing test**

```bash
git add backend/tests/test_prompt_builder.py
git commit -m "test: cover learning-oriented note style prompts"
```

### Task 2: Refactor Prompt Builder To Use A Shared Lightweight Two-Layer Template

**Files:**
- Modify: `backend/app/gpt/prompt_builder.py`
- Test: `backend/tests/test_prompt_builder.py`

- [ ] **Step 1: Add a shared helper for the three learning-heavy styles**

Inside `backend/app/gpt/prompt_builder.py`, add this helper above `get_style_format()`:

```python
def build_learning_timeline_style(style_title, priority_bullets):
    priorities = "\n".join([f"- {item}" for item in priority_bullets])
    return f'''{style_title}：适合学习型内容，请使用轻量双层结构组织笔记。

### 第一层：时间脉络主笔记
- 按讲解推进分段，不要机械地每几分钟切一段
- 当讲者进入新的概念、公式、电路、案例、议题或明显换页时，再开启新段
- 每段建议使用下面结构：

```md
## 阶段标题 *Content-[mm:ss]

这一段在讲什么：
...

关键内容：
- ...
- ...

承接关系：
...
```

- `关键内容` 是主体，尽量高保真保留公式、参数、图示、电路、案例、结论等真正影响理解的内容
- `承接关系` 用一句话说明这段和上一段如何衔接或推进

### 第二层：主题回顾
在全文末尾补一个简短回顾区，只提炼最值得后查的内容，不要把正文重写一遍：

```md
## 主题回顾

### 核心概念 / 术语
- ...

### 关键公式 / 参数 / 指标
- ...

### 重要结论 / 经验 / 决策
- ...
```

### 该风格的重点
{priorities}

### 特别注意
- 如果提供了截图或视频理解信息，请把画面切换、公式页、电路图、结果图表当作分段和补充细节的重要依据
- 保留关键数值、单位、工具名、方法名，不要只写抽象总结
- 不要把笔记写成只有结论的静态摘要，要保留讲者展开内容的过程
'''
```

- [ ] **Step 2: Replace the three existing style blocks with shared-helper calls**

Update the three entries in `style_map` from long static strings to these calls:

```python
'rf_course': build_learning_timeline_style(
    '10. **射频课程笔记**',
    [
        '优先保留推导顺序',
        '优先解释公式的物理意义和参数单位',
        '优先保留图、式、电路描述之间的对应关系',
        '区分理论结论、工程经验值和设计注意事项',
    ],
),

'tech_share': build_learning_timeline_style(
    '11. **技术分享笔记**',
    [
        '优先保留问题动机和背景',
        '优先保留方案演进和关键取舍',
        '优先保留实现细节、踩坑和修正过程',
        '优先提炼工具、框架、性能数据和最佳实践',
    ],
),

'rfic_meeting': build_learning_timeline_style(
    '12. **RFIC会议纪要**',
    [
        '优先保留议题推进顺序',
        '优先保留决策理由、约束条件和目标指标',
        '优先保留行动项、下一步和未决问题',
        '优先保留频率、增益、噪声系数、功耗、工艺节点等规格信息',
    ],
),
```

- [ ] **Step 3: Run the focused test suite**

Run:

```bash
python -m pytest backend/tests/test_prompt_builder.py -q
```

Expected: `4 passed`

- [ ] **Step 4: Run the existing backend smoke tests that touch prompt-adjacent code**

Run:

```bash
python -m pytest backend/tests/test_universal_gpt_checkpoint.py backend/tests/test_request_chunker.py -q
```

Expected: all tests PASS, confirming the prompt refactor did not break unrelated GPT utility paths.

- [ ] **Step 5: Commit the implementation**

```bash
git add backend/app/gpt/prompt_builder.py backend/tests/test_prompt_builder.py
git commit -m "feat(note): redesign learning-oriented note prompts"
```

### Task 3: Manual Sanity Check The Generated Prompt Text

**Files:**
- Modify: `backend/app/gpt/prompt_builder.py`
- Test: `backend/tests/test_prompt_builder.py`

- [ ] **Step 1: Print one generated prompt for human inspection**

Run:

```bash
python - <<'PY'
import importlib.util
from pathlib import Path

module_path = Path("backend/app/gpt/prompt_builder.py")
spec = importlib.util.spec_from_file_location("prompt_builder", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print(module.generate_base_prompt(
    title="RFIC Session",
    segment_text="讨论LNA增益、NF和功耗之间的取舍。",
    tags="RFIC,LNA",
    _format=["link"],
    style="rfic_meeting",
))
PY
```

Expected:

- the base prompt content still appears first
- the `原片跳转` guidance is still appended
- the learning-heavy style text clearly contains `时间脉络主笔记` and `主题回顾`
- the prompt reads like a lightweight study note instruction, not a rigid report template

- [ ] **Step 2: If the prompt reads too long or repetitive, trim only the shared helper text**

Keep these parts intact:

```text
时间脉络主笔记
主题回顾
按讲解推进分段
视频理解画面信号可用于辅助分段
风格侧重点
```

Allowed trims:

- remove duplicated explanatory wording
- shorten bullet prose while keeping meaning
- shorten style-specific bullets to one clause each

- [ ] **Step 3: Re-run the focused tests after trimming**

Run:

```bash
python -m pytest backend/tests/test_prompt_builder.py -q
```

Expected: still PASS

- [ ] **Step 4: Commit the sanity-trim pass if any text changed**

```bash
git add backend/app/gpt/prompt_builder.py
git commit -m "refactor(note): tighten learning prompt wording"
```

If no text changed after inspection, skip this commit.

## Self-Review

Spec coverage check:

- shared lightweight two-layer structure: covered in Task 2 helper and assertions in Task 1
- style-specific differences for the three learning-heavy modes: covered in Task 2 shared-helper calls
- video-understanding cues as segmentation hints: covered in Task 2 helper text and Task 3 inspection
- no backend or frontend structural changes: preserved by file scope and commands in all tasks

Placeholder scan:

- no `TODO`, `TBD`, or implicit “handle later” language remains
- all changed files, commands, and test expectations are explicit

Type consistency:

- helper name is `build_learning_timeline_style`
- tests refer to `get_style_format()` and `generate_base_prompt()`, which already exist
- planned assertions align with the exact phrases introduced by the helper
