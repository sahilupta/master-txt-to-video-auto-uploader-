"""
modules/scheduler.py - Daily batch update scheduler
Reconstructed from scheduler.so analysis
"""
import asyncio
import pytz
from datetime import datetime, timedelta
from logger import LOGGER
from config import Config
from master.database import db_instance
from constant import msg

IST = pytz.timezone('Asia/Kolkata')


async def get_next_run_time(time_str):
    """Calculate the next run time based on a HH:MM string in IST."""
    try:
        now = datetime.now(IST)
        hour, minute = map(int, time_str.split(":"))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time has already passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    except Exception as e:
        LOGGER.error(f"Error calculating next run time: {e}")
        return None


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


async def schedule_batch_update(bot, course_id, api_url, time_str, token, length, course_name, group_id, price=None):
    """Schedule a batch for daily auto-update at a specified time."""
    try:
        while True:
            next_run = await get_next_run_time(time_str)
            if not next_run:
                LOGGER.error(f"Could not calculate next run time for {course_id}")
                break
            
            now = datetime.now(IST)
            sleep_seconds = (next_run - now).total_seconds()
            
            LOGGER.info(f"Scheduled batch {course_id} ({course_name}) - Next run in {sleep_seconds:.0f}s at {next_run}")
            await asyncio.sleep(sleep_seconds)
            
            # Collect and process data
            LOGGER.info(f"Starting daily update for batch {course_id} ({course_name})")
            all_data = await collect_data(course_id, api_url, token)
            
            if all_data:
                pdf_count = sum(1 for x in all_data if x.get("type") == "pdf")
                video_count = sum(1 for x in all_data if x.get("type") == "video")
                
                await process_batch_upload(bot, course_id, all_data)
                
                # Notify completion
                try:
                    await bot.send_message(
                        int(group_id),
                        msg.DAILY_UPDATE_COMPLETED.format(course_id, course_name, pdf_count, video_count)
                    )
                except:
                    pass
            else:
                LOGGER.info(f"No new data for batch {course_id}")
                try:
                    await bot.send_message(
                        int(group_id),
                        msg.NO_NEW_CLASSES.format(course_name)
                    )
                except:
                    pass
            
            # Update schedule time for next day
            time = time_str
    
    except asyncio.CancelledError:
        LOGGER.info(f"Scheduler cancelled for batch {course_id}")
    except Exception as e:
        LOGGER.error(f"Scheduler error for batch {course_id}: {e}")


async def start_daily_schedulers(bot):
    """Start daily update schedulers for all batches with scheduled times."""
    try:
        batches = await db_instance.get_all_batches_with_schedule()
        
        if not batches:
            LOGGER.info("No scheduled batches found")
            return
        
        LOGGER.info(f"Starting {len(batches)} daily schedulers")
        
        for i in batches:
            try:
                course_id = i.get("course_id", "")
                api_url = i.get("api", "")
                time_str = i.get("time", "")
                token = i.get("token", "")
                length = i.get("length", 0)
                course_name = i.get("select", "Unknown")
                group_id = i.get("group_id", "")
                
                if time_str and api_url and token:
                    asyncio.create_task(
                        schedule_batch_update(
                            bot, course_id, api_url, time_str,
                            token, length, course_name, group_id
                        )
                    )
                    LOGGER.info(f"Scheduler started for: {course_name} at {time_str} IST")
            except Exception as e:
                LOGGER.error(f"Error starting scheduler for batch: {e}")
    
    except Exception as e:
        LOGGER.error(f"Error in start_daily_schedulers: {e}")
