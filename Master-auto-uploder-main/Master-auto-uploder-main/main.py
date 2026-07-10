import pyromod.listen
from config import Config
from pyrogram import Client, idle
import asyncio
from logger import LOGGER
from modules.retasks import recover_incomplete_batches
from modules.scheduler import start_daily_schedulers
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Flask App running!"
if __name__ == "__main__":
    bot = Client(
        "Bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=30,
        plugins=dict(root="plugins"),
        workers=1000,
    )
    
    async def main():
        await bot.start()
        bot_info = await bot.get_me()
        LOGGER.info(f"<--- @{bot_info.username} Started --->")
        asyncio.create_task(recover_incomplete_batches(bot))
        asyncio.create_task(start_daily_schedulers(bot))
        LOGGER.info("Daily update schedulers started")
        await idle()
    
    asyncio.get_event_loop().run_until_complete(main())
    LOGGER.info("<--- Bot Stopped --->")
