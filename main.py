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

# ─── HTML TEMPLATES ───────────────────────────────────────────────────────────

BASE_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --teal:    #1cc2bf;
  --teal2:   #0ff5f0;
  --dark:    #050b18;
  --dark2:   #080f22;
  --card:    rgba(10, 20, 45, 0.85);
  --border:  rgba(28, 194, 191, 0.25);
  --glow:    0 0 20px rgba(28,194,191,0.5), 0 0 60px rgba(28,194,191,0.15);
}

html, body {
  width: 100%; height: 100%;
  background: var(--dark);
  color: white;
  font-family: 'Rajdhani', sans-serif;
  overflow: hidden;
}

/* ── canvas particles ── */
#canvas {
  position: fixed; inset: 0;
  z-index: 0; pointer-events: none;
}

/* ── scanlines overlay ── */
body::after {
  content: '';
  position: fixed; inset: 0; z-index: 1;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.07) 2px,
    rgba(0,0,0,0.07) 4px
  );
  pointer-events: none;
}

/* ── grid background ── */
body::before {
  content: '';
  position: fixed; inset: 0; z-index: 0;
  background-image:
    linear-gradient(rgba(28,194,191,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(28,194,191,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* ── center wrapper ── */
.scene {
  position: relative; z-index: 2;
  display: flex; align-items: center; justify-content: center;
  width: 100%; height: 100vh;
}

/* ── card ── */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 48px 56px;
  width: min(480px, 92vw);
  text-align: center;
  backdrop-filter: blur(18px);
  box-shadow: var(--glow), inset 0 1px 0 rgba(255,255,255,0.05);
  animation: fadeUp .8s cubic-bezier(.16,1,.3,1) both;
}

@keyframes fadeUp {
  from { opacity:0; transform: translateY(30px) scale(.97); }
  to   { opacity:1; transform: translateY(0)   scale(1);    }
}

/* ── logo ── */
.logo-wrap {
  position: relative; display: inline-block; margin-bottom: 28px;
}
.logo-ring {
  width: 80px; height: 80px;
  border-radius: 50%;
  border: 2px solid var(--teal);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 6px;
  box-shadow: var(--glow);
  animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { box-shadow: var(--glow); }
  50%      { box-shadow: 0 0 35px rgba(28,194,191,.8), 0 0 80px rgba(28,194,191,.3); }
}
.logo-ring svg { width:40px; height:40px; fill: var(--teal); }

/* ── heading ── */
h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.7rem; font-weight: 900;
  letter-spacing: .12em;
  color: var(--teal);
  text-shadow: 0 0 20px rgba(28,194,191,.6);
  margin-bottom: 6px;
}
.subtitle {
  font-size: .85rem; letter-spacing: .2em;
  color: rgba(255,255,255,.35);
  text-transform: uppercase;
  margin-bottom: 28px;
}

/* ── divider ── */
.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--teal), transparent);
  margin: 0 auto 28px;
  opacity: .5;
}

/* ── greeting ── */
.greeting {
  font-size: 1rem; color: rgba(255,255,255,.6);
  letter-spacing: .05em; margin-bottom: 6px;
}
.username {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.25rem; color: #fff;
  letter-spacing: .08em; margin-bottom: 28px;
}

/* ── badge ── */
.badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(28,194,191,.08);
  border: 1px solid rgba(28,194,191,.3);
  border-radius: 999px;
  padding: 6px 18px; margin-bottom: 32px;
  font-size: .78rem; letter-spacing: .15em;
  color: var(--teal); text-transform: uppercase;
}
.badge::before {
  content: ''; width:7px; height:7px; border-radius:50%;
  background: var(--teal);
  box-shadow: 0 0 8px var(--teal);
  animation: blink 1.4s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ── button ── */
.btn {
  display: inline-block; width: 100%;
  padding: 16px 32px;
  background: transparent;
  border: 2px solid var(--teal);
  border-radius: 8px;
  color: var(--teal);
  font-family: 'Orbitron', sans-serif;
  font-size: .85rem; font-weight: 700;
  letter-spacing: .18em; text-transform: uppercase;
  cursor: pointer;
  position: relative; overflow: hidden;
  transition: color .3s, box-shadow .3s;
}
.btn::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--teal);
  transform: scaleX(0); transform-origin: left;
  transition: transform .35s cubic-bezier(.16,1,.3,1);
  z-index: -1;
}
.btn:hover { color: var(--dark); box-shadow: var(--glow); }
.btn:hover::before { transform: scaleX(1); }
.btn:active { transform: scale(.98); }

/* ── status card (confirm page) ── */
.status-icon {
  width: 72px; height: 72px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px;
  font-size: 2rem;
}
.status-icon.ok  { background: rgba(28,194,191,.12); border: 2px solid var(--teal); box-shadow: var(--glow); }
.status-icon.err { background: rgba(255,80,80,.12);  border: 2px solid #ff5050; box-shadow: 0 0 20px rgba(255,80,80,.4); }

.result-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem; letter-spacing: .1em;
}
.result-text.ok  { color: var(--teal); text-shadow: 0 0 15px rgba(28,194,191,.5); }
.result-text.err { color: #ff5050; }

.hint {
  margin-top: 18px;
  font-size: .8rem; letter-spacing: .1em;
  color: rgba(255,255,255,.25);
}

/* ── corner decorations ── */
.corner { position: absolute; width:18px; height:18px; }
.corner.tl { top:14px;  left:14px;  border-top:2px solid var(--teal); border-left:2px solid var(--teal);  }
.corner.tr { top:14px;  right:14px; border-top:2px solid var(--teal); border-right:2px solid var(--teal); }
.corner.bl { bottom:14px; left:14px;  border-bottom:2px solid var(--teal); border-left:2px solid var(--teal);  }
.corner.br { bottom:14px; right:14px; border-bottom:2px solid var(--teal); border-right:2px solid var(--teal); }
"""

PARTICLES_JS = """
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let W, H, dots = [];

function resize() {
  W = canvas.width  = window.innerWidth;
  H = canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

class Dot {
  constructor() { this.reset(); }
  reset() {
    this.x  = Math.random() * W;
    this.y  = Math.random() * H;
    this.vx = (Math.random() - .5) * .35;
    this.vy = (Math.random() - .5) * .35;
    this.r  = Math.random() * 1.5 + .5;
    this.a  = Math.random() * .6 + .2;
  }
  update() {
    this.x += this.vx; this.y += this.vy;
    if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
  }
  draw() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI*2);
    ctx.fillStyle = `rgba(28,194,191,${this.a})`;
    ctx.fill();
  }
}

