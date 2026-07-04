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
client = discord.Client(intents=intents)

mensajes_lol = {}
inscritos = {1: [], 2: [], 3: [], 4: []}

class BotonesLOL(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="1", style=discord.ButtonStyle.primary, custom_id="grupo_1"))
        self.add_item(Button(label="2", style=discord.ButtonStyle.primary, custom_id="grupo_2"))
        self.add_item(Button(label="3", style=discord.ButtonStyle.primary, custom_id="grupo_3"))
        self.add_item(Button(label="4", style=discord.ButtonStyle.primary, custom_id="grupo_4"))

@tasks.loop(minutes=1)
async def reloj_lol():
    now = datetime.datetime.now(TIMEZONE)
    # CADA 2 HORAS EN PUNTO
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
                await mensajes_lol[canal_id].edit(content=f"@everyone **LOL {nombre_canal}**", embed=embed, view=BotonesLOL())
            else:
                msg = await canal.send(f"@everyone **LOL {nombre_canal}**", embed=embed, view=BotonesLOL())
                mensajes_lol[canal_id] = msg

def crear_embed(now, nombre_canal):
    hora_inicio = (now + datetime.timedelta(hours=1)).strftime("%H:%M")
    hora_fin = (now + datetime.timedelta(hours=2)).strftime("%H:%M")
    fecha = now.strftime("%d/%m/%y")

    desc = f"**Event Info:**\n📅 {fecha}\n🕒 {hora_inicio} - {hora_fin}\n\n"
    desc += "**Description:**\nJoin team and wait for invite\n"

    for i in range(1, 5):
        menciones = [f"<@{m}>" for m in inscritos[i]]
        if not menciones: menciones = ["-"]
        desc += f"\n**Team {i} 60+ (channel {i+1}) ({len(inscritos[i])}/6)**\n" + "\n".join(menciones) + "\n-"

    total = sum(len(v) for v in inscritos.values())
    desc += f"\n\nSign ups: Total: {total} - Role: 0 - Status: 0"

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
    if message.content == "!testlol":
        await message.channel.send("Probando...")
        await publicar_lol(datetime.datetime.now(TIMEZONE))

@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data["custom_id"].startswith("grupo_"):
        grupo = int(interaction.data["custom_id"].split("_")[1])
        user_id = interaction.user.id

        # TOGGLE: Si ya esta, lo quita. Si no esta, lo mete
        if user_id in inscritos[grupo]:
            inscritos[grupo].remove(user_id)
            await interaction.response.send_message(f"Te saliste del Team {grupo}", ephemeral=True)
        else:
            # primero lo quito de otros teams
            for g in inscritos:
                if user_id in inscritos[g]:
                    inscritos[g].remove(user_id)
            if len(inscritos[grupo]) < 6:
                inscritos[grupo].append(user_id)
                await interaction.response.send_message(f"Te uniste al Team {grupo}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Team {grupo} Full", ephemeral=True)

        await actualizar_embed()

client.run(TOKEN)
