# 注册监听器
from events.handlers import cleanup_temp_files
from events.signals import transcription_finished


def  register_handler():
    transcription_finished.connect(cleanup_temp_files)

