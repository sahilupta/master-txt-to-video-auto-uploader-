"""
modules/tasks.py - Task processing module
Reconstructed from tasks.so analysis
"""
import asyncio
import os
from logger import LOGGER
from config import Config
from master.database import db_instance
from master import helper, logdb
from constant import msg
from modules.manager import create_topic


async def process_batch_upload(bot, course_id, all_data):
    """Process and upload all files in a batch."""
    try:
        data = None
        # Find batch by course_id
        cursor = db_instance.batches.find({"course_id": course_id})
        batches = await cursor.to_list(length=1)
        data = batches[0] if batches else {}
        
        if not data:
            LOGGER.error(f"Batch not found for course_id: {course_id}")
            return
        
        course_name = data.get("select", "Unknown")
        save_dir = os.path.join("downloads", str(course_id))
        credit = data.get("credit", "")
        file_credit = data.get("filename", "")
        thumb = data.get("thumb", None)
        chat_id = data.get("group_id", "")
        
        p_count = 0
        v_count = 0
        
        for i, url_data in enumerate(all_data):
            try:
                url = url_data.get("url", "")
                subjectname = url_data.get("subjectName", "General")
                topicname = url_data.get("topicName", "General")
                
                # Check if already uploaded
                if await db_instance.is_file_uploaded(course_id, url):
                    continue
                
                # Get or create forum topic
                check_thread = await db_instance.get_topic(chat_id, subjectname)
                forum_id = check_thread
                if not forum_id:
                    try:
                        forum_id = await create_topic(bot, chat_id, subjectname)
                    except:
                        forum_id = None
                
                name = url_data.get("name", f"file_{i}")
                name = await helper.sanitize_name(name)
                timestamp = url_data.get("timestamp", "")
                
                video_caption = msg.VIDEO_CAPTION_V2.format(
                    name, course_name, topicname,
                    helper.convert_timestamp(timestamp) if timestamp else "N/A",
                    credit or ""
                )
                pdf_caption = msg.PDF_CAPTION_V2.format(
                    name, course_name, topicname,
                    await helper.convert_timestamp(timestamp) if timestamp else "N/A",
                    credit or ""
                )
                
                # Check DB for existing copy
                success = await logdb.check_and_send_from_db(
                    bot, url, chat_id, video_caption, pdf_caption, p_count, v_count, forum_id
                )
                
                if success:
                    await db_instance.mark_file_uploaded(course_id, url, chat_id)
                    if url_data.get("type") == "pdf":
                        p_count += 1
                    else:
                        v_count += 1
                    continue
                
                if url_data.get("type") == "video":
                    yt_video_id = await helper.get_youtube_video_id(url)
                    if yt_video_id:
                        from constant.buttom import yt_keyboard
                        kb = yt_keyboard(
                            f"https://www.youtube.com/watch?v={yt_video_id}",
                            f"https://www.youtube.com/watch?v={yt_video_id}"
                        )
                        sent_msg = await bot.send_message(
                            int(chat_id),
                            msg.YT_VIDEO_CAPTION + f"\n\n<b>{name}</b>",
                            reply_markup=kb,
                            message_thread_id=forum_id
                        )
                        await db_instance.save_msg_id(url, sent_msg.id)
                        await db_instance.mark_file_uploaded(course_id, url, chat_id)
                        v_count += 1
                        continue
                    
                    filename = await helper.download_video(url, name, save_dir, credit)
                    if filename:
                        sent_msg = await helper.send_vid(
                            bot, url, video_caption, filename, name, int(chat_id), forum_id, thumb
                        )
                        if sent_msg:
                            await db_instance.mark_file_uploaded(course_id, url, chat_id)
                            v_count += 1
                
                elif url_data.get("type") == "pdf":
                    pdf_path = os.path.join(save_dir, f"{name}.pdf")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    try:
                        cmd = f'wget -O "{pdf_path}" "{url}"'
                        proc = await asyncio.create_subprocess_shell(
                            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                        )
                        await proc.communicate()
                        
                        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                            prog = await bot.send_document(
                                int(chat_id),
                                document=pdf_path,
                                caption=pdf_caption,
                                file_name=f"{name}.pdf",
                                message_thread_id=forum_id
                            )
                            await db_instance.save_msg_id(url, prog.id)
                            
                            try:
                                copy = await prog.copy(int(Config.LOG_CHANNEL))
                            except:
                                pass
                            
                            await db_instance.mark_file_uploaded(course_id, url, chat_id)
                            p_count += 1
                    except Exception as e:
                        LOGGER.error(f"PDF upload error: {e}")
                    finally:
                        try:
                            if os.path.exists(pdf_path):
                                os.remove(pdf_path)
                        except:
                            pass
                
                # Update progress
                await db_instance.save_batch_status(
                    data.get("user_id", ""),
                    course_id,
                    f"Processing: {i + 1}/{len(all_data)} | PDFs: {p_count} | Videos: {v_count}"
                )
                
            except Exception as e:
                LOGGER.error(f"Error processing file {i}: {e}")
                continue
        
        # Mark completed
        await db_instance.save_batch_status(
            data.get("user_id", ""), course_id, "completed"
        )
        
        try:
            await bot.send_message(
                int(chat_id),
                msg.LAST_BATCH_COMPLETED.format(course_id, course_name, p_count, v_count)
            )
        except:
            pass
        
        LOGGER.info(f"Batch {course_id} completed: {p_count} PDFs, {v_count} Videos")
        
        # Cleanup
        try:
            import shutil
            if os.path.exists(save_dir):
                shutil.rmtree(save_dir)
        except:
            pass
    
    except Exception as e:
        LOGGER.error(f"Error in process_batch_upload: {e}")
