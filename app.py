
import hashlib
import hmac
import html as htmllib
import json
import os
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from datetime import time as dtime

import altair as alt
import joblib
import pandas as pd
import streamlit as st

# ------------------------------------------------------------------
# FORCE LIGHT THEME (works even without .streamlit/config.toml)
# ------------------------------------------------------------------
try:
    for _k, _v in {
        "theme.base": "light",
        "theme.primaryColor": "#1fbf96",
        "theme.backgroundColor": "#fbf4e4",
        "theme.secondaryBackgroundColor": "#f3e8cd",
        "theme.textColor": "#0f2f29",
    }.items():
        st._config.set_option(_k, _v)
except Exception:
    pass

st.set_page_config(page_title="DenguePulse", page_icon="🦟", layout="wide")

# ------------------------------------------------------------------
# ICONS (inline SVG, Lucide-style outline set)
# ------------------------------------------------------------------
ICONS = {
    "thermometer": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "droplets": '<path d="M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"/><path d="M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97"/>',
    "rain": '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/>',
    "activity": '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    "pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "stethoscope": '<path d="M11 2v2"/><path d="M5 2v2"/><path d="M5 3H4a2 2 0 0 0-2 2v4a6 6 0 0 0 12 0V5a2 2 0 0 0-2-2h-1"/><path d="M8 15a6 6 0 0 0 12 0v-3"/><circle cx="20" cy="10" r="2"/>',
    "hospital": '<path d="M12 6v4"/><path d="M14 14h-4"/><path d="M14 18h-4"/><path d="M14 8h-4"/><path d="M18 12h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/><path d="M18 22V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v18"/>',
    "bed": '<path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/>',
    "shield-alert": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "cpu": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "trend": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "bug": '<path d="m8 2 1.88 1.88"/><path d="M14.12 3.88 16 2"/><path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"/><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"/><path d="M12 20v-9"/><path d="M6.53 9C4.6 8.8 3 7.1 3 5"/><path d="M6 13H2"/><path d="M3 21c0-2.1 1.7-3.9 3.8-4"/><path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"/><path d="M22 13h-4"/><path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "siren": '<path d="M7 18v-6a5 5 0 1 1 10 0v6"/><path d="M5 21a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-1a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2z"/><path d="M21 12h1"/><path d="M18.5 4.5 18 5"/><path d="M2 12h1"/><path d="M12 2v1"/><path d="m4.929 4.929.707.707"/><path d="M12 12v6"/>',
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
}


def icon(name, size=22, stroke="currentColor", sw=2):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[name]}</svg>')


# ------------------------------------------------------------------
# DESIGN SYSTEM
# ------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Manrope:wght@400;500;600;700&display=swap');

:root{
  --cream:#fbf4e4; --cream-2:#f3e8cd; --edge:#dccfa8;
  --sea:#1fbf96; --sea-deep:#0b4f43; --sea-dark:#073b32;
  --ink:#0f2f29; --muted:#56726a;
  --neon:#4dffc3; --neon-2:#2df5a8;
  --fd:'Bricolage Grotesque',sans-serif; --fb:'Manrope',sans-serif;
  color-scheme:light;
}
html, body, .stApp, [class*="css"]{ font-family:var(--fb); color:var(--ink); }

/* ---------- background ---------- */
.stApp{
  background:
    radial-gradient(520px 420px at 4% 22%, rgba(77,255,195,.34) 0%, transparent 70%),
    radial-gradient(560px 460px at 98% 88%, rgba(31,191,150,.28) 0%, transparent 70%),
    radial-gradient(1200px 600px at 10% -10%, #d9f7ea 0%, transparent 60%),
    linear-gradient(160deg,#fbf4e4 0%,#f6edd6 50%,#e9f6ec 100%);
}
header[data-testid="stHeader"]{ background:transparent; }
#MainMenu, footer, .stDeployButton{ visibility:hidden; display:none; }
.block-container{ padding-top:1.6rem; max-width:1280px; position:relative; z-index:1; }

/* ---------- entrance ---------- */
@keyframes rise{ from{ opacity:0; transform:translateY(22px);} to{ opacity:1; transform:none;} }
.rise{ animation:rise .7s cubic-bezier(.2,.8,.2,1) both; }

/* ---------- 3D tilt (driven by JS variables) ---------- */
.tilt{
  position:relative; transform-style:preserve-3d;
  transform:perspective(900px) rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg)) scale(var(--sc,1));
  transition:transform .18s ease-out, box-shadow .3s ease; will-change:transform;
}
.tilt:hover{ --sc:1.025; }
.tilt::after{
  content:""; position:absolute; inset:0; border-radius:inherit; pointer-events:none; opacity:0;
  background:radial-gradient(280px circle at var(--mx,50%) var(--my,0%), rgba(255,255,255,.6), transparent 60%);
  transition:opacity .25s ease;
}
.tilt:hover::after{ opacity:1; }
.tilt .ico3d{ transform:translateZ(38px); }
.tilt .v, .tilt .name{ transform:translateZ(26px); }

/* ---------- HERO ---------- */
.hero{
  display:grid; grid-template-columns:1.15fr .85fr; align-items:center; gap:10px;
  padding:44px 52px; margin-bottom:30px; border-radius:40px; position:relative; overflow:hidden;
  background:
    radial-gradient(500px 340px at 85% 30%, rgba(77,255,195,.28), transparent 70%),
    radial-gradient(420px 300px at 0% 100%, rgba(45,245,168,.14), transparent 70%),
    linear-gradient(135deg,#0d5e4f 0%,#073b32 60%,#04271f 100%);
  box-shadow:0 30px 70px rgba(7,59,50,.35), 0 8px 0 #052e27, inset 0 2px 0 rgba(255,255,255,.18);
}
.hero .pill{
  display:inline-flex; align-items:center; gap:9px; padding:7px 16px; border-radius:999px;
  background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.2);
  color:#c9fbe8; font-size:.74rem; font-weight:700; letter-spacing:.16em;
}
.hero .dot{ width:8px; height:8px; border-radius:50%; background:var(--neon); box-shadow:0 0 12px var(--neon);
  animation:blink 2s ease-in-out infinite; }
