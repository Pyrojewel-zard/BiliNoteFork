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
        prompt_builder.BASE_PROMPT = "标题:{video_title}\n正文:{segment_text}\n标签:{tags}"
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