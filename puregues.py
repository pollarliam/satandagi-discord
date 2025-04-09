import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import yt_dlp
import google.generativeai as genai
import requests
import random

# Carrega variáveis do .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Coordenadas de Guanambi - BA
LATITUDE = -14.2233
LONGITUDE = -42.7819

# Configura Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
looping = False
last_url = None
queue = []

chuva_videos = [
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359346638367359110/ssstwitter.com_1743637252978.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359346638618886205/ssstwitter.com_1743651836097.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347438078398534/ssstwitter.com_1744126432099.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347438468731060/ssstwitter.com_1744132965721.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347438925906152/ssstwitter.com_1744132453883.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347439181496573/ssstwitter.com_1744143722035.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347439487811818/ssstwitter.com_1744164004270.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347439886401677/ssstwitter.com_1744163955452.mp4",
    "https://cdn.discordapp.com/attachments/1359012678097571902/1359347469804376064/ssstwitter.com_1743628290497.mp4",
]

@bot.event
async def on_ready():
    print(f'🤖 Bot {bot.user.name} está online!')
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

# -------------- SLASH COMMANDS --------------

@bot.tree.command(name="play", description="Toca uma música pelo nome ou link")
@app_commands.describe(search="Nome da música ou link do YouTube")
async def slash_play(interaction: discord.Interaction, search: str):
    ctx = await bot.get_context(interaction)
    await play(ctx, search=search)
    await interaction.response.send_message("🎶 Tocando música, puregues!", ephemeral=True)

@bot.tree.command(name="chuva", description="Previsão de chuva em Guanambi")
async def slash_chuva(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await chuva(ctx)

@bot.tree.command(name="pause", description="Pausa a música")
async def slash_pause(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await pause(ctx)
    await interaction.response.send_message("⏸️ Música pausada, puregues!", ephemeral=True)

@bot.tree.command(name="resume", description="Retoma a música")
async def slash_resume(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await resume(ctx)
    await interaction.response.send_message("▶️ Música retomada, puregues!", ephemeral=True)

@bot.tree.command(name="fila", description="Mostra a fila de músicas")
async def slash_fila(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await fila(ctx)

@bot.tree.command(name="skip", description="Pula para a próxima música")
async def slash_skip(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await skip(ctx)
    await interaction.response.send_message("⏭️ Pulando música, puregues!", ephemeral=True)

@bot.tree.command(name="stop", description="Para a música e sai do canal")
async def slash_stop(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await stop(ctx)
    await interaction.response.send_message("👋 Desconectando, puregues!", ephemeral=True)

@bot.tree.command(name="loop", description="Ativa/desativa o loop")
async def slash_loop(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await loop_command(ctx)
    await interaction.response.send_message("🔁 Loop atualizado, puregues!", ephemeral=True)

# -------------- PREFIX COMMANDS --------------

@bot.command(name="pure")
async def pure_command(ctx):
    await ctx.send("puregues")

@bot.command(name="loop")
async def loop_command(ctx):
    global looping
    looping = not looping
    estado = "ativado" if looping else "desativado"
    await ctx.send(f"🔁 Loop {estado}, puregues!")

@bot.command(name="play")
async def play(ctx, *, search: str):
    global last_url
    last_url = search
    queue.append(search)

    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz, puregues.")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    if vc.is_playing():
        await ctx.send("🎶 Música adicionada à fila, puregues!")
        return

    await tocar_musica(ctx, vc)

async def tocar_musica(ctx, vc):
    global queue
    if not queue:
        return

    search = queue.pop(0)
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': 'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'default_search': 'ytsearch',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search, download=True)
            video = info['entries'][0] if 'entries' in info else info
            filename = ydl.prepare_filename(video).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            title = video['title']

        def after_playing(error):
            if looping:
                queue.insert(0, search)
            fut = asyncio.run_coroutine_threadsafe(tocar_musica(ctx, vc), bot.loop)
            try:
                fut.result()
            except Exception as e:
                print("Erro ao tocar próxima música:", e)

        vc.play(discord.FFmpegPCMAudio(source=filename), after=after_playing)
        await ctx.send(f"🎶 Tocando: {title}")
    except Exception as e:
        print("Erro ao tocar música:", e)
        await ctx.send("❌ Não consegui tocar a música, puregues.")

@bot.command(name="fila")
async def fila(ctx):
    if not queue:
        await ctx.send("📭 A fila está vazia, puregues.")
    else:
        texto_fila = "\n".join(f"{i+1}. {item}" for i, item in enumerate(queue))
        await ctx.send(f"📃 Fila atual:\n{texto_fila}")

@bot.command(name="skip")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Pulando para a próxima música, puregues!")
    else:
        await ctx.send("❌ Não estou tocando nada, puregues.")

@bot.command(name="pause")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Música pausada, puregues!")
    else:
        await ctx.send("❌ Não estou tocando nada para pausar, puregues.")

@bot.command(name="resume")
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Música retomada, puregues!")
    else:
        await ctx.send("❌ Não tem música pausada pra retomar, puregues.")

@bot.command(name="stop")
async def stop(ctx):
    global queue
    queue = []
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Saí do canal de voz e limpei a fila, puregues.")
    else:
        await ctx.send("❌ Não estou em nenhum canal de voz.")

@bot.command(name="chuva")
async def chuva(ctx):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=precipitation_probability_max&timezone=America%2FSao_Paulo"
        response = requests.get(url)
        data = response.json()
        chance = data['daily']['precipitation_probability_max'][0]

        if chance >= 50:
            await ctx.send(f"🌧️ PUTA QUE PARIU VAI CHOVER SIM  ({chance}% de chance) https://tenor.com/view/jose-mourinho-celebration-nobmakis-confetti-gif-12372464465630294612")
        elif 20 <= chance < 50:
            await ctx.send(f"🤔 talvez... ({chance}% de chance)\nhttps://cdn.discordapp.com/attachments/1359012678097571902/1359346468187668621/ssstwitter.com_1744163841770.mp4")
        else:
            video = random.choice(chuva_videos)
            await ctx.send(f"☀️ vai ter chuva não betinha! ({chance}% de chance)\n{video}")
    except Exception as e:
        print("Erro ao verificar previsão do tempo:", e)
        await ctx.send("❌ Não consegui prever a chuva agora, puregues...")

@bot.event
async def on_message(message):
    if bot.user in message.mentions and not message.author.bot:
        prompt = f"seja um bot babaca com as pessoas, e seja meio doidinho da cabeça e seja tipo um tio do zap zap, puregues: {message.content}"
        try:
            response = model.generate_content(prompt)
            resposta_texto = response.text.strip() if hasattr(response, 'text') else "🤖 Não consegui pensar em nada agora, puregues!"
            await message.channel.send(resposta_texto)
        except Exception as e:
            print("Erro ao usar Gemini:", e)
            await message.channel.send("🧠 vai se fuder puregues.")
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
