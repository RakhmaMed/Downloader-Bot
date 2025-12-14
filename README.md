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

    Copy `env.example` to `.env` and set values:

    ```bash
    cp env.example .env
    ```

    Required:
    - `BOT_TOKEN` — Telegram bot token from @BotFather.
    - `BOT_MODE` — `polling` (default) or `webhook`.

    Webhook mode needs extra variables:
    - `WEBHOOK_HOST` — public `https://your-domain` served by nginx with SSL.
    - `WEBHOOK_PATH` — path proxied to the bot (e.g. `/telegram/webhook`).
    - `WEBHOOK_PORT` / `WEBHOOK_LISTEN` — local bind for nginx upstream.
    - `WEBHOOK_SECRET` — optional shared secret for Telegram.

## Usage

1.  **Run the bot:**

    Using the helper script (preferred):

    ```bash
    chmod +x manage.sh
    ./manage.sh install        # one time dependency install
    ./manage.sh run-polling    # foreground polling
    ```

    Webhook (requires nginx proxy + HTTPS):

    ```bash
    BOT_MODE=webhook WEBHOOK_HOST=https://your-domain ./manage.sh run-webhook
    ```

    Background with logs:

    ```bash
    ./manage.sh deploy
    # logs: logs/bot.log
    ```

    Or run directly with Python:

    ```bash
    uv run main.py   # reads BOT_MODE from .env
    ```

2.  **Interact with the bot:**
    *   Start the bot with `/start`.
    *   Send a YouTube or Instagram link (e.g., `https://www.youtube.com/watch?v=...` or `https://www.instagram.com/reel/...`).
    *   The bot will download the video and send it to you.

## Docker

Build the image (runs dependency install via `uv` and bundles `ffmpeg`):

```bash
docker build -t downloader-bot .
```

Run the container, passing the bot token (either via `--env-file .env` or `-e BOT_TOKEN=...`):

```bash
docker run --rm \
  --env-file .env \
  downloader-bot
```

## Webhook behind nginx

1. Set in `.env`:
   - `BOT_MODE=webhook`
   - `WEBHOOK_HOST=https://your-domain`
   - `WEBHOOK_PATH=/telegram/webhook`
   - `WEBHOOK_PORT=8081` (default)

2. Example nginx location (TLS terminates in nginx):

```
location /telegram/webhook {
    proxy_pass http://127.0.0.1:8081;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

3. Start the bot:

```bash
./manage.sh install
./manage.sh deploy   # runs in background, uses BOT_MODE from .env
```