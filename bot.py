import discord
from discord.ui import View, Button
from discord.ext import tasks
from datetime import datetime
import pytz
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

# === CONFIGURA ESTO ===
CANAL_AVISO_ID = 1512527404914970856 # <-- CANAL DE AVISOS c30
SALAS = {
    1: {"canal_id": 1512527404914970856, "nombre": "Aquí es donde los guerreros nacen", "emoji": "⚔️"}, # c30
    2: {"canal_id": 1512527470111490148, "nombre": "Zona de cornudos", "emoji": "😈"}, # c60
    3: {"canal_id": 1512527491850436690, "nombre": "Donde los cornudos se revelan", "emoji": "🔥"} # c80
}
MAX_JUGADORES = 4
TIMEZONE = pytz.timezone("Europe/Madrid")
TOKEN = os.getenv("TOKEN") # Para Railway
# ======================

inscritos = {1: [], 2: [], 3: []}
mensaje_lol = None
apuntes_abiertos = False

class BotonesLOL(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Sala 1", emoji="⚔️", style=discord.ButtonStyle.primary, custom_id="sala_1")
    async def sala1(self, interaction: discord.Interaction, button: Button):
        await self.apuntar(interaction, 1)

    @discord.ui.button(label="Sala 2", emoji="😈", style=discord.ButtonStyle.secondary, custom_id="sala_2")
    async def sala2(self, interaction: discord.Interaction, button: Button):
        await self.apuntar(interaction, 2)

    @discord.ui.button(label="Sala 3", emoji="🔥", style=discord.ButtonStyle.danger, custom_id="sala_3")
    async def sala3(self, interaction: discord.Interaction, button: Button):
        await self.apuntar(interaction, 3)

    @discord.ui.button(label="Desapuntarme", emoji="❌", style=discord.ButtonStyle.danger, row=1)
    async def desapuntarse(self, interaction: discord.Interaction, button: Button):
        if not apuntes_abiertos:
            return await interaction.response.send_message("❌ Los apuntes están cerrados.", ephemeral=True)
        user = interaction.user
        for sala, lista in inscritos.items():
            if user.id in lista:
                lista.remove(user.id)
                await interaction.response.send_message("Te has desapuntado.", ephemeral=True)
                return await actualizar_embed()
        await interaction.response.send_message("No estabas apuntado.", ephemeral=True)

    async def apuntar(self, interaction, sala_elegida):
        if not apuntes_abiertos:
            return await interaction.response.send_message("❌ Los apuntes están cerrados.", ephemeral=True)
        user = interaction.user
        for lista in inscritos.values():
            if user.id in lista: lista.remove(user.id)
        if len(inscritos[sala_elegida]) >= MAX_JUGADORES:
            return await interaction.response.send_message(f"❌ La **Sala {sala_elegida}** está llena.", ephemeral=True)
        inscritos[sala_elegida].append(user.id)
        await interaction.response.send_message(f"✅ Apuntado a **Sala {sala_elegida}: {SALAS[sala_elegida]['nombre']}**", ephemeral=True)
        await actualizar_embed()

async def actualizar_embed():
    global mensaje_lol
    if not mensaje_lol: return
    total = sum(len(v) for v in inscritos.values())
    fecha = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
    desc = f"> **\"La exp no se farmea viendo TikToks\"**\n> **Regla:** Pica tu sala 1 vez. Solo se cambia para equilibrar.\n\n"
    for i in range(1, 4):
        menciones = " ".join([f"<@{uid}>" for uid in inscritos[i]]) if inscritos[i] else "-"
        desc += f"**[SALA {i}] | {len(inscritos[i])}/{MAX_JUGADORES}**\n**{SALAS[i]['nombre']}**\n{menciones}\n\n"
    desc += f"─────────────────────────────────\n**Leveando: {total}/12** | **ID:** #{datetime.now().strftime('%H%M')}"
    embed = discord.Embed(title="⚔️ LOL 60 - MAPA DE LEVEO ⚔️", description=desc, color=0xff5500, timestamp=datetime.now(TIMEZONE))
    embed.set_footer(text=f"P.D: Si no te apuntas, sigue con TikTok. El 99 espera. | {fecha}")
    await mensaje_lol.edit(embed=embed, view=BotonesLOL())

@tasks.loop(minutes=1)
async def reloj_lol():
    global mensaje_lol, apuntes_abiertos, inscritos
    now = datetime.now(TIMEZONE)
    canal = client.get_channel(CANAL_AVISO_ID)
    if not canal: return

    # AVISO CADA 2 HORAS EN PUNTO 24/7
if now.minute == 0 and now.hour % 2 == 0 and not mensaje_lol:
    inscritos = {1: [], 2: [], 3: []}
    apuntes_abiertos = True
    embed = discord.Embed(title="⚔️ LOL 60 - MAPA DE LEVEO ⚔️", description="Cargando...", color=0xff5500)
    mensaje_lol = await canal.send("@everyone ⚔️ **ABREN APUNTES PARA EL LOL** ⚔️", embed=embed, view=BotonesLOL())
    await actualizar_embed()

    # CIERRA 1 HORA DESPUES
if now.minute == 0 and (now.hour - 1) % 2 == 0 and apuntes_abiertos:
        apuntes_abiertos = False
        embed = discord.Embed(title="🔒 LOL CERRADO", description="El mapa de leveo ha empezado. ¡Suerte, gasolinas!", color=0x000)
        await mensaje_lol.edit(embed=embed, view=None)
        mensaje_lol = None

@client.event
async def on_ready():
    print(f"Bot 24/7 activo como {client.user}")
    reloj_lol.start()

client.run(TOKEN)
