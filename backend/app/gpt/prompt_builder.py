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


def build_learning_timeline_style(style_title, priority_bullets):
    """构建学习型内容的轻量双层提示模板。

    Args:
        style_title: 风格标题（如 "10. **射频课程笔记**"）
        priority_bullets: 该风格的重点列表

    Returns:
        格式化的提示文本
    """
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
        # RF/射频领域专用风格 - 使用共享轻量双层模板
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
