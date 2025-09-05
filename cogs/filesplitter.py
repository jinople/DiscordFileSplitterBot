import discord
from discord.ext import commands
from discord import app_commands
import os
import aiohttp
import json
import io
import aiofiles
import asyncio
from pathlib import Path

class FileSplitterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.upload_dir = "uploads"
        self.max_chunk_size = 8 * 1024 * 1024
        self.uploaded_files = {}

    async def cog_load(self):
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    @app_commands.command(name="upload", description="Uploads a large file from a local path.")
    @app_commands.describe(file_path="The full path to the file to upload.")
    @app_commands.describe(channel_name="The name of the channel for the upload (optional).")
    async def upload_file(self, interaction: discord.Interaction, file_path: str, channel_name: str = None):
        """Uploads a large file from a local path by splitting it into chunks."""
        absolute_path = Path(file_path).resolve()

        await interaction.response.send_message(f"Starting to process file from path: `{absolute_path}`...", ephemeral=True)

        if not absolute_path.exists():
            await interaction.followup.send(f"Error: The file path `{absolute_path}` does not exist.", ephemeral=True)
            return

        original_filename = absolute_path.name
        file_size = os.path.getsize(absolute_path)

        if not channel_name:
            sanitized_name = original_filename.lower().replace('.', '-').replace('_', '-')
        else:
            sanitized_name = channel_name.lower().replace(' ', '-')

        try:
            new_channel = await interaction.guild.create_text_channel(name=sanitized_name)
            self.uploaded_files[original_filename] = new_channel.id
            await interaction.followup.send(f"Created channel {new_channel.mention} for the upload.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to create channel: {e}", ephemeral=True)
            return

        await new_channel.send(f"Starting upload of `{original_filename}`...")

        try:
            total_parts = (file_size + self.max_chunk_size - 1) // self.max_chunk_size
            
            async with aiofiles.open(absolute_path, "rb") as f:
                for i in range(total_parts):
                    if (i + 1) % 50 == 0:
                        await asyncio.sleep(5)

                    retries = 3
                    chunk_uploaded = False
                    while retries > 0:
                        try:
                            chunk = await f.read(self.max_chunk_size)
                            if not chunk:
                                break

                            chunk_filename = f"{original_filename}.part_{i+1}_of_{total_parts}"
                            
                            chunk_file = discord.File(fp=io.BytesIO(chunk), filename=chunk_filename)

                            await new_channel.send(f"Part {i+1} of {total_parts}", file=chunk_file)
                            await asyncio.sleep(1)
                            chunk_uploaded = True
                            break
                        except discord.errors.HTTPException as e:
                            retries -= 1
                            await new_channel.send(f"An error occurred with part {i+1}: {e}. Retrying... ({retries} attempts left)")
                            await asyncio.sleep(10)
                        except Exception as e:
                            await new_channel.send(f"An unexpected error occurred: {e}")
                            retries = 0

                    if not chunk_uploaded:
                        await new_channel.send(f"🔴 Upload failed after all retries. The file is incomplete.")
                        return

            await new_channel.send(f"Upload complete for `{original_filename}`. To download, go to that channel and use the `/download` command.")
            
        except Exception as e:
            await new_channel.send(f"An error occurred during upload: {e}")

    @app_commands.command(name="resume", description="Resumes a failed file upload.")
    @app_commands.describe(file_path="The full path to the file to resume.")
    async def resume_upload(self, interaction: discord.Interaction, file_path: str):
        """Resumes a failed file upload from a local path."""
        absolute_path = Path(file_path).resolve()

        await interaction.response.send_message(f"Attempting to resume upload of `{absolute_path}`...", ephemeral=True)

        if not absolute_path.exists():
            await interaction.followup.send(f"Error: The file path `{absolute_path}` does not exist.", ephemeral=True)
            return

        original_filename = absolute_path.name
        file_size = os.path.getsize(absolute_path)
        
        sanitized_name = original_filename.lower().replace('.', '-').replace('_', '-')
        upload_channel = discord.utils.get(interaction.guild.channels, name=sanitized_name)

        if not upload_channel:
            await interaction.followup.send(f"Error: A channel for `{original_filename}` was not found. Please start a new upload with `/upload`.", ephemeral=True)
            return

        await upload_channel.send(f"Resuming upload in {upload_channel.mention}.")

        try:
            start_part = 0
            async for message in upload_channel.history(limit=None, oldest_first=False):
                if message.author == self.bot.user and message.attachments:
                    try:
                        filename = message.attachments[0].filename
                        last_part_number = int(filename.split('_')[-2])
                        start_part = last_part_number
                        await upload_channel.send(f"Found last part: {last_part_number}. Resuming from part {start_part + 1}.")
                        break
                    except (IndexError, ValueError):
                        continue
            
            total_parts = (file_size + self.max_chunk_size - 1) // self.max_chunk_size
            
            async with aiofiles.open(absolute_path, "rb") as f:
                if start_part > 0:
                    await f.seek(start_part * self.max_chunk_size)
                
                for i in range(start_part, total_parts):
                    if (i + 1) % 50 == 0:
                        await asyncio.sleep(5)

                    retries = 3
                    chunk_uploaded = False
                    while retries > 0:
                        try:
                            chunk = await f.read(self.max_chunk_size)
                            if not chunk:
                                break

                            chunk_filename = f"{original_filename}.part_{i+1}_of_{total_parts}"
                            
                            chunk_file = discord.File(fp=io.BytesIO(chunk), filename=chunk_filename)

                            await upload_channel.send(f"Part {i+1} of {total_parts}", file=chunk_file)
                            await asyncio.sleep(1)
                            chunk_uploaded = True
                            break
                        except discord.errors.HTTPException as e:
                            retries -= 1
                            await upload_channel.send(f"An error occurred with part {i+1}: {e}. Retrying... ({retries} attempts left)")
                            await asyncio.sleep(10)
                        except Exception as e:
                            await upload_channel.send(f"An unexpected error occurred: {e}")
                            retries = 0

                    if not chunk_uploaded:
                        await upload_channel.send(f"🔴 Upload failed after all retries. The file is incomplete.")
                        return

            await upload_channel.send(f"Upload complete for `{original_filename}`. To download, go to that channel and use the `/download` command.")
            
        except Exception as e:
            await upload_channel.send(f"An error occurred during upload: {e}")

    @app_commands.command(name="download", description="Downloads and rebuilds a file from a channel.")
    @app_commands.describe(channel_name="The name of the channel to download from (optional).")
    async def download_file(self, interaction: discord.Interaction, channel_name: str = None):
        """Downloads and rebuilds a previously uploaded file from its dedicated channel."""
        
        if not channel_name:
            channel = interaction.channel
            await interaction.response.send_message(f"Starting download and reassembly from the current channel...")
        else:
            channel = discord.utils.get(interaction.guild.channels, name=channel_name.lower().replace(' ', '-'))
            if not channel:
                await interaction.response.send_message(f"Error: Could not find channel named `{channel_name}`.", ephemeral=True)
                return
            await interaction.response.send_message(f"Starting download and reassembly from channel `{channel_name}`...")

        original_filename = ""
        total_parts = 0
        try:
            first_message_with_file = None
            async for message in channel.history(limit=None, oldest_first=True):
                if message.author == self.bot.user and message.attachments:
                    first_message_with_file = message
                    break
            
            if not first_message_with_file:
                await interaction.followup.send(f"Error: Could not find any file attachments in this channel.")
                return

            first_filename = first_message_with_file.attachments[0].filename
            original_filename = ".".join(first_filename.split('.part_')[0].split('.'))
            total_parts = int(first_filename.split('_')[-1].split('.')[0])

            download_path = os.path.join(self.upload_dir, original_filename)
            
            async with aiohttp.ClientSession() as session:
                async with aiofiles.open(download_path, "wb") as f:
                    async for message in channel.history(limit=None, oldest_first=True):
                        if message.author == self.bot.user and message.attachments:
                            attachment = message.attachments[0]
                            chunk_url = attachment.url
                            
                            await channel.send(f"Downloading {attachment.filename}...")
                            
                            async with session.get(chunk_url) as resp:
                                await f.write(await resp.read())
            
            final_file_size = Path(download_path).stat().st_size
            if final_file_size >= (total_parts * self.max_chunk_size) - 100:
                await channel.send(f"Successfully rebuilt `{original_filename}`. It's now available on the bot's server.")
            else:
                await channel.send(f"🔴 Download failed. The file is incomplete.", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred during download: {e}")

    @app_commands.command(name="download_from_part", description="Resumes a failed download from a specific part number.")
    @app_commands.describe(file_path="The full path to the partially downloaded file.")
    @app_commands.describe(part_number="The part number to resume from.")
    @app_commands.describe(channel_name="The channel name where the file was uploaded.")
    async def download_from_part(self, interaction: discord.Interaction, file_path: str, part_number: int, channel_name: str = None):
        """Resumes a failed download from a specific part number."""
        absolute_path = Path(file_path).resolve()
        
        await interaction.response.send_message(f"Attempting to resume download of `{absolute_path}` from part {part_number}...", ephemeral=True)

        if not absolute_path.exists():
            await interaction.followup.send(f"Error: The file path `{absolute_path}` does not exist.", ephemeral=True)
            return

        original_filename = absolute_path.name
        
        if not channel_name:
            channel = interaction.channel
            await interaction.followup.send(f"Resuming download in the current channel.")
        else:
            channel = discord.utils.get(interaction.guild.channels, name=channel_name.lower().replace(' ', '-'))
            if not channel:
                await interaction.followup.send(f"Error: Could not find channel named `{channel_name}`.", ephemeral=True)
                return
            await interaction.followup.send(f"Resuming download in channel `{channel_name}`.")
        
        try:
            total_parts = 0
            first_message_with_file = None
            async for message in channel.history(limit=None, oldest_first=True):
                if message.author == self.bot.user and message.attachments:
                    first_message_with_file = message
                    break
            
            if not first_message_with_file:
                await interaction.followup.send(f"Error: Could not find any file attachments from the bot in this channel.", ephemeral=True)
                return

            first_filename = first_message_with_file.attachments[0].filename
            total_parts = int(first_filename.split('_')[-1].split('.')[0])
            
            async with aiohttp.ClientSession() as session:
                async with aiofiles.open(absolute_path, "ab") as f:
                    await f.seek((part_number - 1) * self.max_chunk_size)

                    async for message in channel.history(limit=None, oldest_first=True):
                        if message.author == self.bot.user and message.attachments:
                            attachment = message.attachments[0]
                            try:
                                filename = attachment.filename
                                current_part_index = int(filename.split('_')[-2])
                                
                                if current_part_index >= part_number:
                                    chunk_url = attachment.url
                                    await channel.send(f"Downloading {filename}...")
                                    async with session.get(chunk_url) as resp:
                                        await f.write(await resp.read())
                            except (IndexError, ValueError):
                                continue

            final_file_size = absolute_path.stat().st_size
            expected_parts = final_file_size // self.max_chunk_size
            if final_file_size % self.max_chunk_size > 0:
                expected_parts += 1
                
            if expected_parts >= total_parts:
                await channel.send(f"✅ Successfully resumed and rebuilt `{original_filename}`. It's now available on the bot's server.")
            else:
                await channel.send(f"🔴 Download failed. Expected {total_parts} parts, but only have data for {expected_parts} parts.", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred during download from part: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(FileSplitterCog(bot))