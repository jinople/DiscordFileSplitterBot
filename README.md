README.md
FileSplitterBot 🤖
FileSplitterBot is a powerful and reliable Discord bot designed to handle large file transfers by splitting, uploading, and reassembling files directly from your computer.

Features
Large File Support: Upload files larger than Discord's standard 8MB limit.

Automatic Splitting: The bot automatically splits large files into Discord-friendly chunks.

Robust Uploads: The bot is designed to handle rate-limiting and connection issues during long uploads.

Local File System Integration: Upload and download files directly to and from your computer.

Setup Guide
Follow these steps to get your own FileSplitterBot up and running.

1. Prerequisites
You will need the following to run the bot:

Python 3.9+ installed on your computer.

A Discord Bot Token from the Discord Developer Portal.

Your Discord Server ID (you can get this by turning on Developer Mode in Discord and right-clicking your server's icon).

2. Project Installation
First, clone the project from GitHub and navigate into the project folder.

Next, create and activate a virtual environment to manage dependencies:

Bash

python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
Install all the required libraries using the requirements.txt file:

Bash

pip install -r requirements.txt
3. Configuration
Copy the .env.template file to a new file named .env. Open the .env file and add your bot token and guild ID:

TOKEN="YOUR_BOT_TOKEN_HERE"
GUILD_ID="YOUR_GUILD_ID_HERE"
4. Running the Bot
To start the bot, use the start.bat file for Windows or start.sh for macOS/Linux. This will activate the virtual environment and run the main script.

Bash

# On Windows
start.bat
# On macOS/Linux
sh start.sh
Your bot will then appear online in your Discord server.

Using the Commands
All of the bot's commands are slash commands (/). Once your bot is online, it will automatically sync the commands to your server.

/upload: Uploads a large file by specifying the local file path and an optional channel name.

/download: Downloads and reassembles all the file chunks in the current channel.

Support & Monetization
This bot is a passion project, and any support helps cover server costs and encourages continued development. If you find it useful, you can support its development by donating.

https://buymeacoffee.com/jinokin
