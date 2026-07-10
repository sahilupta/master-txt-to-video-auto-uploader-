"""
master/buttom.py - Button and batch management UI
Reconstructed from buttom.so analysis
"""
import asyncio
from pyrogram.types import InlineKeyboardButton as KB, InlineKeyboardMarkup as KM
from master.database import db_instance
from constant import msg


# ============================================================
# FUNCTIONS
# ============================================================

async def show_all_batches_buttom(user_id):
    """Show all batches for a user as inline buttons (for stats)."""
    try:
        batches = await db_instance.get_all_batches(user_id)
        if not batches:
            return None
        
        buttons = []
        for batch in batches:
            batch_name = batch.get("select", batch.get("course_id", "Unknown"))
            buttons.append([KB(f"📊 {batch_name}", callback_data=f"stats_{batch.get('course_id', '')}")])
        
        buttons.append([KB("❌ Close ❌", callback_data="close")])
        return KM(buttons)
    except Exception as e:
        print(f"Error in show_all_batches_buttom: {e}")
        return None


async def show_all_batches_buttom_delete(user_id):
    """Show all batches for a user as inline buttons (for deletion)."""
    try:
        batches = await db_instance.get_all_batches(user_id)
        if not batches:
            return None
        
        buttons = []
        for batch in batches:
            batch_name = batch.get("select", batch.get("course_id", "Unknown"))
            buttons.append([KB(f"🗑️ {batch_name}", callback_data=f"del_{batch.get('course_id', '')}")])
        
        buttons.append([KB("❌ Close ❌", callback_data="close")])
        return KM(buttons)
    except Exception as e:
        print(f"Error in show_all_batches_buttom_delete: {e}")
        return None


async def show_all_batches_buttom_manage(user_id):
    """Show all batches for a user as inline buttons (for management)."""
    try:
        batches = await db_instance.get_all_batches(user_id)
        if not batches:
            return None
        
        buttons = []
        for batch in batches:
            batch_name = batch.get("select", batch.get("course_id", "Unknown"))
            buttons.append([KB(f"⚙️ {batch_name}", callback_data=f"manage_{batch.get('course_id', '')}")])
        
        buttons.append([KB("❌ Close ❌", callback_data="close")])
        return KM(buttons)
    except Exception as e:
        print(f"Error in show_all_batches_buttom_manage: {e}")
        return None


async def delete_batch(bot, user_id, course_id):
    """Delete a batch from the database."""
    try:
        batch = await db_instance.get_batch(user_id, course_id)
        if not batch:
            return msg.BATCH_NOT_FOUND
        
        await db_instance.delete_batch(user_id, course_id)
        await db_instance.delete_batch_status(user_id, course_id)
        return msg.BATCH_DELETED
    except Exception as e:
        print(f"Error deleting batch: {e}")
        return msg.GENERAL_ERROR


async def manage_batch(bot, m, course_id):
    """Manage a specific batch - show management options."""
    try:
        x = m.chat.id if hasattr(m, 'chat') else m.from_user.id
        
        keyboard = KM([
            [KB("📊 Statistics", callback_data=f"stats_{course_id}")],
            [KB("⏰ Update Schedule", callback_data=f"schedule_{course_id}")],
            [KB("🗑️ Delete Batch", callback_data=f"del_{course_id}")],
            [KB("🔙 Back", callback_data="manage_batch"), KB("❌ Close", callback_data="close")]
        ])
        
        await m.edit_text(
            f"<b>➣━━━━━ ⚙️ MANAGE BATCH ━━━━━➣</b>\n\n"
            f"<b>🆔 Course ID:</b> <code>{course_id}</code>\n\n"
            f"Select an option below:",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error managing batch: {e}")


async def get_batch_statistics(bot, user_id, course_id):
    """Get and display batch statistics."""
    try:
        batch = await db_instance.get_batch(user_id, course_id)
        if not batch:
            return msg.BATCH_NOT_FOUND
        
        check = await db_instance.get_batch_status(user_id, course_id)
        
        stats = {
            "course_id": course_id,
            "name": batch.get("select", "Unknown"),
            "status": check.get("status", "Unknown") if check else "Not Started",
            "pdfs": check.get("pdf_count", 0) if check else 0,
            "videos": check.get("video_count", 0) if check else 0,
            "schedule": batch.get("time", "Not Set")
        }
        
        return msg.BATCH_STATUS.format(
            stats["course_id"],
            stats["name"],
            stats["status"],
            stats["pdfs"],
            stats["videos"],
            stats["schedule"]
        )
    except Exception as e:
        print(f"Error getting batch statistics: {e}")
        return msg.GENERAL_ERROR

