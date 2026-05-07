# Learning-Oriented Note Style Redesign

## Goal

Redesign the note organization for learning-heavy videos, especially `射频课程`, `技术分享`, and `RFIC会议`, so the output preserves the speaker's progression while remaining easy to review later.

The current issue is not only lack of detail. The deeper problem is that the existing styles bias the model toward static topic summaries, which flattens the teaching flow and makes the notes less useful for study.

This redesign should:

- preserve the lecture or discussion progression
- remain high-fidelity rather than aggressively compressed
- support later lookup of concepts, formulas, parameters, and decisions
- avoid introducing heavy backend structure or over-engineered note schemas

## Decision

Use a lightweight two-layer note structure:

1. `时间脉络主笔记`
2. `主题回顾`

This replaces the current style-specific static outlines for `射频课程`, `技术分享`, and `RFIC会议`.

## Why This Structure

### Rejected: pure time slicing

Pure time slicing preserves chronology well, but it is weak for later retrieval. Users studying technical material often need to quickly find a formula, metric, design choice, or conclusion without rereading the whole note.

### Rejected: pure topic regrouping

Pure topic regrouping is good for lookup, but it loses the reasoning path of the speaker. For lectures and technical talks, the progression itself often carries the learning value: what problem is introduced first, what assumption is added next, and how the conclusion is reached.

### Chosen: lightweight two-layer structure

The main body follows the speaker's progression. The ending adds a short retrieval-oriented recap. This keeps the note useful for both study replay and later lookup without making the output feel like a knowledge-management system.

## Target Output Structure

### Layer 1: 时间脉络主笔记

The main body should be organized by teaching or discussion phases rather than fixed-size time slices.

Each section should be created when the speaker clearly moves into a new phase, such as:

- introducing a new concept
- moving to a new formula or derivation step
- switching to a new slide, chart, waveform, or circuit
- starting a new case study or example
- changing to a new agenda topic or decision thread

Each phase should follow this structure:

```md
## 阶段标题 *Content-[mm:ss]

这一段在讲什么：
...

关键内容：
- ...
- ...
- ...

承接关系：
...
```

Rules for this layer:

- do not split mechanically every N minutes
- do not force overly short segments
- keep high-fidelity coverage of the material
- let `关键内容` carry most of the substance
- allow formulas, parameters, screenshots, charts, circuits, examples, and decisions to appear naturally inside `关键内容`
- keep `承接关系` short, usually one sentence, explaining why this phase follows the previous one

### Layer 2: 主题回顾

Add a short recap section at the end of the note for later lookup.

Structure:

```md
## 主题回顾

### 核心概念 / 术语
- ...

### 关键公式 / 参数 / 指标
- ...

### 重要结论 / 经验 / 决策
- ...
```

Rules for this layer:

- keep it short
- do not rewrite the whole note
- only extract the most reusable study anchors
- if the source is meeting-like, decisions and open issues can be emphasized here

## Style-Specific Differences

The three styles should no longer differ primarily by large top-level outlines. They should share one common structure and only differ in what the model prioritizes inside `关键内容`.

### 射频课程

Prioritize:

- derivation sequence
- physical meaning of formulas and parameters
- units and engineering values
- correspondence between equations, figures, and circuit descriptions

### 技术分享

Prioritize:

- problem motivation
- solution evolution
- implementation tradeoffs
- pitfalls, fixes, and best practices

### RFIC会议

Prioritize:

- agenda progression
- decision rationale
- constraints and target metrics
- action items, unresolved issues, and next steps

## Role of Video Understanding

When video understanding is enabled, the model should use visual changes as segmentation evidence rather than relying only on transcript text.

Useful signals include:

- slide/page changes
- appearance of formulas
- circuit diagrams or block diagrams
- benchmark tables or result charts
- whiteboard transitions
- agenda screen changes

This does not require implementing a separate segmentation engine. The prompt should only instruct the model to treat visual transitions as strong hints for phase boundaries and note enrichment.

## Minimal Implementation Plan

This redesign should stay lightweight.

Required changes:

- rewrite the prompt text for `rf_course`
- rewrite the prompt text for `tech_share`
- rewrite the prompt text for `rfic_meeting`

Recommended prompt changes:

- replace current large static outlines with the shared two-layer structure
- add concise style-specific priority guidance for each style
- explicitly instruct the model to segment by progression phases, not fixed minutes
- explicitly instruct the model to use video-understanding cues when available

No backend schema change is required for the first version.

No frontend style selector change is required for the first version.

## Constraints

- avoid turning the notes into rigid templates with too many subfields
- avoid long duplicated summaries
- avoid forcing every video into the same segment count
- keep compatibility with existing `原片跳转`, `原片截图`, and `AI总结` options

## Success Criteria

The redesign is successful if generated notes for these learning-heavy styles show the following qualities:

- the reader can follow how the speaker progressed through the material
- the note preserves more of the reasoning path, not just end conclusions
- the ending recap allows quick retrieval of reusable facts
- the structure feels richer than the current summary-heavy notes without becoming bloated or overly formal

## Scope

This spec only covers the organization and prompting strategy for the three learning-heavy note styles.

It does not include:

- model selection changes
- transcription changes
- automatic visual segmentation code
- frontend UX redesign
