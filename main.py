import nextcord
from nextcord.ext import commands
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import aiohttp

# --- UZUPEŁNIJ TO ---
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GUILD_ID = 1496581706508140564  # ID Twojego serwera
ROLE_ID = 1498042097704501258   # ID rangi 18+
REDIRECT_URI = "https://neuralisverify.onrender.com"

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
        body {
            background-color: #050b18;
            color: #ffffff;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .container {
            text-align: center;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
            padding: 60px;
            border-radius: 30px;
            border: 1px solid rgba(28, 194, 191, 0.2);
            box-shadow: 0 25px 50px rgba(0,0,0,0.7);
            backdrop-filter: blur(15px);
            max-width: 500px;
            width: 90%;
        }
        .logo {
            font-size: 38px;
            color: #1cc2bf;
            margin-bottom: 10px;
            font-weight: 300;
            text-transform: uppercase;
            letter-spacing: 3px;
        }
        .logo b { color: #ffffff; font-weight: 800; letter-spacing: 1px; }
        p {
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 45px;
            font-size: 16px;
            line-height: 1.6;
        }
        .verify-btn {
            background: linear-gradient(135deg, #1cc2bf 0%, #15918f 100%);
            color: #ffffff;
            border: none;
            padding: 20px 50px;
            font-size: 15px;
            font-weight: 800;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-transform: uppercase;
            letter-spacing: 2px;
            box-shadow: 0 10px 20px rgba(28, 194, 191, 0.2);
        }
        .verify-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(28, 194, 191, 0.4);
            filter: brightness(1.1);
        }
        .user-highlight { color: #1cc2bf; font-weight: bold; }
    </style>
    """

    html_content = f"""
    <html>
        <head>
            <title>NeuralisBETS Verification</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {css}
        </head>
        <body>
            <div class="container">
                <div class="logo">Neuralis<b>BETS</b></div>
                <p>Witaj <span class="user-highlight">{user_name}</span>!<br>Kliknij poniższy przycisk, aby potwierdzić pełnoletniość i odblokować dostęp do serwera.</p>
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
        if not guild: return "Nie znaleziono serwera."
        member = guild.get_member(int(user_id))
        if not member: return "Nie znaleziono Cię na serwerze."
        role = guild.get_role(ROLE_ID)
        if not role: return "Nie znaleziono rangi."
        try:
            await member.add_roles(role)
            return "Sukces"
        except Exception as e: return str(e)

    future = asyncio.run_coroutine_threadsafe(give_role(), bot.loop)
    result = future.result()

    css_res = """
    <style>
        body { background-color: #050b18; color: white; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { padding: 50px; border-radius: 25px; background: rgba(255,255,255,0.02); border: 1px solid #1cc2bf; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
        h2 { color: #1cc2bf; text-transform: uppercase; letter-spacing: 2px; }
        .success-icon { font-size: 60px; margin-bottom: 20px; }
    </style>
    """

    if result == "Sukces":
        content = '<div class="box"><div class="success-icon">✅</div><h2>Weryfikacja udana!</h2><p>Twoja ranga została nadana. Możesz wrócić na Discorda.</p></div>'
    else:
        content = f'<div class="box" style="border-color: #ff4444;"><div class="success-icon">❌</div><h2 style="color: #ff4444;">Błąd</h2><p>{result}</p></div>'

    return HTMLResponse(f"<html><head>{css_res}</head><body>{content}</body></html>")
import threading

def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Uruchomienie bota Discord w tle
    import threading
    threading.Thread(target=lambda: bot.run(os.getenv("DISCORD_TOKEN"))).start()
    
    # Uruchomienie serwera WWW (FastAPI)
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
