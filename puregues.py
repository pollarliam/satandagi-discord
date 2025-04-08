import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import yt_dlp
import google.generativeai as genai

# Carrega variáveis do .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configura a API do Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Intents do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Variáveis globais
looping = False
last_url = None

@bot.event
async def on_ready():
    print(f'🤖 Bot {bot.user.name} está online!')
    canal = bot.get_channel(1359012678097571902)
    if canal:
        await canal.send("oi puregues")
    else:
        print("⚠️ Canal não encontrado.")

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
async def play(ctx, url: str = None):
    global last_url

    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz, puregues.")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    if url:
        last_url = url
    elif not last_url:
        await ctx.send("❌ Nenhuma música foi tocada ainda para repetir, puregues!")
        return

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
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(last_url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

    def after_playing(error):
        if looping:
            fut = asyncio.run_coroutine_threadsafe(play(ctx), bot.loop)
            try:
                fut.result()
            except Exception as e:
                print("Erro ao repetir música:", e)

    vc.play(discord.FFmpegPCMAudio(source=filename), after=after_playing)
    await ctx.send(f"🎶 Tocando: {info['title']}")

@bot.command(name="stop")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Saí do canal de voz, puregues.")
    else:
        await ctx.send("❌ Não estou em nenhum canal de voz.")

@bot.event
async def on_message(message):
    if bot.user in message.mentions and not message.author.bot:
        prompt = f"imita a personagem Ayumu Osaka Kasuga de Azumanga Daiohas: {message.content}"

        try:
            response = model.generate_content(prompt)
            resposta_texto = response.text.strip() if hasattr(response, 'text') else "🤖 Não consegui pensar em nada agora, puregues!"
            await message.channel.send(resposta_texto)
        except Exception as e:
            print("Erro ao usar Gemini:", e)
            await message.channel.send("🧠 Deu tilt no meu cérebro, puregues... tenta de novo.")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
