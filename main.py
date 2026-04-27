import nextcord
from nextcord.ext import commands
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import aiohttp
import os
import threading

# --- KONFIGURACJA POBIERANA Z RENDER ---
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

    html_content = f"""
    <html>
        <body style="background-color: #050b18; color: white; font-family: sans-serif; text-align: center; padding-top: 100px;">
            <h1 style="color: #1cc2bf;">NeuralisBETS</h1>
            <p>Witaj <b>{user_name}</b>! Kliknij przycisk, aby odebrać rangę:</p>
            <form action="/confirm" method="post">
                <input type="hidden" name="user_id" value="{user_id}">
                <button type="submit" style="background: #1cc2bf; color: white; border: none; padding: 15px 30px; border-radius: 8px; cursor: pointer; font-weight: bold;">POTWIERDZAM 18 LAT</button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.post("/confirm")
async def confirm(user_id: str = Form(...)):
    async def give_role():
        guild = bot.get_guild(GUILD_ID)
        if not guild: return "Błąd: Nie znaleziono serwera."
        member = guild.get_member(int(user_id))
        if not member: return "Błąd: Nie znaleziono użytkownika na serwerze."
        role = guild.get_role(ROLE_ID)
        if not role: return "Błąd: Nie znaleziono roli."
        try:
            await member.add_roles(role)
            return "Sukces"
        except Exception as e: return str(e)

    if bot.is_ready():
        future = asyncio.run_coroutine_threadsafe(give_role(), bot.loop)
        result = future.result()
    else:
        result = "Bot się jeszcze uruchamia, spróbuj za chwilę."

    return HTMLResponse(f"<html><body style='background:#050b18;color:white;text-align:center;padding-top:50px;'><h2>{result}</h2></body></html>")

def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    # Start bota w osobnym wątku
    if TOKEN:
        threading.Thread(target=run_bot, daemon=True).start()
    
    # Start serwera FastAPI
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
