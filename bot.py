import discord
from discord.ext import commands, tasks
import datetime, os, pytz

intents = discord.Intents.default(); intents.message_content = True; intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")
CANALES = {"C30": int(os.getenv("C30_CHANNEL_ID")), "C60": int(os.getenv("C60_CHANNEL_ID")), "C80": int(os.getenv("C80_CHANNEL_ID"))}
TZ_ESPANA = pytz.timezone("Europe/Madrid"); TZ_VENEZUELA = pytz.timezone("America/Caracas"); TZ_COLOMBIA = pytz.timezone("America/Bogota")
TEAMS = ["RATAS", "PRINCESOS", "LESBIANO", "NOSLEGENDS"]
inscritos = {c: {team: [] for team in TEAMS} for c in CANALES.keys()}

def crear_embed(nombre_canal, hora_pub):
    h1 = hora_pub + datetime.timedelta(hours=1); h2 = h1 + datetime.timedelta(hours=1)
    fecha = h1.strftime("%d/%m/%y")
    h1_ve = h1.astimezone(TZ_VENEZUELA); h2_ve = h2.astimezone(TZ_VENEZUELA)
    h1_co = h1.astimezone(TZ_COLOMBIA); h2_co = h2.astimezone(TZ_COLOMBIA)

    embed = discord.Embed(title=f"LOL {nombre_canal}", color=0xE74C3C)
    embed.add_field(name="Info del Evento:", value=f"📅 {fecha}\n🇪🇸 ESPAÑA: {h1.strftime('%H:%M')} - {h2.strftime('%H:%M')}\n🇻🇪 VENEZUELA: {h1_ve.strftime('%H:%M')} - {h2_ve.strftime('%H:%M')}\n🇨🇴 COLOMBIA: {h1_co.strftime('%H:%M')} - {h2_co.strftime('%H:%M')}", inline=False)
    embed.add_field(name="Descripción:", value="🔥 VER TIK TOKS NO TE VA A AYUDAR A SUBIR DE NIVEL UNETE!! 🔥", inline=False)

    total = 0
    for i, team in enumerate(TEAMS):
        lista = inscritos[nombre_canal] # ARREGLADO
        total += len(lista)
        menciones = "\n".join([f"<@{u}>" for u in lista]) if lista else "-"
        embed.add_field(name=f"TEAM {team} ({nombre_canal}) - (ch{i+2}) ({len(lista)}/6)", value=menciones, inline=False)

    embed.set_footer(text=f"Total Inscritos: {total}/24")
    return embed

class ViewBot(discord.ui.View):
    def __init__(self, canal):
        super().__init__(timeout=None); self.canal = canal
        for team in TEAMS:
            style = discord.ButtonStyle.danger if team=="RATAS" else discord.ButtonStyle.primary if team=="PRINCESOS" else discord.ButtonStyle.success if team=="LESBIANO" else discord.ButtonStyle.secondary
            btn = discord.ui.Button(label=f"TEAM {team}", style=style)
            btn.callback = self.make_callback(team)
            self.add_item(btn)

    def make_callback(self, team):
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            salio = False

            # ARREGLADO: AHORA SÍ RECORRE CADA TEAM
            for t in TEAMS:
                if user_id in inscritos[self.canal]:
                    inscritos[self.canal].remove(user_id)
                    if t == team: salio = True

            if not salio and len(inscritos[self.canal]) < 6:
                inscritos[self.canal].append(user_id)

            hora_msg = interaction.message.embeds[0].timestamp.replace(tzinfo=pytz.utc).astimezone(TZ_ESPANA) - datetime.timedelta(hours=1)
            await interaction.message.edit(embed=crear_embed(self.canal, hora_msg), view=ViewBot(self.canal))
            await interaction.response.send_message("Listo", ephemeral=True)
        return callback

async def publicar(nombre_canal, hora_forzada):
    channel = client.get_channel(CANALES[nombre_canal])
    inscritos[nombre_canal] = {team: [] for team in TEAMS}
    embed = crear_embed(nombre_canal, hora_forzada)
    await channel.send(content=f"**LOL {nombre_canal} - INSCRIPCIONES ABIERTAS**", embed=embed, view=ViewBot(nombre_canal))

@client.event
async def on_ready():
    print('CONECTADO')
    now = datetime.datetime.now(TZ_ESPANA).replace(minute=0, second=0, microsecond=0)
    for c in CANALES.keys(): await publicar(c, now)
    reloj.start()

@tasks.loop(minutes=1)
async def reloj():
    now = datetime.datetime.now(TZ_ESPANA)
    if now.minute == 0 and now.hour % 2 == 0:
        for c in CANALES.keys(): await publicar(c, now)

client.run(TOKEN)
