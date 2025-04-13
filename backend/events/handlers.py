import os


def cleanup_temp_files(data):
    print(f"🧹 清理转写文件：{data['file_path']}")
    os.remove(data['file_path'])


