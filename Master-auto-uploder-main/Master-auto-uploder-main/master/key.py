"""
master/key.py - App selection and paid app management
Reconstructed from key.so analysis
"""
import motor.motor_asyncio
from pyrogram.types import InlineKeyboardButton as KB, InlineKeyboardMarkup as KM
from config import Config
from modules import appx_master
from constant import msg

# String constants from .so analysis
DB_NAME = "APPX_API"
DB_URL = Config.DB_URL
pass101 = "KCzMfCaj7DgGCBPh"
pass2 = "NmC1fGZDNNBEfdh0"
pass3 = "NmC1fGdcccsfdh0"
pass4 = "NmC1fGdcccsfdh0"
pass5 = "NmC1fGdcccsfdh0"
pass6 = "NmC1fGdcccsfdh0"
pass7 = "NmC1fGdcccsfdh0"
pass8 = "NmC1fGdcccsfdh0"
us = "master"

# App identifier map for tracking unique app IDs
app_identifier_map = {}


class Database:
    """Separate database class for APPX API storage."""
    def __init__(self, uri, database_name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[database_name]
        self.appx_api = self.db["appx_api"]

    async def get_appx_api(self):
        cursor = self.appx_api.find({})
        return await cursor.to_list(length=None)


db_instance = Database(DB_URL, DB_NAME)


async def get_appx_api():
    """Fetch all appx API entries from database."""
    try:
        apis = await db_instance.get_appx_api()
        return apis
    except Exception as e:
        print(f"Error getting appx api: {e}")
        return []


async def gen_alpha_paid_kb():
    """Generate alphabet keyboard for paid apps."""
    try:
        apis = await get_appx_api()
        if not apis:
            return None
        
        # Collect unique first letters from app names
        keys = set()
        for api in apis:
            app_name = api.get("app_name", api.get("name", ""))
            if app_name:
                first_letter = app_name[0].upper()
                keys.add(first_letter)
        
        keys = sorted(list(keys))
        
        # Build keyboard rows of 5 buttons each
        keyboard = []
        for i in range(0, len(keys), 5):
            row = []
            for j in range(i, min(i + 5, len(keys))):
                row.append(KB(keys[j], callback_data=f"appx_{keys[j]}_0"))
            keyboard.append(row)
        
        keyboard.append([KB("❌ Close ❌", callback_data="close")])
        return KM(keyboard)
    except Exception as e:
        print(f"Error generating alpha keyboard: {e}")
        return None


async def gen_apps_paid_kb(letter, page=0, apps_per_page=10):
    """Generate keyboard of apps starting with a specific letter, with pagination."""
    try:
        apis = await get_appx_api()
        if not apis:
            return None
        
        app_dict = {}
        letter_grouped = []
        
        for app in apis:
            api = app.get("api", app.get("url", ""))
            app_name = app.get("app_name", app.get("name", ""))
            first_letter = app_name[0].upper() if app_name else ""
            
            if first_letter == letter.upper():
                letter_grouped.append(app)
        
        start = page * apps_per_page
        end = start + apps_per_page
        paginated_apps = letter_grouped[start:end]
        total_pages = (len(letter_grouped) + apps_per_page - 1) // apps_per_page
        
        keyboard = []
        for idx, app in enumerate(paginated_apps):
            app_name = app.get("app_name", app.get("name", "Unknown"))
            unique_id = f"{start + idx}"
            app_identifier_map[unique_id] = app
            keyboard.append([KB(f"📱 {app_name}", callback_data=f"app_paid:{unique_id}")])
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(KB("⬅️ Prev", callback_data=f"appx_{letter}_{page - 1}"))
        if page < total_pages - 1:
            nav_buttons.append(KB("➡️ Next", callback_data=f"appx_{letter}_{page + 1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([KB("🔙 Back", callback_data="appxlist"), KB("❌ Close", callback_data="close")])
        return KM(keyboard)
    except Exception as e:
        print(f"Error generating apps keyboard: {e}")
        return None


async def appx_page_paid(call_msg, letter, page):
    """Handle pagination for paid apps list."""
    try:
        markup = await gen_apps_paid_kb(letter, page)
        if markup:
            total_pages = 1  # Will be calculated inside
            text = f"<b>➣━━━━━ 📱 APPS ({letter}) ━━━━━➣</b>\n\nSelect an app:"
            try:
                await call_msg.edit_text(text, reply_markup=markup)
            except Exception as e:
                print(f"Edit error: {e}")
        else:
            try:
                await call_msg.edit_text("<b>❌ No apps found for this letter.</b>")
            except:
                pass
    except Exception as e:
        print(f"Error in appx_page_paid: {e}")


async def handle_app_paid(bot, data, call_msg, a):
    """Handle when user selects a paid app."""
    try:
        if isinstance(data, str):
            app_id = data
        else:
            app_id = str(data)
        
        app_details = app_identifier_map.get(app_id)
        if not app_details:
            await call_msg.edit_text("<b>❌ App not found. Please try again.</b>")
            return
        
        app_name = app_details.get("app_name", app_details.get("name", "Unknown"))
        api = app_details.get("api", app_details.get("url", ""))
        
        # Start the batch add process
        await appx_master.add_batch(bot, call_msg, api, app_name)
    except Exception as e:
        print(f"Error in handle_app_paid: {e}")
        try:
            await call_msg.edit_text(f"<b>❌ Error: {e}</b>")
        except:
            pass
