import discord
from discord.ext import commands, tasks
import datetime
import os
import asyncio
import pytz # NUEVO

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

# TOKENS Y CANALES
TOKEN = os.getenv("TOKEN")
C30_CHANNEL_ID = int(os.getenv("C30_CHANNEL_ID"))
C60_CHANNEL_ID = int(os.getenv("C60_CHANNEL_ID"))
C80_CHANNEL_ID = int(os.getenv("C80_CHANNEL_ID"))
KEEP_ALIVE = os.getenv("KEEP_ALIVE")

# ZONAS HORARIAS REALES - ARREGLADO
TZ_ESPANA = pytz.timezone("Europe/Madrid")
TZ_VENEZUELA = pytz.timezone("America/Caracas")
TZ_COLOMBIA = pytz.timezone("America/Bogota")

# DATOS
NOMBRES_TEAM = {1: "C30", 2: "C60", 3: "C80"}
inscritos = {1: [], 2: [], 3: []}
mensaje_ids = {1: None, 2: None, 3: None}

async def crear_embed(grupo):
    embed = discord.Embed(
        title=f"📢 PARTIDA {NOMBRES_TEAM[grupo]}",
        description=f"Únete a la partida de {NOMBRES_TEAM[grupo]}",
        color=0x00ff00,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    lista = inscritos[grupo]
    if lista:
        texto = "\n".join([f"<@{user_id}>" for user_id in lista])
    else:
        texto = "Nadie inscrito aún"
    embed.add_field(name=f"Jugadores [{len(lista)}/6]", value=texto, inline=False)

    view = discord.ui.View(timeout=None)
    btn_unirse = discord.ui.Button(label="Unirse/Salir", style=discord.ButtonStyle.primary, custom_id=f"grupo_{grupo}")
    view.add_item(btn_unirse)
    return embed, view

async def actualizar_embed():
    for grupo, channel_id in [(1, C30_CHANNEL_ID), (2, C60_CHANNEL_ID), (3, C80_CHANNEL_ID)]:
        channel = client.get_channel(channel_id)
        if not channel: continue
        embed, view = await crear_embed(grupo)
        if mensaje_ids[grupo]:
            try:
                msg = await channel.fetch_message(mensaje_ids[grupo])
                await msg.edit(embed=embed, view=view)
            except:
                msg = await channel.send(embed=embed, view=view)
                mensaje_ids[grupo] = msg.id
        else:
            msg = await channel.send(embed=embed, view=view)
            mensaje_ids[grupo] = msg.id

async def publicar_lol(hora_utc):
    global inscritos, mensaje_ids
    inscritos = {1: [], 2: [], 3: []}
    mensaje_ids = {1: None, 2: None, 3: None}

    hora_es = hora_utc.astimezone(TZ_ESPANA)
    hora_ve = hora_utc.astimezone(TZ_VENEZUELA)
    hora_co = hora_utc.astimezone(TZ_COLOMBIA)

    texto_horas = f"**Horarios:**\n🇪🇸 España: {hora_es.strftime('%H:%M')}\n🇻🇪 Venezuela: {hora_ve.strftime('%H:%M')}\n🇨🇴 Colombia: {hora_co.strftime('%H:%M')}"

    for grupo, channel_id in [(1, C30_CHANNEL_ID), (2, C60_CHANNEL_ID), (3, C80_CHANNEL_ID)]:
        channel = client.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title=f"🔥 NUEVA PARTIDA {NOMBRES_TEAM[grupo]}",
                description=f"Se abre inscripción para {NOMBRES_TEAM[grupo]}\n\n{texto_horas}",
                color=0xff0000
            )
            await channel.send(content="@everyone", embed=embed)
    await actualizar_embed()
    print(f"Publicado correctamente a las {hora_es.strftime('%H:%M')} ES")

@client.event
async def on_ready():
    print(f'{client.user} conectado')
    reloj_lol.start()
    keep_alive.start()
    # NUEVO: RECUPERAR LAS 18:00 SI SE PERDIO
    now_es = datetime.datetime.now(TZ_ESPANA)
    if now_es.hour >= 18 and now_es.minute < 10: # Si son las 18:00-18:10 y no se publicó
        print("Recuperando publicación de las 18:00 perdida")
        await publicar_lol(now_es.replace(hour=18, minute=0, second=0, microsecond=0).astimezone(datetime.timezone.utc))

@tasks.loop(minutes=1)
async def reloj_lol():
    await client.wait_until_ready() # CLAVE PARA QUE NO FALLE
    now_es = datetime.datetime.now(TZ_ESPANA)
    if now_es.minute == 0 and now_es.hour % 2 == 0:
        print(f"Publicando automaticamente a las {now_es.strftime('%H:%M')} ES")
        await publicar_lol(now_es.astimezone(datetime.timezone.utc))

@tasks.loop(hours=1)
async def keep_alive():
    print(f"Bot vivo: {datetime.datetime.now(TZ_ESPANA).strftime('%H:%M:%S')} ES")

@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"].startswith("grupo_"):
            grupo = int(interaction.data["custom_id"].split("_")[1])
            user_id = interaction.user.id

            if user_id in inscritos[grupo]:
                inscritos[grupo].remove(user_id)
                await interaction.response.send_message(f"Te saliste de {NOMBRES_TEAM[grupo]}", ephemeral=True)
            else:
                for g in inscritos:
                    if user_id in inscritos[g]:
                        inscritos[g].remove(user_id)
                if len(inscritos[grupo]) < 6:
                    inscritos[grupo].append(user_id)
                    await interaction.response.send_message(f"Te uniste a {NOMBRES_TEAM[grupo]}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{NOMBRES_TEAM[grupo]} lleno", ephemeral=True)
            await actualizar_embed()

client.run(TOKEN)
