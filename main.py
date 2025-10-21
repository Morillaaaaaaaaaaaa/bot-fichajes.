import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import datetime

# Lista de canales de los trabajadores
CANALES_TRABAJADORES = [
    1428906272542953573,
    1428906286971617402,
    1428906299030114345,
    1428906312061943898,
    1428906327220031691,
    1428906337391345794,
    1428906361944674314,
    1428906373143461899,
    1428906380454006970,
    1428906391816503336,
    1428906401983369236,
    1428906429376630935,
    1428906445390352536,
    1428906455473459343,
    1428906470875074622,
    1428906485794082877
]

# Canal donde se mostrará el ranking
CANAL_RANKING_ID = 1428919005032353792

# Archivo JSON donde se guardan las horas
ARCHIVO_HORAS = "horas_trabajadores.json"

# Cargar archivo o crear uno nuevo
if os.path.exists(ARCHIVO_HORAS):
    with open(ARCHIVO_HORAS, "r") as f:
        horas_trabajadores = json.load(f)
else:
    horas_trabajadores = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


class FichajeView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🟢 Ingreso", style=discord.ButtonStyle.success, custom_id="ingreso"))
        self.add_item(Button(label="🔴 Retirada", style=discord.ButtonStyle.danger, custom_id="retirada"))
        self.add_item(Button(label="📊 Horas totales", style=discord.ButtonStyle.primary, custom_id="horas"))


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    for guild in bot.guilds:
        for canal_id in CANALES_TRABAJADORES:
            canal = guild.get_channel(canal_id)
            if canal:
                # Eliminar mensajes anteriores del bot
                async for msg in canal.history(limit=10):
                    if msg.author == bot.user:
                        await msg.delete()

                # Enviar panel de fichaje
                view = FichajeView()
                embed = discord.Embed(
                    title="💼 Ministerio de Trabajo",
                    description="Sistema de fichaje del taller\nSelecciona una opción:",
                    color=0x3498db
                )
                await canal.send(embed=embed, view=view)
                print(f"📋 Panel enviado en #{canal.name}")


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data:
        return

    custom_id = interaction.data.get("custom_id")
    canal_id = str(interaction.channel.id)
    ahora = datetime.datetime.now()

    if canal_id not in horas_trabajadores:
        horas_trabajadores[canal_id] = {"ingreso": None, "total_minutos": 0}

    datos = horas_trabajadores[canal_id]

    if custom_id == "ingreso":
        if datos["ingreso"]:
            await interaction.response.send_message("⚠️ Ya habías fichado tu entrada.", ephemeral=True)
            return
        datos["ingreso"] = ahora.isoformat()
        await interaction.response.send_message("✅ Has fichado tu **entrada**.", ephemeral=True)

    elif custom_id == "retirada":
        if not datos["ingreso"]:
            await interaction.response.send_message("⚠️ No habías fichado entrada.", ephemeral=True)
            return
        inicio = datetime.datetime.fromisoformat(datos["ingreso"])
        minutos = (ahora - inicio).total_seconds() / 60  # 1 minuto = 1 hora simulada
        datos["total_minutos"] += minutos
        datos["ingreso"] = None
        await interaction.response.send_message(
            f"👋 Has fichado tu **salida**.\n🕒 Tiempo añadido: {minutos:.2f} horas.", ephemeral=True
        )
        await actualizar_ranking(interaction.guild)

    elif custom_id == "horas":
        if interaction.user.guild_permissions.administrator:
            total = datos["total_minutos"]
            await interaction.response.send_message(f"🕒 Horas totales: {total:.2f}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Solo los administradores pueden ver las horas totales.", ephemeral=True)

    # Guardar cambios
    with open(ARCHIVO_HORAS, "w") as f:
        json.dump(horas_trabajadores, f, indent=4)


async def actualizar_ranking(guild):
    """Actualiza el ranking de horas trabajadas."""
    canal = guild.get_channel(CANAL_RANKING_ID)
    if not canal:
        print("⚠️ Canal de ranking no encontrado.")
        return

    ranking = sorted(horas_trabajadores.items(), key=lambda x: x[1]["total_minutos"], reverse=True)
    texto = "🏆 **Ranking de horas trabajadas** 🏆\n\n"

    for i, (canal_id, datos) in enumerate(ranking, start=1):
        canal_trab = guild.get_channel(int(canal_id))
        nombre = canal_trab.name if canal_trab else f"Canal {canal_id}"
        texto += f"**{i}. {nombre}** — {datos['total_minutos']:.2f} horas\n"

    # Borrar mensajes anteriores y enviar el ranking actualizado
    async for msg in canal.history(limit=5):
        if msg.author == bot.user:
            await msg.delete()

    await canal.send(texto)


# ------------------- Ejecutar bot -------------------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ No se encontró la variable de entorno DISCORD_TOKEN")
bot.run(TOKEN)


# ------------------- Ejecutar bot -------------------
bot.run(os.getenv("MTQyODg3NzM4MTQ2NDIyNzk1MA.G1qAOj.nnZ5zx33N22pRtM5HCJSxbX2OZ0ElorEW6Efzo"))
