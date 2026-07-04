import discord
from discord.ext import commands, tasks
import datetime
import os
import pytz
import sys

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")
C30_CHANNEL_ID = int(os.getenv("C30_CHANNEL_ID"))
C60_CHANNEL_ID = int(os.getenv("C60_CHANNEL_ID"))
C80_CHANNEL_ID = int(os.getenv("C80_CHANNEL_ID"))

TZ_ESPANA = pytz.timezone("Europe/Madrid")
TZ_VENEZUELA = pytz.timezone("America/Caracas")
TZ_COLOMBIA = pytz.timezone("America/Bogota")

NOMBRES_TEAM = {1: "C30", 2: "C60", 3: "C80"}
inscritos = {1: [], 2: [], 3: []}
mensaje_ids = {1: None, 2: None, 3: None}
ya_publico_1831 = False # PARA QUE SOLO LO HAGA 1 VEZ

async def crear_embed(grupo):
    embed = discord.Embed(title=f"📢 PARTIDA {NOMBRES_TEAM[grupo]}", description=f"Únete a la partida de {NOMBRES_TEAM[grupo]}", color=0x00ff00)
    lista = inscritos[grupo]
    texto = "\n".join([f"<@{user_id}>" for user_id in lista]) if lista else "Nadie inscrito aún"
    embed.add_field(name=f"Jugadores [{len(lista)}/6]", value=texto, inline=False)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Unirse/Salir", style=discord.ButtonStyle.primary, custom_id=f"grupo_{grupo}"))
    return embed, view

async def actualizar_embed():
    for grupo, channel_id in [(1, C30_CHANNEL_ID), (2, C60_CHANNEL_ID), (3, C80_CHANNEL_ID)]:
        channel = client.get_channel(channel_id)
        if not channel: continue
        embed, view = await crear_embed(grupo)
        if mensaje_ids[grupo]:
            try: await (await channel.fetch_message(mensaje_ids[grupo])).edit(embed=embed, view=view)
            except: msg = await channel.send(embed=embed, view=view); mensaje_ids[grupo] = msg.id
        else: msg = await channel.send(embed=embed, view=view); mensaje_ids[grupo] = msg.id

async def publicar_lol(hora_utc):
    global inscritos, mensaje_ids
    inscritos = {1: [], 2: [], 3: []}
    mensaje_ids = {1: None, 2: None, 3: None}
    hora_es = hora_utc.astimezone(TZ_ESPANA)
    texto_horas = f"**Horarios:**\n🇪🇸 España: {hora_es.strftime('%H:%M')}\n🇻🇪 Venezuela: {hora_utc.astimezone(TZ_VENEZUELA).strftime('%H:%M')}\n🇨🇴 Colombia: {hora_utc.astimezone(TZ_COLOMBIA).strftime('%H:%M')}"
    for grupo, channel_id in [(1, C30_CHANNEL_ID), (2, C60_CHANNEL_ID), (3, C80_CHANNEL_ID)]:
        channel = client.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title=f"🔥 NUEVA PARTIDA {NOMBRES_TEAM[grupo]}", description=f"Se abre inscripción para {NOMBRES_TEAM[grupo]}\n\n{texto_horas}", color=0xff0000)
            await channel.send(content="@everyone", embed=embed)
    await actualizar_embed()
    print(f"PUBLICADO A LAS {hora_es.strftime('%H:%M')} ES", flush=True)

@client.event
async def on_ready():
    print(f'{client.user} CONECTADO Y LISTO', flush=True)
    reloj_lol.start()

@tasks.loop(minutes=1)
async def reloj_lol():
    global ya_publico_1831
    await client.wait_until_ready()
    now_es = datetime.datetime.now(TZ_ESPANA)
    hora = now_es.hour
    minuto = now_es.minute

    # 1. PUBLICAR 18:31 SOLO 1 VEZ PARA RECUPERAR LA QUE SE PERDIO
    if hora == 18 and minuto == 31 and not ya_publico_1831:
        await publicar_lol(now_es.astimezone(datetime.timezone.utc))
        ya_publico_1831 = True
        print("RECUPERADO 18:31", flush=True)

    # 2. PUBLICAR NORMAL CADA 2 HORAS EN PUNTO: 20:00, 22:00, 00:00...
    if minuto == 0 and hora % 2 == 0:
        await publicar_lol(now_es.astimezone(datetime.timezone.utc))

@client.command()
async def publicar(ctx, hora:str):
    try:
        h, m = map(int, hora.split(":"))
        now_es = datetime.datetime.now(TZ_ESPANA)
        hora_forzada = now_es.replace(hour=h, minute=m, second=0, microsecond=0)
        await publicar_lol(hora_forzada.astimezone(datetime.timezone.utc))
        await ctx.send(f"✅ PUBLICADO A LAS {hora} ES")
    except Exception as e: await ctx.send(f"❌ ERROR: {e}")

@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data["custom_id"].startswith("grupo_"):
        grupo = int(interaction.data["custom_id"].split("_")[1]); user_id = interaction.user.id
        for g in inscritos:
            if user_id in inscritos[g]: inscritos[g].remove(user_id)
        if len(inscritos[grupo]) < 6: inscritos[grupo].append(user_id); await interaction.response.send_message(f"Te uniste a {NOMBRES_TEAM[grupo]}", ephemeral=True)
        else: await interaction.response.send_message(f"{NOMBRES_TEAM[grupo]} LLENO", ephemeral=True)
        await actualizar_embed()

client.run(TOKEN)
