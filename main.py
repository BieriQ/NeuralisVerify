import nextcord
from nextcord.ext import commands
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import aiohttp
import os
import threading

# --- KONFIGURACJA ---
TOKEN = os.getenv("DISCORD_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GUILD_ID = 1496581706508140564
ROLE_ID = 1498042097704501258
REDIRECT_URI = "https://neuralisverify.onrender.com/callback"

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)

bot_loop = None
bot_thread = None


def run_bot():
    global bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    if TOKEN:
        bot_loop.run_until_complete(bot.start(TOKEN))
    else:
        print("❌ BŁĄD: Brak zmiennej DISCORD_TOKEN!")


# lifespan — uruchamia bota przy starcie FastAPI (działa też z: uvicorn main:app)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_thread
    print("🚀 Uruchamianie bota Discord...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    yield
    print("🛑 Zamykanie...")


app = FastAPI(lifespan=lifespan)


class VerifyView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        url = (
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=identify"
        )
        self.add_item(nextcord.ui.Button(label="Weryfikacja 18+", url=url))


@bot.event
async def on_ready():
    print(f"✅ Bot zalogowany jako {bot.user}")
    print(f"✅ Połączono z {len(bot.guilds)} serwerami")


@bot.slash_command(name="setup", guild_ids=[GUILD_ID])
async def setup(interaction: nextcord.Interaction):
    await interaction.send("Kliknij by przejść weryfikację:", view=VerifyView())


@app.get("/")
async def root():
    return {"status": "OK", "bot_ready": bot.is_ready()}


@app.get("/callback")
async def callback(code: str):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://discord.com/api/oauth2/token", data=data
        ) as resp:
            token_data = await resp.json()
            access_token = token_data.get("access_token")

        if not access_token:
            return HTMLResponse("<h1>Błąd autoryzacji. Spróbuj ponownie.</h1>", status_code=400)

        async with session.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as resp:
            user_info = await resp.json()
            user_id = user_info.get("id")
            user_name = user_info.get("username", "Użytkownik")

    html_content = f"""
    <html>
        <body style="background-color: #050b18; color: white; font-family: sans-serif;
                     text-align: center; padding-top: 100px;">
            <h1 style="color: #1cc2bf;">NeuralisBETS</h1>
            <p>Witaj <b>{user_name}</b>! Kliknij przycisk, aby odebrać rangę:</p>
            <form action="/confirm" method="post">
                <input type="hidden" name="user_id" value="{user_id}">
                <button type="submit"
                    style="background: #1cc2bf; color: white; border: none;
                           padding: 15px 30px; border-radius: 8px;
                           cursor: pointer; font-weight: bold;">
                    POTWIERDZAM 18 LAT
                </button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(html_content)


@app.post("/confirm")
async def confirm(user_id: str = Form(...)):
    if not bot.is_ready():
        return HTMLResponse(
            "<html><body style='background:#050b18;color:white;text-align:center;"
            "padding-top:50px;'><h2>Bot się jeszcze uruchamia, odśwież za chwilę.</h2></body></html>"
        )

    async def give_role():
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return "Błąd: Nie znaleziono serwera."
        member = guild.get_member(int(user_id))
        if not member:
            return "Błąd: Nie znaleziono użytkownika na serwerze."
        role = guild.get_role(ROLE_ID)
        if not role:
            return "Błąd: Nie znaleziono roli."
        try:
            await member.add_roles(role)
            return "✅ Ranga została nadana!"
        except Exception as e:
            return f"Błąd: {str(e)}"

    future = asyncio.run_coroutine_threadsafe(give_role(), bot_loop)
    try:
        result = future.result(timeout=10)
    except Exception as e:
        result = f"Błąd wykonania: {str(e)}"

    return HTMLResponse(
        f"<html><body style='background:#050b18;color:white;text-align:center;"
        f"padding-top:50px;'><h2>{result}</h2></body></html>"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
