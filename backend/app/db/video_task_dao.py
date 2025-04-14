from .sqlite_client import get_connection
from app.utils.logger import get_logger
logger = get_logger(__name__)
def init_video_task_table():
    conn = get_connection()
    if conn is None:
        logger.error("Failed to connect to the database.")
        return
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            task_id TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        conn.commit()
        conn.close()
        logger.info("video_tasks table created successfully.")
    except Exception as e:
        logger.error(f"Failed to create video_tasks table: {e}")

def insert_video_task(video_id: str, platform: str, task_id: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO video_tasks (video_id, platform, task_id)
            VALUES (?, ?, ?)
        """, (video_id, platform, task_id))
        conn.commit()
        conn.close()
        logger.info(f"Video task inserted successfully."
                    f"video_id: {video_id}"
                    f"platform: {platform}"
                    f"task_id: {task_id}")
    except Exception as e:
        logger.error(f"Failed to insert video task: {e}")


def get_task_by_video(video_id: str, platform: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_id FROM video_tasks
            WHERE video_id = ? AND platform = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (video_id, platform))
        result = cursor.fetchone()
        conn.close()
        if result is None:
            logger.info(f"No task found for video_id: {video_id} and platform: {platform}")
        logger.info(f"Task found for video_id: {video_id} and platform: {platform}")
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to get task by video: {e}")


def delete_task_by_video(video_id: str, platform: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM video_tasks
            WHERE video_id = ? AND platform = ?
        """, (video_id, platform))

        conn.commit()
        conn.close()
        logger.info(f"Task deleted for video_id: {video_id} and platform: {platform}")
    except Exception as e:
        logger.error(f"Failed to delete task by video: {e}")