for (let i = 0; i < 90; i++) dots.push(new Dot());

function connect() {
  for (let i = 0; i < dots.length; i++)
    for (let j = i+1; j < dots.length; j++) {
      const dx = dots[i].x - dots[j].x, dy = dots[i].y - dots[j].y;
      const d = Math.sqrt(dx*dx + dy*dy);
      if (d < 120) {
        ctx.beginPath();
        ctx.moveTo(dots[i].x, dots[i].y);
        ctx.lineTo(dots[j].x, dots[j].y);
        ctx.strokeStyle = `rgba(28,194,191,${.18*(1-d/120)})`;
        ctx.lineWidth = .6;
        ctx.stroke();
      }
    }
}

(function loop() {
  ctx.clearRect(0, 0, W, H);
  dots.forEach(d => { d.update(); d.draw(); });
  connect();
  requestAnimationFrame(loop);
})();
"""

LOGO_SVG = """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
</svg>"""

SHIELD_SVG = """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
</svg>"""


def page(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NeuralisBETS · Weryfikacja</title>
<style>{BASE_STYLE}</style>
</head>
<body>
<canvas id="canvas"></canvas>
{body}
<script>{PARTICLES_JS}</script>
</body>
</html>"""


def callback_page(user_name: str, user_id: str) -> str:
    body = f"""
<div class="scene">
  <div class="card" style="position:relative;">
    <span class="corner tl"></span><span class="corner tr"></span>
    <span class="corner bl"></span><span class="corner br"></span>

    <div class="logo-ring">{SHIELD_SVG}</div>
    <h1>NeuralisBETS</h1>
    <p class="subtitle">Verification System</p>
    <div class="divider"></div>

    <p class="greeting">Witaj,</p>
    <p class="username">{user_name}</p>

    <div class="badge">Weryfikacja wieku 18+</div>

    <form action="/confirm" method="post">
      <input type="hidden" name="user_id" value="{user_id}">
      <button class="btn" type="submit">⬡ Potwierdzam 18 lat</button>
    </form>
  </div>
</div>"""
    return page(body)


def confirm_page(result: str) -> str:
    ok = result.startswith("✅")
    icon  = "✓" if ok else "✕"
    cls   = "ok" if ok else "err"
    hint  = "Możesz wrócić na serwer Discord." if ok else "Spróbuj ponownie lub skontaktuj się z adminem."

    body = f"""
<div class="scene">
  <div class="card" style="position:relative;">
    <span class="corner tl"></span><span class="corner tr"></span>
    <span class="corner bl"></span><span class="corner br"></span>

    <div class="logo-ring">{LOGO_SVG}</div>
    <h1>NeuralisBETS</h1>
    <p class="subtitle">Verification System</p>
    <div class="divider"></div>

    <div class="status-icon {cls}">{icon}</div>
    <p class="result-text {cls}">{result}</p>
    <p class="hint">{hint}</p>
  </div>
</div>"""
    return page(body)


# ─── BOT ──────────────────────────────────────────────────────────────────────

def run_bot():
    global bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    if TOKEN:
        bot_loop.run_until_complete(bot.start(TOKEN))
    else:
        print("❌ BŁĄD: Brak zmiennej DISCORD_TOKEN!")


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


# ─── ROUTES ───────────────────────────────────────────────────────────────────

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
            return HTMLResponse(confirm_page("✕ Błąd autoryzacji. Spróbuj ponownie."), status_code=400)

        async with session.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as resp:
            user_info = await resp.json()
            user_id   = user_info.get("id")
            user_name = user_info.get("username", "Użytkownik")

    return HTMLResponse(callback_page(user_name, user_id))


@app.post("/confirm")
async def confirm(user_id: str = Form(...)):
    if not bot.is_ready():
        return HTMLResponse(confirm_page("⏳ Bot się uruchamia, odśwież za chwilę."))

    async def give_role():
        guild = bot.get_guild(GUILD_ID)
        if not guild:   return "✕ Nie znaleziono serwera."
        member = guild.get_member(int(user_id))
        if not member:  return "✕ Nie znaleziono użytkownika na serwerze."
        role = guild.get_role(ROLE_ID)
        if not role:    return "✕ Nie znaleziono roli."
        try:
            await member.add_roles(role)
            return "✅ Ranga została nadana!"
        except Exception as e:
            return f"✕ Błąd: {str(e)}"

    future = asyncio.run_coroutine_threadsafe(give_role(), bot_loop)
    try:
        result = future.result(timeout=10)
    except Exception as e:
        result = f"✕ Błąd wykonania: {str(e)}"

    return HTMLResponse(confirm_page(result))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
