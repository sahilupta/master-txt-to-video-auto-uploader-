"""
master/logdb.py - Log database helper for checking and sending from DB
Reconstructed from logdb.so analysis
"""
import asyncio
from logger import LOGGER
from config import Config
from master.database import db_instance
from pyrogram.errors import FloodWait


async def check_and_send_from_db(bot, url, group_id, video_caption, pdf_caption, pdf_counter, video_counter, forum_id=None):
    """Check if a file is already uploaded in DB and send from there instead of re-uploading."""
    try:
        file_data = await db_instance.get_msg_id(url)
        if file_data:
            msg_id = file_data
            try:
                msg_data = await bot.copy_message(
                    chat_id=group_id,
                    from_chat_id=int(Config.LOG_CHANNEL),
                    message_id=msg_id,
                    message_thread_id=forum_id
                )
                return True
            except FloodWait as e:
                LOGGER.warning(f"FloodWait: Sleeping {e.value}s")
                await asyncio.sleep(e.value)
                return await check_and_send_from_db(bot, url, group_id, video_caption, pdf_caption, pdf_counter, video_counter, forum_id)
            except Exception as e:
                LOGGER.error(f"Error copying message: {e}")
                return False
        return False
    except Exception as e:
        LOGGER.error(f"check_and_send_from_db error: {e}")
        return False
