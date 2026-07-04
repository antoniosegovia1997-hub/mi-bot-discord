import discord
from discord.ext import commands, tasks
import datetime
import os
import pytz

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")
C30_CHANNEL_ID = int(os.getenv("C30_CHANNEL_ID"))
C60_CHANNEL_ID = int(os.getenv("C60_CHANNEL_ID"))
C80_CHANNEL_ID = int(os.getenv("C80_CHANNEL_ID"))

CANALES = {
    "C30": C30_CHANNEL_ID,
    "C60": C60_CHANNEL_ID,
    "C80": C80_CHANNEL_ID
}

TZ_ESPANA = pytz.timezone("Europe/Madrid")
TZ_VENEZUELA = pytz.timezone("America/Caracas")
TZ_COLOMBIA = pytz.timezone("America/Bogota")

TEAMS = ["RATAS", "PRINCESOS", "LESBIANO", "NOSLEGENDS"]
inscritos = {c: {team: [] for team in TEAMS} for c in CANALES.keys()}
mensaje_ids = {}

def reset_inscritos(canal):
    inscritos[canal] = {team: [] for team in TEAMS}

async def crear_embed(canal, nombre_canal):
    now_es = datetime.datetime.now(TZ_ESPANA)
    fecha = now_es.strftime("%d/%m/%y")

    hora_es = now_es.strftime("%H:%M")
    hora_ve = now_es.astimezone(TZ_VENEZUELA).strftime("%H:%M")
    hora_co = now_es.astimezone(TZ_COLOMBIA).strftime("%H:%M")

    hora_fin_es = (now_es + datetime.timedelta(hours=1)).strftime("%H:%M")
    hora_fin_ve = (now_es.astimezone(TZ_VENEZUELA) + datetime.timedelta(hours=1)).strftime("%H:%M")
    hora_fin_co = (now_es.astimezone(TZ_COLOMBIA) + datetime.timedelta(hours=1)).strftime("%H:%M")

    embed = discord.Embed(title=f"LOL {nombre_canal} - INSCRIPCIONES ABIERTAS", color=0xff0000)
    embed.add_field(name="Info del Evento:", value=f"📅 {fecha}", inline=False)
    embed.add_field(name="", value=f"🇪🇸 ESPAÑA: {hora_es} - {hora_fin_es}\n🇻🇪 VENEZUELA: {hora_ve} - {hora_fin_ve}\n🇨🇴 COLOMBIA: {hora_co} - {hora_fin_co}", inline=False)
    embed.add_field(name="Descripción:", value="🔥 VER TIK TOKS NO TE VA A AYUDAR A SUBIR DE NIVEL UNETE!! 🔥", inline=False)

    total = 0
    for team in TEAMS:
        lista = inscritos[nombre_canal][team]
        total += len(lista)
        texto = "\n".join([f"<@{u}>" for u in lista]) if lista else "-"
        embed.add_field(name=f"TEAM {team} ({nombre_canal}) - (ch{TEAMS.index(team)+2}) ({len(lista)}/6)", value=texto, inline=False)

    embed.add_field(name=f"Total Inscritos: {total}/24", value="", inline=False)

    view = discord.ui.View(timeout=None)
    for team in TEAMS:
        style = discord.ButtonStyle.red if team=="RATAS" else discord.ButtonStyle.blurple if team=="PRINCESOS" else discord.ButtonStyle.green if team=="LESBIANO" else discord.ButtonStyle.grey
        view.add_item(discord.ui.Button(label=f"TEAM {team}", style=style, custom_id=f"{nombre_canal}_{team}"))
    return embed, view

async def publicar(nombre_canal):
    canal_id = CANALES[nombre_canal]
    channel = client.get_channel(canal_id)
    if not channel:
        print(f"ERROR: NO ENCUENTRO CANAL {nombre_canal} ID: {canal_id}", flush=True)
        return
    reset_inscritos(nombre_canal)
    embed, view = await crear_embed(canal_id, nombre_canal)
    msg = await channel.send(content="@everyone", embed=embed, view=view)
    mensaje_ids[nombre_canal] = msg.id
    print(f"PUBLICADO {nombre_canal}", flush=True)

@client.event
async def on_ready():
    print(f'{client.user} CONECTADO', flush=True)

    # PUBLICAR YA LA DE LAS 18
    for c in CANALES.keys():
        await publicar(c)

    reloj.start()

@tasks.loop(minutes=1)
async def reloj():
    now_es = datetime.datetime.now(TZ_ESPANA)
    if now_es.minute == 0 and now_es.hour % 2 == 0:
        for c in CANALES.keys():
            await publicar(c)

@client.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        canal, team = interaction.data["custom_id"].split("_")
        user_id = interaction.user.id

        for t in TEAMS:
            if user_id in inscritos[canal][t]:
                inscritos[canal][t].remove(user_id)

        if len(inscritos[canal][team]) < 6:
            inscritos[canal][team].append(user_id)
            await interaction.response.send_message(f"Te uniste a TEAM {team}", ephemeral=True)
        else:
            await interaction.response.send_message(f"TEAM {team} LLENO", ephemeral=True)

        channel = client.get_channel(CANALES[canal])
        embed, view = await crear_embed(CANALES[canal], canal)
        await (await channel.fetch_message(mensaje_ids[canal])).edit(embed=embed, view=view)

client.run(TOKEN)
