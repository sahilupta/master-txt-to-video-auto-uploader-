"""
modules/manager.py - Group/topic management
Reconstructed from manager.so analysis
"""
from pyrogram.enums import ChatType
from pyrogram.errors import ChatAdminRequired, ChatWriteForbidden
from master.database import db_instance


async def create_topic(bot, GROUP_ID, subjectname):
    """Create a forum topic in a group."""
    try:
        result = await bot.create_forum_topic(int(GROUP_ID), subjectname)
        forum_id = result.id
        await db_instance.save_topic(GROUP_ID, forum_id, subjectname)
        return forum_id
    except Exception as e:
        print(f"Error creating topic: {e}")
        return None


async def set_chat(bot, GROUP_ID, editable1):
    """Verify bot has permissions in a group chat."""
    try:
        chat = await bot.get_chat(int(GROUP_ID))
        bot_member = await bot.get_chat_member(int(GROUP_ID), (await bot.get_me()).id)
        
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if bot_member.privileges:
                return True
            else:
                await editable1.edit_text(
                    "<b>❌ Bot needs admin permissions in the group!</b>"
                )
                return False
        else:
            await editable1.edit_text(
                "<b>❌ Invalid group ID. Please provide a valid group/supergroup ID.</b>"
            )
            return False
    except ChatAdminRequired:
        await editable1.edit_text(
            "<b>❌ Bot needs admin permissions in the group!</b>"
        )
        return False
    except ChatWriteForbidden:
        await editable1.edit_text(
            "<b>❌ Bot cannot write messages in this group!</b>"
        )
        return False
    except Exception as e:
        await editable1.edit_text(
            f"<b>❌ Error: {e}</b>"
        )
        return False
