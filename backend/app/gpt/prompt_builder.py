from app.gpt.prompt import BASE_PROMPT

note_formats = [
    {'label': '目录', 'value': 'toc'},
    {'label': '原片跳转', 'value': 'link'},
    {'label': '原片截图', 'value': 'screenshot'},
    {'label': 'AI总结', 'value': 'summary'}
]

note_styles = [
    {'label': '精简', 'value': 'minimal'},
    {'label': '详细', 'value': 'detailed'},
    {'label': '学术', 'value': 'academic'},
    {"label": '教程',"value": 'tutorial', },
    {'label': '小红书', 'value': 'xiaohongshu'},
    {'label': '生活向', 'value': 'life_journal'},
    {'label': '任务导向', 'value': 'task_oriented'},
    {'label': '商业风格', 'value': 'business'},
    {'label': '会议纪要', 'value': 'meeting_minutes'},
    # RF/射频领域专用风格
    {'label': '射频课程', 'value': 'rf_course'},
    {'label': '技术分享', 'value': 'tech_share'},
    {'label': 'RFIC会议', 'value': 'rfic_meeting'},
]


# 生成 BASE_PROMPT 函数
def generate_base_prompt(title, segment_text, tags, _format=None, style=None, extras=None):
    # 生成 Base Prompt 开头部分
    prompt = BASE_PROMPT.format(
        video_title=title,
        segment_text=segment_text,
        tags=tags
    )

    # 添加用户选择的格式
    if _format:
        prompt += "\n" + "\n".join([get_format_function(f) for f in _format])

    # 根据用户选择的笔记风格添加描述
    if style:
        prompt += "\n" + get_style_format(style)

    # 添加额外内容
    if extras:
        prompt += f"\n{extras}"
    return prompt


# 获取格式函数
def get_format_function(format_type):
    format_map = {
        'toc': get_toc_format,
        'link': get_link_format,
        'screenshot': get_screenshot_format,
        'summary': get_summary_format
    }
    return format_map.get(format_type, lambda: '')()


