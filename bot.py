import os
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import re
import subprocess
from dotenv import load_dotenv
load_dotenv()

# Replace 'YOUR_BOT_TOKEN' with your bot's token
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

ffmpeg_folder = "ffmpeg"
ffmpeg_repo_url = "https://git.ffmpeg.org/ffmpeg.git"
ffmpeg_path = os.path.join(ffmpeg_folder, "bin", "ffmpeg.exe")

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send(f"{ctx.author.name} is not connected to a voice channel")
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel")
    else:
        await ctx.send("The bot is not connected to a voice channel.")

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def clone_ffmpeg():
    print("Cloning FFmpeg...")
    subprocess.run(["git", "clone", ffmpeg_repo_url, ffmpeg_folder], check=True)
    print("FFmpeg cloned successfully.")

if not os.path.exists(ffmpeg_path):
    clone_ffmpeg()

@bot.command(name='play', help='To play a song')
async def play(ctx, *, query: str):
    if not ctx.voice_client:
        await join(ctx)
    
    async with ctx.typing():
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'default_search': 'auto',  # Use 'auto' to search for both videos and playlists
                'verbose': True,
                'noplaylist': True,
                'restrictfilenames': True,
                'nocheckcertificate': True,
                'logtostderr': True
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                if is_valid_url(query):
                    info = ydl.extract_info(query, download=False)
                else:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                
                url = info['url']
                print(f"Playing URL: {url}")
                print(f"Video Info: {info}")

            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            source = discord.FFmpegPCMAudio(url, executable=ffmpeg_path, **ffmpeg_options)
            ctx.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
            await ctx.send(f'Now playing: {info["title"]}')
        except Exception as e:
            await ctx.send(f"An error occurred while trying to play the song: {e}")
            print(f"Error: {e}")

@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused the song")
    else:
        await ctx.send("No audio is playing.")

@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed the song")
    else:
        await ctx.send("The song is not paused.")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Stopped the song")
    else:
        await ctx.send("No audio is playing.")

bot.run(TOKEN)
