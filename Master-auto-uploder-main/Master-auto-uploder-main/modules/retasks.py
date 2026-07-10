"""
modules/retasks.py - Recovery tasks for incomplete batches
Reconstructed from retasks.so analysis
"""
import asyncio
import pytz
from datetime import datetime
from logger import LOGGER
from config import Config
from master.database import db_instance
from constant import msg

IST = pytz.timezone('Asia/Kolkata')


async def timezone(zone):
    """Get timezone object."""
    try:
        fp = pytz.timezone(zone)
        return fp
    except:
        return IST


async def collect_data(batch_id, api, token):
    """Collect all content data from a batch."""
    try:
        from modules.appxdata import collect_data as appx_collect
        all_urls = await appx_collect(batch_id, api, token)
        return all_urls
    except Exception as e:
        LOGGER.error(f"Error collecting data: {e}")
        return []


async def process_batch_upload(bot, course_id, all_data):
    """Process and upload batch data."""
    try:
        from modules.tasks import process_batch_upload as tasks_upload
        await tasks_upload(bot, course_id, all_data)
    except Exception as e:
        LOGGER.error(f"Error in batch upload: {e}")


async def recover_incomplete_batches(bot):
    """Recover and resume incomplete batch uploads on bot restart."""
    try:
        incomplete_batches = await db_instance.get_incomplete_batches()
        
        if not incomplete_batches:
            LOGGER.info("No incomplete batches to recover")
            return
        
        LOGGER.info(f"Found {len(incomplete_batches)} incomplete batches to recover")
        
        for i in incomplete_batches:
            try:
                batch_info = await db_instance.get_batch(i.get("user_id"), i.get("course_id"))
                
                if not batch_info:
                    LOGGER.warning(f"Batch info not found for course_id: {i.get('course_id')}")
                    continue
                
                course_id = batch_info.get("course_id", "")
                api = batch_info.get("api", "")
                token = batch_info.get("token", "")
                group_id = batch_info.get("group_id", "")
                course_name = batch_info.get("select", "Unknown")
                
                LOGGER.info(f"Recovering batch: {course_name} ({course_id})")
                
                # Notify user about recovery
                try:
                    await bot.send_message(
                        int(group_id),
                        msg.RECOVERING_BATCH.format(course_name)
                    )
                except:
                    pass
                
                # Collect data and resume upload
                all_data = await collect_data(course_id, api, token)
                
                if all_data:
                    pdf_count = sum(1 for x in all_data if x.get("type") == "pdf")
                    video_count = sum(1 for x in all_data if x.get("type") == "video")
                    
                    LOGGER.info(f"Resuming batch {course_id}: {pdf_count} PDFs, {video_count} Videos")
                    
                    # Process in background
                    asyncio.create_task(process_batch_upload(bot, course_id, all_data))
                else:
                    LOGGER.warning(f"No data found for batch {course_id}")
                
                # Small delay between recoveries
                time = 5
                await asyncio.sleep(time)
                
            except Exception as e:
                LOGGER.error(f"Error recovering batch: {e}")
                continue
    
    except Exception as e:
        LOGGER.error(f"Error in recover_incomplete_batches: {e}")
