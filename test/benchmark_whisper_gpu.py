"""
Whisper 模型性能测试脚本 - 远程服务器 GPU 版本

测试 faster-whisper 不同模型在 RTX 5090 上的转录速率和准确性
"""

import os
import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from faster_whisper import WhisperModel


@dataclass
class BenchmarkResult:
    """测试结果"""
    model_name: str
    model_size_gb: float
    load_time_sec: float
    transcribe_time_sec: float
    audio_duration_sec: float
    realtime_factor: float
    language: str
    language_probability: float
    segment_count: int
    full_text: str
    text_length: int
    device: str
    compute_type: str


def get_model_size(model_path: str) -> float:
    """获取模型大小 (GB)"""
    model_file = Path(model_path) / "model.bin"
    if model_file.exists():
        return model_file.stat().st_size / (1024 ** 3)
    return 0.0


def get_audio_duration(audio_path: str) -> float:
    """获取音频时长 (秒)"""
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def extract_audio(video_path: str, audio_path: str, duration: int = None) -> None:
    """从视频中提取音频"""
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", video_path]
    if duration:
        cmd.extend(["-t", str(duration)])
    cmd.extend([
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        audio_path
    ])
    subprocess.run(cmd, capture_output=True, check=True)


def benchmark_model(
    model_name: str,
    model_path: str,
    audio_path: str,
    device: str = "cuda",
    compute_type: str = "float16"
) -> BenchmarkResult:
    """测试单个模型"""

    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"设备: {device}, 计算类型: {compute_type}")
    print(f"{'='*60}")

    # 获取模型大小
    model_size = get_model_size(model_path)
    print(f"模型大小: {model_size:.2f} GB")

    # 加载模型
    print("加载模型中...")
    load_start = time.time()
    model = WhisperModel(
        model_size_or_path=model_path,
        device=device,
        compute_type=compute_type
    )
    load_time = time.time() - load_start
    print(f"模型加载耗时: {load_time:.2f} 秒")

    # 转录
    print("开始转录...")
    transcribe_start = time.time()
    segments, info = model.transcribe(audio_path)

    # 收集结果
    segments_list = list(segments)
    transcribe_time = time.time() - transcribe_start

    full_text = " ".join(seg.text.strip() for seg in segments_list)

    print(f"转录耗时: {transcribe_time:.2f} 秒")
    print(f"检测语言: {info.language} (概率: {info.language_probability:.2%})")
    print(f"片段数: {len(segments_list)}")

    # 获取音频时长
    audio_duration = get_audio_duration(audio_path)
    realtime_factor = transcribe_time / audio_duration
    print(f"音频时长: {audio_duration:.2f} 秒")
    print(f"实时因子: {realtime_factor:.3f}x (越小越快)")

    return BenchmarkResult(
        model_name=model_name,
        model_size_gb=round(model_size, 2),
        load_time_sec=round(load_time, 2),
        transcribe_time_sec=round(transcribe_time, 2),
        audio_duration_sec=round(audio_duration, 2),
        realtime_factor=round(realtime_factor, 3),
        language=info.language,
        language_probability=round(info.language_probability, 4),
        segment_count=len(segments_list),
        full_text=full_text,
        text_length=len(full_text),
        device=device,
        compute_type=compute_type
    )


def main():
    # 配置 - 使用绝对路径
    models_dir = Path("/home/DataTransfer/Pyrojewel/vscode/BiliNoteFork/backend/models/whisper")
    test_data_dir = Path("/home/DataTransfer/Pyrojewel/vscode/BiliNoteFork/testData")
    output_dir = Path("/home/DataTransfer/Pyrojewel/vscode/BiliNoteFork/test")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 测试视频
    video_path = test_data_dir / "Efficient and Accurate RF 3D-IC Model Extraction Solution with EMX Simulator.mp4"
    audio_path = output_dir / "test_audio_120s.wav"

    # 提取音频（如果不存在）
    if not audio_path.exists():
        print(f"从视频提取前 120 秒音频: {video_path}")
        extract_audio(str(video_path), str(audio_path), duration=120)
        print(f"音频已保存: {audio_path}")

    # 要测试的模型
    models_to_test = [
        "whisper-medium",
        "whisper-large-v3-turbo",
        "whisper-large-v3",
    ]

    results = []

    for model_name in models_to_test:
        model_path = models_dir / model_name
        if not model_path.exists():
            print(f"跳过: {model_name} (模型不存在)")
            continue

        try:
            result = benchmark_model(
                model_name=model_name,
                model_path=str(model_path),
                audio_path=str(audio_path),
                device="cuda",
                compute_type="float16"
            )
            results.append(result)
        except Exception as e:
            print(f"测试失败 {model_name}: {e}")
            import traceback
            traceback.print_exc()

    # 保存结果
    results_file = output_dir / "benchmark_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {results_file}")

    # 打印摘要
    print("\n" + "=" * 80)
    print("性能对比摘要")
    print("=" * 80)
    print(f"{'模型':<25} {'大小(GB)':<10} {'加载(s)':<10} {'转录(s)':<10} {'实时因子':<10} {'文本长度':<10}")
    print("-" * 80)
    for r in sorted(results, key=lambda x: x.transcribe_time_sec):
        print(f"{r.model_name:<25} {r.model_size_gb:<10.2f} {r.load_time_sec:<10.2f} {r.transcribe_time_sec:<10.2f} {r.realtime_factor:<10.3f} {r.text_length:<10}")

    # 保存转录文本
    for r in results:
        text_file = output_dir / f"transcript_{r.model_name}.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(r.full_text)
        print(f"转录文本已保存: {text_file}")


if __name__ == "__main__":
    main()
