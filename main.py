import os
import logging
import asyncio
import uuid
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    filename_template = f"downloads/{random_id}_%(title)s.%(ext)s"
    
    # Ensure downloads directory exists
    os.makedirs('downloads', exist_ok=True)

    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # Prefer mp4
        'outtmpl': filename_template,
        'noplaylist': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

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
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