# 风格描述的处理
def get_style_format(style):
    style_map = {
        'minimal': '1. **精简信息**: 仅记录最重要的内容，简洁明了。',
        'detailed': '2. **详细记录**: 包含完整的内容和每个部分的详细讨论。需要尽可能多的记录视频内容，最好详细的笔记',
        'academic': '3. **学术风格**: 适合学术报告，正式且结构化。',
        'xiaohongshu': '''4. **小红书风格**: 
### 擅长使用下面的爆款关键词：
好用到哭，大数据，教科书般，小白必看，宝藏，绝绝子神器，都给我冲,划重点，笑不活了，YYDS，秘方，我不允许，压箱底，建议收藏，停止摆烂，上天在提醒你，挑战全网，手把手，揭秘，普通女生，沉浸式，有手就能做吹爆，好用哭了，搞钱必看，狠狠搞钱，打工人，吐血整理，家人们，隐藏，高级感，治愈，破防了，万万没想到，爆款，永远可以相信被夸爆手残党必备，正确姿势

### 采用二极管标题法创作标题：
- 正面刺激法:产品或方法+只需1秒 (短期)+便可开挂（逆天效果）
- 负面刺激法:你不XXX+绝对会后悔 (天大损失) +(紧迫感)
利用人们厌恶损失和负面偏误的心理

### 写作技巧
1. 使用惊叹号、省略号等标点符号增强表达力，营造紧迫感和惊喜感。
2. **使用emoji表情符号，来增加文字的活力**
3. 采用具有挑战性和悬念的表述，引发读、“无敌者好奇心，例如“暴涨词汇量”了”、“拒绝焦虑”等
4. 利用正面刺激和负面激，诱发读者的本能需求和动物基本驱动力，如“离离原上谱”、“你不知道的项目其实很赚”等
5. 融入热点话题和实用工具，提高文章的实用性和时效性，如“2023年必知”、“chatGPT狂飙进行时”等
6. 描述具体的成果和效果，强调标题中的关键词，使其更具吸引力，例如“英语底子再差，搞清这些语法你也能拿130+”
7. 使用吸引人的标题：''',

        'life_journal': '5. **生活向**: 记录个人生活感悟，情感化表达。',
        'task_oriented': '6. **任务导向**: 强调任务、目标，适合工作和待办事项。',
        'business': '7. **商业风格**: 适合商业报告、会议纪要，正式且精准。',
        'meeting_minutes': '8. **会议纪要**: 适合商业报告、会议纪要，正式且精准。',
        "tutorial":"9.**教程笔记**:尽可能详细的记录教程,特别是关键点和一些重要的结论步骤",
        # RF/射频领域专用风格
        'rf_course': '''10. **射频课程笔记**: 专为射频/微波/RF课程设计，请按以下结构组织笔记：

### 笔记结构要求：
1. **课程概述**：简要说明本节课程的主题和学习目标
2. **核心概念**：提取关键概念，使用表格对比相似概念（如：S参数 vs Z参数、PA vs LNA等）
3. **公式推导**：保留所有公式，使用LaTeX格式，并标注公式中各参数的物理意义
4. **电路分析**：如有电路图描述，提取拓扑结构、关键元件作用、设计考量
5. **设计要点**：总结实际设计中的经验法则和注意事项
6. **行业术语**：首次出现的专业术语需给出中英文对照和简要解释

### 特别注意：
- 保留所有数值参数和单位（dB、dBm、GHz等）
- 区分理论值与工程经验值
- 标注仿真工具相关内容（ADS、Cadence、HFSS等）
- 提取课程中提到的经典论文或参考资料名称''',

        'tech_share': '''11. **技术分享笔记**: 适合技术分享/技术讲座视频，请按以下结构组织：

### 笔记结构要求：
1. **分享主题**：一句话概括分享的核心内容
2. **背景与动机**：为什么会有这个技术方案/问题
3. **技术方案**：
   - 核心思路（用流程图或步骤列表呈现）
   - 关键技术点（每个点的原理简述）
   - 与现有方案的对比优势
4. **实践案例**：提取具体的应用场景和数据结果
5. **经验总结**：踩过的坑、最佳实践、建议
6. **延伸思考**：未解决的问题、可能的改进方向

### 特别注意：
- 代码片段需标注语言和上下文
- 架构图描述要清晰（模块、接口、数据流）
- 保留性能指标和基准测试数据
- 提取推荐的工具、库、框架名称''',

        'rfic_meeting': '''12. **RFIC会议纪要**: 专为RFIC/射频集成电路相关会议设计，请按以下结构组织：

### 会议纪要结构：
1. **会议信息**
   - 会议主题
   - 关键参会人员（如有提及）
   - 会议日期（如视频中有）

2. **议题与讨论**
   每个议题按以下格式记录：
   - **议题名称**
   - 背景/问题陈述
   - 讨论要点（使用项目符号）
   - 决策/结论
   - 待办事项（含负责人和截止时间，如有）

3. **技术决策记录**
   - 关键技术选型的理由
   - 风险点和应对措施
   - 性能指标要求

4. **下一步计划**
   - 明确的行动项
   - 里程碑节点

### 特别注意：
- 区分"已确定"和"待讨论"的内容
- 保留所有规格参数（频率、增益、噪声系数、功耗等）
- 标注设计约束和工艺节点信息
- 提及的EDA工具和IP名称需保留''',
    }
    return style_map.get(style, '')


# 格式化输出内容
def get_toc_format():
    return '''
    9. **目录**: 自动生成一个基于 `##` 级标题的目录。不需要插入原片跳转
    '''


def get_link_format():
    return '''
    10. **原片跳转**: 为每个主要章节添加时间戳，使用格式 `*Content-[mm:ss]`。 
    重要：**始终**在章节标题前加上 `*Content` 前缀，例如：`AI 的发展史 *Content-[01:23]`。一定是标题在前 插入标记在后
    '''


def get_screenshot_format():
    return '''
11. **原片截图**:你收到的截图一般是一个网格，网格的每张图片就是一个时间点，左上角会包含时间mm:ss的格式，请你结合我发你的图片插入截图提示，请你帮助用户更好的理解视频内容，请你认真的分析每个图片和对应的转写文案，插入最合适的内容来备注用户理解，请一定按照这个格式 返回否则系统无法解析：
- 格式：`*Screenshot-[mm:ss]`

    '''


def get_summary_format():
    return '''
    12. **AI总结**: 在笔记末尾加入简短的AI生成总结,并且二级标题 就是 AI 总结 例如 ## AI 总结。
    '''
