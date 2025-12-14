import asyncio
import logging
import os
import uuid

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv
import yt_dlp

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Env config
BOT_MODE = os.getenv("BOT_MODE", "polling").lower()
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook/bot")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8081"))
WEBHOOK_LISTEN = os.getenv("WEBHOOK_LISTEN", "0.0.0.0")
DOWNLOADS_DIR = "downloads"

# Initialize Bot and Dispatcher
token = os.getenv('BOT_TOKEN')
if not token or token == 'your_bot_token_here':
    print("Error: BOT_TOKEN not configured in .env file.")
    exit(1)

bot = Bot(token=token)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hi! Send me a YouTube or Instagram link and I'll download it for you.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Simply paste a valid URL from YouTube or Instagram, and I will try to download the video for you.")

def download_media(url):
    """
    Downloads media from the given URL using yt-dlp.
    Returns the path to the downloaded file.
    """
    # Create a unique filename to avoid collisions
    random_id = str(uuid.uuid4())[:8]
    filename_template = f"{DOWNLOADS_DIR}/{random_id}_%(title)s.%(ext)s"
    
    # Ensure downloads directory exists
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # Prefer mp4
        'outtmpl': filename_template,
        'noplaylist': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def build_webhook_url() -> str:
    """
    Build a full webhook URL combining the public host and path.
    Raises if required settings are missing.
    """
    if not WEBHOOK_HOST:
        raise RuntimeError("WEBHOOK_HOST is required when BOT_MODE=webhook")

    host = WEBHOOK_HOST.rstrip("/")
    path = "/" + WEBHOOK_PATH.lstrip("/")
    return f"{host}{path}"

async def run_webhook():
    """
    Run the bot in webhook mode behind an HTTP server (nginx handles TLS).
    """
    webhook_url = build_webhook_url()
    secret = WEBHOOK_SECRET or None

    # Configure aiohttp app
    app = web.Application()
    app["bot"] = bot

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=secret,
    ).register(app, path="/" + WEBHOOK_PATH.lstrip("/"))

    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
    )

    await site.start()

    await bot.set_webhook(
        url=webhook_url,
        secret_token=secret,
        drop_pending_updates=True,
    )

    logger.info("Webhook server started")
    logger.info("Listening on http://%s:%s%s", WEBHOOK_LISTEN, WEBHOOK_PORT, WEBHOOK_PATH)
    logger.info("Webhook URL set to %s", webhook_url)
    if secret:
        logger.info("Secret token enabled for webhook validation")

    try:
        await asyncio.Future()  # Run forever
    finally:
        await bot.delete_webhook(drop_pending_updates=False)
        await runner.cleanup()
        logger.info("Webhook server stopped")

@dp.message(F.text)
async def handle_message(message: types.Message):
    url = message.text
    if not url:
        return
        
    # Basic URL check
    if not any(x in url for x in ['youtube.com', 'youtu.be', 'instagram.com']):
        await message.answer("Please send a valid YouTube or Instagram URL.")
        return

    status_msg = await message.answer("Finding video...")
    
    try:
        # Run blocking download in a separate thread
        loop = asyncio.get_running_loop()
        await status_msg.edit_text("Downloading...")
        
        file_path = await loop.run_in_executor(None, download_media, url)
        
        await status_msg.edit_text("Uploading...")
        
        # Check file size (Telegram Bot API limit is ~50MB for sendVideo)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            await status_msg.edit_text(f"File is too large ({file_size / (1024*1024):.1f} MB). Bot API limit is 50MB.")
        else:
            video_file = FSInputFile(file_path)
            await message.answer_video(video_file)
            
            # Clean up status message if successful
            await status_msg.delete()

        # Cleanup file
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        error_text = str(e)
        # Simplify error message for user
        if "sign in" in error_text.lower():
            error_text = "Content requires sign-in or is private."
        
        await status_msg.edit_text(f"Error: {error_text}")
        # Attempt minimal cleanup if file exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def main():
    if BOT_MODE == "webhook":
        await run_webhook()
    else:
        # Ensure webhook is disabled when running in polling mode
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot is running in polling mode...")
        await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
