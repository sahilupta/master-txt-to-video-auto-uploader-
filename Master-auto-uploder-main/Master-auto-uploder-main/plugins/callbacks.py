from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from master import key as master_key
from master import buttom as master_buttom
from constant import buttom, msg
from modules import appx_master
from config import Config
import json
import asyncio
import traceback

# ============================================================
# COMPLETE CALLBACK HANDLER BRIDGE
# Based on deep analysis of ALL compiled .so modules
# ============================================================
#
# master.buttom function signatures:
#   show_all_batches_buttom(user_id) -> returns list of buttons 
#   show_all_batches_buttom_delete(user_id) -> returns list of buttons
#   show_all_batches_buttom_manage(user_id) -> returns list of buttons
#   delete_batch(bot, user_id, course_id) -> handles deletion
#   manage_batch(bot, m, course_id) -> handles management
#   get_batch_statistics(bot, user_id, course_id) -> handles stats
#
# master.key function signatures:
#   handle_app_paid(bot, data, call_msg, a) -> handles app selection
#   appx_page_paid(call_msg, letter, page) -> handles pagination
#   gen_alpha_paid_kb() -> returns alphabet keyboard
#   gen_apps_paid_kb(letter, page, apps_per_page) -> returns apps keyboard
#   get_appx_api() -> fetches api data
#
# modules.appx_master function signatures:
#   add_batch(bot, m, api, app_name) -> multi-step batch add flow
#   password_login(email, password, api) -> login with password
#   otp_login(phNum, api, editable, bot, m) -> OTP login
#   set_chat(bot, GROUP_ID, editable1) -> set group chat
#   collect_data(batch_id, api, token) -> collect data from API
#   process_batch_upload(bot, course_id, all_data) -> process upload
# ============================================================


# ---------- BATCH LIST BUTTONS (return keyboard markup) ----------

@Client.on_callback_query(filters.regex("^appxlist$"))
async def cb_appxlist(bot: Client, query: CallbackQuery):
    """ADD Batch - show apps for selection via master.key"""
    try:
        # Show alphabet keyboard for app selection
        kb = await master_key.gen_alpha_paid_kb()
        if kb:
            await query.message.edit_text(
                msg.APP,
                reply_markup=kb
            )
        else:
            await query.answer("No apps found.", show_alert=True)
    except Exception as e:
        print(f"Error in appxlist: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^delete_batch$"))
async def cb_delete_batch(bot: Client, query: CallbackQuery):
    """Delete Batch - show batches for deletion"""
    try:
        user_id = query.from_user.id
        buttons = await master_buttom.show_all_batches_buttom_delete(user_id)
        if buttons:
            if isinstance(buttons, InlineKeyboardMarkup):
                await query.message.edit_text(
                    "<b>➣━━━━━ 🗑️ DELETE BATCH ━━━━━➣</b>\n\nSelect a batch to delete:",
                    reply_markup=buttons
                )
            elif isinstance(buttons, list):
                kb = InlineKeyboardMarkup([[btn] for btn in buttons] + [[InlineKeyboardButton("❌ Close ❌", callback_data="close")]])
                await query.message.edit_text(
                    "<b>➣━━━━━ 🗑️ DELETE BATCH ━━━━━➣</b>\n\nSelect a batch to delete:",
                    reply_markup=kb
                )
            else:
                await query.message.edit_text(str(buttons))
        else:
            await query.answer("No batches found.", show_alert=True)
    except Exception as e:
        print(f"Error in delete_batch: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^manage_batch$"))
async def cb_manage_batch_list(bot: Client, query: CallbackQuery):
    """Manage Batch - show batches for management"""
    try:
        user_id = query.from_user.id
        buttons = await master_buttom.show_all_batches_buttom_manage(user_id)
        if buttons:
            if isinstance(buttons, InlineKeyboardMarkup):
                await query.message.edit_text(
                    "<b>➣━━━━━ ⚙️ MANAGE BATCH ━━━━━➣</b>\n\nSelect a batch to manage:",
                    reply_markup=buttons
                )
            elif isinstance(buttons, list):
                kb = InlineKeyboardMarkup([[btn] for btn in buttons] + [[InlineKeyboardButton("❌ Close ❌", callback_data="close")]])
                await query.message.edit_text(
                    "<b>➣━━━━━ ⚙️ MANAGE BATCH ━━━━━➣</b>\n\nSelect a batch to manage:",
                    reply_markup=kb
                )
            else:
                await query.message.edit_text(str(buttons))
        else:
            await query.answer("No batches found.", show_alert=True)
    except Exception as e:
        print(f"Error in manage_batch: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^show_batch$"))
