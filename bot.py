import discord
from discord.ui import View, Button
import asyncio
import datetime
import os
from discord.ext import tasks

# CONFIG
TOKEN = os.getenv("TOKEN")
CANALES_AVISO_ID = [1512527404914970856, 1512527470111490148, 1512527491850436690] # c30, c60, c80
TIMEZONE = datetime.timezone(datetime.timedelta(hours=-5)) # Peru -5

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# VARIABLES GLOBALES
mensajes_lol = {} # guarda 1 mensaje por canal
inscritos = {1: [], 2: [], 3: []}
apuntes_abiertos = False

class BotonesLOL(View):
    def __init__(self):
        super().__init__(timeout=None)
        for i in range(1, 4):
            self.add_item(Button(label=f"Grupo {i}", style=discord.ButtonStyle.green, custom_id=f"grupo_{i}"))

    @discord.ui.button(label="Salir", style=discord.ButtonStyle.red, custom_id="salir")
    async def salir(self, interaction: discord.Interaction, button: Button):
        for g in inscritos:
            if interaction.user.id in inscritos[g]:
                inscritos[g].remove(interaction.user.id)
        await interaction.response.send_message("Te saliste de todos los grupos", ephemeral=True)
        await actualizar_embed()

@tasks.loop(minutes=1)
async def reloj_lol():
    global mensajes_lol, apuntes_abiertos, inscritos
    now = datetime.datetime.now(TIMEZONE)

    # AVISO CADA 2 HORAS EN PUNTO 24/7 EN c30, c60, c80
    if now.minute == 0 and now.hour % 2 == 0 and len(mensajes_lol) == 0:
        inscritos = {1: [], 2: [], 3: []}
        apuntes_abiertos = True
        embed = discord.Embed(title="⚔️ LOL 60 - MAPA DE LEVEO ⚔️", description="Cargando...", color=0xff5500)
        for canal_id in CANALES_AVISO_ID:
            canal = client.get_channel(canal_id)
            if canal:
                msg = await canal.send("@everyone ⚔️ **ABREN APUNTES PARA EL LOL** ⚔️", embed=embed, view=BotonesLOL())
                mensajes_lol[canal_id] = msg
        await actualizar_embed()
    
    # CIERRE DE APUNTES A LOS 30 MIN
    if now.minute == 30 and len(mensajes_lol) > 0:
        apuntes_abiertos = False
        for msg in mensajes_lol.values():
            await msg.edit(content="❌ **APUNTES CERRADOS** ❌", embed=None, view=None)
        mensajes_lol = {}

async def actualizar_embed():
    if len(mensajes_lol) == 0: return
    desc = ""
    for g, miembros in inscritos.items():
        menciones = [f"<@{m}>" for m in miembros]
        desc += f"**Grupo {g}** ({len(miembros)}/6):\n" + "\n".join(menciones) + "\n\n"
    embed = discord.Embed(title="⚔️ LOL 60 - MAPA DE LEVEO ⚔️", description=desc, color=0x00ff00)
    for msg in mensajes_lol.values():
        await msg.edit(embed=embed)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    reloj_lol.start()

@client.event
async def on_interaction(interaction: discord.Interaction):
    global apuntes_abiertos
    if not apuntes_abiertos: return
    if interaction.data["custom_id"].startswith("grupo_"):
        grupo = int(interaction.data["custom_id"].split("_")[1])
        for g in inscritos:
            if interaction.user.id in inscritos[g]:
                inscritos[g].remove(interaction.user.id)
        if len(inscritos[grupo]) < 6:
            inscritos[grupo].append(interaction.user.id)
        await interaction.response.send_message(f"Te apuntaste al Grupo {grupo}", ephemeral=True)
        await actualizar_embed()

client.run(TOKEN)