@keyframes blink{ 50%{ opacity:.35; } }
.hero-title{ font-family:var(--fd); font-weight:800; font-size:3.7rem; line-height:1.02; letter-spacing:-.03em;
  color:#fff7e3; margin:20px 0 16px; }
.hero-title em{ font-style:normal; background:linear-gradient(90deg,#7affd6,#2df5a8 60%,#d9ffe9);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.hero-sub{ color:#b9d8cc; font-size:1.08rem; max-width:520px; margin:0 0 28px; line-height:1.6; }
.hero-stats{ display:flex; gap:14px; flex-wrap:wrap; }
.hstat{ padding:14px 20px; border-radius:20px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.16);
  box-shadow:0 5px 0 rgba(0,0,0,.18); min-width:108px; }
.hstat b{ display:block; font-family:var(--fd); font-size:1.7rem; color:#fff7e3; line-height:1.1; }
.hstat span{ font-size:.7rem; letter-spacing:.14em; color:#9fc9b9; font-weight:700; text-transform:uppercase; }

/* 3D scene */
.scene{ position:relative; height:370px; display:grid; place-items:center; perspective:1100px;
  transform-style:preserve-3d; transform:rotateX(var(--sx,0deg)) rotateY(var(--sy,0deg)); transition:transform .25s ease-out; }
.orb{
  width:196px; height:196px; border-radius:50%; display:grid; place-items:center; position:relative; z-index:2;
  background:radial-gradient(circle at 32% 26%, #f3fffa 0%, #8dffd8 20%, #1fbf96 56%, #0a6a57 100%);
  box-shadow:inset -20px -24px 40px rgba(4,50,40,.5), inset 12px 12px 28px rgba(255,255,255,.75),
             0 44px 60px -22px rgba(0,0,0,.55), 0 0 90px rgba(77,255,195,.5);
  animation:bob 6s ease-in-out infinite; }
.orb svg{ filter:drop-shadow(0 6px 8px rgba(4,50,40,.45)); }
@keyframes bob{ 50%{ transform:translateY(-14px);} }
.ring{ position:absolute; border-radius:50%; border:2px solid rgba(122,255,214,.55);
  box-shadow:0 0 22px rgba(77,255,195,.45), inset 0 0 22px rgba(77,255,195,.2);
  transform:rotateX(72deg) rotateZ(0deg); animation:spin 16s linear infinite; }
.ring::after{ content:""; position:absolute; top:-7px; left:50%; width:14px; height:14px; border-radius:50%;
  background:var(--neon); box-shadow:0 0 16px var(--neon); margin-left:-7px; }
.r1{ width:318px; height:318px; }
.r2{ width:410px; height:410px; border-color:rgba(255,247,227,.28); animation-duration:26s; animation-direction:reverse; }
@keyframes spin{ to{ transform:rotateX(72deg) rotateZ(360deg);} }
.chip3d{ position:absolute; z-index:3; display:flex; align-items:center; gap:10px; padding:11px 16px; border-radius:18px;
  background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.3); color:#fff7e3;
  box-shadow:0 8px 0 rgba(0,0,0,.16), 0 18px 30px rgba(0,0,0,.25); transform:translateZ(70px);
  animation:float 5s ease-in-out infinite; }
.chip3d b{ display:block; font-size:.86rem; line-height:1.1; }
.chip3d span{ font-size:.68rem; color:#b9ecd7; letter-spacing:.08em; font-weight:700; }
.chip3d .mini{ width:34px; height:34px; border-radius:12px; display:grid; place-items:center; color:#053b2c;
  background:linear-gradient(145deg,#8bffd8,#2df5a8); box-shadow:0 3px 0 #11a074; }
.c1{ top:14%; left:-2%; } .c2{ bottom:16%; left:2%; animation-delay:-1.6s; } .c3{ top:30%; right:-3%; animation-delay:-3s; }
@keyframes float{ 50%{ transform:translateZ(70px) translateY(-10px);} }

/* ---------- section headings ---------- */
.sec{ display:flex; align-items:center; gap:14px; margin:2px 0 16px; }
.sec .badge{ width:46px; height:46px; border-radius:16px; display:grid; place-items:center; flex:none; color:#06483a;
  background:linear-gradient(145deg,#a8ffe2,#2df5a8);
  box-shadow:0 5px 0 #11a074, 0 12px 20px rgba(31,191,150,.4), inset 0 2px 2px rgba(255,255,255,.85); }
.sec-t{ font-family:var(--fd); font-weight:800; font-size:1.5rem; color:var(--sea-deep); letter-spacing:-.02em; line-height:1.1; }
.sec-s{ color:var(--muted); font-size:.9rem; margin-top:3px; }

/* ---------- panels ---------- */
[class*="st-key-panel_"]{
  background:rgba(255,255,255,.7) !important; border:1px solid #fff !important; border-radius:30px !important;
  padding:24px 26px !important;
  box-shadow:0 6px 0 rgba(220,207,168,.75), 0 22px 46px rgba(11,79,67,.13), inset 0 1px 0 #fff !important; }

/* ---------- clay cards ---------- */
.clay{ border-radius:28px; padding:22px 24px; position:relative;
  background:linear-gradient(160deg,#fffdf6,#f4ead0);
  box-shadow:0 7px 0 var(--edge), 0 22px 38px rgba(120,100,50,.2), inset 0 2px 3px rgba(255,255,255,.95); }
.clay.dark{ background:linear-gradient(160deg,#10705c,#073b32); color:#fff7e3;
  box-shadow:0 7px 0 #04271f, 0 22px 40px rgba(7,59,50,.4), inset 0 2px 3px rgba(255,255,255,.18); }
.ico3d{ width:50px; height:50px; border-radius:17px; display:grid; place-items:center; color:#06483a;
  background:linear-gradient(145deg,#a8ffe2,#2df5a8);
  box-shadow:0 5px 0 #11a074, 0 12px 18px rgba(31,191,150,.4), inset 0 2px 2px rgba(255,255,255,.85); }
.clay .k{ font-size:.7rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); margin-top:18px; }
.clay.dark .k{ color:#9fd3c0; }
.clay .v{ font-family:var(--fd); font-size:2.6rem; font-weight:800; color:var(--sea-deep); line-height:1.1; letter-spacing:-.02em; }
.clay.dark .v{ color:var(--neon); text-shadow:0 0 24px rgba(77,255,195,.55); }
.clay .v small{ font-size:1rem; font-weight:700; color:var(--muted); margin-left:5px; font-family:var(--fb); }
.clay.dark .v small{ color:#9fd3c0; }
.clay .note{ font-size:.82rem; color:#9fd3c0; margin-top:6px; }
.bar{ height:9px; border-radius:99px; margin-top:14px; background:rgba(11,79,67,.1);
  box-shadow:inset 0 2px 3px rgba(11,79,67,.18); overflow:hidden; }
.bar i{ display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#1fbf96,#4dffc3);
  box-shadow:0 0 12px rgba(77,255,195,.8); }

/* ---------- risk ---------- */
.risk{ text-align:center; }
.ring2{ width:176px; height:176px; border-radius:50%; margin:4px auto 18px; display:grid; place-items:center;
  box-shadow:0 10px 0 rgba(220,207,168,.8), 0 24px 36px rgba(11,79,67,.22); }
.ring2 .inner{ width:132px; height:132px; border-radius:50%; display:grid; place-items:center;
  background:linear-gradient(160deg,#fffdf6,#f1e6c9);
  box-shadow:inset 5px 5px 12px rgba(160,140,100,.3), inset -5px -5px 12px rgba(255,255,255,.95); }
.ring2 .num{ font-family:var(--fd); font-size:2.8rem; font-weight:800; color:var(--sea-deep); line-height:1; }
.ring2 .num small{ display:block; font-size:.62rem; letter-spacing:.16em; color:var(--muted); font-family:var(--fb); font-weight:800; margin-top:4px; }
.tier{ display:inline-block; padding:9px 24px; border-radius:999px; font-weight:800; letter-spacing:.14em; font-size:.82rem; color:#fff; }
.risk .msg{ color:var(--muted); margin:14px 0 14px; font-size:.95rem; }
.scale{ display:flex; gap:6px; }
.scale i{ flex:1; height:9px; border-radius:99px; }
.scale-l{ display:flex; justify-content:space-between; font-size:.66rem; letter-spacing:.1em; color:var(--muted); font-weight:700; margin-top:7px; }

/* ---------- tabs: 3D keycaps ---------- */
div[role="tablist"]{ gap:16px !important; border:none !important; box-shadow:none !important;
  background:transparent !important; padding:6px 4px 24px !important; }
[data-baseweb="tab-border"], [data-baseweb="tab-highlight"]{ display:none !important; height:0 !important; }
button[role="tab"]{
  height:auto !important; margin:0 !important; padding:13px 28px !important; border:none !important;
  border-radius:18px !important; background:linear-gradient(180deg,#fffdf6,#f4ead0) !important;
  box-shadow:0 6px 0 var(--edge), 0 14px 22px rgba(120,100,50,.18), inset 0 2px 2px #fff !important;
  transition:transform .15s ease, box-shadow .15s ease !important; }
button[role="tab"]:hover{ transform:translateY(-3px); }
button[role="tab"]:active{ transform:translateY(4px); box-shadow:0 2px 0 var(--edge) !important; }
button[role="tab"] p{ color:var(--sea-deep) !important; font-family:var(--fb) !important; font-weight:800 !important;
  font-size:.98rem !important; text-transform:none !important; letter-spacing:0 !important; }
button[role="tab"][aria-selected="true"]{
  background:linear-gradient(180deg,#8bffd8,#2df5a8) !important;
  box-shadow:0 6px 0 #11a074, 0 0 30px rgba(45,245,168,.6), inset 0 2px 2px rgba(255,255,255,.8) !important; }
button[role="tab"][aria-selected="true"] p{ color:#04362a !important; }

/* ---------- neon keycap button ---------- */
.stButton > button{
  border:none; border-radius:20px; padding:15px 40px; font-weight:800; font-size:1rem; letter-spacing:.03em; color:#04362a;
  background:linear-gradient(180deg,#8bffd8,#2df5a8);
  box-shadow:0 7px 0 #11a074, 0 18px 34px rgba(45,245,168,.55), 0 0 50px rgba(77,255,195,.4), inset 0 2px 2px rgba(255,255,255,.85);
  transition:transform .15s ease, box-shadow .15s ease; }
.stButton > button:hover{ transform:translateY(-3px); color:#04362a;
  box-shadow:0 10px 0 #11a074, 0 24px 44px rgba(45,245,168,.7), 0 0 70px rgba(77,255,195,.55), inset 0 2px 2px rgba(255,255,255,.85); }
.stButton > button:active{ transform:translateY(6px); box-shadow:0 1px 0 #11a074, 0 6px 16px rgba(45,245,168,.5), inset 0 2px 2px rgba(255,255,255,.6); }
.stButton > button p{ color:#04362a !important; font-weight:800 !important; }

/* ---------- inputs ---------- */
label p{ font-weight:800 !important; color:var(--sea-deep) !important; font-size:.76rem !important;
  text-transform:uppercase; letter-spacing:.12em; }
[data-baseweb="select"], [data-baseweb="input"], [data-baseweb="textarea"]{
  background:linear-gradient(145deg,#f1e6c9,#fffaf0) !important; border:none !important; border-radius:18px !important;
  box-shadow:inset 4px 4px 9px rgba(160,140,100,.3), inset -4px -4px 9px rgba(255,255,255,.95) !important; }
[data-baseweb="select"] > div, [data-baseweb="select"] > div > div, [data-baseweb="base-input"],
[data-baseweb="input"] > div, [data-baseweb="input"] input, [data-baseweb="select"] input{
  background:transparent !important; border:none !important; box-shadow:none !important; color:var(--ink) !important;
  -webkit-text-fill-color:var(--ink) !important; font-weight:600; }
[data-baseweb="select"] svg, .stNumberInput svg{ fill:var(--sea-deep) !important; color:var(--sea-deep) !important; }
.stNumberInput button{ background:transparent !important; border:none !important; color:var(--sea-deep) !important; }
input::placeholder{ color:#8aa399 !important; -webkit-text-fill-color:#8aa399 !important; opacity:1 !important; }
[data-baseweb="popover"] > div, [data-baseweb="menu"], ul[role="listbox"]{
  background:#fffaf0 !important; border-radius:16px !important; border:none !important; box-shadow:0 18px 40px rgba(11,79,67,.2) !important; }
[role="option"], [data-baseweb="menu"] li{ background:transparent !important; color:var(--ink) !important; }
[role="option"]:hover, [role="option"][aria-selected="true"]{ background:#d6f6e8 !important; }

/* checkboxes as 3D chips */
.stCheckbox{ background:linear-gradient(180deg,#fffdf6,#f4ead0); padding:11px 18px; border-radius:18px; margin-bottom:12px;
  box-shadow:0 5px 0 var(--edge), 0 12px 18px rgba(120,100,50,.14), inset 0 2px 2px #fff; transition:transform .15s ease; }
.stCheckbox:hover{ transform:translateX(6px); }
.stCheckbox label p{ text-transform:none !important; letter-spacing:0 !important; font-size:.98rem !important; font-weight:700 !important; }
label[data-baseweb="checkbox"] > span:first-child{ background:#fffaf0 !important; border:2px solid var(--sea) !important; border-radius:8px !important; }
label[data-baseweb="checkbox"]:has(input:checked) > span:first-child{
  background:var(--sea) !important; box-shadow:0 0 14px rgba(45,245,168,.9); }
.stCheckbox:has(input:checked){ background:linear-gradient(180deg,#e6fff5,#bdf5de);
  box-shadow:0 5px 0 #8fdcc0, 0 12px 22px rgba(31,191,150,.28), inset 0 2px 2px #fff; }

/* ---------- notices ---------- */
div[data-testid="stAlert"]{ border-radius:22px !important; border-left:6px solid var(--neon-2) !important;
  background:#fffaf0 !important; box-shadow:0 5px 0 var(--edge), 0 12px 20px rgba(120,100,50,.12) !important; }
div[data-testid="stAlert"] *{ background-color:transparent !important; color:var(--ink) !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]){ border-left-color:#f5a524 !important; }
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]){ border-left-color:#ff5a4f !important; }

/* ---------- result / tips / hospital ---------- */
.result{ display:flex; gap:20px; align-items:center; border-radius:28px; padding:24px 28px; margin:22px 0 10px;
  background:linear-gradient(160deg,#fffdf6,#f4ead0); }
.result .ico3d{ width:62px; height:62px; border-radius:20px; flex:none; color:#fff; }
.result h3{ font-family:var(--fd) !important; margin:0 0 4px; font-size:1.5rem; }
.result p{ margin:0; color:var(--ink); }
.tip{ text-align:left; }
.tip .t{ font-family:var(--fd); font-weight:800; font-size:1.1rem; color:var(--sea-deep); margin:16px 0 4px; }
.tip p{ margin:0; color:var(--muted); font-size:.9rem; line-height:1.5; }
.meter{ display:flex; align-items:center; gap:16px; }
.meter .lbl{ font-weight:800; color:var(--sea-deep); white-space:nowrap; font-size:.9rem; }
.meter .bar{ flex:1; margin:0; height:12px; }

.name{ font-family:var(--fd); font-size:1.3rem; font-weight:800; color:var(--sea-deep); margin:16px 0 12px; letter-spacing:-.01em; }
.row{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }
.chip{ display:inline-flex; align-items:center; gap:6px; font-size:.78rem; font-weight:800; padding:7px 14px; border-radius:999px; color:var(--sea-deep);
  background:linear-gradient(180deg,#eafcf4,#c8f1de); box-shadow:0 3px 0 #a5dcc4, inset 0 1px 1px #fff; }
.status{ display:inline-flex; align-items:center; gap:9px; font-weight:800; font-size:.9rem; }
.status i{ width:11px; height:11px; border-radius:50%; }
.mini-stat .v{ font-size:2rem; }
code{ background:#d6f6e8 !important; color:var(--sea-deep) !important; border-radius:8px !important; padding:2px 8px !important; }
hr{ border-color:rgba(11,79,67,.12) !important; }
.foot{ text-align:center; color:var(--muted); font-size:.85rem; margin:46px 0 10px; }

@media (max-width:900px){
  .hero{ grid-template-columns:1fr; padding:30px 24px; } .hero-title{ font-size:2.5rem; }
  .scene{ height:290px; } .r2{ display:none; }
}

/* ---------- doctor finder ---------- */
.doc-head{ display:flex; gap:14px; align-items:center; }
.avatar{ width:58px; height:58px; border-radius:50%; flex:none; display:grid; place-items:center; font-family:var(--fd);
  font-weight:800; font-size:1.15rem; color:#06483a;
  background:radial-gradient(circle at 30% 25%,#effff8,#8bffd8 45%,#1fbf96);
  box-shadow:inset -4px -5px 10px rgba(4,50,40,.3), inset 3px 3px 8px rgba(255,255,255,.8), 0 6px 0 #11a074, 0 14px 20px rgba(31,191,150,.4); }
.doc-head .name{ margin:0; font-size:1.15rem; line-height:1.2; }
.deg{ font-size:.8rem; color:var(--muted); margin-top:4px; line-height:1.4; }
.kv{ display:flex; gap:10px; align-items:flex-start; font-size:.88rem; margin:9px 0; color:var(--ink); font-weight:600; }
.kv svg{ flex:none; margin-top:2px; color:var(--sea); }
.kv small{ display:block; color:var(--muted); font-size:.78rem; font-weight:500; }
.avail{ display:flex; gap:12px; align-items:center; padding:12px 14px; border-radius:18px; border:2px solid; margin:14px 0 8px;
  background:rgba(255,255,255,.7); }
.avail i{ width:12px; height:12px; border-radius:50%; flex:none; }
.avail b{ display:block; font-size:.92rem; }
.avail span{ font-size:.78rem; color:var(--muted); }
.verify{ font-size:.74rem; color:var(--muted); margin-bottom:12px; }
.actions{ display:flex; gap:10px; flex-wrap:wrap; }
.linkbtn{ display:inline-flex; align-items:center; gap:7px; padding:9px 16px; border-radius:14px; font-weight:800; font-size:.82rem;
  color:#04362a !important; text-decoration:none !important; background:linear-gradient(180deg,#8bffd8,#2df5a8);
  box-shadow:0 4px 0 #11a074; transition:transform .15s ease; }
.linkbtn:hover{ transform:translateY(-2px); }
.linkbtn.alt{ background:linear-gradient(180deg,#fffdf6,#f4ead0); color:var(--sea-deep) !important; box-shadow:0 4px 0 var(--edge); }
.chip.red{ background:linear-gradient(180deg,#ffe3df,#ffc4bd); color:#9a2a20; box-shadow:0 3px 0 #f0a39b; }
.chip.dark{ background:linear-gradient(180deg,#10705c,#073b32); color:#d9fff0; box-shadow:0 3px 0 #04271f; }
.chip.amber{ background:linear-gradient(180deg,#fff1d2,#ffe2a6); color:#7a4e07; box-shadow:0 3px 0 #efca85; }
[role="radiogroup"]{ gap:6px; }
[role="radiogroup"] label{ background:linear-gradient(180deg,#fffdf6,#f4ead0); padding:8px 16px; border-radius:14px;
  box-shadow:0 4px 0 var(--edge); margin-right:6px; transition:transform .15s ease; }
[role="radiogroup"] label:hover{ transform:translateY(-2px); }
[role="radiogroup"] label:has(input:checked){ background:linear-gradient(180deg,#8bffd8,#2df5a8); box-shadow:0 4px 0 #11a074; }
[role="radiogroup"] label p, .stToggle label p{ text-transform:none !important; letter-spacing:0 !important;
  font-size:.95rem !important; font-weight:700 !important; }
.legend{ display:flex; gap:18px; flex-wrap:wrap; font-size:.84rem; color:var(--ink); }
.legend span{ display:inline-flex; align-items:center; gap:8px; font-weight:600; }
.legend i{ width:11px; height:11px; border-radius:50%; display:inline-block; }

/* ---- final high-priority fix against dark-theme leftovers ---- */
html body .stApp [data-testid="stAlert"]{ background:#fffaf0 !important; }
html body .stApp [data-baseweb="select"], html body .stApp [data-baseweb="input"]{
  background:linear-gradient(145deg,#f1e6c9,#fffaf0) !important; }
html body .stApp [data-baseweb="select"] *, html body .stApp [data-baseweb="input"] *{
  background-color:transparent !important; color:#0f2f29 !important; -webkit-text-fill-color:#0f2f29 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------
# INTERACTIVITY (mouse tilt + hero parallax), injected once into the page
# ------------------------------------------------------------------
TILT_JS = """
(function(){
  if (window.__dpTilt) return; window.__dpTilt = true;
  var MAX = 8;
  function bind(el){
    if (el.__dp) return; el.__dp = true; var raf = null;
    el.addEventListener('mousemove', function(e){
      var r = el.getBoundingClientRect();
      var px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
      if (raf) return;
      raf = requestAnimationFrame(function(){
        raf = null;
        el.style.setProperty('--rx', ((0.5 - py) * MAX * 2) + 'deg');
        el.style.setProperty('--ry', ((px - 0.5) * MAX * 2) + 'deg');
        el.style.setProperty('--mx', (px * 100) + '%');
        el.style.setProperty('--my', (py * 100) + '%');
      });
    });
    el.addEventListener('mouseleave', function(){
      el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg');
    });
  }
  function scan(){ document.querySelectorAll('.tilt').forEach(bind); }
  scan();
  var t; new MutationObserver(function(){ clearTimeout(t); t = setTimeout(scan, 120); })
    .observe(document.body, {childList: true, subtree: true});
  var sraf = null;
  document.addEventListener('mousemove', function(e){
    if (sraf) return;
    sraf = requestAnimationFrame(function(){
      sraf = null;
      var s = document.querySelector('.scene'); if (!s) return;
      var x = e.clientX / window.innerWidth - 0.5, y = e.clientY / window.innerHeight - 0.5;
      s.style.setProperty('--sy', (x * 16) + 'deg'); s.style.setProperty('--sx', (-y * 12) + 'deg');
    });
  });
})();
"""
try:
    import streamlit.components.v1 as components
    components.html(
        "<script>(function(){var d=window.parent.document;if(d.getElementById('dp-js'))return;"
        "var s=d.createElement('script');s.id='dp-js';s.textContent=" + json.dumps(TILT_JS) +
        ";d.head.appendChild(s);})();</script>", height=0)
except Exception:
    pass


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def render(markup: str):
    """Render HTML safely (strips indentation and blank lines so markdown never breaks the block)."""
    cleaned = "\n".join(line.strip() for line in markup.strip().splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


_panel_count = [0]


def panel():
    _panel_count[0] += 1
    return st.container(key=f"panel_{_panel_count[0]}")


def section(icon_name, title, sub=""):
    render(f"""
    <div class="sec rise"><span class="badge">{icon(icon_name, 24, sw=2.2)}</span>
    <div><div class="sec-t">{title}</div><div class="sec-s">{sub}</div></div></div>
    """)


def stat_card(icon_name, label, value, unit="", pct=50):
    pct = max(4, min(100, pct))
    render(f"""
    <div class="clay tilt rise">
      <div class="ico3d">{icon(icon_name, 24, sw=2.2)}</div>
      <div class="k">{label}</div>
      <div class="v">{value}<small>{unit}</small></div>
      <div class="bar"><i style="width:{pct}%"></i></div>
    </div>
    """)


def feature_card(icon_name, label, value, unit, note):
    render(f"""
    <div class="clay dark tilt rise">
      <div class="ico3d">{icon(icon_name, 24, sw=2.2)}</div>
      <div class="k">{label}</div>
      <div class="v">{value}<small>{unit}</small></div>
      <div class="note">{note}</div>
    </div>
    """)


# ------------------------------------------------------------------
# LOAD ASSETS
# ------------------------------------------------------------------
@st.cache_resource
def load_model():
    return joblib.load("models/dengue_model.pkl")


@st.cache_data
def load_data():
    d = pd.read_csv("data/processed/dengue_clean.csv")
    d["date"] = pd.to_datetime(d["date"])
    return d


@st.cache_data
def load_hospitals():
    return pd.read_csv("data/raw/hospital.csv")



# ------------------------------------------------------------------
# DOCTOR DATA + SCHEDULE LOGIC
# ------------------------------------------------------------------
BD_TZ = timezone(timedelta(hours=6))  # Bangladesh has no daylight saving
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DOCTORS_FILE = "data/raw/doctors.csv"
SCHEDULE_FILE = "data/doctor_schedules.csv"
SCHEDULE_COLS = ["doctor_id", "ward", "days", "day_from", "day_to", "night_duty", "night_from", "night_to",
                 "emergency", "notes", "verified_by", "verified_at", "rt_status", "rt_by", "rt_at"]
RT_TTL_HOURS = 3  # a live confirmation stops counting after this long
TITLES = {"prof", "professor", "dr", "assoc", "asst", "associate", "assistant", "md", "m", "mohammad", "muhammad"}


def now_bd():
    return datetime.now(BD_TZ)


def _find(cols, keys, exact=None):
    low = {c: c.lower().strip() for c in cols}
    if exact:
        for c, lc in low.items():
            if lc == exact:
                return c
    for k in keys:
        for c, lc in low.items():
            if k in lc:
                return c
    return None


@st.cache_data
def load_doctors():
    try:
        raw = pd.read_csv(DOCTORS_FILE, dtype=str, encoding="utf-8-sig", on_bad_lines="skip").fillna("")
    except Exception:
        return pd.DataFrame()
    cols = list(raw.columns)
    mapping = {
        "city": _find(cols, ["city"], "city"),
        "category": _find(cols, ["requested", "category"]),
        "specialty": _find(cols, ["specialty", "speciality"]),
        "name": _find(cols, ["name"], "name"),
        "degrees": _find(cols, ["degree", "qualification"]),
        "chamber": _find(cols, ["chamber", "hospital", "location", "address"]),
        "phone": _find(cols, ["phone", "mobile", "contact"]),
    }
    out = pd.DataFrame(index=raw.index)
    for key, col in mapping.items():
        out[key] = raw[col].astype(str).str.strip() if col else ""
    out = out[out["name"] != ""].copy()
    out["spec"] = out["specialty"].where(out["specialty"] != "", out["category"])
    out["doctor_id"] = [hashlib.md5(f"{n}|{c}|{h}".encode()).hexdigest()[:10]
                        for n, c, h in zip(out["name"], out["city"], out["chamber"])]
    return out.drop_duplicates("doctor_id").reset_index(drop=True)


def load_schedules():
    s = pd.DataFrame(columns=SCHEDULE_COLS)
    if os.path.exists(SCHEDULE_FILE):
        try:
            s = pd.read_csv(SCHEDULE_FILE, dtype=str, encoding="utf-8-sig").fillna("")
        except Exception:
            s = pd.DataFrame(columns=SCHEDULE_COLS)
    for c in SCHEDULE_COLS:
        if c not in s.columns:
            s[c] = ""
    return s[SCHEDULE_COLS]


def upsert_schedule(doctor_ids, **fields):
    s = load_schedules()
    for did in doctor_ids:
        mask = s["doctor_id"] == did
        if not mask.any():
            blank = {c: "" for c in SCHEDULE_COLS}
            blank["doctor_id"] = did
            s = pd.concat([s, pd.DataFrame([blank])], ignore_index=True)
            mask = s["doctor_id"] == did
        for k, v in fields.items():
            s.loc[mask, k] = v
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
    tmp = SCHEDULE_FILE + ".tmp"
    s.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, SCHEDULE_FILE)


def _t(s):
    try:
        h, m = str(s).split(":")[:2]
        return int(h) * 60 + int(m)
    except Exception:
        return None


def _to_time(s, dh, dm):
    m = _t(s)
    return dtime(m // 60, m % 60) if m is not None else dtime(dh, dm)


def fmt12(s):
    m = _t(s)
    if m is None:
        return "—"
    h, mm = divmod(m, 60)
    return f"{(h % 12) or 12}:{mm:02d} {'AM' if h < 12 else 'PM'}"


def fmt_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%d %b, %I:%M %p")
    except Exception:
        return ""


def _in_window(t, a, b):
    if a is None or b is None:
        return False
    return a <= t <= b if a <= b else (t >= a or t <= b)


def has_schedule(sc):
    return (bool(sc) and bool(str(sc.get("days", "")).strip())
            and (bool(sc.get("day_from") and sc.get("day_to")) or sc.get("night_duty") == "yes"))


def scheduled_shift(sc, dt):
    """'day', 'night' or None: is this doctor on the *published schedule* at dt (not a live confirmation)."""
    if not has_schedule(sc):
        return None
    days = [d for d in str(sc.get("days", "")).split(",") if d]
    t = dt.hour * 60 + dt.minute
    wd, prev = DAYS[dt.weekday()], DAYS[(dt.weekday() - 1) % 7]
    if wd in days and _in_window(t, _t(sc.get("day_from")), _t(sc.get("day_to"))):
        return "day"
    if sc.get("night_duty") == "yes":
        a, b = _t(sc.get("night_from")), _t(sc.get("night_to"))
        if a is not None and b is not None:
            if a <= b:
                if wd in days and a <= t <= b:
                    return "night"
            else:  # overnight shift, e.g. 22:00 to 06:00
                if t >= a and wd in days:
                    return "night"
                if t <= b and prev in days:
                    return "night"
    return None


def rt_state(sc, now):
    if not sc or not sc.get("rt_status") or not sc.get("rt_at"):
        return None
    try:
        at = datetime.fromisoformat(sc["rt_at"])
    except Exception:
        return None
    if at.tzinfo is None:
        at = at.replace(tzinfo=BD_TZ)
    if now - at > timedelta(hours=RT_TTL_HOURS):
        return None  # expired, never treated as current
    return sc["rt_status"], at, sc.get("rt_by", "")


def availability(sc, eval_dt, is_now):
    """Only a fresh staff confirmation is 'confirmed'. A schedule alone is never shown as confirmed."""
    if is_now:
        rt = rt_state(sc, now_bd())
        if rt:
            status, at, by = rt
            sub = f"Confirmed by {by or 'hospital staff'} at {at:%I:%M %p}"
            if status == "available":
                return {"kind": "confirmed_yes", "label": "Confirmed available now", "sub": sub, "color": "#1fbf96"}
            return {"kind": "confirmed_no", "label": "Confirmed NOT available", "sub": sub, "color": "#ff5a4f"}
    if not has_schedule(sc):
        return {"kind": "unknown", "label": "Schedule not verified", "sub": "No confirmed information. Call before you go.", "color": "#8a9a94"}
    shift = scheduled_shift(sc, eval_dt)
    if shift:
        return {"kind": "scheduled", "shift": shift, "label": f"Scheduled · {shift} shift",
                "sub": "Not confirmed live. Please call to confirm.", "color": "#f5a524"}
    return {"kind": "off", "label": "Not on schedule at this time", "sub": "Outside the listed duty hours.", "color": "#8a9a94"}


def tonight_availability(sc, now):
    if has_schedule(sc) and sc.get("night_duty") == "yes" and DAYS[now.weekday()] in str(sc.get("days", "")).split(","):
        return {"kind": "scheduled", "shift": "night", "label": "Scheduled · night duty tonight",
                "sub": f"{fmt12(sc.get('night_from'))} – {fmt12(sc.get('night_to'))} · not confirmed live, please call.",
                "color": "#f5a524"}
    return None


def maps_link(chamber, city):
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(f"{chamber} {city} Bangladesh")


def doctor_card(r, sc, av):
    esc = htmllib.escape
    sc = sc or {}
    words = [w for w in re.findall(r"[A-Za-z]+", r.name) if w.lower() not in TITLES]
    initials = ((words[0][0] + (words[1][0] if len(words) > 1 else "")) if words else "DR").upper()
    days = [d for d in str(sc.get("days", "")).split(",") if d]
    day_txt = (f"{fmt12(sc.get('day_from'))} – {fmt12(sc.get('day_to'))}"
               if days and sc.get("day_from") and sc.get("day_to") else "Not listed")
    night_txt = (f"{fmt12(sc.get('night_from'))} – {fmt12(sc.get('night_to'))}"
                 if sc.get("night_duty") == "yes" and sc.get("night_from") else "No night duty listed")
    chips = []
    if r.spec:
        chips.append(f'<span class="chip">{icon("stethoscope", 14, sw=2.4)} {esc(r.spec)}</span>')
    if sc.get("emergency") == "yes":
        chips.append(f'<span class="chip red">{icon("siren", 14, sw=2.4)} Emergency duty</span>')
    if sc.get("night_duty") == "yes":
        chips.append(f'<span class="chip dark">{icon("moon", 14, sw=2.4)} Night duty</span>')
    place = ", ".join(x for x in [sc.get("ward", ""), r.city] if x)
    verified = (f"Schedule verified by {esc(sc.get('verified_by', 'staff'))} · {fmt_date(sc.get('verified_at', ''))}"
                if sc.get("verified_at") else "No verified schedule yet")
    actions = []
    if r.phone:
        first = re.split(r"[,/;]", r.phone)[0]
        digits = re.sub(r"[^\d+]", "", first)
        actions.append(f'<a class="linkbtn" href="tel:{digits}">{icon("phone", 14, sw=2.4)} {esc(r.phone[:34])}</a>')
    actions.append(f'<a class="linkbtn alt" href="{maps_link(r.chamber or r.name, r.city)}" target="_blank" rel="noopener">'
                   f'{icon("pin", 14, sw=2.4)} Directions</a>')
    render(f"""
    <div class="clay tilt rise" style="margin-bottom:30px;">
      <div class="doc-head"><div class="avatar">{esc(initials)}</div>
        <div><div class="name">{esc(r.name)}</div><div class="deg">{esc(r.degrees[:110])}</div></div></div>
      <div class="row" style="margin-top:14px;">{''.join(chips)}</div>
      <div class="kv">{icon('hospital', 17)}<span>{esc(r.chamber or 'Chamber not listed')}<small>{esc(place)}</small></span></div>
      <div class="kv">{icon('calendar', 17)}<span>{' · '.join(days) if days else 'Duty days not listed'}</span></div>
      <div class="kv">{icon('sun', 17)}<span>Day: {day_txt}</span></div>
      <div class="kv">{icon('moon', 17)}<span>Night: {night_txt}</span></div>
      <div class="avail" style="border-color:{av['color']}66;"><i style="background:{av['color']};box-shadow:0 0 12px {av['color']};"></i>
        <div><b style="color:{av['color']};">{av['label']}</b><span>{av['sub']}</span></div></div>
      <div class="verify">{verified}</div>
      <div class="actions">{''.join(actions)}</div>
    </div>
    """)


def admin_password():
    try:
        return str(st.secrets["ADMIN_PASSWORD"])
    except Exception:
        return os.environ.get("ADMIN_PASSWORD", "dengue-admin")


def page_find_doctor():
    esc = htmllib.escape
    section("user", "Find a doctor", "Search by city, ward, specialization and time")
    st.warning("**How to read availability:** a green status means hospital staff confirmed it within the last "
               f"{RT_TTL_HOURS} hours. An amber status only means the doctor is *on the published schedule*. "
               "It is not a guarantee. Always call to confirm, especially at night or in an emergency.")
    if doctors.empty:
        st.error("Could not load `data/raw/doctors.csv`. Check the file path and try again.")
        return
    sd = load_schedules().set_index("doctor_id").to_dict("index")
    now = now_bd()

    with panel():
        a, b, c = st.columns(3, gap="large")
        with a:
            cities = sorted(x for x in doctors["city"].unique() if x)
            city = st.selectbox("City", ["All cities"] + cities, key="fd_city")
        base = doctors if city == "All cities" else doctors[doctors["city"] == city]
        with b:
            wards = sorted({sd[i]["ward"] for i in base["doctor_id"] if i in sd and sd[i]["ward"]})
            ward = st.selectbox("Ward", ["Any ward"] + wards, key="fd_ward")
        with c:
            specs = sorted(x for x in base["spec"].unique() if x)
            spec = st.selectbox("Specialization", ["All specialties"] + specs, key="fd_spec")
        d, e = st.columns([2, 1], gap="large")
        with d:
            when = st.radio("Availability time", ["Any time", "Right now", "Tonight (night duty)", "Pick a time"],
                            horizontal=True, key="fd_when")
        with e:
            q = st.text_input("Doctor name", placeholder="e.g. Rafiqul", key="fd_q")
        eval_dt = now
        if when == "Pick a time":
            p1, p2 = st.columns(2, gap="large")
            wd_sel = p1.selectbox("Day", DAYS, index=now.weekday(), key="fd_day")
            t_sel = p2.time_input("Time", value=dtime(22, 0), key="fd_time")
            eval_dt = (now + timedelta(days=(DAYS.index(wd_sel) - now.weekday()) % 7)).replace(
                hour=t_sel.hour, minute=t_sel.minute, second=0, microsecond=0)
        t1, t2 = st.columns(2, gap="large")
        emerg_only = t1.toggle("Emergency duty only", key="fd_em")
        verified_only = t2.toggle("Verified schedules only", key="fd_ver")

    f = base
    if spec != "All specialties":
        f = f[f["spec"] == spec]
    if q:
        f = f[f["name"].str.contains(q, case=False, na=False, regex=False)]

    rows = []
    for r in f.itertuples(index=False):
        sc = sd.get(r.doctor_id)
        if ward != "Any ward" and (not sc or sc.get("ward") != ward):
            continue
        if verified_only and not (sc and sc.get("verified_at")):
            continue
        if emerg_only and not (sc and sc.get("emergency") == "yes"):
            continue
        if when == "Right now":
            av = availability(sc, now, True)
            if av["kind"] not in ("confirmed_yes", "scheduled"):
                continue
        elif when == "Tonight (night duty)":
            tn = tonight_availability(sc, now)
            if tn is None:
                continue
            av0 = availability(sc, now, True)
            av = av0 if av0["kind"] in ("confirmed_yes", "confirmed_no") else tn
        elif when == "Pick a time":
            av = availability(sc, eval_dt, False)
            if av["kind"] != "scheduled":
                continue
        else:
            av = availability(sc, now, True)
        rows.append((r, sc, av))

    rank = {"confirmed_yes": 0, "scheduled": 1, "off": 2, "unknown": 3, "confirmed_no": 4}
    rows.sort(key=lambda x: (rank[x[2]["kind"]], x[0].name))

    # ---- hospitals with doctors on duty ----
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    section("hospital", "Hospitals with doctors on duty", "Confirmed live and scheduled are counted separately")
    hosp = {}
    for r, sc, av in rows:
        if not r.chamber or av["kind"] not in ("confirmed_yes", "scheduled"):
            continue
        h = hosp.setdefault(r.chamber, {"yes": 0, "sch": 0, "night": False, "city": r.city})
        if av["kind"] == "confirmed_yes":
            h["yes"] += 1
        else:
            h["sch"] += 1
        if av.get("shift") == "night" or (sc and sc.get("night_duty") == "yes"):
            h["night"] = True
    top = sorted(hosp.items(), key=lambda kv: (-kv[1]["yes"], -kv[1]["sch"]))[:6]
    if not top:
        st.info("No hospital has a doctor on duty for this search yet. Hospital staff can add schedules in the "
                "**Staff Admin** tab. Until then, doctors show as *schedule not verified*.")
    else:
        cols = st.columns(3, gap="large")
        for i, (name, h) in enumerate(top):
            chips = []
            if h["yes"]:
                chips.append(f'<span class="chip">● {h["yes"]} confirmed live</span>')
            if h["sch"]:
                chips.append(f'<span class="chip amber">{h["sch"]} scheduled · unconfirmed</span>')
            if h["night"]:
                chips.append(f'<span class="chip dark">{icon("moon", 14, sw=2.4)} Night shift</span>')
            with cols[i % 3]:
                render(f"""
                <div class="clay tilt rise" style="margin-bottom:26px;">
                  <div class="ico3d">{icon('hospital', 24, sw=2.2)}</div>
                  <div class="name">{esc(name[:70])}</div>
                  <div class="row">{''.join(chips)}</div>
                  <div class="actions"><a class="linkbtn alt" href="{maps_link(name, h['city'])}" target="_blank" rel="noopener">{icon('pin', 14, sw=2.4)} Open in Maps</a></div>
                </div>
                """)

    # ---- map ----
    chambers = list(dict.fromkeys(r.chamber for r, _, _ in rows if r.chamber))[:60]
    if chambers:
        with panel():
            section("pin", "Hospital location map", "Pick a hospital from your results")
            pick = st.selectbox("Hospital / chamber", chambers, key="fd_map")
            city_for = next((r.city for r, _, _ in rows if r.chamber == pick), "")
            try:
                import streamlit.components.v1 as _c
                _c.iframe("https://www.google.com/maps?q=" + urllib.parse.quote_plus(f"{pick} {city_for} Bangladesh")
                          + "&output=embed", height=340)
            except Exception:
                st.markdown(f"[Open {pick} in Google Maps]({maps_link(pick, city_for)})")

    # ---- doctor cards ----
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    section("user", f"{len(rows)} doctors found", "Confirmed first, then scheduled, then unverified")
    render(f"""
    <div class="legend" style="margin-bottom:20px;">
      <span><i style="background:#1fbf96"></i>Confirmed by staff (last {RT_TTL_HOURS}h)</span>
      <span><i style="background:#f5a524"></i>On schedule, not confirmed</span>
      <span><i style="background:#8a9a94"></i>Not on schedule / not verified</span>
      <span><i style="background:#ff5a4f"></i>Confirmed not available</span>
    </div>
    """)
    if not rows:
        st.info("No doctors match these filters. Try widening the city, specialty or time.")
        return
    limit = st.session_state.get("fd_limit", 12)
    cols = st.columns(2, gap="large")
    for i, (r, sc, av) in enumerate(rows[:limit]):
        with cols[i % 2]:
            doctor_card(r, sc, av)
    if len(rows) > limit:
        if st.button("Show more doctors", icon=":material/expand_more:", key="fd_more"):
            st.session_state["fd_limit"] = limit + 12
            st.rerun()


def page_admin():
    section("lock", "Staff admin", "For authorised hospital staff only")
    if not st.session_state.get("is_admin"):
        with panel():
            st.markdown("Sign in to update doctor schedules and confirm real-time availability.")
            pw = st.text_input("Staff password", type="password", key="adm_pw")
            if st.button("Sign in", icon=":material/lock_open:", key="adm_login"):
                if hmac.compare_digest(pw.encode(), admin_password().encode()):
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        return
    if doctors.empty:
        st.error("Could not load `data/raw/doctors.csv`.")
        return

    top1, top2 = st.columns([4, 1], gap="large")
    with top1:
        staff = st.text_input("Your name / staff ID (recorded with every change)", key="adm_staff")
    with top2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Sign out", icon=":material/logout:", key="adm_out"):
            st.session_state["is_admin"] = False
            st.rerun()

    with panel():
        a, b = st.columns(2, gap="large")
        with a:
            cities = sorted(x for x in doctors["city"].unique() if x)
            city = st.selectbox("City", ["All cities"] + cities, key="adm_city")
        with b:
            search = st.text_input("Search doctor", placeholder="Name", key="adm_search")
        pool = doctors if city == "All cities" else doctors[doctors["city"] == city]
        if search:
            pool = pool[pool["name"].str.contains(search, case=False, na=False, regex=False)]
        pool = pool.head(300)
        if pool.empty:
            st.info("No doctors match.")
            return
        lookup = pool.set_index("doctor_id")
        sel = st.selectbox(
            "Doctor", lookup.index.tolist(), key="adm_doc",
            format_func=lambda i: f"{lookup.loc[i, 'name']} · {lookup.loc[i, 'spec']} · {lookup.loc[i, 'chamber']}"[:120])
        chosen = lookup.loc[sel]
        sched = load_schedules()
        cur = sched[sched["doctor_id"] == sel]
        sc = cur.iloc[0].to_dict() if not cur.empty else {}

        with st.form("sched_form"):
            ward = st.text_input("Ward", value=sc.get("ward", ""))
            days = st.multiselect("Duty days", DAYS, default=[d for d in str(sc.get("days", "")).split(",") if d in DAYS])
            c1, c2 = st.columns(2, gap="large")
            day_from = c1.time_input("Day shift starts", value=_to_time(sc.get("day_from"), 9, 0))
            day_to = c2.time_input("Day shift ends", value=_to_time(sc.get("day_to"), 14, 0))
            night = st.toggle("Night duty", value=sc.get("night_duty") == "yes")
            n1, n2 = st.columns(2, gap="large")
            night_from = n1.time_input("Night shift starts", value=_to_time(sc.get("night_from"), 22, 0))
            night_to = n2.time_input("Night shift ends", value=_to_time(sc.get("night_to"), 6, 0))
            emerg = st.toggle("Emergency duty", value=sc.get("emergency") == "yes")
            notes = st.text_area("Notes (optional)", value=sc.get("notes", ""))
            same = st.checkbox("Apply this schedule to every doctor at the same chamber")
            submitted = st.form_submit_button("Save verified schedule", icon=":material/save:")
        if submitted:
            if not staff.strip():
                st.error("Enter your name or staff ID first. Every change is recorded.")
            elif not days:
                st.error("Choose at least one duty day.")
            else:
                ids = [sel]
                if same and chosen["chamber"]:
                    ids = doctors[(doctors["chamber"] == chosen["chamber"]) & (doctors["city"] == chosen["city"])]["doctor_id"].tolist()
                upsert_schedule(ids, ward=ward.strip(), days=",".join(days),
                                day_from=day_from.strftime("%H:%M"), day_to=day_to.strftime("%H:%M"),
                                night_duty="yes" if night else "no", night_from=night_from.strftime("%H:%M"),
                                night_to=night_to.strftime("%H:%M"), emergency="yes" if emerg else "no",
                                notes=notes.strip(), verified_by=staff.strip(),
                                verified_at=now_bd().isoformat(timespec="minutes"))
                st.success(f"Saved schedule for {len(ids)} doctor(s). This is a *scheduled* time, not a live confirmation.")

        st.markdown("**Real-time confirmation**")
        st.caption(f"Use these only after you have actually checked. A confirmation shows to patients for "
                   f"{RT_TTL_HOURS} hours, then expires on its own.")
        r1, r2, r3 = st.columns(3, gap="large")
        stamp = now_bd().isoformat(timespec="minutes")
        if r1.button("Confirm available now", icon=":material/check_circle:", key="rt_yes"):
            if staff.strip():
                upsert_schedule([sel], rt_status="available", rt_by=staff.strip(), rt_at=stamp)
                st.success("Marked as confirmed available.")
            else:
                st.error("Enter your name or staff ID first.")
        if r2.button("Confirm NOT available", icon=":material/cancel:", key="rt_no"):
            if staff.strip():
                upsert_schedule([sel], rt_status="unavailable", rt_by=staff.strip(), rt_at=stamp)
                st.success("Marked as confirmed not available.")
            else:
                st.error("Enter your name or staff ID first.")
        if r3.button("Clear confirmation", icon=":material/restart_alt:", key="rt_clr"):
            upsert_schedule([sel], rt_status="", rt_by="", rt_at="")
            st.success("Confirmation cleared.")

    # fresh preview of what patients will see
    fresh = load_schedules()
    cur = fresh[fresh["doctor_id"] == sel]
    sc = cur.iloc[0].to_dict() if not cur.empty else None
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section("user", "What patients see", "Live preview for the selected doctor")
    pc1, pc2 = st.columns([1, 1], gap="large")
    row = next(doctors[doctors["doctor_id"] == sel].itertuples(index=False))
    with pc1:
        doctor_card(row, sc, availability(sc, now_bd(), True))
    with pc2:
        n_sched = int((fresh["days"] != "").sum())
        n_ver = int((fresh["verified_at"] != "").sum())
        n_live = sum(1 for _, x in fresh.iterrows() if rt_state(x.to_dict(), now_bd()))
        stat_card("calendar", "Doctors with a schedule", f"{n_sched}", "", min(100, n_sched))
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        stat_card("check", "Live confirmations active", f"{n_live}", "", min(100, n_live * 10))
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        st.download_button("Download schedules (CSV)", fresh.to_csv(index=False).encode("utf-8"),
                           file_name="doctor_schedules.csv", mime="text/csv", icon=":material/download:")


model = load_model()
df = load_data()
hospitals = load_hospitals()
doctors = load_doctors()

# ------------------------------------------------------------------
# HERO
# ------------------------------------------------------------------
render(f"""
<div class="hero rise">
  <div>
    <span class="pill"><span class="dot"></span>LIVE MONITORING</span>
    <div class="hero-title">Spot dengue<br>before it <em>spreads.</em></div>
    <p class="hero-sub">Ward-level outbreak forecasts, a quick symptom check and a live view of hospital capacity, all in one place.</p>
    <div class="hero-stats">
      <div class="hstat"><b>{df['city'].nunique()}</b><span>Cities</span></div>
      <div class="hstat"><b>{df['ward_id'].nunique()}</b><span>Wards tracked</span></div>
      <div class="hstat"><b>{len(hospitals)}</b><span>Facilities</span></div>
      <div class="hstat"><b>{len(doctors)}</b><span>Doctors listed</span></div>
    </div>
  </div>
  <div class="scene" aria-hidden="true">
    <div class="ring r2"></div>
    <div class="ring r1"></div>
    <div class="orb">{icon('activity', 84, '#ffffff', 1.7)}</div>
    <div class="chip3d c1"><div class="mini">{icon('cpu', 18, sw=2.2)}</div><div><b>AI forecast</b><span>NEXT WEEK</span></div></div>
    <div class="chip3d c2"><div class="mini">{icon('pin', 18, sw=2.2)}</div><div><b>Ward level</b><span>PRECISE</span></div></div>
    <div class="chip3d c3"><div class="mini">{icon('droplets', 18, sw=2.2)}</div><div><b>Rain lag</b><span>2 &amp; 4 WEEKS</span></div></div>
  </div>
</div>
""")

tab1, tab2, tab4, tab3, tab5 = st.tabs([
    ":material/dashboard:  Outbreak Dashboard",
    ":material/stethoscope:  Patient Assessment",
    ":material/medical_services:  Find a Doctor",
    ":material/local_hospital:  Hospital Support",
    ":material/admin_panel_settings:  Staff Admin",
])

# ==================================================================
# TAB 1 : OUTBREAK DASHBOARD
# ==================================================================
with tab1:
    col_side, col_main = st.columns([1, 3], gap="large")
    pred, risk_score, latest_data, ward_df, ward = 0, 0, pd.DataFrame(), pd.DataFrame(), ""

    with col_side:
        with panel():
            section("pin", "Location", "Pick a city and ward")
            city = st.selectbox("City", df["city"].unique())
            ward = st.selectbox("Ward", df[df["city"] == city]["ward_id"].unique())

            ward_df = df[(df["city"] == city) & (df["ward_id"] == ward)].sort_values("date")
            latest_data = ward_df.tail(1)

            if not latest_data.empty:
                features = ["rainfall_mm", "avg_temp_c", "relative_humidity_pct", "rain_lag_2w", "rain_lag_4w",
                            "temp_rolling_4w", "humidity_rolling_4w", "dengue_lag_1w", "month", "week"]
                pred = max(0, float(model.predict(latest_data[features])[0]))
                risk_score = min(100, int((pred / 50) * 100))
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                feature_card("cpu", "Predicted cases", f"{int(pred)}", " next wk", "AI inference active for this ward")

    with col_main:
        if latest_data.empty:
            st.info("No data available for this ward.")
        else:
            section("gauge", f"Current conditions", f"Latest readings for {ward}")
            c1, c2, c3 = st.columns(3, gap="large")
            temp = latest_data["avg_temp_c"].values[0]
            hum = latest_data["relative_humidity_pct"].values[0]
            rainv = latest_data["rainfall_mm"].values[0]
            with c1:
                stat_card("thermometer", "Avg temperature", f"{temp:.1f}", "°C", temp / 40 * 100)
            with c2:
                stat_card("droplets", "Humidity", f"{hum:.1f}", "%", hum)
            with c3:
                stat_card("rain", "Rainfall", f"{rainv:.1f}", "mm", rainv / 100 * 100)

            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            col_chart, col_risk = st.columns([2, 1], gap="large")

            with col_chart:
                with panel():
                    section("trend", "Dengue & rainfall trend", "Weekly cases against rainfall")
                    chart_df = ward_df[["date", "dengue_cases", "rainfall_mm"]]
                    x = alt.X("date:T", title=None, axis=alt.Axis(grid=False, labelColor="#56726a", domainColor="#bfd9cf"))
                    cases = alt.Chart(chart_df).mark_area(
                        line={"color": "#0b9f7a", "strokeWidth": 2.8},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[alt.GradientStop(color="rgba(45,245,168,0.6)", offset=0),
                                   alt.GradientStop(color="rgba(45,245,168,0.02)", offset=1)],
                            x1=1, x2=1, y1=1, y2=0),
                        interpolate="monotone",
                    ).encode(x=x, y=alt.Y("dengue_cases:Q", title="Cases",
                                          axis=alt.Axis(labelColor="#0b9f7a", titleColor="#0b9f7a", gridColor="#e3ecdf")),
                             tooltip=["date:T", "dengue_cases:Q"])
                    rain = alt.Chart(chart_df).mark_line(
                        color="#e0a458", strokeWidth=2, strokeDash=[5, 4], interpolate="monotone"
                    ).encode(x=x, y=alt.Y("rainfall_mm:Q", title="Rainfall (mm)",
                                          axis=alt.Axis(labelColor="#c4873a", titleColor="#c4873a", grid=False)),
                             tooltip=["date:T", "rainfall_mm:Q"])
                    chart = (alt.layer(cases, rain).resolve_scale(y="independent")
                             .properties(height=300).configure(background="transparent")
                             .configure_view(strokeWidth=0))
                    try:
                        st.altair_chart(chart, width="stretch")
                    except TypeError:
                        st.altair_chart(chart, use_container_width=True)

            with col_risk:
                with panel():
                    section("shield-alert", "Risk level", "From the AI forecast")
                    if risk_score > 75:
                        color, tier, msg, idx = "#ff5a4f", "CRITICAL", "Immediate vector control required.", 3
                    elif risk_score > 50:
                        color, tier, msg, idx = "#f5a524", "HIGH", "Deploy medical resources.", 2
                    elif risk_score > 25:
                        color, tier, msg, idx = "#8bd450", "MEDIUM", "Monitor closely.", 1
                    else:
                        color, tier, msg, idx = "#1fbf96", "LOW", "Normal conditions.", 0
                    seg = ["#1fbf96", "#8bd450", "#f5a524", "#ff5a4f"]
                    scale = "".join(
                        f'<i style="background:{c};opacity:{1 if i <= idx else .2}"></i>' for i, c in enumerate(seg))
                    render(f"""
                    <div class="risk tilt">
                      <div class="ring2" style="background:conic-gradient({color} {risk_score}%, rgba(11,79,67,.1) 0);">
                        <div class="inner"><div class="num">{risk_score}<small>OUT OF 100</small></div></div>
                      </div>
                      <span class="tier" style="background:{color};box-shadow:0 5px 0 rgba(0,0,0,.2), 0 0 22px {color}99;">{tier} RISK</span>
                      <p class="msg">{msg}</p>
                      <div class="scale">{scale}</div>
                      <div class="scale-l"><span>LOW</span><span>CRITICAL</span></div>
                    </div>
                    """)
                                        # --- BONUS: Model Validation Metrics ---
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#0b4f43; font-size:0.85rem; font-weight:800; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px;'>🎯 Model Validation</h4>", unsafe_allow_html=True)
                    try:
                        with open("models/validation_metrics.txt", "r") as f:
                            metrics = f.read().split('\n')
                        mae_val = metrics[0].split(': ')[1]
                        rmse_val = metrics[1].split(': ')[1]
                        render(f"""
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <div class="chip" style="flex: 1; justify-content: center; font-size: 0.9rem;">MAE: {mae_val}</div>
                            <div class="chip" style="flex: 1; justify-content: center; font-size: 0.9rem;">RMSE: {rmse_val}</div>
                        </div>
                        <p style="font-size: 0.7rem; color: #56726a; margin-top: 10px; text-align: center;">Chronological Split (Train: Pre-2025)</p>
                        """)
                    except Exception:
                        st.caption("Validation metrics not found.")

# ==================================================================
# TAB 2 : PATIENT ASSESSMENT
# ==================================================================
with tab2:
    section("stethoscope", "Symptom checker", "A quick guide, not a diagnosis")
    st.warning("**Disclaimer:** This is an AI-based assessment and not a medical diagnosis. "
               "See a doctor immediately if symptoms are severe.")

    with panel():
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.number_input("Patient age", min_value=1, max_value=120, value=25)
            st.selectbox("Patient city", df["city"].unique(), key="p_city")
        with col2:
            st.markdown("**Select symptoms**")
            s_fever = st.checkbox(":material/thermostat:  High fever")
            s_headache = st.checkbox(":material/psychology:  Severe headache")
            s_pain = st.checkbox(":material/fitness_center:  Muscle / body pain")
            s_rash = st.checkbox(":material/blur_on:  Skin rash")
            s_vomit = st.checkbox(":material/sick:  Vomiting / nausea")

        count = sum([s_fever, s_headache, s_pain, s_rash, s_vomit])
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        m1, m2 = st.columns([2, 1], gap="large")
        with m1:
            render(f"""
            <div class="meter"><span class="lbl">{count} of 5 symptoms</span>
            <div class="bar"><i style="width:{max(4, count * 20)}%"></i></div></div>
            """)
        with m2:
            assess = st.button("Assess symptoms", icon=":material/vital_signs:")

    if assess:
        if count >= 4:
            c, t, m, ic = "#ff5a4f", "High risk of dengue", "Multiple severe symptoms. Please visit the nearest hospital immediately.", "shield-alert"
        elif count >= 2:
            c, t, m, ic = "#f5a524", "Moderate risk", "Monitor your temperature closely and consult a doctor if symptoms persist.", "triangle"
        else:
            c, t, m, ic = "#1fbf96", "Low risk", "Rest and stay hydrated. If you develop a fever, consult a physician.", "shield-check"
        render(f"""
        <div class="result tilt rise" style="border-left:8px solid {c};box-shadow:0 7px 0 #dccfa8, 0 24px 40px {c}44;">
          <div class="ico3d" style="background:linear-gradient(145deg,{c},{c}cc);box-shadow:0 5px 0 rgba(0,0,0,.2), 0 12px 20px {c}66;">{icon(ic, 30, '#fff', 2.2)}</div>
          <div><h3 style="color:{c} !important;">{t}</h3><p>{m}</p></div>
        </div>
        """)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section("shield-check", "Prevention essentials", "Small habits that cut your risk")
    t1, t2, t3 = st.columns(3, gap="large")
    tips = [
        ("bug", "Block bites", "Use repellent and wear long sleeves, especially at dawn and dusk."),
        ("droplets", "Remove standing water", "Empty buckets, pots and trays weekly so mosquitoes can't breed."),
        ("thermometer", "Watch your fever", "A fever lasting over two days needs a doctor's check, not guesswork."),
    ]
    for col, (ic, ttl, body) in zip((t1, t2, t3), tips):
        with col:
            render(f"""
            <div class="clay tip tilt rise">
              <div class="ico3d">{icon(ic, 24, sw=2.2)}</div>
              <div class="t">{ttl}</div><p>{body}</p>
            </div>
            """)

# ==================================================================
# TAB 3 : HOSPITAL SUPPORT
# ==================================================================
with tab3:
    section("hospital", "Hospital & doctor availability", "Find capacity near you")
    st.info("Schedules are verified for duty hours, but real-time availability must be confirmed by phone.")

    with panel():
        f1, f2 = st.columns(2, gap="large")
        with f1:
            selected_city = st.selectbox("City", hospitals["city"].unique())
        with f2:
            query = st.text_input("Search by name", placeholder="e.g. Medical College")

    filtered = hospitals[hospitals["city"] == selected_city]
    if query:
        filtered = filtered[filtered["hospital_name"].str.contains(query, case=False, na=False)]

    total_beds = pd.to_numeric(filtered["total_beds"], errors="coerce").sum()
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3, gap="large")
    with s1:
        stat_card("hospital", "Facilities found", f"{len(filtered)}", "", min(100, len(filtered) * 10))
    with s2:
        stat_card("bed", "Total beds", f"{int(total_beds)}", "", min(100, total_beds / 20))
    with s3:
        stat_card("pin", "City", f"{htmllib.escape(str(selected_city))}", "", 100)

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("No facilities match this search. Try another city or clear the search box.")

    def status_color(text):
        t = str(text).lower()
        if any(w in t for w in ("full", "critical", "over", "limited")):
            return "#ff5a4f"
        if any(w in t for w in ("moderate", "busy", "partial")):
            return "#f5a524"
        return "#1fbf96"

    cols = st.columns(2, gap="large")
    esc = htmllib.escape
    for i, (_, row) in enumerate(filtered.iterrows()):
        sc = status_color(row["capacity_status"])
        with cols[i % 2]:
            render(f"""
            <div class="clay hosp tilt rise" style="margin-bottom:30px;">
              <div class="ico3d">{icon('hospital', 24, sw=2.2)}</div>
              <div class="name">{esc(str(row['hospital_name']))}</div>
              <div class="row">
                <span class="chip">{icon('layers', 14, sw=2.4)} {esc(str(row['hospital_type']))}</span>
                <span class="chip">{icon('bed', 14, sw=2.4)} {esc(str(row['total_beds']))} beds</span>
              </div>
              <div class="status" style="color:{sc};"><i style="background:{sc};box-shadow:0 0 12px {sc};"></i>{esc(str(row['capacity_status']))}</div>
            </div>
            """)

# ==================================================================
# TAB 4 : FIND A DOCTOR   |   TAB 5 : STAFF ADMIN
# ==================================================================
with tab4:
    page_find_doctor()

with tab5:
    page_admin()

with tab5:
    page_admin()

render('<div class="foot">DenguePulse · built by Team [KILL-9] · Empowering public health with AI</div>')
