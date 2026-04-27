import nextcord
from nextcord.ext import commands
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
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

bot = commands.Bot(intents=nextcord.Intents.all())
app = FastAPI()

class VerifyView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
        self.add_item(nextcord.ui.Button(label="Weryfikacja 18+", url=url))

@bot.event
async def on_ready():
    print(f"✅ Bot zalogowany jako {bot.user}")

@bot.slash_command(name="setup")
async def setup(interaction: nextcord.Interaction):
    await interaction.send("Kliknij by przejść weryfikację:", view=VerifyView())

@app.get("/callback")
async def callback(code: str):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('https://discord.com/api/oauth2/token', data=data) as resp:
            token_data = await resp.json()
            access_token = token_data.get('access_token')
        async with session.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'}) as resp:
            user_info = await resp.json()
            user_id = user_info.get('id')
            user_name = user_info.get('username')

    css = """
    <style>
        body { background-color: #050b18; color: #ffffff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { text-align: center; background: rgba(255, 255, 255, 0.05); padding: 60px; border-radius: 30px; border: 1px solid rgba(28, 194, 191, 0.2); max-width: 500px; width: 90%; }
        .logo { font-size: 38px; color: #1cc2bf; margin-bottom: 10px; font-weight: 300; text-transform: uppercase; }
        .logo b { color: #ffffff; font-weight: 800; }
        .verify-btn { background: #1cc2bf; color: white; border: none; padding: 20px 50px; font-size: 15px; font-weight: 800; border-radius: 12px; cursor: pointer; text-transform: uppercase; margin-top: 20px; }
        .user-highlight { color: #1cc2bf; font-weight: bold; }
    </style>
    """

    html_content = f"""
    <html>
        <head><title>NeuralisBETS Verification</title><meta name="viewport" content="width=device-width, initial-scale=1.0">{css}</head>
        <body>
            <div class="container">
                <div class="logo">Neuralis<b>BETS</b></div>
                <p>Witaj <span class="user-highlight">{user_name}</span>!<br>Kliknij poniższy przycisk, aby potwierdzić pełnoletniość.</p>
                <form action="/confirm" method="post">
                    <input type="hidden" name="user_id" value="{user_id}">
                    <button type="submit" class="verify-btn">Oświadczam, że mam 18 lat</button>
                </form>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.post("/confirm")
async def confirm(user_id: str = Form(...)):
    async def give_role():
        guild = bot.get_guild(GUILD_ID)
        if not guild: return "Nie znaleziono serwera (sprawdź ID)."
        member = guild.get_member(int(user_id))
        if not member: return "Nie ma Cię na serwerze."
        role = guild.get_role(ROLE_ID)
        if not role: return "Nie znaleziono roli (sprawdź ID)."
        try:
            await member.add_roles(role)
            return "Sukces"
        except Exception as e: return f"Błąd uprawnień: {e}"

    if bot.is_ready():
        future = asyncio.run_coroutine_threadsafe(give_role(), bot.loop)
        result = future.result()
    else:
        result = "Bot nie jest jeszcze gotowy."

    if result == "Sukces":
        content = "<h2>Weryfikacja udana!</h2>"
    else:
        content = f"<h2>Błąd: {result}</h2>"
    
    return HTMLResponse(f"<html><body style='background:#050b18;color:white;text-align:center;padding-top:50px;'>{content}</body></html>")

if __name__ == "__main__":
    if TOKEN:
        # Odpalenie bota w tle
        t = threading.Thread(target=bot.run, args=(TOKEN,))
        t.daemon = True
        t.start()
    
    # Odpalenie serwera FastAPI
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