async def cb_show_batch_list(bot: Client, query: CallbackQuery):
    """Show Batch - show batches for statistics"""
    try:
        user_id = query.from_user.id
        buttons = await master_buttom.show_all_batches_buttom(user_id)
        if buttons:
            if isinstance(buttons, InlineKeyboardMarkup):
                await query.message.edit_text(
                    "<b>➣━━━━━ 📊 SHOW BATCH ━━━━━➣</b>\n\nSelect a batch to view stats:",
                    reply_markup=buttons
                )
            elif isinstance(buttons, list):
                kb = InlineKeyboardMarkup([[btn] for btn in buttons] + [[InlineKeyboardButton("❌ Close ❌", callback_data="close")]])
                await query.message.edit_text(
                    "<b>➣━━━━━ 📊 SHOW BATCH ━━━━━➣</b>\n\nSelect a batch to view stats:",
                    reply_markup=kb
                )
            else:
                await query.message.edit_text(str(buttons))
        else:
            await query.answer("No batches found.", show_alert=True)
    except Exception as e:
        print(f"Error in show_batch: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


# ---------- CLOSE ----------

@Client.on_callback_query(filters.regex("^close$"))
async def cb_close(bot: Client, query: CallbackQuery):
    """Close button - deletes the message"""
    try:
        await query.message.delete()
    except Exception as e:
        await query.answer("⚠️ Could not close.", show_alert=True)


# ---------- SPECIFIC BATCH ACTIONS ----------

@Client.on_callback_query(filters.regex("^del_"))
async def cb_del_specific(bot: Client, query: CallbackQuery):
    """Handle specific batch deletion - del_<course_id>"""
    try:
        user_id = query.from_user.id
        course_id = query.data.replace("del_", "")
        await master_buttom.delete_batch(bot, user_id, course_id)
        await query.answer("✅ Batch deleted!", show_alert=True)
        # Refresh the message
        try:
            await query.message.delete()
        except:
            pass
    except Exception as e:
        print(f"Error in del_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^manage_(?!batch$)"))
async def cb_manage_specific(bot: Client, query: CallbackQuery):
    """Handle specific batch management - manage_<course_id>"""
    try:
        course_id = query.data.replace("manage_", "")
        await master_buttom.manage_batch(bot, query.message, course_id)
    except Exception as e:
        print(f"Error in manage_specific: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^batch_"))
async def cb_batch_action(bot: Client, query: CallbackQuery):
    """Handle batch-related callbacks - batch_<course_id>"""
    try:
        course_id = query.data.replace("batch_", "")
        await master_buttom.manage_batch(bot, query.message, course_id)
    except Exception as e:
        print(f"Error in batch_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^stats_"))
async def cb_stats(bot: Client, query: CallbackQuery):
    """Handle stats callbacks - stats_<course_id>"""
    try:
        user_id = query.from_user.id
        course_id = query.data.replace("stats_", "")
        stats_text = await master_buttom.get_batch_statistics(bot, user_id, course_id)
        await query.message.edit_text(stats_text)
    except Exception as e:
        print(f"Error in stats_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


# ---------- APP PAID / APPX HANDLERS (master.key) ----------

@Client.on_callback_query(filters.regex("^app_paid"))
async def cb_app_paid(bot: Client, query: CallbackQuery):
    """Handle app paid callback - app_paid:<json_data>"""
    try:
        raw = query.data
        # Parse data - format could be app_paid:<json> or app_paid_<data>
        if ":" in raw:
            data_str = raw.split(":", 1)[1]
        else:
            data_str = raw.replace("app_paid_", "").replace("app_paid", "")
        
        try:
            data = json.loads(data_str)
        except:
            data = data_str
        
        await master_key.handle_app_paid(bot, data, query.message, query)
    except Exception as e:
        print(f"Error in app_paid: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^appx_"))
