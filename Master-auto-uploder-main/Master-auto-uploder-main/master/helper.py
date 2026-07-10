"""
master/helper.py - Helper functions for video/file processing
Reconstructed from helper.so analysis
"""
import asyncio
import os
import re
import time
from datetime import datetime, timezone
from PIL import Image
from logger import LOGGER
from config import Config
from master.database import db_instance

UTC = timezone.utc


def convert_timestamp(ts):
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts, tz=UTC)
        elif isinstance(ts, str):
            # Try parsing various formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"]:
                try:
                    dt = datetime.strptime(ts, fmt)
                    break
                except ValueError:
                    continue
            else:
                dt = datetime.now(UTC)
        else:
            dt = datetime.now(UTC)
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    except Exception as e:
        LOGGER.error(f"Timestamp conversion error: {e}")
        return str(ts)


async def download_video(url, name, save_dir, credit=None):
    try:
        video_name = await sanitize_name(name)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        output_path = os.path.join(save_dir, f"{video_name}.mkv")
        cmd = f'yt-dlp -o "{output_path}" "{url}"'
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            LOGGER.info(f"Downloaded: {video_name}")
            return output_path
        else:
            LOGGER.error(f"Download failed: {stderr.decode()}")
            return None
    except Exception as e:
        LOGGER.error(f"Download error: {e}")
        return None


async def duration(video):
    try:
        proc = await asyncio.create_subprocess_shell(
            f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        output, _ = await proc.communicate()
        return int(float(output.decode().strip()))
    except:
        return 0


async def get_youtube_video_id(url):
    try:
        youtube_regex = r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})'
        match = re.search(youtube_regex, url)
        if match:
            vid_id = match.group(1)
            return vid_id
        return None
    except:
        return None


async def sanitize_name(name):
    if not name:
        return "untitled"
    # Remove special characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    name = name[:200]  # Limit length
    return name if name else "untitled"


async def send_vid(bot, url, caption, filename, name, chat_id, forum_id=None, thumbs=None):
    try:
        thumb = None
        if thumbs:
            thumb = await thumbnail_gen(thumbs, filename)
        
        dur = await duration(filename)
        start_time = time.time()
        
        try:
            if forum_id:
                reply = await bot.send_video(
                    chat_id=chat_id,
                    video=filename,
                    caption=caption,
                    duration=dur,
                    thumb=thumb,
                    file_name=f"{name}.mkv",
                    message_thread_id=forum_id,
                    supports_streaming=True
                )
            else:
                reply = await bot.send_video(
                    chat_id=chat_id,
                    video=filename,
                    caption=caption,
                    duration=dur,
                    thumb=thumb,
                    file_name=f"{name}.mkv",
                    supports_streaming=True
                )
            
            # Save message ID to database
            await db_instance.save_msg_id(url, reply.id)
            
            # Copy to log channel
            try:
                copy = await reply.copy(int(Config.LOG_CHANNEL))
            except Exception as e:
                LOGGER.error(f"Failed to copy to log: {e}")
            
            return reply
        except Exception as e:
            LOGGER.error(f"Send video error: {e}")
            raise e
    except Exception as e:
        LOGGER.error(f"send_vid error: {e}")
        return None
    finally:
        # Cleanup
        try:
            if thumb and os.path.exists(thumb):
                os.remove(thumb)
            if filename and os.path.exists(filename):
                os.remove(filename)
        except:
            pass


async def temp_File_name(name):
    name = await sanitize_name(name)
    name = name.replace(" ", "_")
    return os.path.join("downloads", f"{name}_{int(time.time())}")


async def thumbnail_gen(thumb, filename):
    try:
        if thumb and thumb.startswith("http"):
            # Download thumbnail
            cmd = f'wget -O "thumb_{int(time.time())}.jpg" "{thumb}"'
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
            thumb_path = f"thumb_{int(time.time())}.jpg"
            if os.path.exists(thumb_path):
                mark = await watermark_image(thumb_path, "@AutoUploader")
                return mark
        elif thumb and os.path.exists(thumb):
            watermarked_image = await watermark_image(thumb, "@AutoUploader")
            return watermarked_image
        
        # Generate from video
        thumb_path = f"thumb_{int(time.time())}.jpg"
        cmd = f'ffmpeg -i "{filename}" -ss 00:00:01.000 -vframes 1 "{thumb_path}" -y'
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if os.path.exists(thumb_path):
            return thumb_path
        return None
    except Exception as e:
        LOGGER.error(f"Thumbnail gen error: {e}")
        return None


async def watermark_image(image_path, watermark):
    try:
        img = Image.open(image_path)
        _, height = img.size
        font_size = max(int(height * 0.05), 12)
        
        # Use ffmpeg for watermarking
        output_path = f"wm_{os.path.basename(image_path)}"
        cmd = f'ffmpeg -i "{image_path}" -vf "drawtext=text=\'{watermark}\':fontsize={font_size}:fontcolor=white:x=10:y=H-th-10" "{output_path}" -y'
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        
        if os.path.exists(output_path):
            return output_path
        return image_path
    except Exception as e:
        LOGGER.error(f"Watermark error: {e}")
        return image_path
