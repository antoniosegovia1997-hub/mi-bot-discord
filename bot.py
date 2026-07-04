import discord
from discord.ext import commands, tasks
import datetime, os, pytz

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")
CANALES = {
    "C30": int(os.getenv("C30_CHANNEL_ID")),
    "C60": int(os.getenv("C60_CHANNEL_ID")),
    "C80": int(os.getenv("C80_CHANNEL_ID"))
}

TZ_ESPANA = pytz.timezone("Europe/Madrid")
TZ_VENEZUELA = pytz.timezone("America/Caracas")
TZ_COLOMBIA = pytz.timezone("America/Bogota")

TEAMS = ["RATAS", "PRINCESOS", "LESBIANO", "NOSLEGENDS"]
inscritos = {}

def reset_canal(canal):
    inscritos[canal] = []

def crear_embed(nombre_canal, hora_pub):
    h1 = hora_pub + datetime.timedelta(hours=3) # +3H IGUAL QUE TU FOTO
    h2 = h1 + datetime.timedelta(hours=1)
    fecha = h1.strftime("%d/%m/%y")

    h1_ve = h1.astimezone(TZ_VENEZUELA)
    h2_ve = h2.astimezone(TZ_VENEZUELA)
    h1_co = h1.astimezone(TZ_COLOMBIA)
    h2_co = h2.astimezone(TZ_COLOMBIA)

    embed = discord.Embed(title=f"LOL {nombre_canal}", color=0xE74C3C)
    embed.add_field(
        name="Info del Evento:",
        value=f"📅 {fecha}\n🇪🇸 ESPAÑA: {h1.strftime('%H:%M')} - {h2.strftime('%H:%M')}\n🇻🇪 VENEZUELA: {h1_ve.strftime('%H:%M')} - {h2_ve.strftime('%H:%M')}\n🇨🇴 COLOMBIA: {h1_co.strftime('%H:%M')} - {h2_co.strftime('%H:%M')}",
        inline=False
    )
    embed.add_field(name="Descripción:", value="🔥 VER TIK TOKS NO TE VA A AYUDAR A SUBIR DE NIVEL UNETE!! 🔥", inline=False)

    total = len(inscritos[nombre_canal])
    for i, team in enumerate(TEAMS):
        team_lista = [u for u in inscritos[nombre_canal] if u[1] == team]
        menciones = "\n".join([f"<@{u[0]}>" for u in team_lista]) if team_lista else "-"
        embed.add_field(name=f"TEAM {team} ({nombre_canal}) - (ch{i+2}) ({len(team_lista)}/6)", value=menciones, inline=False)

    embed.set_footer(text=f"Total Inscritos: {total}/24")
    return embed

class ViewBot(discord.ui.View):
    def __init__(self, canal):
        super().__init__(timeout=None)
        self.canal = canal
        for team in TEAMS:
            if team == "RATAS": style = discord.ButtonStyle.danger
            elif team == "PRINCESOS": style = discord.ButtonStyle.primary
            elif team == "LESBIANO": style = discord.ButtonStyle.success
            else: style = discord.ButtonStyle.secondary

            btn = discord.ui.Button(label=f"TEAM {team}", style=style)
            btn.callback = self.make_callback(team)
            self.add_item(btn)

    def make_callback(self, team):
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            lista = inscritos[self.canal]

            # Quitar de todos los teams
            lista = [u for u in lista if u[0]!= user_id]

            # Ver si el team está lleno
            team_count = len([u for u in lista if u[1] == team])
            if team_count >= 6:
                await interaction.response.send_message(f"TEAM {team} LLENO", ephemeral=True)
                return

            lista.append((user_id, team))
            inscritos[self.canal] = lista

            hora_msg = datetime.datetime.now(TZ_ESPANA).replace(minute=0, second=0, microsecond=0)
            await interaction.message.edit(embed=crear_embed(self.canal, hora_msg), view=ViewBot(self.canal))
            await interaction.response.send_message(f"Te uniste a TEAM {team}", ephemeral=True)
        return callback

async def publicar(nombre_canal, hora_pub):
    channel = client.get_channel(CANALES[nombre_canal])
    reset_canal(nombre_canal)
    embed = crear_embed(nombre_canal, hora_pub)
    await channel.send(content=f"**LOL {nombre_canal} - INSCRIPCIONES ABIERTAS**", embed=embed, view=ViewBot(nombre_canal))

@client.event
async def on_ready():
    print(f'CONECTADO COMO {client.user}')
    now = datetime.datetime.now(TZ_ESPANA).replace(minute=0, second=0, microsecond=0)
    # Publicar los 3 canales al iniciar
    for c in CANALES.keys():
        await publicar(c, now)
    reloj.start()

@tasks.loop(minutes=1)
async def reloj():
    now = datetime.datetime.now(TZ_ESPANA)
    if now.minute == 0 and now.hour % 2 == 0: # 18:00, 20:00, 22:00...
        for c in CANALES.keys():
            await publicar(c, now)

client.run(TOKEN)
