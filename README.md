# Telegram Downloader Bot

A Telegram bot built with [aiogram](https://docs.aiogram.dev/) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) that downloads videos from YouTube and Instagram and sends them back to the user.

## Features

-   **Multi-Platform Support**: Downloads videos from YouTube and Instagram.
-   **Automatic Upload**: Sends the downloaded video file directly to the chat.
-   **Size Limit Check**: Handles Telegram's 50MB bot API limit gracefully.
-   **Clean Up**: Automatically deletes downloaded files after processing to save space.

## Prerequisites

-   Python 3.8 or higher.
-   [uv](https://github.com/astral-sh/uv) (recommended) or pip.
-   A Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather)).

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/downloader_bot.git
    cd downloader_bot
    ```

2.  **Install dependencies:**

    Using `uv`:

    ```bash
    uv sync
    ```

    Or using `pip`:

    ```bash
    pip install .
    ```

3.  **Configuration:**

    Create a `.env` file in the root directory (or rename `.env.example`):

    ```bash
    cp .env.example .env
    ```

    Open `.env` and add your Telegram Bot Token:

    ```env
    BOT_TOKEN=your_bot_token_here
    ```

## Usage

1.  **Run the bot:**

    Using `uv`:

    ```bash
    uv run main.py
    ```

    Or with standard python:

    ```bash
    python main.py
    ```

2.  **Interact with the bot:**
    *   Start the bot with `/start`.
    *   Send a YouTube or Instagram link (e.g., `https://www.youtube.com/watch?v=...` or `https://www.instagram.com/reel/...`).
    *   The bot will download the video and send it to you.
