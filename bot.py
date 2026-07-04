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
TIMEZONE = datetime.timezone(datetime.timedelta(hours=-5))

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

class BotonesLOL(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="TEAM RATAS", style=discord.ButtonStyle.danger, custom_id="grupo_1"))
        self.add_item(Button(label="TEAM PRINCESOS", style=discord.ButtonStyle.primary, custom_id="grupo_2"))
        self.add_item(Button(label="TEAM LESBIANO", style=discord.ButtonStyle.success, custom_id="grupo_3"))
        self.add_item(Button(label="TEAM NOSLEGENDS", style=discord.ButtonStyle.secondary, custom_id="grupo_4"))

@tasks.loop(minutes=1)
async def reloj_lol():
    now = datetime.datetime.now(TIMEZONE)
    if now.minute == 0 and now.hour % 2 == 0:
        await publicar_lol(now)

async def publicar_lol(now):
    global inscritos
    inscritos = {1: [], 2: [], 3: [], 4: []}

    for canal_id, nombre_canal in CANALES_AVISO_ID.items():
        canal = client.get_channel(canal_id)
        if canal:
            embed = crear_embed(now, nombre_canal)
            if canal_id in mensajes_lol:
                await mensajes_lol[canal_id].edit(content=f"@everyone **LOL {nombre_canal} - INSCRIPCIONES ABIERTAS**", embed=embed, view=BotonesLOL())
            else:
                msg = await canal.send(f"@everyone **LOL {nombre_canal} - INSCRIPCIONES ABIERTAS**", embed=embed, view=BotonesLOL())
                mensajes_lol[canal_id] = msg

def crear_embed(now, nombre_canal):
    # CALCULO HORA AUTOMATICA
    hora_actual_par = now.replace(minute=0, second=0, microsecond=0)
    if hora_actual_par.hour % 2!= 0:
        hora_actual_par = hora_actual_par + datetime.timedelta(hours=1)

    hora_inicio = hora_actual_par + datetime.timedelta(hours=1)
    hora_fin = hora_actual_par + datetime.timedelta(hours=2)

    fecha = now.strftime("%d/%m/%y")

    desc = f"**Info del Evento:**\n📅 {fecha}\n🕒 {hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}\n\n"
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
        desc += f"\n**{NOMBRES_TEAM[i]} ({nombre_canal}) - Canal Voz {i} ({len(inscritos[i])}/6)**\n" + "\n".join(menciones) + "\n"

    total = sum(len(v) for v in inscritos.values())
    desc += f"\n**Total Inscritos: {total}/24**"

    embed = discord.Embed(title=f"LOL {nombre_canal}", description=desc, color=0xff0000)
    return embed

async def actualizar_embed():
    for canal_id, nombre_canal in CANALES_AVISO_ID.items():
        if canal_id in mensajes_lol:
            embed = crear_embed(datetime.datetime.now(TIMEZONE), nombre_canal)
            await mensajes_lol[canal_id].edit(embed=embed)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    reloj_lol.start()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content == "!lolnuevo":
        await message.channel.send("✅ Publicando LOL en C30, C60 y C80...")
        await publicar_lol(datetime.datetime.now(TIMEZONE))

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
