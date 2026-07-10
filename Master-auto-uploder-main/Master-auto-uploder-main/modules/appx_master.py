"""
modules/appx_master.py - Main batch add and processing logic
Reconstructed from appx_master.so analysis
"""
import asyncio
import re
import jwt
import pytz
from datetime import datetime
from pyrogram.types import InlineKeyboardButton as KB, InlineKeyboardMarkup as KM
from logger import LOGGER
from config import Config
from master.database import db_instance
from master.server import HttpxClient
from constant import msg
from modules import appxdata

IST = pytz.timezone('Asia/Kolkata')

scraper = HttpxClient(verify_ssl=False)

headers = {
    'User-Agent': 'okhttp/4.9.1',
    'Accept-Encoding': 'gzip',
    'client-service': 'Appx',
    'auth-key': 'appxapi',
    'source': 'website',
    'user-id': '',
    'authorization': '',
    'user_app_category': '',
    'language': 'en',
    'device_type': 'ANDROID'
}


async def check_server():
    """Check if the server is reachable."""
    try:
        response = await scraper.get("https://www.google.com")
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        LOGGER.error(f"Server check error: {e}")
        return False


def get_user_id(token):
    """Extract user ID from JWT token."""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("id", decoded.get("user_id", decoded.get("sub", "")))
    except Exception as e:
        LOGGER.error(f"Token decode error: {e}")
        return None


async def password_login(email, password, api):
    """Login using email and password."""
    try:
        payload = {
            "useremail": email,
            "password": password
        }
        hdr = {**headers, "Content-Type": "application/json"}
        
        login = await scraper.post(f"{api}/post/userLogin?extra_details=0", json=payload, headers=hdr)
        login_data = login.json()
        
        if isinstance(login_data, dict):
            token = login_data.get("token", login_data.get("data", {}).get("token", ""))
            if token:
                return {"success": True, "token": token, "message": "Login Successful"}
            else:
                return {"success": False, "message": login_data.get("message", "Login Failed")}
        return {"success": False, "message": "Invalid response"}
    except Exception as e:
        LOGGER.error(f"Login error: {e}")
        return {"success": False, "message": str(e)}


async def otp_login(phNum, api, editable, bot, m):
    """Login using OTP verification."""
    try:
        params = {"phone": phNum}
        r1 = await scraper.get(f"{api}/get/sendotp", params=params, headers=headers)
        
        await editable.edit_text(msg.OTP_SENT)
        
        # Wait for OTP input
        input2 = await bot.listen(m.chat.id, timeout=120)
        otp = input2.text.strip()
        
        r2 = await scraper.post(f"{api}/verifyOtp", json={"phone": phNum, "otp": otp}, headers=headers)
        login_data = r2.json()
        
        if isinstance(login_data, dict):
            token = login_data.get("token", login_data.get("data", {}).get("token", ""))
            if token:
                return {"success": True, "token": token}
            return {"success": False, "message": login_data.get("message", "OTP Verification Failed")}
        return {"success": False, "message": "Invalid response"}
    except Exception as e:
        LOGGER.error(f"OTP login error: {e}")
        return {"success": False, "message": str(e)}


async def timezone(zone):
    """Get file path for a timezone."""
    try:
        fp = pytz.timezone(zone)
        return fp
    except:
        return IST


async def set_chat(bot, GROUP_ID, editable1):
    """Verify bot has access to a group."""
    try:
        chat = await bot.get_chat(int(GROUP_ID))
        bot_member = await bot.get_chat_member(int(GROUP_ID), (await bot.get_me()).id)
        
        if bot_member.privileges:
            return True
        else:
            await editable1.edit_text("<b>❌ Bot needs admin permissions in the group!</b>")
            return False
    except Exception as e:
        await editable1.edit_text(f"<b>❌ Error setting chat: {e}</b>")
        return False


from modules import appxdata, apnaex_extractor

# ... (rest of imports are same)

# ... (check_server, get_user_id, password_login, otp_login, timezone, set_chat functions remain same)

