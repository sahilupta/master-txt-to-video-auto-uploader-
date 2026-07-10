"""
constant/buttom.py - Keyboard button layouts for the bot
Reconstructed from constant/buttom.so analysis
"""
from pyrogram.types import InlineKeyboardButton as KB, InlineKeyboardMarkup as KM
from config import Config


def contact():
    """Contact/support keyboard."""
    keyboard = KM([
        [KB("📞 Contact Admin", url=Config.USERLINK)],
        [KB("📺 Tutorial", url=Config.TUTORIAL_VIDEO)],
        [KB("🏠 Home", callback_data="home"), KB("❌ Close", callback_data="close")]
    ])
    return keyboard


def help_keyboard():
    """Help menu keyboard."""
    keyboard = KM([
        [KB("📱 Add Batch", callback_data="appxlist")],
        [KB("📊 My Batches", callback_data="show_batch")],
        [KB("⚙️ Manage Batch", callback_data="manage_batch")],
        [KB("🗑️ Delete Batch", callback_data="delete_batch")],
        [KB("📞 Contact", url=Config.USERLINK)],
        [KB("🏠 Home", callback_data="home"), KB("❌ Close", callback_data="close")]
    ])
    return keyboard


def home():
    """Home/start screen keyboard."""
    keyboard = KM([
        [KB("📱 Add Batch", callback_data="appxlist")],
        [KB("📊 My Batches", callback_data="show_batch"), KB("⚙️ Manage", callback_data="manage_batch")],
        [KB("🗑️ Delete Batch", callback_data="delete_batch")],
        [KB("📚 Help", callback_data="help"), KB("⚖️ Legal", callback_data="legal")],
        [KB("❌ Close ❌", callback_data="close")]
    ])
    return keyboard


def yt_keyboard(watchurl, downloadurl):
    """YouTube video action keyboard."""
    keyboard = KM([
        [KB("▶️ Watch", url=watchurl)],
        [KB("📥 Download", url=downloadurl)],
        [KB("❌ Close", callback_data="close")]
    ])
    return keyboard