async def cb_appx_action(bot: Client, query: CallbackQuery):
    """Handle appx page callbacks - appx_<letter>_<page>"""
    try:
        parts = query.data.split("_")
        letter = parts[1] if len(parts) > 1 else ""
        page = int(parts[2]) if len(parts) > 2 else 0
        await master_key.appx_page_paid(query.message, letter, page)
    except Exception as e:
        print(f"Error in appx_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^page_"))
async def cb_page_action(bot: Client, query: CallbackQuery):
    """Handle pagination callbacks - page_<letter>_<page>"""
    try:
        parts = query.data.split("_")
        letter = parts[1] if len(parts) > 1 else ""
        page = int(parts[2]) if len(parts) > 2 else 0
        await master_key.appx_page_paid(query.message, letter, page)
    except Exception as e:
        print(f"Error in page_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^alpha_"))
async def cb_alpha_action(bot: Client, query: CallbackQuery):
    """Handle alphabet selection callbacks - alpha_<letter>"""
    try:
        parts = query.data.split("_")
        letter = parts[1] if len(parts) > 1 else ""
        page = int(parts[2]) if len(parts) > 2 else 0
        await master_key.appx_page_paid(query.message, letter, page)
    except Exception as e:
        print(f"Error in alpha_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


# ---------- HOME / BACK BUTTON ----------

@Client.on_callback_query(filters.regex("^home$"))
async def cb_home(bot: Client, query: CallbackQuery):
    """Go back to home/start screen"""
    try:
        from master.utils import send_random_photo
        user_mention = query.from_user.mention
        photo = await send_random_photo()
        await query.message.delete()
        caption = msg.START.format(user_mention, Config.USERLINK)
        kb = buttom.home()
        
        if photo:
            await bot.send_photo(
                query.message.chat.id,
                photo=photo,
                caption=caption,
                reply_markup=kb
            )
        else:
            await bot.send_message(
                query.message.chat.id,
                text=caption,
                reply_markup=kb,
                disable_web_page_preview=True
            )
    except Exception as e:
        print(f"Error in home: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^help$"))
async def cb_help(bot: Client, query: CallbackQuery):
    """Help button callback"""
    try:
        await query.message.edit_text(
            msg.HELP.format(Config.USERLINK),
            reply_markup=buttom.help_keyboard()
        )
    except Exception as e:
        print(f"Error in help: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^legal$"))
async def cb_legal(bot: Client, query: CallbackQuery):
    """Legal disclaimer callback"""
    try:
        await query.message.edit_text(
            msg.DISCLAIMER,
            reply_markup=buttom.contact()
        )
    except Exception as e:
        print(f"Error in legal: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^schedule_"))
async def cb_schedule(bot: Client, query: CallbackQuery):
    """Handle schedule update callback - schedule_<course_id>"""
    try:
        course_id = query.data.replace("schedule_", "")
        await query.message.edit_text(msg.SCHEDULE_TIME)
        # Listen for new time input
        input_msg = await bot.listen(query.message.chat.id, timeout=120)
        new_time = input_msg.text.strip()
        if new_time.lower() == "no":
            new_time = None
        else:
            # Validate HH:MM format
            try:
                h, mi = new_time.split(":")
                int(h)
                int(mi)
            except:
                await bot.send_message(query.message.chat.id, msg.INVALID_TIME_FORMAT)
                return
        from master.database import db_instance
        await db_instance.update_batch_schedule(query.from_user.id, course_id, new_time)
        await bot.send_message(query.message.chat.id, msg.BATCH_UPDATED)
    except asyncio.TimeoutError:
        await bot.send_message(query.message.chat.id, "<b>⏰ Timeout! Please try again.</b>")
    except Exception as e:
        print(f"Error in schedule_: {e}")
        traceback.print_exc()
        await query.answer(f"⚠️ Error: {e}", show_alert=True)


# ---------- CATCH-ALL FOR UNKNOWN CALLBACKS ----------

@Client.on_callback_query()
async def cb_unknown(bot: Client, query: CallbackQuery):
    """Catch any unhandled callbacks - prevents silent failures"""
    print(f"⚠️ Unhandled callback: {query.data}")
    await query.answer(f"⚠️ Unknown action: {query.data}", show_alert=False)