async def collect_data(batch_id, api, token, userid):
    """Collect all content data from a batch using NEW ApnaEx logic."""
    try:
        LOGGER.info(f"Starting extraction for batch {batch_id} using ApnaEx logic...")
        
        # Clean token for ApnaEx logic (it constructs its own headers)
        clean_token = token.replace("Bearer ", "") if token else ""
        
        # 1. Try new ApnaEx extraction logic
        all_urls = await apnaex_extractor.extract_batch_apnaex_logic(batch_id, api, clean_token, userid)
        
        # 2. Fallback to old logic if new logic returns nothing (optional, can be removed if confident)
        if not all_urls:
            LOGGER.warning("ApnaEx logic returned no data. Falling back to legacy appxdata...")
            all_urls = await appxdata.collect_data(batch_id, api, token)
            
        return all_urls
    except Exception as e:
        LOGGER.error(f"Error collecting data: {e}")
        return []


async def add_batch(bot, m, api, app_name):
    """Multi-step batch add flow."""
    try:
        editable = await m.reply_text(msg.LOGIN_OPTIONS) if hasattr(m, 'reply_text') else await m.edit_text(msg.LOGIN_OPTIONS)
        
        # Step 1: Get login credentials
        input1 = await bot.listen(m.chat.id, timeout=300)
        raw_text = input1.text.strip()
        
        # Parse login type
        if "*" in raw_text:
            # Email*Password format
            email, password = raw_text.split("*", 1)
            email = email.strip()
            password = password.strip()
            log_in = await password_login(email, password, api)
        elif raw_text.startswith("+") or raw_text.isdigit():
            # Mobile number for OTP login
            phNum = raw_text.strip()
            log_in = await otp_login(phNum, api, editable, bot, m)
        else:
            # Assume it's a token
            token = raw_text.strip()
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                if decoded:
                    log_in = {"success": True, "token": token}
                else:
                    log_in = {"success": False, "message": "Invalid Token"}
            except:
                await editable.edit_text(msg.INVALID_TOKEN)
                return
        
        if not log_in.get("success"):
            await editable.edit_text(msg.LOGIN_ERROR.format(log_in.get("message", "Login Failed")))
            return
        
        token = log_in["token"]
        userid = get_user_id(token)
        
        await editable.edit_text(msg.LOGIN_SUCCESS.format("Fetching batches..."))
        
        # Step 2: Fetch and display batches
        try:
            # Use requests compatible headers
            import requests
            hdr = {
                'User-Agent': 'okhttp/4.9.1',
                'Accept-Encoding': 'gzip', 
                'client-service': 'Appx',
                'auth-key': 'appxapi',
                'source': 'website',
                'user-id': str(userid) if userid else '',
                'authorization': token.replace("Bearer ", "") if token else '',
                'language': 'en',
                # 'device_type': 'ANDROID' # Removed to match successful debug script
            }
            
            bdetail = None # Initialize bdetail
            
            # Try v2 first
            try:
                res2 = await asyncio.to_thread(requests.get, f"{api}/get/mycoursev2?userid={userid}", headers=hdr, verify=False)
                if res2.status_code == 200:
                    bdetail = res2.json()
                else:
                    bdetail = None
            except Exception as e:
                LOGGER.error(f"Error fetching mycoursev2: {e}")
                bdetail = None

            # Fallback to v1 if v2 fails or has no data
            if not bdetail or (isinstance(bdetail, dict) and not bdetail.get('data')):
                try:
                    res1 = await asyncio.to_thread(requests.get, f"{api}/get/mycourse?userid={userid}", headers=hdr, verify=False)
                    if res1.status_code == 200:
                        bdetail = res1.json()
                except Exception as e:
                    LOGGER.error(f"Error fetching mycourse (v1 fallback): {e}")
                    pass # bdetail remains None or previous value
            
            if isinstance(bdetail, dict):
                bdetail = bdetail.get("data", [])
            elif not isinstance(bdetail, list): # Ensure bdetail is a list if not already
                bdetail = []
        except Exception as e:
            LOGGER.error(f"Error fetching batch details: {e}")
            bdetail = []
        
        if not bdetail:
            await editable.edit_text("<b>❌ No batches found for this account.</b>")
            return
        
        # Display batches
        cc = len(bdetail)
        sent_messages = []
        message_header = f"<b><blockquote>BATCH-ID  -  BATCH NAME  -   PRICE</b></blockquote>\n\n"
        all_batches = ""
        
        for n, i in enumerate(bdetail, 1):
            batch_name = i.get("name", i.get("batchName", "Unknown"))
            batch_id = i.get("_id", i.get("id", i.get("course_id", "")))
            batch_price = i.get("price", i.get("amount", "N/A"))
            all_batches += f"`{n}.` - <b>{batch_name}</b> - {batch_price}₹\n"
        
        # Send in chunks if too long
        for chunk in [all_batches[i:i+3000] for i in range(0, len(all_batches), 3000)]:
            sent_message = await bot.send_message(m.chat.id, message_header + chunk)
            sent_messages.append(sent_message)
            message_header = ""
        
        await editable.edit_text(msg.BATCH_SELECTION)
        
        # Step 3: Get batch selection
        editable1 = editable
        input2 = await bot.listen(m.chat.id, timeout=300)
        selected = input2.text.strip()
        
        try:
            idx = int(selected) - 1
            if 0 <= idx < len(bdetail):
                select = bdetail[idx]
            else:
                await editable1.edit_text("<b>❌ Invalid selection number.</b>")
                return
        except ValueError:
            # Try matching by name or ID
            select = None
            for b in bdetail:
                if selected in str(b.get("_id", "")) or selected.lower() in b.get("name", "").lower():
                    select = b
                    break
            if not select:
                await editable1.edit_text("<b>❌ Batch not found.</b>")
                return
        
        bid = select.get("_id", select.get("id", ""))
        batch_name = select.get("name", select.get("batchName", "Unknown"))
        
        # Step 4: Get schedule time
        await editable1.edit_text(msg.SCHEDULE_TIME)
        input3 = await bot.listen(m.chat.id, timeout=300)
        time_input = input3.text.strip()
        
        time = None
        if time_input.lower() != "no":
            try:
                # Validate HH:MM format
                h, mi = time_input.split(":")
                int(h)
                int(mi)
                time = time_input
            except:
                await editable1.edit_text(msg.INVALID_TIME_FORMAT)
                return
        
        # Step 5: Get credit/filename
        await editable1.edit_text(msg.CREDIT_OPTIONS)
        input4 = await bot.listen(m.chat.id, timeout=300)
        credit_filename = input4.text.strip()
        
        credit = None
        file_credit = None
        if credit_filename.lower() != "no":
            if "|" in credit_filename:
                parts = credit_filename.split("|")
                credit = parts[0].strip()
                file_credit = parts[1].strip() if len(parts) > 1 else None
            else:
                credit = credit_filename
        
        # Step 6: Get thumbnail
        await editable1.edit_text(msg.THUMBNAIL_OPTIONS)
        input5 = await bot.listen(m.chat.id, timeout=300)
        thumb = input5.text.strip()
        if thumb.lower() == "no":
            thumb = None
        
        # Step 7: Get group ID
        await editable1.edit_text(msg.GROUP_SETUP)
        input6 = await bot.listen(m.chat.id, timeout=300)
        group_id = input6.text.strip()
        
        # Verify group
        success = await set_chat(bot, group_id, editable1)
        if not success:
            return
        
        try:
            chat = await bot.get_chat(int(group_id))
            group_name = chat.title
        except:
            group_name = "Unknown Group"
        
        # Step 8: Collect data and save
        course_id = bid
        
        # Check if batch already exists
        existing = await db_instance.get_batch(m.chat.id, course_id)
        if existing:
            await editable1.edit_text(msg.BATCH_ALREADY_EXISTS)
            return
        
        await editable1.edit_text(msg.COLLECTING_DATA)
        
        all_data = await collect_data(bid, api, token, userid)
        
        if not all_data:
            await editable1.edit_text(msg.NO_DATA_ERROR)
            return
        
        # Count PDFs and videos
        pdf_count = sum(1 for x in all_data if x.get("type") == "pdf")
        video_count = sum(1 for x in all_data if x.get("type") == "video")
        
        # Save batch to database
        await db_instance.add_batch(
            user_id=m.chat.id,
            course_id=course_id,
            api=api,
            token=token,
            select=batch_name,
            time=time,
            group_id=group_id,
            length=len(all_data),
            credit=credit,
            filename=file_credit,
            thumb=thumb
        )
        
        await editable1.edit_text(
            msg.CONFIRM_CONFIG.format(app_name, course_id, batch_name, group_id, time or "Not Set", credit or "None")
        )
        
        # Start processing - delegate to modules.tasks
        from modules.tasks import process_batch_upload as tasks_upload
        await tasks_upload(bot, course_id, all_data)
        
    except asyncio.TimeoutError:
        await m.reply_text("<b>⏰ Timeout! Please try again with /addbatch</b>")
    except Exception as e:
        LOGGER.error(f"Error in add_batch: {e}")
        await m.reply_text(f"<b>❌ Error: {e}</b>")
