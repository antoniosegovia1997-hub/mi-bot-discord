import discord
from discord.ext import commands, tasks
import datetime
import os
import pytz

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")
C30_CHANNEL_ID = int(os.getenv("C30_CHANNEL_ID"))
C60_CHANNEL_ID = int(os.getenv("C60_CHANNEL_ID"))
C80_CHANNEL_ID = int(os.getenv("C80_CHANNEL_ID"))
CANALES = {"C30": C30_CHANNEL_ID, "C60": C60_CHANNEL_ID, "C80": C80_CHANNEL_ID}

TZ_ESPANA = pytz.timezone("Europe/Madrid")
TZ_VENEZUELA = pytz.timezone("America/Caracas")
TZ_COLOMBIA = pytz.timezone("America/Bogota")
TEAMS = ["RATAS", "PRINCESOS", "LESBIANO", "NOSLEGENDS"]
inscritos = {c: {team: [] for team in TEAMS} for c in CANALES.keys()}
mensaje_ids = {}

def reset_inscritos(canal): inscritos[canal] = {team: [] for team in TEAMS}

async def crear_embed(nombre_canal, hora_pub):
    h1 = hora_pub + datetime.timedelta(hours=1)
    h2 = h1 + datetime.timedelta(hours=1)
    fecha = h1.strftime("%d/%m/%y")
    h1_ve, h2_ve = h1.astimezone(TZ_VENEZUELA), h2.astimezone(TZ_VENEZUELA)
    h1_co, h2_co = h1.astimezone(TZ_COLOMBIA), h2.astimezone(TZ_COLOMBIA)

    embed = discord.Embed(title=f"LOL {nombre_canal} - INSCRIPCIONES ABIERTAS", color=0xff0000)
    embed.add_field(name="Info del Evento:", value=f"📅 {fecha}", inline=False)
    embed.add_field(name="", value=f"🇪🇸 ESPAÑA: {h1.strftime('%H:%M')} - {h2.strftime('%H:%M')}\n🇻🇪 VENEZUELA: {h1_ve.strftime('%H:%M')} - {h2_ve.strftime('%H:%M')}\n🇨🇴 COLOMBIA: {h1_co.strftime('%H:%M')} - {h2_co.strftime('%H:%M')}", inline=False)
    embed.add_field(name="Descripción:", value="🔥 VER TIK TOKS NO TE VA A AYUDAR A SUBIR DE NIVEL UNETE!! 🔥", inline=False)

    total = 0
    for i, team in enumerate(TEAMS):
        lista = inscritos[nombre_canal]
        total += len(lista)
        texto = "\n".join([f"<@{u}>" for u in lista]) if lista else "-"
        embed.add_field(name=f"TEAM {team} ({nombre_canal}) - (ch{i+2}) ({len(lista)}/6)", value=texto, inline=False)
    embed.add_field(name=f"Total Inscritos: {total}/24", value="", inline=False)

    view = discord.ui.View(timeout=None)
    for team in TEAMS:
        style = discord.ButtonStyle.red if team=="RATAS" else discord.ButtonStyle.blurple if team=="PRINCESOS" else discord.ButtonStyle.green if team=="LESBIANO" else discord.ButtonStyle.grey
        view.add_item(discord.ui.Button(label=f"TEAM {team}", style=style, custom_id=f"{nombre_canal}_{team}"))
    return embed, view

async def publicar(nombre_canal, hora_forzada):
    channel = client.get_channel(CANALES[nombre_canal])
    reset_inscritos(nombre_canal)
    embed, view = await crear_embed(nombre_canal, hora_forzada)
    msg = await channel.send(embed=embed, view=view) # <- QUITÉ EL @everyone
    mensaje_ids[nombre_canal] = msg.id

@client.event
async def on_ready():
    print(f'CONECTADO')
    hora_18 = datetime.datetime.now(TZ_ESPANA).replace(hour=18, minute=0)
    for c in CANALES.keys(): await publicar(c, hora_18)
    reloj.start()

@tasks.loop(minutes=1)
async def reloj():
    now = datetime.datetime.now(TZ_ESPANA)
    if now.minute == 0 and now.hour % 2 == 0:
        for c in CANALES.keys(): await publicar(c, now)

@client.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        canal, team = interaction.data["custom_id"].split("_")
        user_id = interaction.user.id
        for t in TEAMS:
            if user_id in inscritos[canal][t]: inscritos[canal][t].remove(user_id)
        if len(inscritos[canal]) < 6: inscritos[canal].append(user_id)
        embed, view = await crear_embed(canal, interaction.message.created_at.astimezone(TZ_ESPANA) - datetime.timedelta(hours=1))
        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.defer()

client.run(TOKEN)
