import discord
import aiohttp
from discord.ext import commands, tasks
from datetime import datetime
import os

# Replace with your channel ID
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # From environment variable

# URL of the VATPHIL bookings JSON API
BOOKINGS_URL = "https://cc.vatphil.com/bookings"

# Relevant VATPHIL positions
VATPHIL_POSITIONS = [
    "MNL_CTR", "RPLL_CTR", "RPLL_APP", "RPLL_TWR", "RPLL_GND", "RPLL_DEL",
    "RPLU_TWR", "RPUO_TWR", "RPMD_TWR", "RPMZ_TWR", "RPMC_TWR", "RPVM_TWR",
    "RPLI_TWR", "RPVB_TWR", "RPMR_TWR", "RPLL_S_TWR", "RPLL_S_GND", "RPLL_S_APP",
    "RPLL_M_APP", "RPLL_M_GND", "RPLL_M_TWR"
]

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_bookings.start()

@tasks.loop(minutes=60)  # You can adjust the interval
async def check_bookings():
    async with aiohttp.ClientSession() as session:
        async with session.get(BOOKINGS_URL) as response:
            if response.status != 200:
                print(f"❌ Failed to fetch bookings: {response.status}")
                return
            
            data = await response.json()

            # Filter bookings
            upcoming = [
                booking for booking in data
                if not booking["deleted"]
                and any(pos in booking["callsign"] for pos in VATPHIL_POSITIONS)
                and datetime.strptime(booking["time_start"], "%Y-%m-%d %H:%M:%S") > datetime.utcnow()
            ]

            channel = bot.get_channel(CHANNEL_ID)
            if not channel:
                print("❌ Channel not found!")
                return

            if not upcoming:
                await channel.send("📭 No upcoming VATPHIL bookings.")
                return

            await channel.send("📡 **Upcoming VATPHIL Bookings**:")
            for booking in upcoming:
                embed = discord.Embed(
                    title=f"{booking['callsign']} - {booking['name']}",
                    color=discord.Color.green()
                )
                embed.add_field(name="🕒 Start", value=booking["time_start"], inline=True)
                embed.add_field(name="🕔 End", value=booking["time_end"], inline=True)

                types = []
                if booking["training"]: types.append("👨‍🏫 Training")
                if booking["event"]: types.append("🎉 Event")
                if booking["exam"]: types.append("📝 Exam")
                if not types: types.append("🛫 Standard")

                embed.add_field(name="📌 Type", value=", ".join(types), inline=False)
                embed.set_footer(text=f"User ID: {booking['user_id']}")
                await channel.send(embed=embed)

# Run the bot
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_TOKEN)
