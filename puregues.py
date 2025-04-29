import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import asyncio
import google.generativeai as genai
import requests
import random
import yt_dlp
from datetime import datetime
import replicate

# Carrega variáveis do .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Coordenadas de Guanambi - BA
LATITUDE = -14.2233
LONGITUDE = -42.7819

# Configura Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Configura Replicate
replicate.Client(api_token=REPLICATE_API_TOKEN)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
ultima_chance = 0
queue = []
looping = False
last_url = None

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
    "https://cdn.discordapp.com/attachments/901509560529997895/1360093700952424529/ssstwitter.com_1740593973016.mp4"    
]

chuva_confirmada_videos = [
    "https://cdn.discordapp.com/attachments/901509560529997895/1360101334644162741/Download_20.mp4",
    "https://cdn.discordapp.com/attachments/901509560529997895/1360100064248467518/ssstwitter.com_1744343514384.mp4",
    "https://cdn.discordapp.com/attachments/901509560529997895/1360102726133878794/pau-do-davibrito.mp4"
]

@bot.event
async def on_ready():
    print(f'🤖 Bot {bot.user.name} está online!')
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    atualizar_previsao.start()

@tasks.loop(minutes=1)
async def atualizar_previsao():
    global ultima_chance
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=precipitation_probability&forecast_days=1&timezone=America%2FSao_Paulo"
        response = requests.get(url)
        data = response.json()
        horas = data['hourly']['time']
        chances = data['hourly']['precipitation_probability']

        agora = datetime.now().strftime("%Y-%m-%dT%H:00")
        if agora in horas:
            indice = horas.index(agora)
            ultima_chance = chances[indice]
            print(f"Previsão atualizada: {ultima_chance}% para {agora}")
        else:
            print(f"Hora atual {agora} não encontrada na previsão.")
    except Exception as e:
        print("Erro ao atualizar previsão de chuva:", e)

@bot.command(name="chuva")
async def chuva(ctx):
    try:
        if ultima_chance >= 50:
            video = random.choice(chuva_confirmada_videos)
            await ctx.send(f"🌧️ Vai chover agora em Guanambi! ({ultima_chance}% de chance)\n{video}")
        elif 20 <= ultima_chance < 50:
            await ctx.send(f"🤔 talvez... ({ultima_chance}% de chance)\nhttps://cdn.discordapp.com/attachments/1359012678097571902/1359346468187668621/ssstwitter.com_1744163841770.mp4")
        else:
            video = random.choice(chuva_videos)
            await ctx.send(f"☀️ vai ter chuva não betinha! ({ultima_chance}% de chance)\n{video}")
    except Exception as e:
        print("Erro ao enviar previsão de chuva:", e)
        await ctx.send("❌ Não consegui prever a chuva agora, puregues...")

@bot.command(name="pure")
async def pure(ctx):
    await ctx.send("puregues")

@bot.command(name="chuca")
async def chuca(ctx):
    await ctx.send("🥺")

@bot.command(name="imagem")
async def imagem(ctx, *, prompt: str):
    try:
        output = replicate.run(
            "stability-ai/sdxl:8cf8a4e5b6b17dc6bfa7fbb9e24bfc4732d2a5ec0f02d5f50c2b9ab7b31d00b0",
            input={"prompt": prompt}
        )
        await ctx.send(f"🖼️ {output[0]}")
    except Exception as e:
        print("Erro ao gerar imagem:", e)
        await ctx.send("❌ Não consegui gerar a imagem, puregues!")

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
