import os
from app.utils.logger import get_logger
logger = get_logger(__name__)

def cleanup_temp_files(data):
    logger.info(f"starting cleanup temp files ：{data['file_path']}")
    os.remove(data['file_path'])
    # 检查是否删除文件
    if os.path.exists(data['file_path']):
        logger.info(f"cleanup temp files failed ：{data['file_path']}")
    else:
        logger.info(f"cleanup temp files success ：{data['file_path']}")


