from pyrogram import Client as bot, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from constant import buttom, msg
from config import Config
from master.utils import send_random_photo
import os, sys

##Code Written By ꧁༒☬𝗦AHIL DEVLOPER☬༒꧂


def fix_keyboard(markup):
    """Fix InlineKeyboardMarkup by removing buttons with empty/invalid URLs."""
    if not markup or not hasattr(markup, 'inline_keyboard'):
        return markup
    fixed_rows = []
    for row in markup.inline_keyboard:
        fixed_row = []
        for btn in row:
            # Skip buttons that have an empty URL (Telegram rejects them)
            if btn.url is not None and btn.url.strip() == '':
                continue
            fixed_row.append(btn)
        if fixed_row:
            fixed_rows.append(fixed_row)
    if not fixed_rows:
        return None
    return InlineKeyboardMarkup(fixed_rows)


@bot.on_message(filters.command("start") & filters.private)
async def start_msg(bot, m):
    try:
        user_mention = m.from_user.mention
        caption = msg.START.format(user_mention, Config.USERLINK)
        kb = fix_keyboard(buttom.home())
        photo = await send_random_photo()
        if photo:
            await bot.send_photo(m.chat.id, photo=photo, caption=caption, reply_markup=kb)
        else:
            await m.reply_text(caption, reply_markup=kb, disable_web_page_preview=True)
    except Exception as e:
        await m.reply_text(f"⚠️ Error: {e}")


@bot.on_message(filters.command("help") & filters.private)
async def help_msg(bot, m):
    try:
        caption = msg.HELP.format(Config.USERLINK)
        kb = fix_keyboard(buttom.help_keyboard())
        photo = await send_random_photo()
        if photo:
            await bot.send_photo(m.chat.id, photo=photo, caption=caption, reply_markup=kb)
        else:
            await m.reply_text(caption, reply_markup=kb, disable_web_page_preview=True)
    except Exception as e:
        await m.reply_text(f"⚠️ Error: {e}")

##Code Written By ꧁༒☬𝗦AHIL DEVLOPER☬༒꧂

@bot.on_message(filters.command("restart") & filters.private)
async def restart_handler(_, m):
    if m.chat.id != Config.ADMIN_ID:
        return await m.reply_text(
            "╭━━━━━━ ERROR ━━━━━━➣\n"
            "┣⪼ ⚠️ **Access Denied**\n"
            "┣⪼ 🔒 Admin only command\n"
            "╰━━━━━━━━━━━━━━━━➣"
        )
    await m.reply_text("🚦**Restarting...**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command("legal") & filters.private)
async def legal_disclaimer(_, m):
    try:
        await m.reply_text(msg.DISCLAIMER,disable_web_page_preview=True,reply_markup=fix_keyboard(buttom.contact()))
    except Exception as e:
        await m.reply_text(f"⚠️ Error: {e}")

##Code Written By ꧁༒☬𝗦AHIL DEVLOPER☬༒꧂

@bot.on_message(filters.command("id"))
async def get_chat_id(_, m):
    await m.reply_text(f"<blockquote><b>The ID of this chat id is:</b></blockquote> `{m.chat.id}`")
    
