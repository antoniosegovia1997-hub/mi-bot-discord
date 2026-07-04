import discord
from discord.ui import View, Button
import datetime
import os
from discord.ext import tasks

TOKEN = os.getenv("TOKEN")
CANALES_AVISO_ID = {
    1512527404914970856: "C30",
    1512527470111490148: "C60",
    1512527491850436690: "C80"
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

mensajes_lol = {}
inscritos = {1: [], 2: [], 3: [], 4: []}

NOMBRES_TEAM = {
    1: "TEAM RATAS",
    2: "TEAM PRINCESOS",
    3: "TEAM LESBIANO",
    4: "TEAM NOSLEGENDS"
}

# ZONAS HORARIAS
TZ_ESPANA = datetime.timezone(datetime.timedelta(hours=2))
TZ_VENEZUELA = datetime.timezone(datetime.timedelta(hours=-4))
TZ_COLOMBIA = datetime.timezone(datetime.timedelta(hours=-5))

class BotonesLOL(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="TEAM RATAS", style=discord.ButtonStyle.danger, custom_id="grupo_1"))
        self.add_item(Button(label="TEAM PRINCESOS", style=discord.ButtonStyle.primary, custom_id="grupo_2"))
        self.add_item(Button(label="TEAM LESBIANO", style=discord.ButtonStyle.success, custom_id="grupo_3"))
        self.add_item(Button(label="TEAM NOSLEGENDS", style=discord.ButtonStyle.secondary, custom_id="grupo_4"))

@tasks.loop(minutes=1)
async def reloj_lol():
    now_es = datetime.datetime.now(TZ_ESPANA)
    # Publica cada 2 horas a las 17 min: 00:17, 02:17, 04:17...
    if now_es.minute == 17 and now_es.hour % 2 == 0:
        print(f"Publicando automaticamente a las {now_es.strftime('%H:%M')} ES")
        await publicar_lol(now_es.astimezone(datetime.timezone.utc))

@tasks.loop(hours=1)
async def keep_alive():
    print("Bot vivo") # Esto evita que Railway lo mate

async def publicar_lol(now_utc):
    global inscritos
    inscritos = {1: [], 2: [], 3: [], 4: []}

    for canal_id, nombre_canal in CANALES_AVISO_ID.items():
        canal = client.get_channel(canal_id)
        if canal:
            embed = crear_embed(now_utc, nombre_canal)
            if canal_id in mensajes_lol:
                await mensajes_lol[canal_id].edit(content=f"@everyone **LOL {nombre_canal} - INSCRIPCIONES ABIERTAS**", embed=embed, view=BotonesLOL())
            else:
                msg = await canal.send(f"@everyone **LOL {nombre_canal} - INSCRIPCIONES ABIERTAS**", embed=embed, view=BotonesLOL())
                mensajes_lol[canal_id] = msg

def crear_embed(now_utc, nombre_canal):
    # TOMAMOS HORA ESPAÑA Y LA REDONDEAMOS A LA HORA PAR
    hora_actual_es = now_utc.astimezone(TZ_ESPANA)
    
    # Si son las 12:17, la hora del evento es 12:00
    # Si son las 13:17, la hora del evento es 14:00
    hora_evento_es = hora_actual_es.replace(minute=0, second=0, microsecond=0)
    if hora_actual_es.hour % 2!= 0:
        hora_evento_es = hora_evento_es + datetime.timedelta(hours=1)

    # El evento dura 2 horas
    hora_fin_es = hora_evento_es + datetime.timedelta(hours=2)

    # Convertir a UTC y otros países
    hora_inicio_utc = hora_evento_es.astimezone(datetime.timezone.utc)
    hora_fin_utc = hora_fin_es.astimezone(datetime.timezone.utc)
    
    hora_inicio_ve = hora_evento_es.astimezone(TZ_VENEZUELA)
    hora_fin_ve = hora_fin_es.astimezone(TZ_VENEZUELA)

    hora_inicio_co = hora_evento_es.astimezone(TZ_COLOMBIA)
    hora_fin_co = hora_fin_es.astimezone(TZ_COLOMBIA)

    fecha = hora_evento_es.strftime("%d/%m/%y")

    desc = f"**Info del Evento:**\n📅 {fecha}\n\n"
    desc += f"🇪🇸 **ESPAÑA:** {hora_evento_es.strftime('%H:%M')} - {hora_fin_es.strftime('%H:%M')}\n"
    desc += f"🇻🇪 **VENEZUELA:** {hora_inicio_ve.strftime('%H:%M')} - {hora_fin_ve.strftime('%H:%M')}\n"
    desc += f"🇨🇴 **COLOMBIA:** {hora_inicio_co.strftime('%H:%M')} - {hora_fin_co.strftime('%H:%M')}\n\n"
    
    desc += "**Descripción:**\n🔥 VER TIK TOKS NO TE VA A AYUDAR A SUBIR DE NIVEL UNETE!! 🔥\n"

    for i in range(1, 5):
        menciones = []
        for user_id in inscritos[i]:
            user = client.get_user(user_id)
            if user:
                menciones.append(f"<@{user_id}>")
            else:
                menciones.append(f"Usuario {user_id}")

        if not menciones: menciones = ["-"]
        
        canal_voz = i + 1
        desc += f"\n**{NOMBRES_TEAM[i]} ({nombre_canal}) - (ch{canal_voz}) ({len(inscritos[i])}/6)**\n" + "\n".join(menciones) + "\n"

    total = sum(len(v) for v in inscritos.values())
    desc += f"\n**Total Inscritos: {total}/24**"

    embed = discord.Embed(title=f"LOL {nombre_canal}", description=desc, color=0xff0000)
    return embed

async def actualizar_embed():
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    for canal_id, nombre_canal in CANALES_AVISO_ID.items():
        if canal_id in mensajes_lol:
            embed = crear_embed(now_utc, nombre_canal)
            await mensajes_lol[canal_id].edit(embed=embed)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    reloj_lol.start()
    keep_alive.start()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content == "!lolnuevo":
        await message.channel.send("✅ Publicando LOL en C30, C60 y C80...")
        await publicar_lol(datetime.datetime.now(datetime.timezone.utc))

@client.event
async def on_interaction(interaction: discord.Interaction):
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
                await interaction.response.send_message(f"{NOMBRES_TEAM[grupo]} Lleno", ephemeral=True)

        await actualizar_embed()

client.run(TOKEN)
