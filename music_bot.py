import os
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

from myserver import server_on

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='+', intents=intents)

music_queue = []
is_playing = False
loop = False
looplist = False

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

def play_next(vc):
    global is_playing, loop, looplist

    if not vc or not vc.is_connected():
        is_playing = False
        return

    if loop:
        song = music_queue[0]
        source = discord.FFmpegPCMAudio(
            song['url'],
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        )
        vc.play(source, after=lambda e: play_next(vc))
        return

    if len(music_queue) > 0:
        if not loop:
            current = music_queue.pop(0)
            if looplist:
                music_queue.append(current)

        if len(music_queue) == 0:
            is_playing = False
            return

        song = music_queue[0]
        source = discord.FFmpegPCMAudio(
            song['url'],
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        )
        vc.play(source, after=lambda e: play_next(vc))
    else:
        is_playing = False

async def play_music(ctx):
    global is_playing

    if len(music_queue) > 0:
        is_playing = True
        song = music_queue[0]
        vc = ctx.voice_client

        source = discord.FFmpegPCMAudio(
            song['url'],
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        )
        vc.play(source, after=lambda e: play_next(vc))
        await ctx.send(f'🎶 Playing: **{song["title"]}**')
    else:
        is_playing = False

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        await ctx.send("คุณต้องอยู่ในห้องเสียงก่อนนะ!")

@bot.command()
async def leave(ctx):
    global music_queue, is_playing, loop, looplist

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        music_queue.clear()
        is_playing = False
        loop = False
        looplist = False
        await ctx.send("👋 ออกจากห้องเสียง และล้างคิวเรียบร้อยแล้ว")
    else:
        await ctx.send("บอทยังไม่ได้ join ห้องเลยจ้า")

@bot.command()
async def play(ctx, url):
    global music_queue, is_playing

    if not ctx.voice_client:
        await ctx.invoke(bot.get_command("join"))

    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        'quiet': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            title = info['title']

        music_queue.append({'url': url2, 'title': title})

        await ctx.send(f'✅ เพิ่มเพลง: **{title}** เข้าในคิว')

        if not is_playing:
            await play_music(ctx)

    except Exception as e:
        await ctx.send(f'❌ เกิดข้อผิดพลาด: {e}')

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ ข้ามเพลงแล้วจ้า~")
    else:
        await ctx.send("❌ ไม่มีเพลงที่กำลังเล่นอยู่")

@bot.command()
async def next(ctx):
    await ctx.invoke(bot.get_command("skip"))

@bot.command()
async def queue(ctx):
    if len(music_queue) == 0:
        await ctx.send("📬 คิวว่างอยู่เลย~")
    else:
        msg = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(music_queue)])
        await ctx.send(f"📃 คิวเพลงตอนนี้:\n{msg}")

@bot.command()
async def loop(ctx):
    global loop
    loop = not loop
    status = "เปิด" if loop else "ปิด"
    await ctx.send(f"🔁 Loop เพลงปัจจุบัน: {status}")

@bot.command()
async def looplist(ctx):
    global looplist
    looplist = not looplist
    status = "เปิด" if looplist else "ปิด"
    await ctx.send(f"🔂 Loop ทั้งคิว: {status}")

server_on()

bot.run(os.getenv('TOKEN'))