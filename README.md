# DiscordFileSplitterBot 🤖

Effortlessly bypass Discord's file upload limits! This bot splits, uploads, and reassembles files larger than Discord's standard 8MB cap, letting you use Discord as near-infinite cloud storage.

---

[![MIT License](https://img.shields.io/github/license/jinople/DiscordFileSplitterBot)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Last Updated](https://img.shields.io/github/last-commit/jinople/DiscordFileSplitterBot)](https://github.com/jinople/DiscordFileSplitterBot/commits/main)

---

## Features

- **Large File Support:** Upload files far bigger than Discord’s native limit.
- **Automatic Splitting:** Files split into Discord-friendly chunks. No manual work!
- **Reliable Uploads:** Handles rate limits and connection issues for long uploads.
- **Local File Integration:** Upload/download directly to and from your machine.

## Quick Start

### 1. Prerequisites

- Python **3.9+** installed.
- A Discord Bot Token (from the [Discord Developer Portal](https://discord.com/developers/applications)).
- Your Discord Server ID (see [Finding Your Server ID](#finding-your-server-id)).

### 2. Project Setup

Clone the repo and enter the directory:
```bash
git clone https://github.com/jinople/DiscordFileSplitterBot.git
cd DiscordFileSplitterBot
```

#### Virtual Environment (Recommended)

A virtual environment keeps dependencies organized and avoids system conflicts.

```bash
# Create virtual environment named "venv"
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration

Open the `.env` file in the project folder. It already contains the template—just fill in your credentials:
```env
TOKEN="YOUR_BOT_TOKEN_HERE"
GUILD_ID="YOUR_GUILD_ID_HERE"
```

### 4. Starting the Bot

```bash
# Windows
start.bat
# macOS/Linux
sh start.sh
```

Your bot will now appear online in your Discord server!

## Usage

Commands are all **slash commands** (`/`):

- `/upload <file_path> [channel]` — Uploads a file, splitting if needed.
- `/download` — Downloads and reassembles all chunks in the channel.

## Troubleshooting

- **Bot not appearing online?** Double-check your token and server ID.
- **Permission errors?** Ensure your bot role can send messages/files.

## Support

This is a passion project—if you find it useful, consider a donation: [cash.app/$NexusConcords](https://cash.app/$NexusConcords)

## License

MIT — Free for personal and non-commercial use.

---

Happy splitting!
