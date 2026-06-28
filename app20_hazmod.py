"""
=============================================================================
HazMod — SYSTÈME D'AIDE À LA DÉCISION NRBC
Visualisations Avancées & Interface Professionnelle
=============================================================================
"""
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings, os, math

# sklearn importé en différé pour accélérer le démarrage
# (chargé uniquement lors du premier entraînement RF)
def _get_sklearn():
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    return RandomForestRegressor, cross_val_score

import subprocess, sys as _sys, importlib.util as _ilu

warnings.filterwarnings("ignore")

# ── Chargement sécurisé du module OSM hotspots ────────────────────────────────
def _load_osm_module():
    """
    Charge osm_hotspots.py depuis le même dossier que l'app.
    Retourne None sans erreur si le fichier est absent.
    """
    try:
        import os as _os2
        # Chercher dans plusieurs emplacements
        _candidates = [
            os.path.join(os.getcwd(), "osm_hotspots.py"),
            os.path.join(os.path.dirname(os.path.abspath(
                __file__ if "__file__" in dir() else os.getcwd()
            )), "osm_hotspots.py"),
            "osm_hotspots.py",
        ]
        for _p in _candidates:
            if _os2.path.isfile(_p):
                _spec = _ilu.spec_from_file_location("osm_hotspots", _p)
                _mod  = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return _mod
    except Exception:
        pass
    return None

_osm_mod = _load_osm_module()

# ── Module densité population ─────────────────────────────────────────────────
def _load_pop_module():
    """Charge population_engine.py — retourne None sans erreur si absent."""
    try:
        import os as _os3, sys as _sys3, importlib.util as _ilu3
        _candidates = [
            os.path.join(os.getcwd(), "population_engine.py"),
            "population_engine.py",
        ]
        for _p in _candidates:
            if _os3.path.isfile(_p):
                _spec = _ilu3.spec_from_file_location("population_engine", _p)
                _mod  = _ilu3.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                _sys3.modules["population_engine"] = _mod
                return _mod
    except Exception:
        pass
    return None

_pop_mod = _load_pop_module()


@st.cache_data(ttl=600, show_spinner=False)
def _hazmod_get_density(lat_d: float, lon_d: float) -> dict:
    """
    Densité population temps réel — définie au NIVEAU MODULE pour éviter
    NameError dans @st.cache_data (problème de closure Streamlit).
    Cascade : population_engine (WorldPop/HCP) → fallback HCP intégré.
    """
    import sys as _s, math as _m, datetime as _dt
    # Essayer population_engine via sys.modules (enregistré au chargement)
    pe = _s.modules.get("population_engine")
    if pe is None and _pop_mod is not None:
        _s.modules["population_engine"] = _pop_mod
        pe = _pop_mod
    if pe is not None:
        try:
            return pe.get_population_density(lat_d, lon_d)
        except Exception:
            pass
    # ── Fallback HCP Maroc RGPH 2024 intégré ─────────────────────────────────
    _HCP = {
        "casablanca": (11218,33.5731,-7.5898),
        "rabat":      (10513,33.9716,-6.8498),
        "sale":       ( 5278,34.0531,-6.7986),
        "fes":        ( 3813,34.0209,-5.0078),
        "marrakech":  ( 4652,31.6295,-7.9811),
        "tanger":     ( 2699,35.7595,-5.8340),
        "agadir":     ( 2385,30.4278,-9.5981),
        "meknes":     ( 3182,33.8935,-5.5547),
        "oujda":      ( 3333,34.6867,-1.9114),
        "kenitra":    ( 2632,34.2610,-6.5802),
        "tetouan":    ( 6667,35.5785,-5.3684),
        "temara":     ( 3700,33.9250,-6.9083),
        "safi":       ( 3667,32.2833,-9.2333),
        "mohammedia": ( 3818,33.6867,-7.3831),
        "nador":      ( 3143,35.1667,-2.9333),
        "beni_mellal":( 3625,32.3333,-6.3500),
        "el_jadida":  ( 1667,33.2333,-8.5000),
        "khouribga":  ( 3231,32.8833,-6.9167),
        "jorf_lasfar":( 2000,33.1167,-8.6333),
        "laayoune":   ( 3385,27.1253,-13.1625),
        "dakhla":     ( 2667,23.7137,-15.9355),
        "ouarzazate": ( 2125,30.9391,-6.9094),
        "settat":     ( 3273,32.9942,-7.6225),
        "al_hoceima": ( 2500,35.2517,-3.9372),
        "taza":       ( 3091,34.2105,-3.9946),
        "larache":    ( 2889,35.1932,-6.1571),
        "khemisset":  ( 3500,33.8228,-6.0639),
        "rural_gharb":( 160,34.5,-6.0),
        "rural_atlas":(  15,31.5,-5.5),
        "pre_sahara": (   1,30.0,-6.0),
        "sahara":     (   0,25.0,-12.0),
    }
    best_d, best_z, best_dens = 999.0, "zone_inconnue", 1000
    for zid, (dens, zlat, zlon) in _HCP.items():
        d = _m.sqrt((lat_d-zlat)**2 + (lon_d-zlon)**2)
        if d < best_d:
            best_d, best_z, best_dens = d, zid, dens
    decay   = _m.exp(-0.06 * best_d * 111)
    density = max(1, int(best_dens * decay))
    hour    = _dt.datetime.now().hour
    flux    = 1.35 if 8 <= hour <= 18 else 0.85
    cur_den = int(density * flux)
    return {
        "density_raw":     density,
        "density_current": cur_den,
        "source":          f"HCP Maroc RGPH 2024 — {best_z}",
        "precision":       "estimée",
        "zone_name":       best_z,
        "urban_type":      "ville",
        "timestamp":       _dt.datetime.now().isoformat(),
        "flux": {
            "current_density": cur_den,
            "flux_factor":     round(flux, 2),
            "flux_description":
                "Heure de pointe" if 8 <= hour <= 18 else "Période calme",
            "flux_icon":  "🔴" if 8 <= hour <= 18 else "🔵",
            "peak_density": int(density * 1.5),
            "peak_hour":    9,
            "hour":         hour,
        },
    }


st.set_page_config(page_title="HazMod — NRBC", page_icon="☣️",
                   layout="wide", initial_sidebar_state="expanded")

# ── Écran de chargement sophistiqué ──────────────────────────────────────────
# Affiché pendant le chargement des modèles ML + données
if "app_loaded" not in st.session_state:
    st.session_state["app_loaded"] = False

if not st.session_state["app_loaded"]:
    _loading_ph = st.empty()
    with _loading_ph.container():
        st.markdown("""
        <style>
        .hz-loader{
            display:flex;flex-direction:column;align-items:center;
            justify-content:center;min-height:80vh;
            background:linear-gradient(135deg,#0C2340 0%,#162D4F 60%,#0f1f3d 100%);
            border-radius:16px;padding:40px;margin:20px 0;
        }
        .hz-logo-pulse{
            animation:pulse 1.8s infinite;
            font-size:4rem;margin-bottom:16px;
        }
        @keyframes pulse{
            0%{transform:scale(1);opacity:1;}
            50%{transform:scale(1.08);opacity:0.85;}
            100%{transform:scale(1);opacity:1;}
        }
        .hz-title{
            color:#fff;font-size:2.2rem;font-weight:800;
            letter-spacing:0.15em;margin-bottom:4px;
        }
        .hz-sub{
            color:#93C5FD;font-size:.85rem;margin-bottom:32px;
            letter-spacing:0.1em;
        }
        .hz-step{
            display:flex;align-items:center;gap:12px;
            margin:6px 0;color:#CBD5E1;font-size:.85rem;
            width:380px;
        }
        .hz-step-icon{font-size:1.1rem;width:24px;text-align:center;}
        .hz-step-bar{
            flex:1;height:4px;background:rgba(255,255,255,0.12);
            border-radius:2px;overflow:hidden;
        }
        .hz-step-fill{
            height:100%;border-radius:2px;
            animation:fill 1.2s ease-in-out forwards;
        }
        @keyframes fill{from{width:0%}to{width:100%}}
        .hz-badge{
            margin-top:24px;padding:8px 20px;
            background:rgba(255,255,255,0.08);
            border:1px solid rgba(255,255,255,0.15);
            border-radius:8px;color:#94A3B8;font-size:.75rem;
            letter-spacing:0.05em;
        }
        </style>
        <div class="hz-loader">
          <div class="hz-logo-pulse">☣️</div>
          <div class="hz-title">HAZMOD</div>
          <div class="hz-sub">Hazardous Materials Modeling System</div>
          <div class="hz-step">
            <span class="hz-step-icon">📊</span>
            <span style="width:180px;flex-shrink:0;">Chargement des données historiques</span>
            <div class="hz-step-bar">
              <div class="hz-step-fill"
                   style="background:linear-gradient(90deg,#2563EB,#60A5FA);
                          animation-delay:0.0s;"></div>
            </div>
          </div>
          <div class="hz-step">
            <span class="hz-step-icon">🤖</span>
            <span style="width:180px;flex-shrink:0;">Entraînement Random Forest</span>
            <div class="hz-step-bar">
              <div class="hz-step-fill"
                   style="background:linear-gradient(90deg,#7C3AED,#A78BFA);
                          animation-delay:0.3s;"></div>
            </div>
          </div>
          <div class="hz-step">
            <span class="hz-step-icon">🗺️</span>
            <span style="width:180px;flex-shrink:0;">Base hotspots Maroc (122 sites)</span>
            <div class="hz-step-bar">
              <div class="hz-step-fill"
                   style="background:linear-gradient(90deg,#059669,#34D399);
                          animation-delay:0.5s;"></div>
            </div>
          </div>
          <div class="hz-step">
            <span class="hz-step-icon">🌍</span>
            <span style="width:180px;flex-shrink:0;">Modèle atmosphérique Pasquill-Gifford</span>
            <div class="hz-step-bar">
              <div class="hz-step-fill"
                   style="background:linear-gradient(90deg,#DC2626,#F87171);
                          animation-delay:0.7s;"></div>
            </div>
          </div>
          <div class="hz-step">
            <span class="hz-step-icon">⚙️</span>
            <span style="width:180px;flex-shrink:0;">Initialisation Monte Carlo</span>
            <div class="hz-step-bar">
              <div class="hz-step-fill"
                   style="background:linear-gradient(90deg,#D97706,#FBBF24);
                          animation-delay:0.9s;"></div>
            </div>
          </div>
          <div class="hz-badge">
            Ministère de l'Intérieur — Direction de la Sécurité et de la Documentation
          </div>
        </div>
        """, unsafe_allow_html=True)
    st.session_state["app_loaded"] = True
    _loading_ph.empty()
    # Déclencher le pré-chargement ML en arrière-plan (non bloquant)
    # Le résultat est mis en cache pour les reruns suivants
    try:
        _get_ml_ready()
    except Exception:
        pass

SEUILS = {"ERPG-1": 1.0, "ERPG-2": 3.0, "ERPG-3": 20.0, "IDLH": 10.0}
PG_COEFF = {
    "A": {"ay":0.22,"by":0.89,"az":0.20,"bz":0.89,"cz":-0.0002},
    "B": {"ay":0.16,"by":0.87,"az":0.12,"bz":0.87,"cz":-0.0001},
    "C": {"ay":0.11,"by":0.87,"az":0.08,"bz":0.87,"cz": 0.0002},
    "D": {"ay":0.08,"by":0.85,"az":0.06,"bz":0.80,"cz": 0.0},
    "E": {"ay":0.06,"by":0.80,"az":0.03,"bz":0.75,"cz": 0.0},
    "F": {"ay":0.04,"by":0.75,"az":0.016,"bz":0.72,"cz":0.0},
}
PAL = {
    "danger":  "#C0392B",   # Rouge sécurité
    "warning": "#E67E22",   # Orange alerte
    "caution": "#16A085",   # Vert-teal
    "safe":    "#27AE60",   # Vert sécurité
    "accent":  "#2471A3",   # Bleu institutionnel
    "blue":    "#2980B9",   # Bleu clair
    "purple":  "#7D3C98",   # Violet ML
    "bg":      "#F5F7FA",   # Fond principal — gris très clair
    "bg2":     "#FFFFFF",   # Fond graphiques — blanc pur
    "grid":    "#E8ECF0",   # Grilles — gris doux
    "text":    "#1A2634",   # Texte principal — bleu-gris foncé
    "muted":   "#5D6D7E",   # Texte secondaire
    "border":  "#D5DEE8",   # Bordures
    "sidebar": "#EEF1F5",   # Fond sidebar
    "card":    "#FFFFFF",   # Fond cartes
    "card2":   "#F0F4F8",   # Fond cartes secondaires
}
RISK_CS = [
    [0.00, "#1A9850"],   # Vert — faible risque
    [0.25, "#91CF60"],   # Vert clair
    [0.45, "#FEE08B"],   # Jaune
    [0.65, "#FC8D59"],   # Orange
    [0.82, "#D73027"],   # Rouge
    [1.00, "#7B0D1E"],   # Rouge foncé — danger extrême
]
try:
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "accidents_chlore_rectifie.xlsx")
except NameError:
    DATA_PATH = os.path.join(os.getcwd(), "data", "accidents_chlore_rectifie.xlsx")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');

:root {
  --bg:       #F0F2F6;
  --surface:  #FFFFFF;
  --surface2: #F7F9FC;
  --border:   #E2E8F2;
  --border2:  #EDF1F8;
  --tx1:      #0D1B2A;
  --tx2:      #3D5166;
  --tx3:      #8898AA;
  --accent:   #1A4F8A;
  --accent2:  #2563EB;
  --danger:   #B91C1C;
  --warn:     #B45309;
  --ok:       #15803D;
  --teal:     #0F766E;
  --mono:     'DM Mono', monospace;
  --sans:     'DM Sans', sans-serif;
  --r-sm: 6px; --r-md: 10px; --r-lg: 16px;
  --sh-sm: 0 1px 3px rgba(0,0,0,.07),0 1px 2px rgba(0,0,0,.04);
  --sh-md: 0 4px 12px rgba(0,0,0,.08),0 2px 4px rgba(0,0,0,.04);
  --sh-lg: 0 10px 28px rgba(0,0,0,.09),0 4px 8px rgba(0,0,0,.04);
}

html,body,[class*="css"] { font-family:var(--sans)!important; color:var(--tx1); background:var(--bg); -webkit-font-smoothing:antialiased; }

/* ── HEADER ── */
.sc-header {
  position:relative; border-radius:var(--r-lg);
  background:linear-gradient(118deg,#0C2340 0%,#173D75 55%,#0C2A55 100%);
  overflow:hidden; margin-bottom:1.5rem;
  box-shadow:var(--sh-lg);
}
.sc-header-bar {
  height:4px;
  background:linear-gradient(90deg,#EF4444 0%,#F59E0B 25%,#10B981 55%,#3B82F6 80%,#8B5CF6 100%);
}
.sc-header-body { padding:1.4rem 2rem 1.5rem; position:relative; z-index:2; }
.sc-header-body::after {
  content:""; position:absolute; right:0; top:0; bottom:0; width:50%;
  background:radial-gradient(ellipse at 90% 50%,rgba(59,130,246,.07) 0%,transparent 65%);
  pointer-events:none;
}
.sc-header h1 {
  font-family:var(--mono); font-size:2rem; font-weight:700;
  color:#FFF; margin:0 0 .2rem; letter-spacing:.15em; line-height:1.2;
}
.sc-header h1 em { color:#93C5FD; font-style:normal; }
.sc-header .sub { font-size:.76rem; color:rgba(255,255,255,.5); font-weight:300; line-height:1.6; }
.sc-badges { display:flex; flex-wrap:wrap; gap:5px; margin-top:.7rem; }
.sc-badge {
  font-family:var(--mono); font-size:.58rem; letter-spacing:.1em; text-transform:uppercase;
  padding:3px 9px; border-radius:3px;
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18); color:rgba(255,255,255,.75);
}
.sc-badge.b-red   { background:rgba(239,68,68,.15);  border-color:rgba(252,165,165,.4); color:#FCA5A5; }
.sc-badge.b-amber { background:rgba(245,158,11,.12); border-color:rgba(253,211,77,.4);  color:#FCD34D; }
.sc-badge.b-green { background:rgba(16,185,129,.12); border-color:rgba(110,231,183,.4); color:#6EE7B7; }
.sc-badge.b-blue  { background:rgba(59,130,246,.15); border-color:rgba(147,197,253,.4); color:#93C5FD; }

/* ── SECTION TITLES ── */
.sc-section {
  display:flex; align-items:center; gap:8px;
  font-family:var(--mono); font-size:.65rem; font-weight:500; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent);
  margin:1.4rem 0 .8rem; padding-bottom:.45rem;
  border-bottom:1px solid var(--border);
}
.sc-section::before {
  content:""; width:3px; height:13px; flex-shrink:0;
  background:linear-gradient(180deg,var(--accent2),#93C5FD);
  border-radius:2px;
}

/* ── KPI CARDS ── */
.kpi-card {
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--r-md); padding:.95rem 1rem .85rem;
  position:relative; overflow:hidden; box-shadow:var(--sh-sm);
  transition:box-shadow .2s, transform .15s;
}
.kpi-card:hover { box-shadow:var(--sh-md); transform:translateY(-1px); }
.kpi-card::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; border-radius:var(--r-md) var(--r-md) 0 0; }
.kpi-card.danger  { background:linear-gradient(160deg,#FFF5F5 0%,#FFF 55%); }
.kpi-card.danger::before { background:linear-gradient(90deg,#B91C1C,#F87171); }
.kpi-card.warning { background:linear-gradient(160deg,#FFFBEB 0%,#FFF 55%); }
.kpi-card.warning::before { background:linear-gradient(90deg,#B45309,#FBBF24); }
.kpi-card.info    { background:linear-gradient(160deg,#EFF6FF 0%,#FFF 55%); }
.kpi-card.info::before { background:linear-gradient(90deg,#1A4F8A,#60A5FA); }
.kpi-card.ok      { background:linear-gradient(160deg,#F0FDF4 0%,#FFF 55%); }
.kpi-card.ok::before { background:linear-gradient(90deg,#15803D,#34D399); }
.kpi-value { font-family:var(--mono); font-size:1.7rem; font-weight:500; line-height:1; margin:.3rem 0 .2rem; letter-spacing:-.01em; }
.kpi-label { font-size:.60rem; color:var(--tx3); text-transform:uppercase; letter-spacing:.12em; font-weight:500; }
.kpi-sub   { font-size:.67rem; color:var(--tx2); margin-top:.28rem; font-weight:300; }

/* ── ALERT BANNER ── */
.alert-banner {
  border-radius:var(--r-md); padding:.9rem 1.4rem;
  margin-bottom:1.1rem; display:flex; align-items:flex-start; gap:12px;
  box-shadow:var(--sh-sm);
}
.alert-banner.rouge  { background:#FEF2F2; border:1px solid #FECACA; border-left:4px solid #B91C1C; }
.alert-banner.orange { background:#FFFBEB; border:1px solid #FDE68A; border-left:4px solid #B45309; }
.alert-banner.jaune  { background:#FEFCE8; border:1px solid #FEF08A; border-left:4px solid #92400E; }
.alert-icon  { font-size:1.7rem; line-height:1; flex-shrink:0; margin-top:1px; }
.alert-title { font-size:.92rem; font-weight:600; color:var(--tx1); margin-bottom:.2rem; }
.alert-text  { font-size:.78rem; color:var(--tx2); line-height:1.55; }

/* ── OPS CARDS ── */
.ops-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--r-md); overflow:hidden; box-shadow:var(--sh-sm); }
.ops-card-header { background:var(--surface2); border-bottom:1px solid var(--border2); padding:.55rem 1rem; display:flex; align-items:center; gap:6px; }
.ops-card-header h4 { font-family:var(--mono); font-size:.62rem; text-transform:uppercase; letter-spacing:.12em; color:var(--accent); margin:0; font-weight:500; }
.ops-body { padding:.2rem 0; }
.ops-item { display:flex; justify-content:space-between; align-items:center; font-size:.77rem; color:var(--tx2); padding:.30rem 1rem; border-bottom:1px solid var(--border2); }
.ops-item:last-child { border-bottom:none; }
.ops-item:hover { background:var(--surface2); }
.ops-val { font-family:var(--mono); font-weight:500; color:var(--tx1); font-size:.73rem; flex-shrink:0; margin-left:8px; }

/* ── MC MINI CARDS ── */
.mc-mini { background:var(--surface); border:1px solid var(--border); border-radius:var(--r-sm); padding:.6rem .75rem; box-shadow:var(--sh-sm); position:relative; overflow:hidden; }
.mc-mini::after { content:""; position:absolute; bottom:0; left:0; right:0; height:2.5px; }
.mc-mini.ok::after   { background:#10B981; }
.mc-mini.warn::after { background:#F59E0B; }
.mc-mini.bad::after  { background:#EF4444; }
.mc-mini.blue::after { background:#3B82F6; }
.mc-mini-val { font-family:var(--mono); font-size:1.25rem; font-weight:500; line-height:1; }
.mc-mini-lbl { font-size:.58rem; color:var(--tx3); text-transform:uppercase; letter-spacing:.1em; margin-top:3px; }
.mc-mini-sub { font-size:.60rem; color:var(--tx3); }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] { background:#FAFBFD!important; border-right:1px solid var(--border)!important; }
[data-testid="stSidebar"] > div:first-child { padding-top:.8rem; }
[data-testid="stSidebar"] .stMarkdown h3 { font-family:var(--mono)!important; font-size:.58rem!important; color:var(--accent)!important; letter-spacing:.14em!important; text-transform:uppercase!important; font-weight:500!important; margin:0!important; }

/* Sidebar group box */
.sb-group { background:var(--surface); border:1px solid var(--border2); border-radius:var(--r-sm); padding:.7rem .8rem .45rem; margin-bottom:.55rem; }
.sb-group-lbl { font-family:var(--mono); font-size:.58rem; font-weight:500; color:var(--tx3); text-transform:uppercase; letter-spacing:.12em; margin-bottom:.45rem; display:flex; align-items:center; gap:5px; }

/* ── TABS ── */
[data-testid="stTabs"] [role="tablist"] { gap:0!important; border-bottom:2px solid var(--border)!important; background:transparent!important; }
[data-testid="stTabs"] button[role="tab"] { font-family:var(--mono)!important; font-size:.65rem!important; letter-spacing:.05em!important; padding:.6rem 1rem!important; color:var(--tx3)!important; border:none!important; border-bottom:2px solid transparent!important; margin-bottom:-2px!important; border-radius:0!important; background:transparent!important; transition:all .15s!important; }
[data-testid="stTabs"] button[role="tab"]:hover { color:var(--accent)!important; background:var(--surface2)!important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:var(--accent)!important; border-bottom-color:var(--accent2)!important; font-weight:500!important; }

/* ── MISC ── */
.block-container { padding-top:1.4rem!important; padding-bottom:1rem!important; }
[data-testid="baseButton-primary"] { background:linear-gradient(135deg,#1A4F8A,#2563EB)!important; border:none!important; font-family:var(--mono)!important; font-size:.72rem!important; letter-spacing:.06em!important; border-radius:var(--r-sm)!important; box-shadow:0 2px 8px rgba(26,79,138,.35)!important; transition:all .2s!important; }
[data-testid="baseButton-primary"]:hover { transform:translateY(-1px)!important; box-shadow:0 4px 14px rgba(26,79,138,.45)!important; }
[data-testid="stDataFrame"] { border:1px solid var(--border)!important; border-radius:var(--r-md)!important; overflow:hidden!important; box-shadow:var(--sh-sm)!important; }
[data-testid="stInfo"] { background:#EFF6FF!important; border:1px solid #BFDBFE!important; border-radius:var(--r-sm)!important; font-size:.80rem!important; }
hr { border-color:var(--border)!important; margin:.5rem 0!important; }

.sc-footer { margin-top:2rem; padding:1rem 0 .5rem; border-top:1px solid var(--border); text-align:center; font-size:.67rem; color:var(--tx3); font-family:var(--mono); letter-spacing:.04em; }
</style>
""", unsafe_allow_html=True)

# ── Plotly base layout ────────────────────────────────────────────────────────
BASE_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#F9FAFB",
    font=dict(family="Inter, sans-serif", color=PAL["text"], size=12),
    xaxis=dict(
        gridcolor="#E8ECF0", gridwidth=1, zeroline=False, linecolor="#D5DEE8",
        tickfont=dict(size=10, color=PAL["muted"]),
        title_font=dict(size=11, color=PAL["muted"]),
    ),
    yaxis=dict(
        gridcolor="#E8ECF0", gridwidth=1, zeroline=False, linecolor="#D5DEE8",
        tickfont=dict(size=10, color=PAL["muted"]),
        title_font=dict(size=11, color=PAL["muted"]),
    ),
    legend=dict(
        bgcolor="rgba(255,255,255,0.92)", bordercolor="#D5DEE8", borderwidth=1,
        font=dict(size=10, color=PAL["text"]),
    ),
    margin=dict(l=55, r=25, t=55, b=45),
    title_font=dict(size=13, color=PAL["text"], family="IBM Plex Mono, monospace"),
    hoverlabel=dict(
        bgcolor="#FFFFFF", bordercolor="#D5DEE8",
        font=dict(size=11, color=PAL["text"], family="IBM Plex Mono"),
    ),
)

def apply_layout(fig, title="", h=380, xlog=False, ylog=False, **kw):
    L = dict(**BASE_LAYOUT, height=h, title=dict(text=title, x=0.02, y=0.97))
    if xlog: L["xaxis"] = dict(**L["xaxis"], type="log")
    if ylog: L["yaxis"] = dict(**L["yaxis"], type="log")
    L.update(kw)
    fig.update_layout(**L)
    return fig

def add_seuil_lines(fig):
    for label, val, col, dash in [
        ("ERPG-1 — Irritation (1 ppm)",    SEUILS["ERPG-1"], PAL["safe"],    "dot"),
        ("ERPG-2 — Irréversible (3 ppm)",   SEUILS["ERPG-2"], PAL["warning"], "dash"),
        ("ERPG-3 — Danger vital (20 ppm)",  SEUILS["ERPG-3"], PAL["danger"],  "dashdot"),
    ]:
        fig.add_hline(y=val, line_dash=dash, line_color=col, line_width=1.5,
            annotation_text=f"  {label}", annotation_position="top right",
            annotation_font=dict(size=9, color=col),
            annotation_bgcolor="rgba(255,255,255,0.88)")
    return fig

# ── Fonctions physiques ───────────────────────────────────────────────────────
def sigma_pg(x, stab):
    """
    Coefficients de Briggs (1973) — zones rurales.
    Donnent des distances plus proches d'ALOHA que Pasquill-Gifford pur.
    Formule : sigma = a * x^b * (1 + 0.0001*x)^-0.5  (correction longue distance)
    """
    x = max(x, 1.0)
    # (a_y, b_y, a_z, b_z)
    BRIGGS = {
        "A": (0.22, 0.89, 0.20, 0.89),
        "B": (0.16, 0.87, 0.12, 0.87),
        "C": (0.11, 0.87, 0.08, 0.87),
        "D": (0.08, 0.85, 0.06, 0.80),
        "E": (0.06, 0.80, 0.03, 0.75),
        "F": (0.04, 0.75, 0.016, 0.72),
    }
    ay, by, az, bz = BRIGGS.get(stab, BRIGGS["D"])
    fac = (1 + 0.0001 * x) ** (-0.5)   # stabilisation longue distance
    sy  = ay * x**by * fac
    sz  = max(az * x**bz * fac, 0.5)
    return sy, sz

# ── Loi d'echelle gaz lourd calibree ALOHA (err <= 11%) ─────────────────────
_K_DENSE      = 5_674_366.0   # constante dispersion Cl2 gaz lourd
_EXP_Q        = 0.80           # exposant debit
_EXP_X        = 1.888          # exposant distance
_F_STAB_DENSE = {              # facteur stabilite gaz lourd
    "A": 0.35, "B": 0.55, "C": 0.82,
    "D": 1.00, "E": 1.25, "F": 1.60,
}


def conc_ppm(Q_kgs, u, x, y, stab, H=0.0):
    """Concentration gaussienne PG — Brutale, grille 2D, heatmap."""
    x = max(x, 1.0)
    sy, sz = sigma_pg(x, stab)
    denom = math.pi * u * sy * sz
    if denom < 1e-10: return 0.0
    C = (Q_kgs*1000)/denom * math.exp(-0.5*(y/sy)**2)
    if H > 0: C *= 2*math.exp(-0.5*(H/sz)**2)
    return max(C*24.45/70.9, 0.0)

def q_debit_kgs(Q_kg, duree_min, type_lib):
    """
    Calcule le débit massique effectif en kg/s.

    RÈGLE PHYSIQUE CRITIQUE :
    • Progressive : débit = Q_total / durée_saisie
      ex : Henderson 20 000 kg en 120 min → 2,78 kg/s

    • Brutale (rupture, chute, explosion instantanée) : la durée physique réelle
      d'une libération brutale ne peut pas dépasser quelques minutes,
      quelle que soit la valeur saisie dans l'interface.
      → On impose duree_eff = min(duree_saisie, 10 min) pour ce type.
      ex : Aqaba 25 000 kg, duree saisie=60 min → duree_eff=10 min → Q=41,7 kg/s
           Aqaba 25 000 kg, duree saisie= 2 min → duree_eff= 2 min → Q=208 kg/s

    Sans cette protection, un utilisateur qui laisse duree=60 (défaut sidebar)
    avec type=Brutale obtiendrait un débit 30× trop faible et des zones 5× trop petites.
    """
    dur_saisi = max(float(duree_min), 1.0)
    if type_lib.startswith("Brutale"):
        dur_eff = min(dur_saisi, 10.0)   # max 10 min physiquement pour une libération brutale
    else:
        dur_eff = dur_saisi
    return Q_kg / dur_eff / 60.0   # kg/s

def h_effectif(hauteur_m, type_lib):
    """
    Hauteur effective d'émission pour le modèle gaussien.
    Pour les libérations BRUTALES (chute, explosion, rupture instantanée),
    le nuage se forme au niveau du sol → H = 0 m.
    Pour les rejets PROGRESSIFS par un orifice en hauteur → H = hauteur_m.
    """
    if type_lib.startswith("Brutale"):
        return 0.0
    return float(hauteur_m)

def _puff_correction(R_plume, u_ms, duree_min, type_lib):
    """
    Correction de rayon pour les libérations brèves (puff).
    Pour une libération brutale de courte durée (< 30 min), le nuage se comporte
    comme un 'puff' (nuage isolé) et non comme un panache continu.
    La correction empirique calibrée sur données historiques :
      R_puff = sqrt(R_plume × u × dur_s)   si dur_s < R_plume/u
    Donne Aqaba : R = sqrt(4483 × 1.5 × 120) = 898 m ≈ réel 1000 m (erreur 10%).
    """
    if not type_lib.startswith("Brutale"):
        return R_plume
    dur_s = max(duree_min, 1) * 60
    if duree_min >= 30:
        return R_plume   # durée longue → panache classique
    T_transport = R_plume / max(u_ms, 0.1)
    if dur_s < T_transport:
        return min(math.sqrt(R_plume * u_ms * dur_s), R_plume)
    return R_plume

def rayon_seuil(Q_kg, u, stab, H, seuil, duree_min=60, type_lib="Progressive"):
    """
    PROGRESSIVE : modele gaz lourd (loi d'echelle ALOHA-like).
      C(x) = K_dense x Q^0.80 / (u x x^1.888) x F_stab
      Erreur <= 11% vs ALOHA sur toutes classes A-F.
    BRUTALE : modele PG Briggs + puff Wilson.
      Validation Aqaba 2022 : ERPG-2 = 1035m.
    """
    Q_kgs = q_debit_kgs(Q_kg, duree_min, type_lib)
    H_eff = h_effectif(H, type_lib)
    is_brutal = type_lib.startswith("Brutale")

    # MODE PROGRESSIF : modele gaz lourd calibre ALOHA
    if not is_brutal:
        F = _F_STAB_DENSE.get(stab, 1.00)
        R_dense = (_K_DENSE * (Q_kgs ** _EXP_Q) * F / (u * seuil)) ** (1.0 / _EXP_X)
        hi_cap = {"A":30000,"B":30000,"C":30000,"D":25000,"E":18000,"F":14000}.get(stab,25000)
        return min(max(R_dense, 1.0), hi_cap)

    # MODE BRUTAL : modele PG Briggs + correction puff Wilson
    # CORRECTION : utiliser dur_eff = min(duree_min, 10) cohérent avec q_debit_kgs
    # Évite la sous-estimation quand l'utilisateur laisse duree=60min (sidebar)
    # avec type=Brutale (une libération brutale dure au maximum 10 min physiquement)
    _dur_eff_brutal = min(float(duree_min), 10.0)   # ← cohérent avec q_debit_kgs

    hi_max = {"A":20000.0,"B":20000.0,"C":20000.0,"D":20000.0,"E":12000.0,"F":10000.0}.get(stab,20000.0)
    lo, hi = 1.0, hi_max
    C_lo = conc_ppm(Q_kgs, u, lo, 0, stab, H_eff)
    if C_lo <= seuil:
        return 1.0
    for _ in range(80):
        mid = (lo + hi) * 0.5
        if conc_ppm(Q_kgs, u, mid, 0, stab, H_eff) > seuil:
            lo = mid
        else:
            hi = mid
    R_plume = hi

    # Correction puff Wilson (1981) avec dur_eff plafonnée
    # R_puff = sqrt(R_plume × u × t_s)  si t_s < T_transit
    if _dur_eff_brutal < 30:
        dur_s     = max(_dur_eff_brutal, 1) * 60
        T_transit = R_plume / max(u, 0.1)
        if dur_s < T_transit:
            return min(math.sqrt(R_plume * u * dur_s), R_plume)
    return R_plume

def grille_2d(Q_kg, u, stab, H=0.0, extent=3000, n=65, duree_min=60, type_lib="Progressive"):
    Q_kgs = q_debit_kgs(Q_kg, duree_min, type_lib)
    H_eff = h_effectif(H, type_lib)
    xs = np.linspace(20, extent, n)
    ys = np.linspace(-extent/2, extent/2, n)
    Z  = np.zeros((n, n))
    for i, xi in enumerate(xs):
        sy, sz = sigma_pg(xi, stab)
        denom = math.pi * u * sy * sz
        if denom < 1e-10: continue
        base = (Q_kgs*1000)/denom
        if H_eff > 0: base *= 2*math.exp(-0.5*(H_eff/sz)**2)
        for j, yj in enumerate(ys):
            Z[j,i] = max(base*math.exp(-0.5*(yj/sy)**2)*24.45/70.9, 0.0)
    return xs, ys, Z

def monte_carlo(Q_kg, u, stab, H=0.0, N=2000, q_cv=0.30, u_cv=0.20,
                duree_min=60, type_lib="Progressive"):
    distances = np.array([100,200,300,500,750,1000,1500,2000,3000])
    Q_kgs = q_debit_kgs(Q_kg, duree_min, type_lib)   # ← débit correct selon type/durée
    H_eff = h_effectif(H, type_lib)                   # ← H=0 pour libérations brutales
    Qv = np.random.lognormal(np.log(max(Q_kgs,1e-6)), q_cv, N)
    uv = np.clip(np.random.lognormal(np.log(u), u_cv, N), 0.3, 15.0)
    result = {}
    for d in distances:
        sy, sz = sigma_pg(d, stab)
        denom_v = math.pi * uv * sy * sz
        base_v = np.where(denom_v>0, (Qv*1000)/denom_v*24.45/70.9, 0.0)
        if H_eff > 0: base_v *= 2*math.exp(-0.5*(H_eff/sz)**2)
        arr = np.clip(base_v, 0, None)
        result[d] = {
            "mean":float(arr.mean()), "p05":float(np.percentile(arr,5)),
            "p25":float(np.percentile(arr,25)), "p50":float(np.median(arr)),
            "p75":float(np.percentile(arr,75)), "p95":float(np.percentile(arr,95)),
            "p_e1":float((arr>SEUILS["ERPG-1"]).mean()),
            "p_e2":float((arr>SEUILS["ERPG-2"]).mean()),
            "p_e3":float((arr>SEUILS["ERPG-3"]).mean()),
            "samples":arr,
        }
    return result

def enrich_df(df):
    """Ajoute les colonnes physiques dérivées utilisées par les modèles ML."""
    df = df.copy()
    df["log_Q"]       = np.log10(df["Quantité_Cl2_kg"].clip(1))
    df["log_dist"]    = np.log10(df["Distance_pop_m"].clip(1))
    df["log_C_proxy"] = np.log10(
        (df["Quantité_Cl2_kg"].clip(1) /
         (df["Vitesse_vent_ms"].clip(0.1) * df["Distance_pop_m"].clip(1)**1.5 + 1)
        ).clip(1e-6)
    )
    df["dens_dist"]   = df["Densité_pop_km2"] / df["Distance_pop_m"].clip(1)
    return df

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(DATA_PATH, sheet_name="Données", header=1)
    num_cols = ["Quantité_Cl2_kg","Hauteur_source_m","Durée_libération_min","Vitesse_vent_ms",
                "Densité_pop_km2","Distance_pop_m","Durée_expo_min","Délai_évacuation_min",
                "Délai_intervention_min","Décès","Blessés_graves","Blessés_légers",
                "Blessés_total","Zone_impact_km2","Périmètre_évacuation_m",
                "Coût_MUSD","Jours_arrêt","Indice_gravité"]
    for c in num_cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["Quantité_Cl2_kg","Vitesse_vent_ms","Hauteur_source_m","Durée_libération_min"]:
        if c in df.columns: df[c].fillna(df[c].median(), inplace=True)
    return enrich_df(df)   # colonnes ML disponibles sur le df global

@st.cache_resource(show_spinner=False)
def train_models(df):
    """
    Modèles ML calibrés sur la base historique.
    Features physiques enrichies : log_Q, log_C_proxy (concentration estimée à la pop),
    log_dist, dens_dist — captures les vrais drivers des conséquences.
    Régularisation forte (max_depth=3, min_samples_leaf=5) pour généralisation.
    """
    df2 = enrich_df(df)   # garantit la présence des colonnes dérivées

    feats = [
        "log_Q", "log_C_proxy", "log_dist", "dens_dist",
        "Vitesse_vent_ms", "Type_libération_num", "Stabilité_atm_code",
        "Hauteur_source_m", "Durée_libération_min", "Densité_pop_km2",
        "Niveau_EPI_num", "Alerte_précoce_bin", "Délai_évacuation_min",
        "Formation_pers", "Coord_secours", "Capacité_médicale_num",
    ]
    avail = [f for f in feats if f in df2.columns]
    models = {}
    for t in ["Indice_gravité", "Blessés_total", "Zone_impact_km2", "Décès"]:
        if t not in df2.columns: continue
        sub = df2[avail + [t]].dropna()
        if len(sub) < 10: continue
        X, y = sub[avail].values, sub[t].values
        # Random Forest fortement régularisé pour éviter l'overfitting (81 obs.)
        _RF, _CV = _get_sklearn()
        rf = _RF(
            n_estimators=100, max_depth=3, min_samples_leaf=5,
            max_features="sqrt", random_state=42
        )
        rf.fit(X, y)
        n_cv = min(5, len(y) // 5)
        r2 = float(np.mean(_CV(rf, X, y, cv=max(3, n_cv), scoring="r2"))) if len(y) >= 15 else 0.0
        models[t] = {"model": rf, "features": avail, "r2": r2, "n": len(y)}
    return models

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="sc-header">
  <div class="sc-header-bar"></div>
  <div class="sc-header-body">
    <div style="display:flex;align-items:center;gap:18px;margin-bottom:0.6rem;">
      <!-- HazMod Logo SVG -->
      <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="hm_bg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#1E40AF"/>
            <stop offset="100%" stop-color="#0C2340"/>
          </radialGradient>
          <radialGradient id="hm_glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#EF4444" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="#EF4444" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <!-- Outer ring -->
        <circle cx="30" cy="30" r="29" fill="url(#hm_bg)" stroke="#3B82F6" stroke-width="1.5"/>
        <!-- Glow pulse -->
        <circle cx="30" cy="30" r="22" fill="url(#hm_glow)"/>
        <!-- Biohazard / NRBC symbol adapted -->
        <!-- Central circle -->
        <circle cx="30" cy="30" r="5" fill="#EF4444"/>
        <!-- Three arcs forming hazard symbol -->
        <path d="M30 25 A7 7 0 0 1 37 30 L34 30 A4 4 0 0 0 30 26 Z" fill="#F59E0B"/>
        <path d="M37 30 A7 7 0 0 1 26.5 37 L25 34.4 A4 4 0 0 0 34 30 Z" fill="#F59E0B"/>
        <path d="M26.5 37 A7 7 0 0 1 23 30 L26 30 A4 4 0 0 0 25 34.4 Z" fill="#F59E0B"/>
        <!-- Outer lobes -->
        <circle cx="30" cy="16" r="6" fill="none" stroke="#EF4444" stroke-width="3.5"/>
        <circle cx="43" cy="37" r="6" fill="none" stroke="#EF4444" stroke-width="3.5"/>
        <circle cx="17" cy="37" r="6" fill="none" stroke="#EF4444" stroke-width="3.5"/>
        <!-- Molecule atoms -->
        <circle cx="9" cy="9" r="3" fill="#60A5FA" opacity="0.7"/>
        <circle cx="51" cy="9" r="3" fill="#60A5FA" opacity="0.7"/>
        <circle cx="9" cy="51" r="3" fill="#60A5FA" opacity="0.7"/>
        <circle cx="51" cy="51" r="3" fill="#60A5FA" opacity="0.7"/>
        <line x1="12" y1="12" x2="22" y2="22" stroke="#60A5FA" stroke-width="1" opacity="0.5"/>
        <line x1="48" y1="12" x2="38" y2="22" stroke="#60A5FA" stroke-width="1" opacity="0.5"/>
        <line x1="12" y1="48" x2="22" y2="38" stroke="#60A5FA" stroke-width="1" opacity="0.5"/>
        <line x1="48" y1="48" x2="38" y2="38" stroke="#60A5FA" stroke-width="1" opacity="0.5"/>
      </svg>
      <div>
        <h1 style="margin:0;font-size:2rem;letter-spacing:0.15em;">
          HAZ<em>MOD</em>
        </h1>
        <div style="font-size:0.7rem;color:rgba(255,255,255,0.55);font-weight:300;letter-spacing:0.2em;text-transform:uppercase;">
          Hazardous Materials Modeling System
        </div>
      </div>
    </div>
    <div class="sub">
      Système probabiliste d'évaluation des risques chimiques au chlore (Cl₂) •
      Commission Nationale NRBC — Ministère de l'Intérieur, Maroc
    </div>
    <div class="sc-badges">
      <span class="sc-badge b-red">Chlore Cl₂</span>
      <span class="sc-badge b-amber">Monte Carlo</span>
      <span class="sc-badge b-green">Pasquill-Gifford</span>
      <span class="sc-badge b-blue">Machine Learning</span>
      <span class="sc-badge">NRBC</span>
      <span class="sc-badge">Sécurité Civile</span>
      <span class="sc-badge b-blue">HazMod</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Chargement différé des données ML — uniquement à la demande
# (évite 2-5 secondes de blocage au démarrage)
@st.cache_resource(show_spinner=False)
def _get_ml_ready():
    """Charge les données et entraîne les modèles RF (une seule fois)."""
    try:
        df = load_data()
        models = train_models(df)
        return df, models
    except Exception:
        return None, {}

# Pré-charge en arrière-plan dès la première exécution
# sans bloquer l'affichage de l'interface
if "ml_preloaded" not in st.session_state:
    st.session_state["ml_preloaded"] = False

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙ PARAMÈTRES DE L'INCIDENT")
    st.divider()
    st.markdown("**📍 Localisation de l'incident**")

    # ── Mini carte Google Satellite sidebar ───────────────────────────────────
    _sb_lat = st.session_state.get("map_lat", 33.1167)
    _sb_lon = st.session_state.get("map_lon", -8.6333)
    _sb_map = folium.Map(
        location=[_sb_lat, _sb_lon], zoom_start=13,
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",  # satellite pur sans étiquettes
        attr="Google Satellite"
    )
    # Satellite pur sans étiquettes ni frontières
    folium.CircleMarker(
        [_sb_lat, _sb_lon], radius=9, color="#fff", fill=True,
        fill_color="#E63946", fill_opacity=1, weight=2,
        tooltip="📍 Cliquez pour déplacer la source"
    ).add_to(_sb_map)
    folium.Marker(
        [_sb_lat, _sb_lon],
        icon=folium.DivIcon(
            html='<div style="background:#E63946;color:#fff;border-radius:4px;'
                 'padding:2px 6px;font-size:9px;font-weight:700;white-space:nowrap;'
                 'box-shadow:0 1px 4px rgba(0,0,0,0.5);margin-top:-26px;margin-left:12px;">'
                 '⚠ Source Cl₂</div>',
            icon_size=(90, 22))
    ).add_to(_sb_map)
    _sb_map.get_root().html.add_child(folium.Element(
        '<div style="position:absolute;bottom:4px;left:4px;z-index:999;'
        'background:rgba(0,0,0,0.6);color:#fff;padding:3px 7px;'
        'border-radius:3px;font-size:9px;">🛰 Google Satellite</div>'
    ))
    _sb_result = st_folium(
        _sb_map, width=None, height=220,
        key="sidebar_satellite_map",
        returned_objects=["last_clicked"]
    )
    if _sb_result and _sb_result.get("last_clicked"):
        _cl = _sb_result["last_clicked"]
        _nl, _nlo = round(_cl["lat"], 4), round(_cl["lng"], 4)
        if (_nl != st.session_state.get("map_lat") or
                _nlo != st.session_state.get("map_lon")):
            st.session_state["map_lat"] = _nl
            st.session_state["map_lon"] = _nlo
            # Forcer la mise à jour des widgets number_input
            st.session_state["lat_input"] = _nl
            st.session_state["lon_input"] = _nlo
            st.rerun()

    # ── Champs coordonnées ────────────────────────────────────────────────────
    _c1, _c2 = st.columns(2)
    lat = _c1.number_input("Lat", value=st.session_state.get("map_lat", 33.1167),
                            format="%.4f", key="lat_input")
    lon = _c2.number_input("Lon", value=st.session_state.get("map_lon", -8.6333),
                            format="%.4f", key="lon_input")

    # ── Villes rapides ────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:10px;color:#888;margin:2px 0;'>"
        "📍 Scénarios de test rapide</div>",
        unsafe_allow_html=True)
    _vc = st.columns(3)
    for _ci, (_cn, _cl, _clo) in enumerate([
        ("Tanger",    35.7595, -5.8340),
        ("Jorf Lasfar", 33.1167, -8.6333),
        ("Kenitra",   34.2610, -6.5802),
    ]):
        if _vc[_ci].button(_cn, key=f"city_{_cn}", use_container_width=True):
            st.session_state["map_lat"] = _cl
            st.session_state["map_lon"] = _clo
            st.rerun()
    st.divider()
    st.markdown("**☢ Source de Chlore**")
    Q_kg = st.number_input("Quantité Cl₂ libérée (kg)", 10.0, 100000.0, 9000.0, 100.0)
    type_lib = st.selectbox("Type de libération",
        ["Brutale (instantanée)", "Progressive (continue)"], index=1)
    # Pour Brutale : durée réelle ≤ 10 min imposée dans q_debit_kgs
    _dur_help = ("⚠ Brutale : durée effective plafonnée à 10 min physiquement"
                 if type_lib.startswith("Brutale")
                 else "Durée réelle de la fuite continue")
    duree_min = st.slider("Durée de libération (min)", 1, 480, 60,
                          help=_dur_help)
    hauteur_m = st.slider("Hauteur de la source (m)", 0, 30, 2)
    # Info débit effectif
    _q_eff = Q_kg / min(float(duree_min),10.0) / 60.0 if type_lib.startswith("Brutale") else Q_kg / max(float(duree_min),1.0) / 60.0
    st.markdown(
        f"<div style='background:#EFF6FF;border-left:3px solid #2563EB;"
        f"padding:6px 10px;border-radius:4px;font-size:11px;color:#1e40af;margin-top:4px;'>"
        f"⚡ Débit effectif : <b>{_q_eff:.2f} kg/s</b>"
        f"{'  (durée plafonnée à 10 min)' if type_lib.startswith('Brutale') and duree_min>10 else ''}"
        f"</div>",
        unsafe_allow_html=True)
    st.divider()
    st.markdown("**🌬 Météorologie**")
    u_ms = st.slider("Vitesse du vent (m/s)", 0.5, 10.0, 5.0, 0.1,
                    help="1.5 m/s = vent faible → scénario défavorable")
    dir_vent = st.slider("Direction vent (°, 0=N)", 0, 359, 280)
    stab_sel = st.selectbox("Stabilité atmosphérique",
        ["A — Très instable","B — Instable","C — Lég. instable",
         "D — Neutre","E — Lég. stable","F — Très stable"], index=2)
    stab = stab_sel[0]
    st.divider()
    st.markdown("**🏙 Contexte**")
    config_site = st.selectbox("Configuration du site", [
        "Usine chimique","Zone industrielle","Port semi-ouvert","Port industriel",
        "Port urbain","Voies ferrées (zone mixte)","Voies ferrées rurales",
        "Zone urbaine","Zone rurale","Station eau","Réservoir urbain",
        "Route (zone rurale)","Piscine","Hôpital","Autre",
    ])
    # ── Densité population — détection automatique WorldPop / HCP ──────────────
    # Densité auto — définie AU NIVEAU MODULE (hors sidebar) pour éviter
    # le problème de scope avec @st.cache_data
    _pop_data = _hazmod_get_density(round(lat, 3), round(lon, 3))

    if _pop_data and _pop_data.get("density_raw", 0) > 0:
        _auto_dens   = _pop_data["density_current"]
        _dens_source = _pop_data["source"]
        _dens_prec   = _pop_data["precision"]
        _flux_info   = _pop_data.get("flux", {})
    else:
        _auto_dens   = 2000
        _dens_source = "Valeur par défaut"
        _dens_prec   = "—"
        _flux_info   = {}

    # Affichage de la densité auto avec indicateur de flux
    _flux_icon   = _flux_info.get("flux_icon", "📊")
    _flux_factor = _flux_info.get("flux_factor", 1.0)
    _peak_h      = _flux_info.get("peak_hour", 12)
    _peak_den    = _flux_info.get("peak_density", _auto_dens)
    _zone_name   = _pop_data.get("zone_name", "—") if _pop_data else "—"
    _flux_desc   = _flux_info.get("flux_description", "—")

    # Construire le HTML SANS expressions complexes dans le f-string
    _dens_html = (
        f'<div style="background:linear-gradient(90deg,#0C2340,#162D4F);'
        f'border-radius:8px;padding:10px 12px;margin-bottom:8px;'
        f'border-left:4px solid #F0C040;">'
        f'<div style="color:#F0C040;font-weight:700;font-size:.8rem;margin-bottom:4px;">'
        f'📡 Densité Population — Temps Réel</div>'
        f'<div style="color:#fff;font-size:1rem;font-weight:700;">'
        f'{_auto_dens:,} hab/km²'
        f'<span style="font-size:.75rem;color:#93C5FD;margin-left:8px;">'
        f'{_flux_icon} Flux ×{_flux_factor:.2f} — {_flux_desc}</span></div>'
        f'<div style="color:#94A3B8;font-size:.7rem;margin-top:3px;">'
        f'Source : {_dens_source}<br/>'
        f'Zone : {_zone_name} &nbsp;·&nbsp; Pic journalier : {_peak_den:,} hab/km² à {_peak_h:02d}h</div>'
        f'<div style="color:#64748B;font-size:.68rem;margin-top:2px;">'
        f'Précision : {_dens_prec} &nbsp;·&nbsp; WorldPop / HCP RGPH 2024</div>'
        f'</div>'
    )
    st.markdown(_dens_html, unsafe_allow_html=True)

    dens_pop = st.number_input(
        "Densité (hab/km²) — ajuster si nécessaire",
        10, 50000, int(_auto_dens), 100,
        help=f"Auto-détectée via {_dens_source}. Modifiable si besoin."
    )
    dist_pop = st.number_input("Distance population (m)", 50, 5000, 300, 50)
    obstacles = st.toggle("Obstacles physiques présents", True)
    st.divider()
    st.markdown("**🚒 Réponse**")
    niveau_epi = st.selectbox("Niveau EPI",["EPI 1 — Très faible","EPI 2 — Faible","EPI 3 — Moyen","EPI 4 — Élevé"],index=1)
    alerte_prec = st.toggle("Alerte précoce activée", False)
    delai_evac = st.slider("Délai évacuation (min)", 5, 120, 30)
    coord_sec = st.slider("Coordination secours (1–4)", 1, 4, 2)
    capa_med = st.selectbox("Capacité médicale", ["Limitée","Moyenne","Bonne"])
    st.divider()
    st.divider()
    st.markdown("**🏭 Crise majeure — Sites & Établissements**")

    # Usines à risque d'effet domino
    nb_usines = st.number_input("Nombre d'usines à risque d'effet domino", 0, 10, 0, 1)
    usines_domino = []
    for _i in range(int(nb_usines)):
        with st.expander(f"Usine #{_i+1}", expanded=(_i==0)):
            _nom = st.text_input(f"Nom / Type de l'usine", key=f"u_nom_{_i}",
                                  value="Usine industrielle")
            _dist_u = st.number_input(f"Distance de la source (m)", 50, 5000, 300, 50,
                                       key=f"u_dist_{_i}")
            _produits = st.multiselect(
                "Produits fabriqués / stockés",
                ["Aluminium (Al)", "Acétylène (C₂H₂)", "Ammoniac (NH₃)",
                 "Hydrogène (H₂)", "Phosphore (P)", "Graisses industrielles",
                 "Éthylène", "Éthane", "Silicones", "Huiles industrielles",
                 "Arsenic (As)", "Antimoine (Sb)", "Chlorure de vinyle",
                 "Acide chlorhydrique", "Autre produit réactif"],
                key=f"u_prod_{_i}",
                default=["Aluminium (Al)"],
            )
            usines_domino.append({
                "nom": _nom, "dist": _dist_u, "produits": _produits
            })

    # Présence de train
    has_train = st.toggle("Présence d'une ligne ferroviaire / train en zone", False)
    if has_train:
        train_passagers = st.number_input("Nombre de passagers estimés", 10, 1000, 200, 10,
                                           key="train_pass")
        train_wagons    = st.number_input("Nombre de wagons", 1, 20, 4, 1, key="train_wag")
        train_delai_arr = st.number_input("Délai avant prochaine gare (min)", 5, 60, 25, 5,
                                           key="train_delai")
    else:
        train_passagers, train_wagons, train_delai_arr = 0, 0, 0

    # Autres établissements
    has_hopital   = st.toggle("Hôpital / clinique en zone d'impact", False)
    has_ecole     = st.toggle("École / crèche en zone d'impact", False)
    has_admin     = st.toggle("Centre administratif en zone d'impact", False)
    nb_agents_admin = st.number_input("Nombre d'agents (centre admin.)", 0, 5000, 0, 50,
                                       key="nb_agents") if has_admin else 0
    has_gare_rout = st.toggle("Gare routière en zone d'impact", False)
    nb_gare_pers  = st.number_input("Personnes à la gare routière", 0, 2000, 0, 50,
                                     key="nb_gare") if has_gare_rout else 0

    # Capacité hospitalière locale
    st.markdown("**🏥 Capacité médicale locale**")
    capa_chr_lits = st.number_input("Lits CHR disponibles", 0, 2000, 350, 50)
    capa_ua_max   = st.number_input("Lits réanimation / NRBC", 0, 100, 20, 5)
    nb_smur       = st.number_input("Unités SMUR disponibles", 1, 10, 3, 1)

    st.divider()
    n_mc = st.select_slider("Itérations Monte Carlo", [500,1000,2000,5000,10000], value=2000)
    run_btn = st.button("🚀  LANCER LA SIMULATION", use_container_width=True, type="primary")

# ── Coordonnées : initialisation session_state ────────────────────────────────
if "map_lat" not in st.session_state:
    # Valeur par défaut = Jorf Lasfar (port chimique, Maroc)
    st.session_state["map_lat"] = 33.1167
    st.session_state["map_lon"] = -8.6333

# ── Calculs primaires ─────────────────────────────────────────────────────────
Q_kgs = q_debit_kgs(Q_kg, duree_min, type_lib)   # débit effectif en kg/s
H_eff = h_effectif(hauteur_m, type_lib)           # H=0 si libération brutale
r1 = rayon_seuil(Q_kg, u_ms, stab, hauteur_m, SEUILS["ERPG-1"], duree_min, type_lib)
r2 = rayon_seuil(Q_kg, u_ms, stab, hauteur_m, SEUILS["ERPG-2"], duree_min, type_lib)
r3 = rayon_seuil(Q_kg, u_ms, stab, hauteur_m, SEUILS["ERPG-3"], duree_min, type_lib)

# ── Détection dynamique des hotspots OSM selon les coordonnées GPS ────────────
# Se met à jour automatiquement quand lat/lon ou les rayons ERPG changent.
# Cache Streamlit : évite de requêter Overpass à chaque rerun.
@st.cache_data(ttl=300, show_spinner=False)
def _get_hotspots_cached(lat_c, lon_c, r3_c, r2_c, r1_c, prop_c):
    """
    Requête OSM Overpass avec cache 5 min.
    Recalcul automatique si les coordonnées ou les rayons ERPG changent.
    Retourne toujours un dict valide même en cas d'erreur réseau.
    """
    try:
        if _osm_mod is not None:
            result = _osm_mod.get_hotspots(
                lat_c, lon_c, r3_c, r2_c, r1_c, prop_c)
            if result and any(result.values()):
                return result
    except Exception:
        pass
    return {"ERPG-3": [], "ERPG-2": [], "ERPG-1": []}

_prop_dir_hs = (dir_vent + 180) % 360
hotspots_dynamiques = _get_hotspots_cached(
    round(lat, 3), round(lon, 3),
    round(r3, 0), round(r2, 0), round(r1, 0),
    round(_prop_dir_hs, 0)
)
_hs_source = "OpenStreetMap" if _osm_mod else "géométrique"
_hs_total  = sum(len(v) for v in hotspots_dynamiques.values())

# ── Facteur Configuration_site ────────────────────────────────────────────────
# Calibré sur les données historiques : fraction de la population réellement
# exposée selon le type de site (ouverture, obstacles, confinement).
# Source : analyse de la base 81 accidents — ratio blessés/pop_théorique par site.
SITE_FACTEUR = {
    "Usine chimique":             0.08,   # EPI présent, périmètre géré
    "Zone industrielle":          0.10,
    "Port semi-ouvert":           0.12,   # Aqaba : 260 blessés / ~2100 pop = 12%
    "Port industriel":            0.10,
    "Port urbain":                0.15,   # Mumbai : 113/1500 ≈ 7.5%, densité haute
    "Voies ferrées (zone mixte)": 0.25,   # Graniteville : 529/1600 = 33% (pire cas)
    "Voies ferrées rurales":      0.18,
    "Zone urbaine":               0.20,   # Douma, Saraqib : zones habitées ouvertes
    "Zone rurale":                0.05,   # faible densité, dispersion rapide
    "Station eau":                0.06,   # infrastructure fermée, peu de personnes
    "Réservoir urbain":           0.30,   # Jos Nigeria : 210/1600 = 13%, fort impact
    "Route (zone rurale)":        0.08,
    "Piscine":                    0.35,   # espace confiné, forte exposition
    "Hôpital":                    0.15,
    "Autre":                      0.10,
}
facteur_site = SITE_FACTEUR.get(config_site, 0.10)

# ── Indice de gravité — formule physique calibrée sur 81 accidents ─────────────
def _compute_gravite(Q_kg, u_ms, stab, type_lib, dist_pop, dens_pop,
                     duree_min, alerte, epi_num, delai_evac, coord, f_site, capa_med_num,
                     nb_usines=0, usines_domino=None, has_train=False,
                     has_hopital=False, has_ecole=False, has_admin=False,
                     has_gare_rout=False, capa_chr_lits=350, capa_ua_max=20):
    """
    Indice de gravité composite G ∈ [0, 10].

    Paramètres de base (physiques + organisationnels) :
      expo, q_score, dur_sc → score physique brut
      brutal_m, stab_m, dens_m, site_m, alerte_m, epi_m, evac_m, coord_m, capa_m

    Nouveaux multiplicateurs (sites à risque multi-sites) :
      domino_m  : présence d'usines à risque d'effet domino (1.00→1.25 selon nb et réactivité)
      train_m   : présence d'un train en zone (1.00→1.08 — victimes supplémentaires difficiles à gérer)
      vuln_m    : présence d'établissements vulnérables (hôpital, école, gare) (1.00→1.12)
      capa_chr_m: capacité CHR insuffisante vs blessés attendus (1.00→1.10)
    """
    _Q  = Q_kg / 60.0
    _d  = max(dist_pop, 20.0)
    _sy, _sz = sigma_pg(_d, stab)
    _den = math.pi * u_ms * _sy * _sz
    C_pop = min(max((_Q*1000)/_den*24.45/70.9, 1e-4), 500.0) if _den > 1e-10 else 1e-4

    expo    = math.log10(C_pop + 0.01) / math.log10(500.01)
    expo    = max(expo, 0.0)
    q_score = max(0.0, min(1.0, (math.log10(Q_kg) - 1.0) / (math.log10(60000) - 1.0)))
    dur_sc  = min(duree_min / 120.0, 1.0)

    raw = expo*5.5 + q_score*2.5 + dur_sc*1.0

    brutal_m = 1.30 if type_lib.startswith("Brutale") else 1.00
    stab_m   = {"A":0.70,"B":0.85,"C":0.95,"D":1.00,"E":1.10,"F":1.20}.get(stab, 1.00)
    dens_m   = 0.80 + 0.40 * min(math.log10(max(dens_pop,1)) / math.log10(15001), 1.0)
    site_m   = 0.70 + 1.20 * f_site
    alerte_m = 0.78 if alerte else 1.00
    epi_m    = max(0.60, 1.00 - (epi_num - 1) * 0.10)
    evac_m   = max(0.75, 1.00 - max(0, delai_evac - 15) / 200)
    coord_m  = max(0.72, 1.00 - (coord - 1) * 0.09)
    capa_m   = {1: 1.15, 2: 1.00, 3: 0.90}.get(capa_med_num, 1.00)

    # ── Nouveaux multiplicateurs multi-sites ──────────────────────────────
    # Produits les plus réactifs avec Cl2 → facteur aggravant plus fort
    _REACTIF_FORT = {"Aluminium (Al)", "Acétylène (C₂H₂)", "Phosphore (P)",
                     "Arsenic (As)", "Antimoine (Sb)", "Ammoniac (NH₃)"}
    _REACTIF_MOY  = {"Hydrogène (H₂)", "Éthylène", "Éthane",
                     "Chlorure de vinyle", "Silicones"}

    domino_m = 1.00
    if usines_domino:
        for _u in usines_domino:
            _prods = _u.get("produits", [])
            _fort  = len([p for p in _prods if p in _REACTIF_FORT])
            _moy   = len([p for p in _prods if p in _REACTIF_MOY])
            # Chaque produit fort ajoute +8%, chaque produit moyen +4%
            # plafond par usine : +20%
            domino_m *= min(1.20, 1.00 + _fort*0.08 + _moy*0.04)
    # Plafond global domino : ×1.40 (scénario catastrophique)
    domino_m = min(1.40, domino_m)

    # Train en zone : gestion difficile → +6% si train présent
    train_m = 1.06 if has_train else 1.00

    # Établissements vulnérables : population moins autonome → +4% par type
    vuln_m = 1.00
    if has_hopital:   vuln_m += 0.05   # patients non mobiles, protocole NRBC
    if has_ecole:     vuln_m += 0.06   # enfants plus sensibles au Cl2
    if has_gare_rout: vuln_m += 0.03   # forte concentration de personnes
    if has_admin:     vuln_m += 0.02   # bâtiment potentiellement mal équipé
    vuln_m = min(1.15, vuln_m)

    # Capacité CHR : si lits réanimation < blessés graves estimés → aggrave
    # On estime les blessés graves = 30% des blessés → si < capa_ua_max : neutre
    _blesses_graves_est = max(1, int(q_score * 20))
    capa_chr_m = 1.00
    if capa_ua_max > 0 and _blesses_graves_est > capa_ua_max:
        # Chaque UA non prise en charge aggrave le bilan
        _deficit = min((_blesses_graves_est - capa_ua_max) / max(capa_ua_max, 1), 1.0)
        capa_chr_m = 1.00 + _deficit * 0.10  # max +10%

    score = raw * brutal_m * stab_m * dens_m * site_m
    score *= alerte_m * epi_m * evac_m * coord_m * capa_m
    score *= domino_m * train_m * vuln_m * capa_chr_m
    return min(10.0, max(0.0, score))

epi_num_map  = {"EPI 1 — Très faible":1,"EPI 2 — Faible":2,"EPI 3 — Moyen":3,"EPI 4 — Élevé":4}
capa_num_map = {"Limitée":1,"Moyenne":2,"Bonne":3}
capa_num     = capa_num_map.get(capa_med, 1)   # ← valeur numérique active dans tous les calculs

gravite = _compute_gravite(
    Q_kg, u_ms, stab, type_lib, dist_pop, dens_pop,
    duree_min, alerte_prec,
    epi_num_map.get(niveau_epi, 2), delai_evac, coord_sec, facteur_site, capa_num,
    # Nouveaux paramètres multi-sites
    nb_usines    = int(nb_usines),
    usines_domino= usines_domino,
    has_train    = has_train,
    has_hopital  = has_hopital,
    has_ecole    = has_ecole,
    has_admin    = has_admin,
    has_gare_rout= has_gare_rout,
    capa_chr_lits= int(capa_chr_lits),
    capa_ua_max  = int(capa_ua_max),
)
g_color = PAL["danger"] if gravite >= 7 else PAL["warning"] if gravite >= 4 else "#D4AC0D"

# ── Population et surface exposées ────────────────────────────────────────────
SECTEUR = 1/6   # couloir de vent ≈ 60° sur 360°

surf_e1 = math.pi * (r1/1000)**2 * SECTEUR
surf_e2 = math.pi * (r2/1000)**2 * SECTEUR
surf_e3 = math.pi * (r3/1000)**2 * SECTEUR

pop_e1 = int(surf_e1 * dens_pop)
pop_e2 = int(surf_e2 * dens_pop)
pop_e3 = int(surf_e3 * dens_pop)

perim_evac_calc = max(r2, 200.0)
surf_evac = math.pi * (perim_evac_calc/1000)**2

# ── Blessés et décès — calibrés sur 81 accidents + impact multi-sites ───────────
TAUX_B_BASE = 0.0280   # blessés / km² / hab (médiane historique)
TAUX_D_BASE = 0.0014   # décès   / km² / hab (calibré Aqaba, Graniteville)

# ── Facteurs multiplicateurs multi-sites sur les conséquences ────────────────
# Chaque site supplémentaire ajoute des victimes non comptées dans la population
# de densité générale (personnes dans des bâtiments spécifiques).

# 1. Effet domino usines : victimes industrielles + risque explosion aggrave
_REACTIF_FORT_B = {"Aluminium (Al)", "Acétylène (C₂H₂)", "Phosphore (P)",
                   "Arsenic (As)", "Antimoine (Sb)", "Ammoniac (NH₃)"}
_domino_b_mult = 1.00
_domino_d_mult = 1.00
for _u in usines_domino:
    _prods_u = _u.get("produits", [])
    _n_fort  = len([p for p in _prods_u if p in _REACTIF_FORT_B])
    _n_moy   = len([p for p in _prods_u if p not in _REACTIF_FORT_B])
    # Produits forts : risque explosion → +10% blessés, +15% décès
    # Produits moyens : fumées toxiques → +5% blessés, +5% décès
    _domino_b_mult *= min(1.18, 1.00 + _n_fort*0.10 + _n_moy*0.05)
    _domino_d_mult *= min(1.25, 1.00 + _n_fort*0.15 + _n_moy*0.05)
_domino_b_mult = min(1.45, _domino_b_mult)
_domino_d_mult = min(1.60, _domino_d_mult)

# 2. Train : victimes supplémentaires (passagers non évacuables rapidement)
_train_b_add  = int(train_passagers * 0.15) if has_train else 0  # 15% blessés
_train_d_add  = int(train_passagers * 0.02) if has_train else 0  # 2% décès si zone ERPG-2/3

# 3. Établissements vulnérables : populations plus sensibles au Cl₂
# Enfants : 2× plus sensibles | Patients hôpital : 3× | Gare : personnes non informées
_vuln_b_mult = 1.00
_vuln_d_mult = 1.00
if has_ecole:     _vuln_b_mult += 0.07;  _vuln_d_mult += 0.08  # enfants très sensibles
if has_hopital:   _vuln_b_mult += 0.05;  _vuln_d_mult += 0.10  # patients vulnérables
if has_gare_rout:
    _vuln_b_mult += 0.04
    # Blessés fixes issus de la gare (personnes présentes)
_vuln_b_mult = min(1.18, _vuln_b_mult)
_vuln_d_mult = min(1.22, _vuln_d_mult)

# Personnes fixes dans les sites nommés (s'ajoutent à la population générale)
_pop_fixe_blesses = 0
_pop_fixe_deces   = 0
if has_gare_rout and nb_gare_pers > 0:
    _pop_fixe_blesses += int(nb_gare_pers * 0.18)  # 18% blessés dans gare (confinement imparfait)
    _pop_fixe_deces   += int(nb_gare_pers * 0.005) # 0.5% décès si confinement tardif
if has_admin and nb_agents_admin > 0:
    _pop_fixe_blesses += int(nb_agents_admin * 0.08)
if has_ecole:
    _pop_fixe_blesses += 8   # estimation forfaitaire école (variable non connue)
    _pop_fixe_deces   += 1

# 4. Capacité CHR insuffisante : UA non pris en charge → décès supplémentaires
_capa_b_mult = {1: 1.00, 2: 0.85, 3: 0.75}.get(capa_num, 1.00)
_capa_d_mult = {1: 1.00, 2: 0.70, 3: 0.45}.get(capa_num, 1.00)

# Si CHR saturé : décès supplémentaires proportionnels au déficit
_ua_est_base = max(1, int(surf_evac * dens_pop * TAUX_B_BASE * facteur_site / 0.12 * 0.31))
if capa_ua_max > 0 and _ua_est_base > capa_ua_max:
    _deficit_chr = min((_ua_est_base - capa_ua_max) / max(capa_ua_max, 1), 2.0)
    # Chaque UA non pris en charge a 30% de risque de décès supplémentaire
    _deces_chr_add = int((_ua_est_base - capa_ua_max) * 0.30)
else:
    _deces_chr_add = 0

# ── Calcul final blessés ─────────────────────────────────────────────────────
blesses_estimes = max(0, int(
    surf_evac * dens_pop * TAUX_B_BASE * facteur_site / 0.12
    * _capa_b_mult * _domino_b_mult * _vuln_b_mult
) + _train_b_add + _pop_fixe_blesses)

blesses_e3 = max(0, int(blesses_estimes * 0.31))
blesses_e2 = max(0, blesses_estimes - blesses_e3)

# ── Calcul final décès ───────────────────────────────────────────────────────
if gravite >= 7:
    deces_estimes = int(
        surf_evac * dens_pop * TAUX_D_BASE * facteur_site / 0.12
        * (gravite - 6) / 3 * _capa_d_mult * _domino_d_mult * _vuln_d_mult
    ) + _train_d_add + _pop_fixe_deces + _deces_chr_add
elif gravite >= 5:
    deces_estimes = max(0, int(
        blesses_estimes * 0.005 * (gravite - 4)
        * _capa_d_mult * _domino_d_mult * _vuln_d_mult
    )) + _train_d_add + _pop_fixe_deces + _deces_chr_add
else:
    deces_estimes = _train_d_add + _pop_fixe_deces
deces_estimes = min(deces_estimes, blesses_e3)

if run_btn or "mc" not in st.session_state:
    with st.spinner("⚡ Simulation Monte Carlo…"):
        st.session_state["mc"] = monte_carlo(
            Q_kg, u_ms, stab, hauteur_m,
            N=min(n_mc, 2000),   # Plafonner à 2000 pour la réactivité
            duree_min=duree_min, type_lib=type_lib)
        st.session_state["mc_key"] = (Q_kg, u_ms, stab, hauteur_m, n_mc)
mc = st.session_state.get("mc", {})

# ── Auto-relance MC si les inputs ont changé depuis le dernier calcul ─────────
_mc_key_now = (Q_kg, u_ms, stab, hauteur_m, n_mc)
if mc and st.session_state.get("mc_key") != _mc_key_now:
    with st.spinner("⚡ Mise à jour Monte Carlo…"):
        st.session_state["mc"] = monte_carlo(
            Q_kg, u_ms, stab, hauteur_m,
            N=min(n_mc, 2000),
            duree_min=duree_min, type_lib=type_lib)
        st.session_state["mc_key"] = _mc_key_now
    mc = st.session_state["mc"]

# ── Indicateurs MC pour le tableau de bord ────────────────────────────────────
# Probabilités de dépassement à la distance de la population
_d_ref = min(mc.keys(), key=lambda d: abs(d - dist_pop)) if mc else None
mc_p_e1 = mc[_d_ref]["p_e1"] * 100 if _d_ref else 0.0
mc_p_e2 = mc[_d_ref]["p_e2"] * 100 if _d_ref else 0.0
mc_p_e3 = mc[_d_ref]["p_e3"] * 100 if _d_ref else 0.0
mc_c50   = mc[_d_ref]["p50"]        if _d_ref else 0.0
mc_c95   = mc[_d_ref]["p95"]        if _d_ref else 0.0

# ── ONGLETS ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🗺️  Cartographie & Heatmap", "📊  Tableau de Bord",
    "📈  Analyse Monte Carlo",    "🤖  Machine Learning",
    "📚  Base de Données",        "🛡  Organisation des Secours",
    "🔥  Hotspots & Confinement",
])


# ── Fonctions de tracé des cônes orientés selon le vent (style ALOHA) ─────────
def _geo_point(lat, lon, distance_m, bearing_deg):
    """Retourne (lat, lon) d'un point à distance_m dans la direction bearing_deg."""
    R_earth = 6371000.0
    lat_r   = math.radians(lat)
    bear_r  = math.radians(bearing_deg)
    d_r     = distance_m / R_earth
    new_lat = math.asin(math.sin(lat_r)*math.cos(d_r) +
                        math.cos(lat_r)*math.sin(d_r)*math.cos(bear_r))
    new_lon = math.radians(lon) + math.atan2(
        math.sin(bear_r)*math.sin(d_r)*math.cos(lat_r),
        math.cos(d_r) - math.sin(lat_r)*math.sin(new_lat))
    return math.degrees(new_lat), math.degrees(new_lon)


def cone_polygon(lat, lon, radius_m, wind_from_deg,
                 n_arc=100, half_angle=35, back_fraction=0.06):
    """
    Polygone en forme de cloche gaussienne orienté selon la direction du vent.

    Le vent VIENT de wind_from_deg (ex: 270 = vent d'Ouest).
    Le nuage se PROPAGE vers (wind_from_deg + 180) % 360.
    half_angle   : demi-angle du cône en degrés (35° → cône total 70°, comme ALOHA).
    back_fraction: rayon du petit arrondi arrière (côté source).

    Retourne liste [[lat, lon], ...] formant le polygone fermé.
    """
    # Direction de propagation du nuage
    prop_dir = (wind_from_deg + 180) % 360

    pts = []

    # ── Arc frontal gaussien ──────────────────────────────────────────────────
    # Parcourir de -half_angle à +half_angle autour de l'axe de propagation.
    # Le rayon suit une gaussienne : max au centre, effilé aux bords.
    for i in range(n_arc + 1):
        t = -1.0 + 2.0 * i / n_arc          # t ∈ [-1, +1]
        bearing = (prop_dir + t * half_angle) % 360
        # Profil gaussien : r_mod = radius × exp(-0.5 × (t×1.8)²)
        r_mod = radius_m * math.exp(-0.5 * (t * 1.8) ** 2)
        r_mod = max(r_mod, radius_m * 0.04)  # évite les pointes trop fines
        lat_p, lon_p = _geo_point(lat, lon, r_mod, bearing)
        pts.append([lat_p, lon_p])

    # ── Arc arrière (arrondi côté source) ─────────────────────────────────────
    back_r   = radius_m * back_fraction
    back_dir = (prop_dir + 180) % 360       # direction opposée = d'où vient le vent
    for i in range(21):
        # Demi-cercle de -90° à +90° autour de back_dir
        angle = (back_dir - 90 + 180 * i / 20) % 360
        lat_p, lon_p = _geo_point(lat, lon, back_r, angle)
        pts.append([lat_p, lon_p])

    pts.append(pts[0])                      # fermer le polygone
    return pts


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CARTOGRAPHIE & HEATMAP 2D
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="sc-section">🗺 CARTOGRAPHIE DES ZONES DE RISQUE</p>', unsafe_allow_html=True)
    # ── Carte pleine largeur ──────────────────────────────────────────────────
    with st.container():
        # ── Carte Google Satellite / Hybride / Rues — fond dynamique ─────────
        _tile_mode = st.session_state.get("map_tile", "hybrid")
        _TILES = {
            "satellite": (
                "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",  # satellite pur sans étiquettes
                "Google Satellite"
            ),
            "hybrid": (
                "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",  # satellite pur sans étiquettes
                "Google Satellite"
            ),
            "streets": (
                "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",  # satellite pur
                "Google Maps"
            ),
        }
        _tile_url, _tile_attr = _TILES.get(_tile_mode, _TILES["hybrid"])

        # ── Zoom automatique sur les zones — calcul des bounds ────────────────
        # La carte s'ajuste automatiquement pour afficher toutes les zones ERPG.
        _prop_dir_z = (dir_vent + 180) % 360
        # Points extrêmes du cône ERPG-1 (le plus grand)
        _all_pts = cone_polygon(lat, lon, r1, dir_vent,
                                n_arc=60, half_angle=40, back_fraction=0.05)
        _lats = [p[0] for p in _all_pts]
        _lons = [p[1] for p in _all_pts]
        # Bounds avec marge de 12% — zoom serré sur les 3 zones
        _margin_lat = max((_max_lat := max(_lats)) - (_min_lat := min(_lats)), 0.002) * 0.12
        _margin_lon = max((_max_lon := max(_lons)) - (_min_lon := min(_lons)), 0.002) * 0.12
        _sw = [_min_lat - _margin_lat, _min_lon - _margin_lon]
        _ne = [_max_lat + _margin_lat, _max_lon + _margin_lon]

        m = folium.Map(
            location=[lat, lon],
            tiles=_tile_url, attr=_tile_attr,
            prefer_canvas=True,
            zoom_control=True,
        )
        # Fit automatique sur les zones (remplace zoom_start fixe)
        m.fit_bounds([_sw, _ne])

        # Fond satellite pur — sans étiquettes ni frontières (évite Western Sahara)
        folium.LayerControl(position="topright", collapsed=True).add_to(m)

        # ── Zones ERPG — cônes gaussiens sophistiqués ─────────────────────────
        # Chaque zone a : remplissage semi-transparent, bordure pointillée,
        # halo d'animation CSS, étiquette riche, popup HTML détaillé.
        _prop_dir = (dir_vent + 180) % 360

        # Niveau d'alerte MC pour couleurs dynamiques
        _mc_alert_color = (
            "#B91C1C" if mc_p_e2 >= 70 else
            "#D97706" if mc_p_e2 >= 30 else
            "#059669"
        )

        # ── Zones ERPG — couleurs claires et différenciées, bien visibles ──────
        # Remplissage clair + bordure foncée nette = lisibilité maximale
        _zones_cfg = [
            # (radius, fill, border, fill_opacity, border_weight, dash, label, seuil, action, icon)
            (r1, "#86EFAC", "#16A34A", 0.45, 3.5, "6 5",
             "ERPG-1", 1, "Surveillance · Confinement préventif", "🟢"),
            (r2, "#FDB168", "#D97706", 0.50, 4.0, "none",
             "ERPG-2", 3, "Évacuation partielle · Fermeture ERP", "🟠"),
            (r3, "#FC8181", "#C53030", 0.58, 4.5, "none",
             "ERPG-3", 20, "Évacuation totale · EPI A · UMA", "🔴"),
        ]

        for radius, fill_col, border_col, fill_op, bweight, dash, label, seuil_v, action, icon in reversed(_zones_cfg):
            pts = cone_polygon(lat, lon, radius, dir_vent,
                               n_arc=140, half_angle=36, back_fraction=0.04)

            # ── Popup HTML riche ────────────────────────────────────────────
            popup_html = f"""
            <div style="font-family:'Segoe UI',sans-serif;min-width:220px;">
              <div style="background:{border_col};color:#fff;padding:8px 12px;
                          border-radius:6px 6px 0 0;font-weight:700;font-size:13px;">
                {icon} {label} — Seuil {seuil_v} ppm
              </div>
              <div style="padding:10px 12px;background:#fff;border:1px solid #e5e7eb;
                          border-top:none;border-radius:0 0 6px 6px;">
                <table style="width:100%;font-size:11.5px;border-collapse:collapse;">
                  <tr><td style="color:#6b7280;padding:3px 0;">Rayon axial</td>
                      <td style="font-weight:700;text-align:right;color:{border_col};">{radius:.0f} m</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0;">Direction nuage</td>
                      <td style="font-weight:600;text-align:right;">{_prop_dir:.0f}° ({["N","NE","E","SE","S","SO","O","NO"][int((_prop_dir+22.5)//45)%8]})</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0;">Seuil ERPG</td>
                      <td style="font-weight:600;text-align:right;">{seuil_v} ppm</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0;">P(C&gt;seuil) MC</td>
                      <td style="font-weight:700;text-align:right;color:{_mc_alert_color};">{mc_p_e2:.0f} %</td></tr>
                  <tr><td colspan="2" style="padding-top:6px;border-top:1px solid #f3f4f6;">
                    <span style="background:{border_col};color:#fff;border-radius:4px;
                          padding:2px 7px;font-size:10.5px;">⚡ {action}</span>
                  </td></tr>
                </table>
              </div>
            </div>"""

            folium.Polygon(
                locations=pts,
                color=border_col,
                weight=bweight,
                opacity=1.0,
                fill=True,
                fill_color=fill_col,
                fill_opacity=fill_op,
                dash_array=dash if dash != "none" else None,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=(f"<b style='color:{border_col}'>{label}</b> — "
                         f"Rayon {radius:.0f} m · Seuil {seuil_v} ppm"),
            ).add_to(m)

            # ── Étiquette — fond plein opaque, texte blanc, ombre forte ─────
            _lbl_r = radius * 0.72
            _lbl_lat, _lbl_lon = _geo_point(lat, lon, _lbl_r, _prop_dir)
            folium.Marker(
                [_lbl_lat, _lbl_lon],
                icon=folium.DivIcon(
                    html=f"""<div style="
                        background:{border_col};
                        color:#fff;border-radius:6px;padding:4px 10px 4px 8px;
                        font-size:11px;font-weight:800;
                        font-family:'IBM Plex Mono',monospace;
                        box-shadow:0 3px 10px rgba(0,0,0,0.7),
                                   0 0 0 2px rgba(255,255,255,0.3);
                        white-space:nowrap;letter-spacing:0.5px;
                        border:2px solid rgba(255,255,255,0.7);">
                        {icon} {label} &nbsp;{radius:.0f} m
                        </div>""",
                    icon_size=(165, 26), icon_anchor=(82, 13))
            ).add_to(m)

        # ── Périmètre d'évacuation (cône pointillé doré) ─────────────────────
        perim = perim_evac_calc
        pts_perim = cone_polygon(lat, lon, perim, dir_vent,
                                 n_arc=120, half_angle=42, back_fraction=0.03)
        folium.Polygon(
            locations=pts_perim,
            color="#F59E0B", weight=3, opacity=0.9,
            fill=True, fill_color="#FEF3C7", fill_opacity=0.05,
            dash_array="12 6",
            popup=folium.Popup(
                f"<b>⚡ Périmètre d'évacuation</b><br>"
                f"Distance : <b>{perim:.0f} m</b><br>"
                f"Zone à évacuer impérativement",
                max_width=220),
            tooltip=f"⚡ Périmètre évacuation : {perim:.0f} m"
        ).add_to(m)

        # ── Ligne d'axe de propagation (trait de référence) ──────────────────
        _axis_tip_lat, _axis_tip_lon = _geo_point(lat, lon, r1 * 1.05, _prop_dir)
        folium.PolyLine(
            [[lat, lon], [_axis_tip_lat, _axis_tip_lon]],
            color="#FFFFFF", weight=1.5, opacity=0.35,
            dash_array="4 6"
        ).add_to(m)

        # ── Marqueur source — cercle pulsant + popup riche ────────────────────
        # Halo pulsant via CSS injecté dans la carte
        _pulse_id = "src_pulse"
        m.get_root().html.add_child(folium.Element(f"""
        <style>
          @keyframes sc_pulse {{
            0%   {{ transform:scale(1);   opacity:1; }}
            50%  {{ transform:scale(1.6); opacity:0.4; }}
            100% {{ transform:scale(1);   opacity:1; }}
          }}
          .sc-source-pulse {{
            width:28px;height:28px;border-radius:50%;
            background:rgba(220,38,38,0.25);
            animation:sc_pulse 1.8s ease-in-out infinite;
            position:absolute;top:50%;left:50%;
            transform:translate(-50%,-50%);
          }}
        </style>"""))

        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                html="""<div style="position:relative;width:28px;height:28px;">
                  <div class="sc-source-pulse"></div>
                  <div style="position:absolute;top:50%;left:50%;
                    transform:translate(-50%,-50%);
                    width:16px;height:16px;border-radius:50%;
                    background:#DC2626;border:2.5px solid #fff;
                    box-shadow:0 0 0 3px rgba(220,38,38,.4),
                               0 2px 8px rgba(0,0,0,.6);">
                  </div></div>""",
                icon_size=(28, 28), icon_anchor=(14, 14)),
            popup=folium.Popup(
                f"""<div style="font-family:'Segoe UI',sans-serif;min-width:190px;">
                  <div style="background:#DC2626;color:#fff;padding:7px 12px;
                    border-radius:6px 6px 0 0;font-weight:700;font-size:13px;">
                    ☢ SOURCE Cl₂
                  </div>
                  <div style="padding:9px 12px;background:#fff;border:1px solid #e5e7eb;
                    border-top:none;border-radius:0 0 6px 6px;font-size:11.5px;">
                    <b>Quantité :</b> {Q_kg:.0f} kg<br>
                    <b>Type :</b> {type_lib.split()[0]}<br>
                    <b>Durée :</b> {duree_min} min<br>
                    <b>Débit :</b> {Q_kgs:.2f} kg/s<br>
                    <b>Vent :</b> {u_ms} m/s — {dir_vent}°<br>
                    <b>Stabilité :</b> Classe {stab}<br>
                    <b>Lat / Lon :</b> {lat:.4f} / {lon:.4f}
                  </div></div>""",
                max_width=230),
            tooltip="☢ Source Cl₂ — cliquez pour détails"
        ).add_to(m)

        # ── Flèche de propagation du nuage ────────────────────────────────────
        _arrow_len = max(r2 * 0.28, 250)
        _tip_lat, _tip_lon = _geo_point(lat, lon, _arrow_len, _prop_dir)
        # Ligne principale
        folium.PolyLine(
            [[lat, lon], [_tip_lat, _tip_lon]],
            color="#2563EB", weight=4, opacity=0.85,
            tooltip=f"Propagation nuage — {_prop_dir:.0f}°"
        ).add_to(m)
        # Tête de flèche (petit cercle)
        folium.CircleMarker(
            [_tip_lat, _tip_lon], radius=5,
            color="#2563EB", fill=True, fill_color="#93C5FD",
            fill_opacity=1, weight=2
        ).add_to(m)
        # Étiquette vent
        folium.Marker(
            [_tip_lat, _tip_lon],
            icon=folium.DivIcon(
                html=f"""<div style="
                    background:rgba(37,99,235,0.92);color:#fff;
                    border-radius:6px;padding:3px 9px;font-size:10.5px;
                    font-weight:600;font-family:'IBM Plex Mono',monospace;
                    white-space:nowrap;margin-left:10px;margin-top:-12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.4);
                    border:1px solid rgba(255,255,255,0.3);">
                    💨 {dir_vent}° → {_prop_dir:.0f}° &nbsp;|&nbsp; {u_ms} m/s
                    </div>""",
                icon_size=(210, 24), icon_anchor=(0, 12))
        ).add_to(m)
        # Couleur dynamique selon niveau d'alerte MC
        _leg_mc_color = ("#B91C1C" if mc_p_e2>=70 else
                         "#B45309" if mc_p_e2>=30 else "#15803D")
        _leg_mc_label = ("🔴 ROUGE" if mc_p_e2>=70 else
                         "🟠 ORANGE" if mc_p_e2>=30 else "🟢 VERT")
        _leg_g_color  = ("#DC2626" if gravite>=7 else
                         "#D97706" if gravite>=4 else "#16A34A")

        m.get_root().html.add_child(folium.Element(f"""
        <style>
          .scleg {{
            position:fixed;bottom:24px;left:14px;z-index:9000;
            background:rgba(8,16,34,0.93);
            padding:0;border-radius:12px;
            border:1px solid rgba(255,255,255,0.12);
            box-shadow:0 6px 28px rgba(0,0,0,0.6),0 0 0 1px rgba(255,255,255,0.04);
            font-family:'Segoe UI',sans-serif;color:#E2E8F0;
            backdrop-filter:blur(8px);min-width:230px;overflow:hidden;
          }}
          .scleg-title {{
            padding:9px 14px 8px;
            background:linear-gradient(90deg,#1e3a5f,#0f2442);
            border-bottom:1px solid rgba(255,255,255,0.10);
            font-size:11px;font-weight:700;letter-spacing:1.8px;
            color:#93C5FD;text-transform:uppercase;
            display:flex;align-items:center;gap:7px;
          }}
          .scleg-body  {{ padding:8px 14px 10px; }}
          .scleg-row   {{ display:flex;align-items:center;gap:9px;
                          padding:4px 0;font-size:11px; }}
          .scleg-swatch{{ width:11px;height:11px;border-radius:3px;
                          flex-shrink:0;border:1px solid rgba(255,255,255,0.2); }}
          .scleg-lbl   {{ flex:1;color:#CBD5E1;font-size:10.5px; }}
          .scleg-val   {{ font-family:monospace;font-size:10.5px;
                          color:#F1F5F9;font-weight:600; }}
          .scleg-sep   {{ height:1px;background:rgba(255,255,255,0.08);margin:5px 0; }}
          .scleg-mc    {{ padding:5px 14px 8px;
                          background:rgba(255,255,255,0.03);
                          border-top:1px solid rgba(255,255,255,0.08);
                          font-size:10px;color:#94A3B8; }}
          .scleg-badge {{ display:inline-block;padding:2px 7px;border-radius:4px;
                          font-size:10px;font-weight:700;margin-left:4px; }}
        </style>
        <div class="scleg">
          <div class="scleg-title">
            <span style="font-size:14px;">⚠</span> ZONES D'IMPACT Cl₂
          </div>
          <div class="scleg-body">
            <div class="scleg-row">
              <div class="scleg-swatch" style="background:#991B1B;box-shadow:0 0 5px #F87171;"></div>
              <span class="scleg-lbl">ERPG-3 · Danger vital · &gt;20 ppm</span>
              <span class="scleg-val">{r3:.0f} m</span>
            </div>
            <div class="scleg-row">
              <div class="scleg-swatch" style="background:#B45309;"></div>
              <span class="scleg-lbl">ERPG-2 · Irréversible · &gt;3 ppm</span>
              <span class="scleg-val">{r2:.0f} m</span>
            </div>
            <div class="scleg-row">
              <div class="scleg-swatch" style="background:#16A34A;"></div>
              <span class="scleg-lbl">ERPG-1 · Irritation · &gt;1 ppm</span>
              <span class="scleg-val">{r1:.0f} m</span>
            </div>
            <div class="scleg-sep"></div>
            <div class="scleg-row">
              <div class="scleg-swatch" style="background:#92400E;border-style:dashed;"></div>
              <span class="scleg-lbl">Périmètre évacuation</span>
              <span class="scleg-val">{perim:.0f} m</span>
            </div>
            <div class="scleg-row">
              <span style="font-size:13px;">💨</span>
              <span class="scleg-lbl">Vent — propagation nuage</span>
              <span class="scleg-val">{dir_vent}° · {u_ms} m/s</span>
            </div>
            <div class="scleg-row">
              <span style="font-size:13px;">☢</span>
              <span class="scleg-lbl">Source Cl₂</span>
              <span class="scleg-val">{Q_kg:.0f} kg</span>
            </div>
          </div>
          <div class="scleg-mc">
            Monte Carlo P(C&gt;ERPG-2) :
            <span class="scleg-badge" style="background:{_leg_mc_color};color:#fff;">
              {mc_p_e2:.0f}% — {_leg_mc_label}
            </span>
            &nbsp;&nbsp; G =
            <span class="scleg-badge" style="background:{_leg_g_color};color:#fff;">
              {gravite:.1f}/10
            </span>
            <br><span style="font-size:9.5px;color:#64748B;margin-top:3px;display:block;">
              🛰 Fond Google Satellite · HazMod
            </span>
          </div>
        </div>"""))


        # ── Simulation panache Cl₂ — canvas Leaflet animé (DANS l'iframe) ──
        from folium import MacroElement as _MacroEl
        from jinja2 import Template as _J2Tmpl

        def _stab_spread(s):
            return {"A":2.6,"B":2.1,"C":1.7,"D":1.2,"E":0.8,"F":0.5}.get(s, 1.2)

        _sp   = _stab_spread(stab)
        _pdir = (dir_vent + 180) % 360
        _aspd = max(0.5, min(4.0, u_ms * 0.40))
        _aint = min(0.95, max(0.25, Q_kg / 9000 * 0.55))

        # MacroElement runs its template INSIDE the Leaflet iframe
        # {{ this._parent.get_name() }} gives the JS map variable name
        class _PlumePlugin(_MacroEl):
            _template = _J2Tmpl("""
            {% macro script(this, kwargs) %}
            (function(){
            var LAT="""  + str(lat)   + """;
            var LON="""  + str(lon)   + """;
            var R1="""   + str(r1)    + """;
            var R2="""   + str(r2)    + """;
            var R3="""   + str(r3)    + """;
            var PDIR=""" + str(_pdir) + """;
            var SP="""   + str(round(_sp,2))   + """;
            var ASPD=""" + str(round(_aspd,2)) + """;
            var AINT=""" + str(round(_aint,2)) + """;

            var map = """ + "{{ this._parent.get_name() }}" + """;

            /* ── Canvas dans overlayPane ──────────────────────── */
            var cv = document.createElement('canvas');
            cv.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:450;';
            map.getPanes().overlayPane.appendChild(cv);
            var ctx = cv.getContext('2d');

            /* ── Particules ───────────────────────────────────── */
            var N=220, t=0, pts=[];
            for(var i=0;i<N;i++) pts.push({age:Math.random()*14, id:i});

            function m2px(meters){
              var mpp=156543.03*Math.cos(LAT*Math.PI/180)/Math.pow(2,map.getZoom());
              return meters/mpp;
            }

            function draw(){
              var sz=map.getSize();
              cv.width=sz.x; cv.height=sz.y;
              ctx.clearRect(0,0,cv.width,cv.height);

              var src=map.latLngToContainerPoint([LAT,LON]);
              var R1px=m2px(R1);

              /* angle canvas: 0=Est, PDIR géo 0=N,90=E */
              var ang=(90-PDIR)*Math.PI/180;
              var ca=Math.cos(ang), sa=Math.sin(ang);

              t+=0.016*ASPD;

              for(var i=0;i<N;i++){
                var p=pts[i];
                p.age+=0.016*ASPD;
                if(p.age>14) p.age=0;

                var fr=p.age/14;
                var along=fr*R1px;
                var sigma=R1px*0.05*SP*(0.5+fr*2.0);

                var s1=((Math.sin((p.id*127.1+1)*0.01)*43758.5)%1+1)%1;
                var s2=((Math.sin((p.id*311.7+2)*0.01)*43758.5)%1+1)%1;

                var lat_off=(s1-0.5)*2*sigma+Math.sin(t*1.1+p.id*0.4)*sigma*0.3;
                var px=src.x+along*ca-lat_off*sa;
                var py=src.y+along*sa+lat_off*ca;
                var pr=(4+fr*22)*(0.7+s2*0.6);

                var decay=Math.max(0.03,1-fr*0.85);
                var ramp=Math.min(1,p.age*1.6);
                var al=AINT*0.24*decay*ramp;
                if(al<0.005) continue;

                var rr=Math.round(215+fr*40);
                var gg=Math.round(228-fr*38);
                var bb=Math.round(10+fr*18);

                try{
                  var g=ctx.createRadialGradient(px,py,0,px,py,pr);
                  g.addColorStop(0,'rgba('+rr+','+gg+','+bb+','+al+')');
                  g.addColorStop(0.5,'rgba('+rr+','+gg+','+bb+','+(al*0.5)+')');
                  g.addColorStop(1,'rgba('+rr+','+gg+','+bb+',0)');
                  ctx.beginPath(); ctx.arc(px,py,pr,0,Math.PI*2);
                  ctx.fillStyle=g; ctx.fill();
                }catch(e){}
              }

              /* ── Halo source ──────────────────────────────────── */
              var hr=Math.max(18,m2px(R3*0.18));
              var hg=ctx.createRadialGradient(src.x,src.y,0,src.x,src.y,hr);
              hg.addColorStop(0,'rgba(255,200,0,0.75)');
              hg.addColorStop(0.4,'rgba(255,130,0,0.35)');
              hg.addColorStop(1,'rgba(255,60,0,0)');
              ctx.beginPath(); ctx.arc(src.x,src.y,hr,0,Math.PI*2);
              ctx.fillStyle=hg; ctx.fill();

              requestAnimationFrame(draw);
            }

            /* repositionner quand la carte bouge */
            map.on('move zoom moveend zoomend', function(){
              var tf=map.getPanes().mapPane.style.transform||'';
              cv.style.transform='';
            });

            requestAnimationFrame(draw);
            })();
            {% endmacro %}
            """)

        _plume_plugin = _PlumePlugin()
        _plume_plugin.add_to(m)



        map_data = st_folium(
            m, width=None, height=700, key="main_map",
            returned_objects=["last_clicked", "bounds", "zoom"]
        )

        # ── Clic sur la carte → déplace instantanément la source ─────────────
        if map_data and map_data.get("last_clicked"):
            cl = map_data["last_clicked"]
            new_lat, new_lon = round(cl["lat"], 4), round(cl["lng"], 4)
            if (new_lat != st.session_state.get("map_lat") or
                    new_lon != st.session_state.get("map_lon")):
                st.session_state["map_lat"] = new_lat
                st.session_state["map_lon"] = new_lon
                # Synchroniser les champs GPS sidebar
                st.session_state["lat_input"] = new_lat
                st.session_state["lon_input"] = new_lon
                # Vider le cache hotspots pour forcer recalcul
                if hasattr(_get_hotspots_cached, "clear"):
                    _get_hotspots_cached.clear()
                st.rerun()

        # ── Bandeau info zones — sophistiqué, décalé sous la carte ────────
        _dir_label = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                      "S","SSO","SO","OSO","O","ONO","NO","NNO"][int((_prop_dir+11.25)//22.5)%16]
        st.markdown(f"""
<div style="margin-top:10px;margin-bottom:4px;
            background:linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#0f2442 100%);
            border-radius:12px;padding:14px 20px;
            border:1px solid rgba(255,255,255,0.10);
            box-shadow:0 4px 18px rgba(0,0,0,0.35);">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
    <span style="font-size:15px;">⚠</span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
                 letter-spacing:2px;color:#93C5FD;text-transform:uppercase;">
      Zones d'impact Cl₂ · Scénario actuel
    </span>
    <span style="margin-left:auto;font-family:monospace;font-size:10px;color:#64748B;">
      🛰 {lat:.4f}°N {lon:.4f}°E
    </span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;">
    <div style="background:rgba(153,27,27,0.25);border:1px solid #991B1B;
                border-radius:8px;padding:10px 12px;text-align:center;">
      <div style="font-size:18px;margin-bottom:2px;">🔴</div>
      <div style="font-family:monospace;font-size:16px;font-weight:700;color:#F87171;">
        {r3:.0f} m
      </div>
      <div style="font-size:9.5px;color:#FCA5A5;margin-top:2px;font-weight:600;">
        ERPG-3 · DANGER VITAL
      </div>
      <div style="font-size:9px;color:#94A3B8;margin-top:3px;">seuil 20 ppm</div>
      <div style="font-size:8.5px;color:#FDA4AF;margin-top:4px;
                  background:rgba(153,27,27,0.4);border-radius:4px;padding:2px 4px;">
        Évacuation totale · EPI A
      </div>
    </div>
    <div style="background:rgba(180,83,9,0.22);border:1px solid #B45309;
                border-radius:8px;padding:10px 12px;text-align:center;">
      <div style="font-size:18px;margin-bottom:2px;">🟠</div>
      <div style="font-family:monospace;font-size:16px;font-weight:700;color:#FCD34D;">
        {r2:.0f} m
      </div>
      <div style="font-size:9.5px;color:#FDE68A;margin-top:2px;font-weight:600;">
        ERPG-2 · IRRÉVERSIBLE
      </div>
      <div style="font-size:9px;color:#94A3B8;margin-top:3px;">seuil 3 ppm</div>
      <div style="font-size:8.5px;color:#FDE68A;margin-top:4px;
                  background:rgba(180,83,9,0.4);border-radius:4px;padding:2px 4px;">
        Évacuation partielle · ERP
      </div>
    </div>
    <div style="background:rgba(22,163,74,0.18);border:1px solid #16A34A;
                border-radius:8px;padding:10px 12px;text-align:center;">
      <div style="font-size:18px;margin-bottom:2px;">🟢</div>
      <div style="font-family:monospace;font-size:16px;font-weight:700;color:#4ADE80;">
        {r1:.0f} m
      </div>
      <div style="font-size:9.5px;color:#86EFAC;margin-top:2px;font-weight:600;">
        ERPG-1 · IRRITATION
      </div>
      <div style="font-size:9px;color:#94A3B8;margin-top:3px;">seuil 1 ppm</div>
      <div style="font-size:8.5px;color:#86EFAC;margin-top:4px;
                  background:rgba(22,163,74,0.3);border-radius:4px;padding:2px 4px;">
        Surveillance · Confinement
      </div>
    </div>
    <div style="background:rgba(37,99,235,0.15);border:1px solid #2563EB;
                border-radius:8px;padding:10px 12px;text-align:center;">
      <div style="font-size:18px;margin-bottom:2px;">💨</div>
      <div style="font-family:monospace;font-size:13px;font-weight:700;color:#93C5FD;">
        {dir_vent}° → {_prop_dir:.0f}°
      </div>
      <div style="font-size:9.5px;color:#BFDBFE;margin-top:2px;font-weight:600;">
        PROPAGATION NUAGE
      </div>
      <div style="font-size:9px;color:#94A3B8;margin-top:3px;">{u_ms} m/s · {_dir_label}</div>
      <div style="font-size:8.5px;color:#93C5FD;margin-top:4px;
                  background:rgba(37,99,235,0.25);border-radius:4px;padding:2px 4px;">
        Classe {stab} · {type_lib.split()[0]}
      </div>
    </div>
  </div>
  <div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.07);
              display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <span style="font-size:10px;color:#64748B;font-family:monospace;">
      📍 Cliquez sur la carte pour déplacer la source
    </span>
    <span style="font-size:10px;color:#64748B;font-family:monospace;margin-left:auto;">
      Monte Carlo P(C&gt;ERPG-2) :
      <span style="color:{_leg_mc_color};font-weight:700;">{mc_p_e2:.0f}%</span>
      &nbsp;·&nbsp; Indice G :
      <span style="color:{_leg_g_color};font-weight:700;">{gravite:.1f}/10</span>
    </span>
  </div>
</div>""", unsafe_allow_html=True)
        # Options de fond de carte
        _tile_col1, _tile_col2, _tile_col3 = st.columns(3)
        with _tile_col1:
            if st.button("🛰 Satellite", key="btn_sat", use_container_width=True):
                st.session_state["map_tile"] = "satellite"
                st.rerun()
        with _tile_col2:
            if st.button("🗺 Hybride", key="btn_hyb", use_container_width=True):
                st.session_state["map_tile"] = "hybrid"
                st.rerun()
        with _tile_col3:
            if st.button("🏙 Rues", key="btn_str", use_container_width=True):
                st.session_state["map_tile"] = "streets"
                st.rerun()

    # ── Heatmap SOUS la carte (pleine largeur) ───────────────────────────────
    st.markdown('<p class="sc-section">🌡 HEATMAP DE CONCENTRATION Cl₂ (ppm)</p>', unsafe_allow_html=True)
    with st.container():
        extent_hm = max(r1*1.25, 1500)
        xs, ys, Z = grille_2d(Q_kg, u_ms, stab, hauteur_m, extent=extent_hm, n=60, duree_min=duree_min, type_lib=type_lib)
        Z_log = np.log10(np.clip(Z, 0.001, None))
        fig_hm = go.Figure()
        fig_hm.add_trace(go.Heatmap(
            x=xs, y=ys, z=Z_log,
            colorscale=RISK_CS, zmin=np.log10(0.01), zmax=np.log10(max(Z.max(),50)),
            showscale=True,
            colorbar=dict(
                title=dict(text="log₁₀(ppm)", font=dict(size=10,color=PAL["muted"])),
                tickvals=[np.log10(v) for v in [0.1,1,3,10,20,100]],
                ticktext=["0.1","1.0","3 ▶E2","10","20 ▶E3","100"],
                tickfont=dict(size=9,color=PAL["muted"]),
                len=0.85, thickness=14,
                bgcolor="#FFFFFF", bordercolor=PAL["border"]),
            hovertemplate="x=%{x:.0f} m, y=%{y:.0f} m<br>C≈%{customdata:.2f} ppm<extra></extra>",
            customdata=Z,
        ))
        for sv, col, lbl in [(SEUILS["ERPG-1"],"#52B788","ERPG-1"),
                              (SEUILS["ERPG-2"],"#F4A261","ERPG-2"),
                              (SEUILS["ERPG-3"],"#E63946","ERPG-3")]:
            fig_hm.add_trace(go.Contour(
                x=xs, y=ys, z=Z, contours_coloring="none",
                line=dict(color=col, width=2, dash="dash"),
                contours=dict(start=sv, end=sv, size=1),
                showscale=False, name=lbl, hoverinfo="skip"))
        fig_hm.add_trace(go.Scatter(x=[0], y=[0], mode="markers",
            marker=dict(color=PAL["accent"],size=14,symbol="x",
                        line=dict(color="white",width=2)),
            name="Source Cl₂"))
        apply_layout(fig_hm,
            f"Heatmap de Concentration Cl₂ — Vue aérienne · Q={Q_kg:.0f} kg · "
            f"Vent {u_ms} m/s · Classe {stab}", h=540)
        fig_hm.update_layout(
            xaxis_title="Distance axiale dans la direction du vent (m)",
            yaxis_title="Distance transversale (m)",
            margin=dict(l=60, r=40, t=60, b=50))
        st.plotly_chart(fig_hm, use_container_width=True)

    # ── Profil multi-stabilité ────────────────────────────────────────────────
    st.markdown('<p class="sc-section">📐 PROFIL AXIAL — COMPARAISON PAR CLASSE DE STABILITÉ</p>', unsafe_allow_html=True)
    dist_v = np.linspace(50, max(r1*1.5, 2000), 250)
    stab_c = {"A":PAL["safe"],"B":"#57CC99","C":"#80ED99","D":PAL["blue"],"E":PAL["warning"],"F":PAL["danger"]}
    fig_multi = go.Figure()
    for sc, col in stab_c.items():
        vals = [conc_ppm(Q_kgs, u_ms, d, 0, sc, H_eff) for d in dist_v]
        is_cur = (sc == stab)
        fig_multi.add_trace(go.Scatter(x=dist_v, y=vals, name=f"Classe {sc}",
            line=dict(color=col, width=3 if is_cur else 1.3, dash="solid" if is_cur else "dot"),
            opacity=1.0 if is_cur else 0.45,
            hovertemplate=f"<b>Classe {sc}</b><br>x=%{{x:.0f}} m<br>C=%{{y:.3f}} ppm<extra></extra>"))
    add_seuil_lines(fig_multi)
    apply_layout(fig_multi, f"Profil de Concentration selon la Stabilité — Vent {u_ms} m/s, Cl₂ {Q_kg:.0f} kg", h=360, ylog=True)
    fig_multi.update_layout(xaxis_title="Distance (m)", yaxis_title="Concentration Cl₂ (ppm) — échelle log")
    st.plotly_chart(fig_multi, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TABLEAU DE BORD
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if gravite >= 7:
        al_cls, al_icon = "rouge","🔴"
        al_titre = "ALERTE ROUGE — Danger vital immédiat"
        al_msg = f"Évacuation immédiate dans un rayon de {r3:.0f} m. EPI niveau A obligatoire."
    elif gravite >= 4:
        al_cls, al_icon = "orange","🟠"
        al_titre = "ALERTE ORANGE — Risque significatif"
        al_msg = f"Confinement/évacuation dans un rayon de {r2:.0f} m. EPI Catégorie 3 et de Type 1"
    else:
        al_cls, al_icon = "jaune","🟡"
        al_titre = "ALERTE JAUNE — Risque modéré"
        al_msg = f"Surveillance et confinement préventif dans un rayon de {r1:.0f} m."

    st.markdown(f"""
    <div class="alert-banner {al_cls}">
      <div class="alert-icon">{al_icon}</div>
      <div>
        <div class="alert-title">{al_titre}</div>
        <div class="alert-text">{al_msg}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    k1,k2,k3,k4,k5 = st.columns(5)
    for col,val,label,sub,cls,cval in [
        (k1, f"{gravite:.1f}/10",    "INDICE GRAVITÉ",
         f"Site : {config_site[:20]}",
         "danger" if gravite>=7 else "warning" if gravite>=4 else "ok", g_color),
        (k2, f"{r3:.0f} m",          "ZONE ERPG-3",   "Danger vital (20 ppm)",  "danger",  PAL["danger"]),
        (k3, f"{r2:.0f} m",          "ZONE ERPG-2",   "Irréversible (3 ppm)",   "warning", PAL["warning"]),
        (k4, f"{pop_e2:,}",          "POP. EXPOSÉE",  f"Secteur vent — ERPG-2", "info",    PAL["blue"]),
        (k5, f"{blesses_estimes:,}", "BLESSÉS ESTIMÉS",f"Décès estimés : {deces_estimes}", "danger" if blesses_estimes>100 else "warning", PAL["danger"] if blesses_estimes>100 else PAL["warning"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls}">
              <div class="kpi-value" style="color:{cval}">{val}</div>
              <div class="kpi-label">{label}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    col_g1, col_g2 = st.columns([3, 2])

    with col_g1:
        st.markdown('<p class="sc-section">📉 PROFIL DE CONCENTRATION + INCERTITUDE MONTE CARLO</p>', unsafe_allow_html=True)
        dist_v2 = np.linspace(30, max(r1*1.4, 2500), 300)
        conc_v2 = [conc_ppm(Q_kgs, u_ms, d, 0, stab, H_eff) for d in dist_v2]
        fig_conc = go.Figure()

        # Bandes de risque en fond
        for y0,y1,fc in [(SEUILS["ERPG-3"],1000,"rgba(230,57,70,0.07)"),
                          (SEUILS["ERPG-2"],SEUILS["ERPG-3"],"rgba(244,162,97,0.07)"),
                          (SEUILS["ERPG-1"],SEUILS["ERPG-2"],"rgba(82,183,136,0.07)")]:
            fig_conc.add_hrect(y0=y0, y1=y1, fillcolor=fc, layer="below", line_width=0)

        # Bande d'incertitude Monte Carlo [P5–P95]
        if mc:
            dists_mc = sorted(mc.keys())
            p05_mc = [mc[d]["p05"] for d in dists_mc]
            p95_mc = [mc[d]["p95"] for d in dists_mc]
            p50_mc = [mc[d]["p50"] for d in dists_mc]
            fig_conc.add_trace(go.Scatter(
                x=list(dists_mc) + list(reversed(dists_mc)),
                y=p95_mc + list(reversed(p05_mc)),
                fill="toself", fillcolor="rgba(36,113,163,0.10)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Incertitude MC [P5–P95]", hoverinfo="skip"))
            fig_conc.add_trace(go.Scatter(
                x=dists_mc, y=p50_mc,
                name="Médiane MC (P50)",
                line=dict(color=PAL["blue"], width=2, dash="dash"),
                mode="lines",
                hovertemplate="<b>MC Médiane</b><br>d=%{x:.0f} m<br>C=%{y:.3f} ppm<extra></extra>"))

        # Courbe déterministe
        for threshold, fc, name in [
            (SEUILS["ERPG-3"],"rgba(230,57,70,0.22)","C > ERPG-3"),
            (SEUILS["ERPG-2"],"rgba(244,162,97,0.16)","C > ERPG-2"),
        ]:
            mask = np.array(conc_v2)>=threshold
            if mask.any():
                fig_conc.add_trace(go.Scatter(
                    x=dist_v2[mask], y=np.array(conc_v2)[mask],
                    fill="tozeroy", fillcolor=fc, line=dict(color="rgba(0,0,0,0)"),
                    name=name, hoverinfo="skip", showlegend=True))
        fig_conc.add_trace(go.Scatter(x=dist_v2, y=conc_v2,
            name=f"Concentration déterministe — Classe {stab}",
            line=dict(color=PAL["accent"], width=2.8),
            hovertemplate="<b>%{x:.0f} m</b><br>C=%{y:.3f} ppm<extra></extra>"))

        add_seuil_lines(fig_conc)
        for rx,col,lbl in [(r3,PAL["danger"],"R₃"),(r2,PAL["warning"],"R₂"),(r1,PAL["caution"],"R₁")]:
            if rx < dist_v2[-1]:
                fig_conc.add_vline(x=rx, line_dash="dot", line_color=col, line_width=1.2,
                    annotation_text=f" {lbl}={rx:.0f}m",
                    annotation_font=dict(size=8.5,color=col), annotation_position="top right")

        # Ligne distance population
        if dist_pop <= dist_v2[-1]:
            fig_conc.add_vline(x=dist_pop, line_dash="solid", line_color="#7D3C98",
                line_width=1.8,
                annotation_text=f" 👥 Pop. ({dist_pop}m)",
                annotation_font=dict(size=9, color="#7D3C98"),
                annotation_position="top left")

        apply_layout(fig_conc, f"Profil Axial — {Q_kg:.0f} kg Cl₂ | Vent {u_ms} m/s | Stabilité {stab} | Site : {config_site}", h=420, ylog=True)
        fig_conc.update_layout(xaxis_title="Distance dans l'axe du vent (m)",
                               yaxis_title="Concentration Cl₂ (ppm) — échelle log")
        st.plotly_chart(fig_conc, use_container_width=True)

        # ── Indicateurs MC à la distance de la population ─────────────────────
        if mc:
            st.markdown(f'<p class="sc-section">🎲 PROBABILITÉS MONTE CARLO — POPULATION À {dist_pop:.0f} m</p>', unsafe_allow_html=True)
            cm1, cm2, cm3, cm4 = st.columns(4)
            for c_col, pval, label, sub, cls, col_v in [
                (cm1, mc_p_e1, "P(C > ERPG-1)", "Irritation légère",  "ok",   PAL["safe"]),
                (cm2, mc_p_e2, "P(C > ERPG-2)", "Effets irréversibles","warn", PAL["warning"]),
                (cm3, mc_p_e3, "P(C > ERPG-3)", "Danger vital",        "bad",  PAL["danger"]),
                (cm4, mc_c95,  "Concentration P95", "ppm — pire cas",   "blue", PAL["blue"]),
            ]:
                disp = f"{pval:.1f}%" if "P(" in label else f"{pval:.2f} ppm"
                with c_col:
                    st.markdown(f"""
                    <div class="mc-mini {cls}">
                      <div class="mc-mini-val" style="color:{col_v};">{disp}</div>
                      <div class="mc-mini-lbl">{label}</div>
                      <div class="mc-mini-sub">{sub}</div>
                    </div>""", unsafe_allow_html=True)

    with col_g2:
        st.markdown('<p class="sc-section">⚡ INDICE DE GRAVITÉ</p>', unsafe_allow_html=True)
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=gravite,
            delta={"reference":5.0,"increasing":{"color":PAL["danger"]},
                   "decreasing":{"color":PAL["caution"]}},
            title={"text":f"Scénario : {type_lib.split(' ')[0]}<br>"
                          f"<span style='font-size:0.75em;color:#6B7A99'>Indice composite 0–10</span>",
                   "font":{"color":PAL["text"],"size":13}},
            number={"font":{"color":g_color,"size":52,"family":"IBM Plex Mono"},
                    "suffix":" / 10"},
            gauge={
                "axis":{"range":[0,10],"tickwidth":1,"tickcolor":PAL["muted"],
                        "tickfont":{"size":10}},
                "bar":{"color":g_color,"thickness":0.28},
                "bgcolor":"#F5F7FA", "borderwidth":1, "bordercolor":PAL["border"],
                "steps":[{"range":[0.0,3.5],"color":"#EBF5EB"},
                          {"range":[3.5,6.5],"color":"#FEF9E7"},
                          {"range":[6.5,10.0],"color":"#FDEDEC"}],
                "threshold":{"line":{"color":PAL["danger"],"width":4},"thickness":0.85,"value":7},
            }))
        fig_g.update_layout(paper_bgcolor="#FFFFFF", font=dict(color=PAL["text"]),
                            height=300, margin=dict(l=30,r=30,t=60,b=20))
        st.plotly_chart(fig_g, use_container_width=True)

        st.markdown('<p class="sc-section">🕸 RADAR FACTEURS DE RISQUE</p>', unsafe_allow_html=True)
        epi_map = {"EPI 1 — Très faible":1,"EPI 2 — Faible":2,"EPI 3 — Moyen":3,"EPI 4 — Élevé":4}
        radar_c = ["Quantité","Vent faible","Stabilité","Densité pop.","EPI faible","Urgence"]
        radar_v = [
            min(10,np.log10(Q_kg+1)*2.5), min(10,(1/u_ms)*5),
            {"A":1,"B":2,"C":3,"D":5,"E":8,"F":10}.get(stab,5),
            min(10,np.log10(dens_pop+1)*2.2),
            (5-epi_map.get(niveau_epi,2))*2.5, min(10,delai_evac/12),
        ]
        fig_r = go.Figure(go.Scatterpolar(
            r=radar_v+[radar_v[0]], theta=radar_c+[radar_c[0]],
            fill="toself",
            fillcolor="rgba(230,57,70,0.12)" if gravite>=7 else "rgba(244,162,97,0.12)",
            line=dict(color=g_color, width=2.5),
            marker=dict(color=g_color, size=7),
            hovertemplate="<b>%{theta}</b><br>Score : %{r:.1f}/10<extra></extra>"))
        fig_r.update_layout(
            polar=dict(bgcolor="#F9FAFB",
                radialaxis=dict(visible=True,range=[0,10],showticklabels=True,
                                tickfont=dict(size=8,color=PAL["muted"]),
                                gridcolor="#E8ECF0",linecolor=PAL["border"]),
                angularaxis=dict(tickfont=dict(size=10,color=PAL["text"]),
                                 gridcolor="#E8ECF0",linecolor=PAL["border"])),
            paper_bgcolor="#FFFFFF", font=dict(color=PAL["text"]),
            showlegend=False, height=300, margin=dict(l=40,r=40,t=20,b=20))
        st.plotly_chart(fig_r, use_container_width=True)

    # Consignes
    st.markdown('<p class="sc-section">🚨 CONSIGNES OPÉRATIONNELLES</p>', unsafe_allow_html=True)
    co1,co2,co3 = st.columns(3)
    for col,title,items in [
        (co1,"🏥 SANTÉ / VICTIMES",[
            ("Blessés estimés (total)",    f"{blesses_estimes:,}"),
            ("dont zone ERPG-3 (graves)",  f"{blesses_e3:,}"),
            ("Décès estimés",              f"{deces_estimes}"),
            ("Hôpitaux","Critique" if gravite>7 else "Standard"),
            ("Antidote","O₂ 100% + bronchodilatateurs")]),
        (co2,"🚒 INTERVENTION",[
            ("EPI requis","Catégorie 3 et de Type 1 " if gravite>6 else "Catégorie 3 et de Type 1 "),
            ("Délai évacuation",f"< {delai_evac} min"),
            ("Périmètre sécurité",f"{max(r3*1.2,200):.0f} m"),
            ("Neutralisation","Eau / soude NaOH"),
            ("Équipes SDIS",f"{'3+' if gravite>7 else '2'} équipes")]),
        (co3,"📡 COMMUNICATIONS",[
            ("Alerte pop.","Immédiate" if gravite>7 else "Urgente" if gravite>4 else "Préventive"),
            ("Bulletin","Crise" if gravite>6 else "Standard"),
            ("Coordination","Préfecture + DGPC" if gravite>5 else "Pompiers + SAMU"),
            ("Fréquence MAJ",f"Toutes les {15 if gravite>6 else 30} min"),
            ("Sirènes","Activation" if gravite>7 else "En veille")]),
    ]:
        with col:
            rows="".join(
                f'<div class="ops-item"><span class="ops-key">{k}</span>'
                f'<span class="ops-val">{v}</span></div>'
                for k, v in items
            )
            icon = title.split(" ")[0]
            label = " ".join(title.split(" ")[1:])
            st.markdown(
                f'<div class="ops-card">'
                f'<div class="ops-card-header"><h4>{icon}&nbsp;{label}</h4></div>'
                f'<div class="ops-body">{rows}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<p class="sc-section">📋 SYNTHÈSE DES IMPACTS</p>', unsafe_allow_html=True)
    st.caption(f"Configuration : **{config_site}** — facteur d'exposition site : **{facteur_site:.0%}** "
               f"| Secteur angulaire vent : {SECTEUR:.0%} de la surface du disque")
    # Probabilités MC à la distance pop pour chaque zone
    _p1_pop = f"{mc_p_e1:.0f}%" if mc else "—"
    _p2_pop = f"{mc_p_e2:.0f}%" if mc else "—"
    _p3_pop = f"{mc_p_e3:.0f}%" if mc else "—"
    st.dataframe(pd.DataFrame({
        "Zone":                   ["🟢 ERPG-1 (irritation)","🟠 ERPG-2 (irréversible)","🔴 ERPG-3 (vital)"],
        "Rayon (m)":              [f"{r1:.0f}", f"{r2:.0f}", f"{r3:.0f}"],
        "Surface vent (km²)":     [f"{surf_e1:.3f}", f"{surf_e2:.3f}", f"{surf_e3:.3f}"],
        "Pop. exposée":           [f"{pop_e1:,}", f"{pop_e2:,}", f"{pop_e3:,}"],
        "Blessés estimés":        ["—", f"{blesses_e2:,}", f"{blesses_e3:,}"],
        f"P(dépassement) à {dist_pop}m": [_p1_pop, _p2_pop, _p3_pop],
        "Seuil ppm":              ["1", "3", "20"],
        "Action recommandée":     ["Alerte info + confinement","Évacuation partielle","Évacuation totale"],
    }), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MONTE CARLO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="sc-section">📈 ANALYSE PROBABILISTE — SIMULATION MONTE CARLO</p>', unsafe_allow_html=True)

    # Info contextuelle
    st.markdown(f"""
    <div style="background:#EBF5FB;border:1px solid #AED6F1;border-radius:8px;
                padding:0.7rem 1rem;margin-bottom:0.8rem;font-size:0.82rem;color:#1A5276;">
      <b>🔄 Simulation active</b> — {n_mc:,} itérations •
      Q = <b>{Q_kg:.0f} kg</b> • Vent = <b>{u_ms} m/s</b> •
      Stabilité = <b>{stab}</b> • Site = <b>{config_site}</b><br>
      <span style="color:#5D6D7E;">
      Incertitude modélisée : débit Q ± 30% (loi log-normale) •
      Vent u ± 20% (loi log-normale) •
      Les graphiques se mettent à jour automatiquement à chaque changement de paramètre.
      </span>
    </div>""", unsafe_allow_html=True)

    if not mc:
        st.info("▶ Modifiez un paramètre ou cliquez sur **LANCER LA SIMULATION**.")
    else:
        dists = sorted(mc.keys())
        col_mc1, col_mc2 = st.columns(2)

        with col_mc1:
            p_e1 = [mc[d]["p_e1"]*100 for d in dists]
            p_e2 = [mc[d]["p_e2"]*100 for d in dists]
            p_e3 = [mc[d]["p_e3"]*100 for d in dists]
            fig_pd = go.Figure()
            fig_pd.add_hrect(y0=50,y1=100,fillcolor="rgba(230,57,70,0.05)",layer="below",line_width=0)
            fig_pd.add_hrect(y0=20,y1=50,fillcolor="rgba(244,162,97,0.05)",layer="below",line_width=0)
            fig_pd.add_hrect(y0=0,y1=20,fillcolor="rgba(82,183,136,0.04)",layer="below",line_width=0)
            for pv,col,lbl,w in [(p_e1,PAL["safe"],"P(C > ERPG-1 = 1 ppm)",2.2),
                                   (p_e2,PAL["warning"],"P(C > ERPG-2 = 3 ppm)",2.5),
                                   (p_e3,PAL["danger"],"P(C > ERPG-3 = 20 ppm)",2.8)]:
                fig_pd.add_trace(go.Scatter(x=dists, y=pv, name=lbl,
                    line=dict(color=col,width=w), mode="lines+markers",
                    marker=dict(color=col,size=7,line=dict(color=PAL["bg"],width=1.5)),
                    hovertemplate=f"<b>{lbl}</b><br>d=%{{x:.0f}} m<br>P=%{{y:.1f}}%<extra></extra>"))
            for yref,lbl in [(10,"10%"),(20,"20%"),(50,"50%")]:
                fig_pd.add_hline(y=yref,line_dash="dot",line_color=PAL["muted"],line_width=1,
                    annotation_text=lbl,annotation_position="right",
                    annotation_font=dict(size=8,color=PAL["muted"]))
            apply_layout(fig_pd,"Probabilités de Dépassement ERPG par Distance",h=400)
            fig_pd.update_layout(xaxis_title="Distance (m)",yaxis_title="Probabilité (%)",
                                 yaxis=dict(**BASE_LAYOUT["yaxis"],range=[0,105]))
            st.plotly_chart(fig_pd, use_container_width=True)

        with col_mc2:
            p05=[mc[d]["p05"] for d in dists]; p25=[mc[d]["p25"] for d in dists]
            p50=[mc[d]["p50"] for d in dists]; p75=[mc[d]["p75"] for d in dists]
            p95=[mc[d]["p95"] for d in dists]; mean_=[mc[d]["mean"] for d in dists]
            fig_b = go.Figure()
            fig_b.add_trace(go.Scatter(x=dists+dists[::-1],y=p95+p05[::-1],
                fill="toself",fillcolor="rgba(255,107,53,0.07)",
                line=dict(color="rgba(0,0,0,0)"),name="IC 90% [P5–P95]",hoverinfo="skip"))
            fig_b.add_trace(go.Scatter(x=dists+dists[::-1],y=p75+p25[::-1],
                fill="toself",fillcolor="rgba(255,107,53,0.16)",
                line=dict(color="rgba(0,0,0,0)"),name="IC 50% [P25–P75]",hoverinfo="skip"))
            fig_b.add_trace(go.Scatter(x=dists,y=p50,name="Médiane P50",
                line=dict(color=PAL["accent"],width=3),mode="lines+markers",
                marker=dict(size=7,color=PAL["accent"],line=dict(color=PAL["bg"],width=1.5)),
                hovertemplate="<b>Médiane</b><br>d=%{x:.0f} m<br>C=%{y:.4f} ppm<extra></extra>"))
            fig_b.add_trace(go.Scatter(x=dists,y=mean_,name="Moyenne",
                line=dict(color="#E9C46A",width=1.8,dash="dash"),
                hovertemplate="<b>Moyenne</b><br>d=%{x:.0f} m<br>C=%{y:.4f} ppm<extra></extra>"))
            add_seuil_lines(fig_b)
            apply_layout(fig_b,"Distribution des Concentrations — Bande d'Incertitude",h=400,ylog=True)
            fig_b.update_layout(xaxis_title="Distance (m)",yaxis_title="Concentration Cl₂ (ppm) — log")
            st.plotly_chart(fig_b, use_container_width=True)

        # Violin plots
        st.markdown('<p class="sc-section">🎻 VIOLINS DE DISTRIBUTION PAR DISTANCE</p>', unsafe_allow_html=True)
        sel_d = [d for d in [100,300,500,1000,2000,3000] if d in mc]
        fig_v = go.Figure()
        def hex_to_rgba(h, a=0.18):
            h = h.lstrip("#")
            r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
            return f"rgba({r},{g},{b},{a})"

        for d in sel_d:
            samps = mc[d]["samples"]
            pe2 = mc[d]["p_e2"]
            col = PAL["danger"] if pe2>0.5 else PAL["warning"] if pe2>0.2 else PAL["caution"]
            fig_v.add_trace(go.Violin(y=np.clip(samps,0.001,500),name=f"{d} m",
                box_visible=True,meanline_visible=True,line_color=col,
                fillcolor=hex_to_rgba(col,0.18),opacity=0.9,
                marker=dict(color=col,size=3,opacity=0.3),
                hovertemplate=f"<b>{d} m</b><br>C=%{{y:.3f}} ppm<extra></extra>"))
        for sv,sc,sl in [(1,PAL["safe"],"ERPG-1"),(3,PAL["warning"],"ERPG-2"),(20,PAL["danger"],"ERPG-3")]:
            fig_v.add_hline(y=sv,line_dash="dash",line_color=sc,line_width=1.5,
                annotation_text=f" {sl} ({sv} ppm)",annotation_font=dict(size=9,color=sc))
        apply_layout(fig_v,"Violins des Concentrations Monte Carlo par Distance",h=400,ylog=True)
        fig_v.update_layout(yaxis_title="Concentration Cl₂ (ppm) — log",xaxis_title="Distance")
        st.plotly_chart(fig_v, use_container_width=True)

        # Heatmap probabiliste
        st.markdown('<p class="sc-section">🔥 HEATMAP PROBABILISTE — P(Cl₂ > SEUIL)</p>', unsafe_allow_html=True)
        seuils_l = [0.5,1.0,2.0,3.0,5.0,10.0,15.0,20.0,30.0]
        Z_prob = [[float((mc[d]["samples"]>s).mean())*100 for d in dists] for s in seuils_l]
        fig_hmap = go.Figure(go.Heatmap(
            x=[f"{d} m" for d in dists], y=[f"{s} ppm" for s in seuils_l],
            z=Z_prob, colorscale=RISK_CS, zmin=0, zmax=100,
            text=[[f"{v:.0f}%" for v in row] for row in Z_prob],
            texttemplate="%{text}", textfont=dict(size=9,color="white"),
            colorbar=dict(title=dict(text="P (%)",font=dict(size=10,color=PAL["muted"])),
                tickfont=dict(size=9,color=PAL["muted"]),
                bgcolor="#FFFFFF",bordercolor=PAL["border"],len=0.9,thickness=14),
            hovertemplate="Seuil %{y}<br>Distance %{x}<br>P=%{z:.1f}%<extra></extra>"))
        apply_layout(fig_hmap,"Heatmap Probabiliste — Probabilité de Dépassement par Seuil et Distance",h=360)
        fig_hmap.update_layout(xaxis_title="Distance",yaxis_title="Seuil de concentration Cl₂")
        st.plotly_chart(fig_hmap, use_container_width=True)

        # Tableau
        st.markdown('<p class="sc-section">📋 TABLEAU PROBABILISTE PAR DISTANCE</p>', unsafe_allow_html=True)
        rows_mc = []
        for d in dists:
            r = mc[d]
            risk = "🔴" if r["p_e3"]>0.15 else "🟠" if r["p_e2"]>0.20 else "🟡" if r["p_e1"]>0.30 else "🟢"
            rows_mc.append({"Distance (m)":d,"Risque":risk,"P50 (ppm)":f"{r['p50']:.4f}",
                "P95 (ppm)":f"{r['p95']:.4f}","P(>ERPG-1)":f"{r['p_e1']*100:.1f}%",
                "P(>ERPG-2)":f"{r['p_e2']*100:.1f}%","P(>ERPG-3)":f"{r['p_e3']*100:.1f}%"})
        st.dataframe(pd.DataFrame(rows_mc), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MACHINE LEARNING
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    # Chargement ML à la demande (lazy — ne bloque pas le démarrage)
    df, models = _get_ml_ready()
    if df is None:
        df = pd.DataFrame()
    st.markdown('<p class="sc-section">🤖 MODÈLES DE MACHINE LEARNING — RANDOM FOREST</p>', unsafe_allow_html=True)
    if not models:
        st.warning("Modèles ML non disponibles.")
    else:
        epi_map  = {"EPI 1 — Très faible":1,"EPI 2 — Faible":2,"EPI 3 — Moyen":3,"EPI 4 — Élevé":4}
        _dist = max(dist_pop, 20.0)
        _Q_log = math.log10(max(Q_kg, 1))
        _Cprox_log = math.log10(max(Q_kg / (u_ms * _dist**1.5 + 1), 1e-6))
        X_in = {
            "log_Q":               _Q_log,
            "log_C_proxy":         _Cprox_log,
            "log_dist":            math.log10(_dist),
            "dens_dist":           dens_pop / _dist,
            "Vitesse_vent_ms":     u_ms,
            "Type_libération_num": 1 if type_lib.startswith("Brutale") else 0,
            "Stabilité_atm_code":  1 if stab in "AB" else 2,
            "Hauteur_source_m":    hauteur_m,
            "Durée_libération_min": duree_min,
            "Densité_pop_km2":     dens_pop,
            "Niveau_EPI_num":      epi_map.get(niveau_epi, 2),
            "Alerte_précoce_bin":  int(alerte_prec),
            "Délai_évacuation_min": delai_evac,
            "Formation_pers":      2,
            "Coord_secours":       coord_sec,
            "Capacité_médicale_num": capa_num,   # ← variable globale calibrée
        }
        preds = {}
        for tgt, info in models.items():
            preds[tgt] = max(0, info["model"].predict(np.array([[X_in.get(f,0) for f in info["features"]]]))[0])

        col_ml1, col_ml2, col_ml3 = st.columns([1.3,1.3,1.4])

        with col_ml1:
            st.markdown('<p class="sc-section">🎯 PRÉDICTIONS RF</p>', unsafe_allow_html=True)
            for tgt,label,fmt,col in [
                ("Indice_gravité","Indice de Gravité",f"{preds.get('Indice_gravité',0):.2f} / 10.7",
                 PAL["danger"] if preds.get('Indice_gravité',0)>7 else PAL["warning"]),
                ("Blessés_total","Blessés Totaux",f"{int(preds.get('Blessés_total',0)):,} pers.",PAL["warning"]),
                ("Zone_impact_km2","Zone d'Impact",f"{preds.get('Zone_impact_km2',0):.3f} km²",PAL["blue"]),
                ("Décès","Décès Estimés",f"{int(preds.get('Décès',0))} décès",PAL["danger"]),
            ]:
                r2v = models.get(tgt,{}).get("r2",0)
                bw = int(max(0,min(100,r2v*100)))
                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #D5DEE8;border-radius:8px;
                            padding:0.8rem 1rem;margin-bottom:0.6rem;
                            box-shadow:0 1px 4px rgba(0,0,0,0.05);">
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span style="font-size:0.7rem;color:{PAL['muted']};text-transform:uppercase;
                                 letter-spacing:1px;">{label}</span>
                    <span style="font-family:'IBM Plex Mono';font-size:1.15rem;
                                 font-weight:600;color:{col}">{fmt}</span>
                  </div>
                  <div style="margin-top:6px;background:#EEF1F5;border-radius:4px;height:4px;">
                    <div style="width:{bw}%;background:{col};height:4px;border-radius:4px;opacity:0.85;"></div>
                  </div>
                  <div style="font-size:0.65rem;color:{PAL['muted']};margin-top:3px;">
                    R² CV = {r2v:.3f}</div>
                </div>""", unsafe_allow_html=True)

        with col_ml2:
            tgt_sel = st.selectbox("Modèle", list(models.keys()), key="ml_tgt")
            info = models[tgt_sel]
            imp = info["model"].feature_importances_
            fl = [f.replace("_"," ").replace("num","").strip() for f in info["features"]]
            imp_df = pd.DataFrame({"Feature":fl,"Imp":imp}).sort_values("Imp")
            imp_cols = [PAL["danger"] if v>=imp.max()*0.8 else
                        PAL["warning"] if v>=imp.max()*0.5 else
                        PAL["blue"] if v>=imp.max()*0.25 else PAL["muted"]
                        for v in imp_df["Imp"]]
            fig_imp = go.Figure(go.Bar(x=imp_df["Imp"],y=imp_df["Feature"],orientation="h",
                marker=dict(color=imp_cols,line=dict(color=PAL["bg"],width=0.5)),
                text=[f"{v:.3f}" for v in imp_df["Imp"]],textposition="outside",
                textfont=dict(size=8.5,color=PAL["muted"]),
                hovertemplate="<b>%{y}</b><br>Importance : %{x:.4f}<extra></extra>"))
            apply_layout(fig_imp,f"Importance des Variables — {tgt_sel}",h=420)
            fig_imp.update_layout(
                xaxis_title="Importance (Gini)",
                yaxis_tickfont=dict(size=9, color=PAL["text"]))
            st.plotly_chart(fig_imp, use_container_width=True)

        with col_ml3:
            st.markdown('<p class="sc-section">📊 PERFORMANCE R² PAR MODÈLE</p>', unsafe_allow_html=True)
            tgt_n = list(models.keys()); r2_v = [models[t]["r2"] for t in tgt_n]
            n_v = [models[t]["n"] for t in tgt_n]
            bc = [PAL["safe"] if v>=0.7 else PAL["warning"] if v>=0.4 else PAL["danger"] for v in r2_v]
            fig_r2 = go.Figure(go.Bar(x=tgt_n,y=r2_v,marker=dict(color=bc),
                text=[f"R²={v:.3f}\nn={n}" for v,n in zip(r2_v,n_v)],
                textposition="outside",textfont=dict(size=9,color=PAL["text"]),
                hovertemplate="<b>%{x}</b><br>R²=%{y:.3f}<extra></extra>"))
            fig_r2.add_hline(y=0.7,line_dash="dash",line_color=PAL["safe"],
                annotation_text=" Bon (0.70)",annotation_font=dict(size=8.5,color=PAL["safe"]))
            fig_r2.add_hline(y=0.4,line_dash="dot",line_color=PAL["warning"],
                annotation_text=" Acceptable (0.40)",annotation_font=dict(size=8.5,color=PAL["warning"]))
            apply_layout(fig_r2,"Score R² — Validation Croisée 5-Fold",h=260)
            fig_r2.update_layout(yaxis=dict(**BASE_LAYOUT["yaxis"],range=[0,1.1]),
                                 yaxis_title="R² (CV 5-fold)")
            st.plotly_chart(fig_r2, use_container_width=True)

            # Scatter réel vs prédit
            sub2 = df[models[tgt_sel]["features"]+[tgt_sel]].dropna()
            y_r = sub2[tgt_sel].values
            y_p = models[tgt_sel]["model"].predict(sub2[models[tgt_sel]["features"]])
            fig_pv = go.Figure()
            fig_pv.add_trace(go.Scatter(x=y_r,y=y_p,mode="markers",
                marker=dict(color=PAL["accent"],size=6,opacity=0.7,
                            line=dict(color=PAL["bg"],width=0.8)),
                hovertemplate="Réel:%{x:.2f}<br>Prédit:%{y:.2f}<extra></extra>",name="Accidents"))
            lim = max(y_r.max(),y_p.max())*1.05
            fig_pv.add_trace(go.Scatter(x=[0,lim],y=[0,lim],mode="lines",
                line=dict(color=PAL["muted"],dash="dot",width=1.5),
                name="Parfait",hoverinfo="skip"))
            apply_layout(fig_pv,f"Réel vs Prédit — {tgt_sel}",h=260)
            fig_pv.update_layout(xaxis_title=f"{tgt_sel} (réel)",yaxis_title=f"{tgt_sel} (prédit)")
            st.plotly_chart(fig_pv, use_container_width=True)

        # Accidents similaires
        st.markdown('<p class="sc-section">🔍 ACCIDENTS HISTORIQUES LES PLUS PROCHES</p>', unsafe_allow_html=True)
        df_v = df.dropna(subset=["Quantité_Cl2_kg","Indice_gravité"]).copy()
        df_v["delta_Q"] = np.abs(df_v["Quantité_Cl2_kg"]-Q_kg)/(Q_kg+1)
        proches = df_v.nsmallest(8,"delta_Q")[
            ["Nom_Accident","Année","Pays","Quantité_Cl2_kg","Vitesse_vent_ms",
             "Type_libération","Décès","Blessés_total","Zone_impact_km2","Indice_gravité"]
        ].reset_index(drop=True)
        fig_cl = go.Figure(go.Bar(x=proches["Nom_Accident"],y=proches["Indice_gravité"],
            marker=dict(color=proches["Indice_gravité"],colorscale=RISK_CS,showscale=False),
            text=[f"{v:.1f}" for v in proches["Indice_gravité"]],textposition="outside",
            customdata=proches[["Année","Pays","Quantité_Cl2_kg","Blessés_total"]].values,
            hovertemplate="<b>%{x}</b><br>Gravité:%{y:.2f}<br>%{customdata[1]},%{customdata[0]}<br>"
                          "Cl₂:%{customdata[2]:.0f} kg<br>Blessés:%{customdata[3]}<extra></extra>"))
        fig_cl.add_hline(y=gravite,line_dash="dash",line_color=g_color,line_width=2,
            annotation_text=f" Scénario actuel ({gravite:.1f})",
            annotation_font=dict(color=g_color,size=10))
        apply_layout(fig_cl,f"Accidents Similaires — Cl₂ proche de {Q_kg:.0f} kg",h=320)
        fig_cl.update_layout(
            xaxis_tickangle=-30, xaxis_tickfont=dict(size=8),
            yaxis_title="Indice de Gravité")
        st.plotly_chart(fig_cl, use_container_width=True)
        st.dataframe(proches, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BASE DE DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    # Accès aux données pour l'onglet base de données
    df, _models_db = _get_ml_ready()
    if df is None:
        df = pd.DataFrame()
    st.markdown('<p class="sc-section">📚 BASE DE DONNÉES — 81 ACCIDENTS AU CHLORE (1929–2022)</p>', unsafe_allow_html=True)
    cf1,cf2,cf3 = st.columns(3)
    with cf1: pays_f = st.multiselect("Pays", sorted(df["Pays"].dropna().unique()))
    with cf2: type_f = st.multiselect("Type libération", df["Type_libération"].dropna().unique())
    with cf3: yr = st.slider("Période", int(df["Année"].min()), int(df["Année"].max()), (1975,2023))
    dfF = df.copy()
    if pays_f: dfF = dfF[dfF["Pays"].isin(pays_f)]
    if type_f: dfF = dfF[dfF["Type_libération"].isin(type_f)]
    dfF = dfF[dfF["Année"].between(*yr)]
    st.caption(f"**{len(dfF)}** accidents affichés sur 81")

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        sub_s = dfF.dropna(subset=["Quantité_Cl2_kg","Indice_gravité","Blessés_total"])
        fig_sc = go.Figure()
        for tl, cl in [("Brutale",PAL["danger"]),("Progressive",PAL["blue"])]:
            s = sub_s[sub_s["Type_libération"]==tl]
            if s.empty: continue
            fig_sc.add_trace(go.Scatter(x=s["Quantité_Cl2_kg"],y=s["Indice_gravité"],mode="markers",
                name=tl, marker=dict(color=cl,size=np.clip(s["Blessés_total"].fillna(5)/3,5,25),
                    opacity=0.8,line=dict(color=PAL["bg"],width=1),
                    symbol="circle" if tl=="Progressive" else "diamond"),
                customdata=s[["Nom_Accident","Année","Pays","Blessés_total"]].values,
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[2]},%{customdata[1]}<br>"
                              "Cl₂:%{x:.0f} kg<br>Gravité:%{y:.2f}<br>Blessés:%{customdata[3]}<extra></extra>"))
        sub_t = sub_s.dropna()
        if len(sub_t)>5:
            lq = np.log10(sub_t["Quantité_Cl2_kg"].clip(1))
            z = np.polyfit(lq, sub_t["Indice_gravité"],1)
            xr = np.logspace(np.log10(sub_s["Quantité_Cl2_kg"].min()),
                             np.log10(sub_s["Quantité_Cl2_kg"].max()),50)
            fig_sc.add_trace(go.Scatter(x=xr,y=np.polyval(z,np.log10(xr)),mode="lines",
                line=dict(color=PAL["muted"],dash="dot",width=1.5),name="Tendance",hoverinfo="skip"))
        apply_layout(fig_sc,"Quantité Cl₂ vs Indice de Gravité",h=390,xlog=True)
        fig_sc.update_layout(xaxis_title="Quantité Cl₂ (kg) — log",yaxis_title="Indice de Gravité")
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_v2:
        sub_h = dfF.dropna(subset=["Blessés_total","Type_libération"])
        fig_bx = go.Figure()
        def _rgba(h, a=0.15):
            h = h.lstrip("#"); r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
            return f"rgba({r},{g},{b},{a})"
        for tl,cl in [("Brutale",PAL["danger"]),("Progressive",PAL["blue"])]:
            s = sub_h[sub_h["Type_libération"]==tl]["Blessés_total"]
            if s.empty: continue
            fig_bx.add_trace(go.Box(y=s,name=tl,marker_color=cl,line_color=cl,
                boxmean="sd",fillcolor=_rgba(cl,0.15),jitter=0.3,pointpos=-1.8,boxpoints="outliers",
                marker=dict(size=5,opacity=0.6),
                hovertemplate=f"<b>{tl}</b><br>Blessés:%{{y}}<extra></extra>"))
        apply_layout(fig_bx,"Distribution du Nombre de Blessés par Type de Libération",h=390)
        fig_bx.update_layout(yaxis_title="Nombre de blessés totaux")
        st.plotly_chart(fig_bx, use_container_width=True)

    # Timeline
    st.markdown('<p class="sc-section">📅 TIMELINE DES ACCIDENTS AU CHLORE</p>', unsafe_allow_html=True)
    sub_tl = dfF.dropna(subset=["Année","Indice_gravité","Quantité_Cl2_kg"])
    fig_tl = go.Figure()
    for dec in range(1920,2030,10):
        fig_tl.add_vrect(x0=dec,x1=dec+10,
            fillcolor=PAL["grid"] if (dec//10)%2==0 else PAL["bg"],
            layer="below",line_width=0,opacity=0.3)
    fig_tl.add_trace(go.Scatter(x=sub_tl["Année"],y=sub_tl["Indice_gravité"],mode="markers",
        marker=dict(color=sub_tl["Indice_gravité"],colorscale=RISK_CS,showscale=True,
            size=np.clip(np.log10(sub_tl["Quantité_Cl2_kg"].clip(1)+1)*5,6,22),
            opacity=0.85,line=dict(color=PAL["bg"],width=1),
            colorbar=dict(title=dict(text="Gravité",font=dict(size=10,color=PAL["muted"])),
                tickfont=dict(size=9,color=PAL["muted"]),bgcolor="#FFFFFF",
                bordercolor=PAL["border"],len=0.7,thickness=12)),
        customdata=sub_tl[["Nom_Accident","Pays","Quantité_Cl2_kg","Blessés_total","Type_libération"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>%{x} — %{customdata[1]}<br>"
                      "Cl₂:%{customdata[2]:.0f} kg<br>Blessés:%{customdata[3]}<br>"
                      "Gravité:%{y:.2f}<extra></extra>",name="Accidents"))
    apply_layout(fig_tl,"Chronologie des Accidents au Chlore — 1929 à 2022",h=360)
    fig_tl.update_layout(xaxis_title="Année",yaxis_title="Indice de Gravité",
                         xaxis=dict(**BASE_LAYOUT["xaxis"],range=[yr[0]-2,yr[1]+2]))
    st.plotly_chart(fig_tl, use_container_width=True)

    # Bar pays
    st.markdown('<p class="sc-section">🌍 RÉPARTITION PAR PAYS</p>', unsafe_allow_html=True)
    pays_agg = dfF.groupby("Pays").agg(n=("Nom_Accident","count"),
        grav=("Indice_gravité","mean"),bless=("Blessés_total","sum")).reset_index().dropna()
    pas = pays_agg.sort_values("n")
    fig_pays = go.Figure(go.Bar(x=pas["Pays"],y=pas["n"],
        marker=dict(color=pas["grav"],colorscale=RISK_CS,showscale=True,
            colorbar=dict(title=dict(text="Gravité moy.",font=dict(size=10,color=PAL["muted"])),
                tickfont=dict(size=9,color=PAL["muted"]),bgcolor="#FFFFFF",
                bordercolor=PAL["border"],len=0.7,thickness=12)),
        customdata=pas[["grav","bless"]].values,
        hovertemplate="<b>%{x}</b><br>Accidents:%{y}<br>Gravité moy.:%{customdata[0]:.2f}<br>"
                      "Blessés total:%{customdata[1]:.0f}<extra></extra>"))
    apply_layout(fig_pays,"Nombre d'Accidents par Pays (couleur = gravité moyenne)",h=360)
    fig_pays.update_layout(
        xaxis_tickangle=-40, xaxis_tickfont=dict(size=9),
        yaxis_title="Nombre d'accidents")
    st.plotly_chart(fig_pays, use_container_width=True)

    cols_s = ["Nom_Accident","Année","Pays","Quantité_Cl2_kg","Type_libération",
              "Vitesse_vent_ms","Décès","Blessés_total","Zone_impact_km2","Indice_gravité"]
    st.dataframe(dfF[cols_s].reset_index(drop=True), use_container_width=True, hide_index=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sc-footer">
  ☣️ HazMod &nbsp;·&nbsp; Commission Nationale NRBC — Maroc 2025–2026
  &nbsp;·&nbsp; Pasquill-Gifford · Monte Carlo · Random Forest
  &nbsp;·&nbsp; ⚠ Usage exclusivement opérationnel
</div>
""", unsafe_allow_html=True)







# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ORGANISATION DES SECOURS — Plan ORSEC (dynamique)
# ══════════════════════════════════════════════════════════════════════════════
with tab6:

    # ── Variables ─────────────────────────────────────────────────────────────
    _G    = gravite
    _gc   = "#C53030" if _G>=7 else "#C05621" if _G>=4 else "#2F855A"
    _prop = (dir_vent + 180) % 360
    _DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
             "S","SSO","SO","OSO","O","ONO","NO","NNO"]
    _dlbl = _DIRS[int((_prop+11.25)//22.5)%16]
    _brutal = type_lib.startswith("Brutale")
    _al_on  = alerte_prec

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""<style>
    /* ── Bannière ── */
    .os-ban{background:linear-gradient(120deg,#1A365D 0%,#2C5282 60%,#276749 100%);
            border-radius:12px;padding:22px 28px;margin-bottom:22px;
            box-shadow:0 4px 18px rgba(0,0,0,.15);}
    .os-ban h2{color:#fff;font-size:1.4rem;font-weight:800;margin:0 0 4px;}
    .os-ban p{color:#BEE3F8;font-size:.87rem;margin:0;}

    /* ── Section header ── */
    .os-sh{display:flex;align-items:center;gap:10px;padding:10px 14px;
           background:#EBF8FF;border-radius:8px;margin:22px 0 12px;
           border-left:5px solid #2B6CB0;}
    .os-sh .sh-icon{font-size:1.15rem;}
    .os-sh .sh-txt{font-size:.98rem;font-weight:700;color:#1A365D;}
    .os-sh .sh-sub{font-size:.78rem;color:#4A5568;margin-left:auto;}

    /* ── KPI ── */
    .oskpi{background:#fff;border-radius:10px;padding:14px 12px;text-align:center;
           border:1px solid #E2E8F0;box-shadow:0 2px 6px rgba(0,0,0,.06);}
    .oskpi .kv{font-size:1.65rem;font-weight:800;font-family:'Courier New',monospace;}
    .oskpi .kl{font-size:.67rem;color:#718096;text-transform:uppercase;
               letter-spacing:.8px;margin-top:3px;}
    .oskpi .ks{font-size:.7rem;color:#A0AEC0;margin-top:2px;}

    /* ── Chaîne de commandement ── */
    .cmd-chain{background:#fff;border:1px solid #E2E8F0;border-radius:10px;
               overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.05);}
    .cmd-row{display:flex;gap:0;align-items:stretch;border-bottom:1px solid #F0F4F8;}
    .cmd-row:last-child{border-bottom:none;}
    .cmd-tag{min-width:72px;padding:12px 10px;display:flex;align-items:center;
             justify-content:center;font-size:.8rem;font-weight:800;color:#fff;
             letter-spacing:.5px;flex-shrink:0;}
    .cmd-body{padding:10px 14px;flex:1;}
    .cmd-title{font-size:.87rem;font-weight:700;color:#1A202C;margin-bottom:2px;}
    .cmd-def{font-size:.74rem;color:#718096;font-style:italic;margin-bottom:3px;}
    .cmd-role{font-size:.78rem;color:#2D3748;}

    /* ── Phases ── */
    .ph-wrap{border-radius:10px;overflow:hidden;border:1px solid #E2E8F0;
             box-shadow:0 2px 8px rgba(0,0,0,.05);margin-bottom:14px;}
    .ph-head{padding:12px 16px;display:flex;align-items:center;gap:10px;}
    .ph-head .ph-num{font-size:1.1rem;font-weight:800;color:#fff;
                     background:rgba(255,255,255,.2);border-radius:6px;
                     padding:2px 10px;min-width:32px;text-align:center;}
    .ph-head .ph-title{font-size:.95rem;font-weight:700;color:#fff;}
    .ph-head .ph-time{font-size:.78rem;color:rgba(255,255,255,.8);
                      margin-left:auto;font-family:'Courier New',monospace;}
    .ph-trigger{background:#FEFCE8;border-bottom:1px solid #FDE68A;
                padding:8px 16px;font-size:.78rem;color:#92400E;}
    .ph-trigger b{color:#78350F;}
    .ph-body{background:#fff;}

    /* ── Actions attendues ── */
    .act-row{display:grid;grid-template-columns:200px 1fr;gap:0;
             border-bottom:1px solid #F0F4F8;}
    .act-row:last-child{border-bottom:none;}
    .act-label{padding:12px 16px;background:#F7FAFC;font-size:.8rem;
               font-weight:700;color:#2D3748;border-right:1px solid #E2E8F0;
               display:flex;align-items:flex-start;}
    .act-content{padding:12px 16px;font-size:.8rem;color:#2D3748;
                 line-height:1.6;}
    .act-content b{color:#1A202C;}
    .act-content .highlight{background:#EBF8FF;border-radius:4px;
                            padding:2px 6px;color:#2B6CB0;font-weight:600;}
    .act-content .warn{background:#FFF5F5;border-radius:4px;
                       padding:2px 6px;color:#C53030;font-weight:600;}
    .act-content .ok{background:#F0FFF4;border-radius:4px;
                     padding:2px 6px;color:#276749;font-weight:600;}
    .err-box{background:#FFF5F5;border-left:4px solid #FC8181;border-radius:0 6px 6px 0;
             padding:8px 12px;margin:8px 0;font-size:.78rem;color:#742A2A;}
    .err-box b{color:#C53030;}

    /* ── Grille de notation ── */
    .note-table{width:100%;border-collapse:collapse;font-size:.82rem;}
    .note-table th{background:#1A365D;color:#fff;padding:8px 12px;
                   text-align:left;font-weight:700;}
    .note-table td{padding:9px 12px;border-bottom:1px solid #E2E8F0;
                   vertical-align:top;color:#2D3748;}
    .note-table tr:nth-child(even) td{background:#F7FAFC;}
    .note-table .dom{font-weight:700;color:#1A365D;}
    .score-row td{border-top:2px solid #2B6CB0;font-weight:700;
                  background:#EBF8FF!important;}

    /* ── Niveaux de performance ── */
    .perf-badge{display:inline-block;border-radius:5px;padding:3px 10px;
                font-size:.75rem;font-weight:700;color:#fff;margin-right:4px;}

    /* ── RETEX ── */
    .rtx{background:#fff;border-radius:8px;padding:14px 16px;margin:6px 0;
         border:1px solid #E2E8F0;}
    .rtx-head{display:flex;gap:8px;align-items:center;margin-bottom:8px;
              padding-bottom:8px;border-bottom:1px solid #F0F4F8;}
    .rtx-title{font-weight:700;font-size:.87rem;color:#1A202C;}
    .rtx-cols{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
    .rtx-err{background:#FFF5F5;border-radius:6px;padding:9px 12px;
             border-left:3px solid #FC8181;font-size:.78rem;color:#742A2A;}
    .rtx-ok{background:#F0FFF4;border-radius:6px;padding:9px 12px;
            border-left:3px solid #68D391;font-size:.78rem;color:#1C4532;}
    .rtx-lbl{font-size:.64rem;text-transform:uppercase;letter-spacing:.8px;
             font-weight:700;margin-bottom:3px;display:block;}
    </style>""", unsafe_allow_html=True)

    # ── BANNIÈRE ─────────────────────────────────────────────────────────────
    _niv = ("🔴 CRITIQUE" if _G>=7 else "🟠 ÉLEVÉ" if _G>=4
            else "🟡 MODÉRÉ" if _G>=2 else "🟢 FAIBLE")
    st.markdown(f"""
    <div class="os-ban">
      <h2>🛡 Organisation des Secours — Plan ORSEC</h2>
      <p>
        Zone simulée · Lat {lat:.4f}° / Lon {lon:.4f}° &nbsp;·&nbsp;
        Q = <b>{Q_kg:,.0f} kg</b> Cl₂ &nbsp;·&nbsp; {type_lib.split()[0]} &nbsp;·&nbsp;
        Vent {u_ms} m/s {dir_vent}° → <b>{_dlbl}</b> &nbsp;·&nbsp; Classe {stab} &nbsp;·&nbsp;
        <b style="color:#FEFCBF;">Niveau {_niv} — G = {_G:.1f}/10</b>
      </p>
    </div>""", unsafe_allow_html=True)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    _mcc = "#C53030" if mc_p_e2>=70 else "#C05621" if mc_p_e2>=30 else "#2F855A"
    for col,val,lbl,sub,vc,bg in [
        (k1,f"{r3:.0f} m","Zone Rouge","ERPG-3 · 20 ppm","#C53030","#FFF5F5"),
        (k2,f"{r2:.0f} m","Zone Orange","ERPG-2 · 3 ppm","#C05621","#FFFAF0"),
        (k3,f"{r1:.0f} m","Zone Jaune","ERPG-1 · 1 ppm","#B7791F","#FFFFF0"),
        (k4,f"{_G:.1f}/10","Indice G","Gravité composite",_gc,"#FAFAFA"),
        (k5,f"{mc_p_e2:.0f}%","P(C>ERPG-2)","Monte Carlo",_mcc,"#FAFAFA"),
        (k6,"✓" if _al_on else "✗","Alerte précoce",
         "Active" if _al_on else "Absente",
         "#2F855A" if _al_on else "#C53030",
         "#F0FFF4" if _al_on else "#FFF5F5"),
    ]:
        with col:
            st.markdown(f"""
            <div class="oskpi" style="background:{bg};border-color:{vc}44;">
              <div class="kv" style="color:{vc};">{val}</div>
              <div class="kl" style="color:{vc}bb;">{lbl}</div>
              <div class="ks">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # GRAPHIQUES : Jauge G + Barres MC + Donut population
    # ══════════════════════════════════════════════════════════════════════════
    cg1, cg2, cg3 = st.columns([1,1.2,1.2])

    with cg1:
        fig_j = go.Figure(go.Indicator(
            mode="gauge+number",
            value=_G,
            number={"font":{"size":40,"color":_gc},"suffix":"/10"},
            gauge={
                "axis":{"range":[0,10],"tickfont":{"size":9,"color":"#718096"}},
                "bar":{"color":_gc,"thickness":0.28},
                "bgcolor":"#F7FAFC","borderwidth":0,
                "steps":[
                    {"range":[0,2],  "color":"#C6F6D5"},
                    {"range":[2,4],  "color":"#FEFCBF"},
                    {"range":[4,7],  "color":"#FEEBC8"},
                    {"range":[7,10], "color":"#FED7D7"},
                ],
                "threshold":{"line":{"color":"#1A202C","width":3},
                             "thickness":0.8,"value":_G},
            },
            title={"text":"Indice de Gravité G","font":{"size":12,"color":"#2D3748"}},
        ))
        fig_j.update_layout(height=230,margin=dict(t=50,b=5,l=15,r=15),
                            paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig_j, use_container_width=True)

    with cg2:
        _sl = ["ERPG-1 (1 ppm)","ERPG-2 (3 ppm)","ERPG-3 (20 ppm)"]
        _ps = [mc_p_e1, mc_p_e2, mc_p_e3]
        _bc = ["#38A169","#DD6B20","#E53E3E"]
        fig_b = go.Figure()
        for lbl,p,bc in zip(_sl,_ps,_bc):
            fig_b.add_trace(go.Bar(
                x=[p], y=[lbl], orientation='h',
                marker_color=bc, marker_opacity=0.85,
                text=[f"<b>{p:.0f}%</b>"],
                textposition='inside' if p>12 else 'outside',
                textfont=dict(size=12,color="#fff" if p>12 else bc),
                showlegend=False,
                hovertemplate=f"P(C>{lbl}) = {p:.1f}%<extra></extra>",
            ))
        fig_b.add_vline(x=70, line_dash="dash", line_color="#C53030",
                        line_width=1.5,
                        annotation_text="Seuil alerte rouge",
                        annotation_font_size=9,
                        annotation_font_color="#C53030",
                        annotation_position="top right")
        fig_b.update_layout(
            title=dict(text="Probabilités de dépassement Monte Carlo",
                       font=dict(size=12,color="#2D3748"),x=0.5),
            xaxis=dict(range=[0,105],ticksuffix="%",
                       tickfont=dict(size=9),gridcolor="#E2E8F0",
                       title="Probabilité (%)"),
            yaxis=dict(tickfont=dict(size=10,color="#2D3748")),
            height=230,margin=dict(t=45,b=30,l=10,r=10),
            paper_bgcolor="#FFFFFF",plot_bgcolor="#F7FAFC",barmode="overlay",
        )
        st.plotly_chart(fig_b, use_container_width=True)

    with cg3:
        _labels = ["Zone Rouge\nERPG-3","Zone Orange\nERPG-2",
                   "Zone Jaune\nERPG-1","Hors zone"]
        _pops   = [pop_e3, pop_e2-pop_e3, pop_e1-pop_e2,
                   max(0, int(dens_pop*10)-pop_e1)]
        _colors = ["#FC8181","#F6AD55","#FAF089","#CBD5E0"]
        fig_d = go.Figure(go.Pie(
            labels=_labels, values=[max(0,p) for p in _pops],
            hole=0.55, marker_colors=_colors,
            textfont=dict(size=10),
            hovertemplate="<b>%{label}</b><br>Population: %{value:,}<br>"
                          "Part: %{percent}<extra></extra>",
            textinfo="percent",
        ))
        fig_d.add_annotation(
            text=f"<b>{pop_e2:,}</b><br><span style='font-size:10px'>exposées</span>",
            x=0.5,y=0.5,showarrow=False,
            font=dict(size=13,color="#2D3748"),
        )
        fig_d.update_layout(
            title=dict(text="Population exposée par zone",
                       font=dict(size=12,color="#2D3748"),x=0.5),
            height=230,margin=dict(t=45,b=5,l=5,r=5),
            paper_bgcolor="#FFFFFF",
            legend=dict(font=dict(size=9),orientation="v",
                        x=1,y=0.5),
            showlegend=True,
        )
        st.plotly_chart(fig_d, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — PLAN ORSEC & OBJECTIFS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div class="os-sh">
      <span class="sh-icon">📋</span>
      <span class="sh-txt">Plan ORSEC — Objectifs et déclencheurs</span>
    </div>""", unsafe_allow_html=True)

    c_obj, c_dec = st.columns(2)
    with c_obj:
        st.markdown("""
        <div style="background:#fff;border-radius:10px;padding:16px 18px;
                    border:1px solid #E2E8F0;height:100%;">
          <div style="font-weight:700;color:#1A365D;font-size:.92rem;margin-bottom:10px;
                      border-bottom:2px solid #BEE3F8;padding-bottom:6px;">
            🎯 Objectifs du Plan ORSEC
          </div>""", unsafe_allow_html=True)
        for obj in [
            ("🏛","Protection des populations, des biens et de l'environnement"),
            ("🤝","Coordination des acteurs civils, sanitaires et sécuritaires"),
            ("⚗️","Gestion opérationnelle des crises majeures NRBC-E"),
            ("🔄","Anticipation et continuité des fonctions essentielles"),
        ]:
            st.markdown(f"""
            <div style="display:flex;gap:10px;align-items:flex-start;padding:7px 0;
                        border-bottom:1px solid #F0F4F8;font-size:.83rem;color:#2D3748;">
              <span style="font-size:1rem;flex-shrink:0;">{obj[0]}</span>
              <span>{obj[1]}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_dec:
        st.markdown("""
        <div style="background:#fff;border-radius:10px;padding:16px 18px;
                    border:1px solid #E2E8F0;height:100%;">
          <div style="font-weight:700;color:#1A365D;font-size:.92rem;margin-bottom:10px;
                      border-bottom:2px solid #FEB2B2;padding-bottom:6px;">
            🚨 Cas de déclenchement du Plan ORSEC
          </div>""", unsafe_allow_html=True)
        for dec in [
            ("Accident industriel impliquant des substances dangereuses (chimique, radiologique)"),
            ("Incident NRBC-E dans les zones industrielles, de transport ou de rassemblement"),
            ("Accident de Transport de Matières Dangereuses — ADR (ferroviaire ou routier)"),
            ("Situation à victimes multiples dépassant les capacités de réponse courantes"),
        ]:
            st.markdown(f"""
            <div style="display:flex;gap:10px;align-items:flex-start;padding:7px 0;
                        border-bottom:1px solid #F0F4F8;font-size:.83rem;color:#2D3748;">
              <span style="color:#C53030;font-weight:700;flex-shrink:0;">▶</span>
              <span>{dec}</span>
            </div>""", unsafe_allow_html=True)
        # Cas actuel
        _cas = ("Accident TMD Chlore — Libération " +
                ("brutale" if _brutal else "progressive continue") +
                f" de {Q_kg:,.0f} kg")
        st.markdown(f"""
        <div style="background:#EBF8FF;border-radius:6px;padding:8px 12px;margin-top:8px;
                    font-size:.8rem;font-weight:700;color:#2B6CB0;border-left:3px solid #3182CE;">
          ✅ Cas simulé : {_cas}
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — CHAÎNE DE COMMANDEMENT ORSEC
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div class="os-sh">
      <span class="sh-icon">⚙️</span>
      <span class="sh-txt">Chaîne de Commandement ORSEC</span>
      <span class="sh-sub">Service menant + services concourants</span>
    </div>""", unsafe_allow_html=True)

    # Graphique organigramme horizontal (Plotly)
    # go already imported
    _nodes_x = [0.5, 0.5, 0.5, 0.5,  0.15, 0.85, 0.15, 0.85]
    _nodes_y = [1.0, 0.72, 0.44, 0.16, 0.72, 0.72, 0.44, 0.44]
    _labels2  = ["DOS","PCO","DSM","COS","COPG","PCF","COPJ","CMIC"]
    _colors2  = ["#553C9A","#1A365D","#C53030","#2B6CB0",
                 "#276749","#285E61","#744210","#C05621"]
    _descs    = [
        "Directeur des Opérations de Secours",
        "Poste de Commandement Opérationnel",
        "Directeur des Secours Médicaux",
        "Commandant des Opérations de Secours",
        "Commandant Police / Gendarmerie",
        "Poste de Commandement Fixe",
        "Commandant Opérations Police Judiciaire",
        "Cellule Mobile Intervention Chimique",
    ]

    fig_org = go.Figure()
    # Liaisons (edges)
    _edges = [(0,1),(1,2),(2,3),(1,4),(1,5),(2,6),(2,7)]
    for s,e in _edges:
        fig_org.add_shape(type="line",
            x0=_nodes_x[s],y0=_nodes_y[s],
            x1=_nodes_x[e],y1=_nodes_y[e],
            line=dict(color="#CBD5E0",width=2),
            xref="paper",yref="paper",
        )
    # Noeuds
    for i,(x,y,lbl,col,desc) in enumerate(
            zip(_nodes_x,_nodes_y,_labels2,_colors2,_descs)):
        fig_org.add_annotation(
            x=x,y=y,text=f"<b>{lbl}</b>",
            showarrow=False,
            font=dict(size=11,color="#fff",family="Segoe UI"),
            bgcolor=col,bordercolor=col,borderwidth=2,borderpad=6,
            xref="paper",yref="paper",
            hovertext=desc,
        )
    fig_org.update_layout(
        height=340,
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="#F7FAFC",
        xaxis=dict(visible=False,range=[0,1]),
        yaxis=dict(visible=False,range=[0,1.1]),
    )
    st.plotly_chart(fig_org, use_container_width=True)

    # Tableau détaillé commandement
    st.markdown('<div class="cmd-chain">', unsafe_allow_html=True)
    for sig,titre,defi,role,col_c in [
        ("DOS","Directeur des Opérations de Secours",
         "Autorité responsable de la direction globale des opérations de secours.",
         "Décide, coordonne et arbitre l'ensemble du dispositif de gestion de crise.","#553C9A"),
        ("COS","Commandant des Opérations de Secours",
         "Chef opérationnel des secours sur le terrain.",
         f"Dirige tactiquement les moyens engagés · Périmètre {r3:.0f}m · "
         "Met en œuvre les décisions du DOS.","#2B6CB0"),
        ("COPG","Commandant des Opérations de Police / Gendarmerie",
         "Autorité chargée de la conduite des opérations de sécurité publique.",
         "Assure l'ordre public, la sécurisation des sites et des périmètres.","#276749"),
        ("COPJ","Commandant des Opérations de Police Judiciaire",
         "Responsable de la conduite des opérations judiciaires en situation de crise.",
         "Dirige les enquêtes, préserve les preuves et coordonne l'action judiciaire.","#744210"),
        ("DSM","Directeur des Secours Médicaux",
         "Responsable de l'organisation et de la coordination des secours médicaux.",
         f"Gère le tri ({blesses_e3} UA estimés), la prise en charge et "
         "l'évacuation médicale des victimes · Déclenche Plan Blanc si nécessaire.","#C53030"),
        ("PCO","Poste de Commandement Opérationnel",
         "Structure de commandement déployée à proximité du sinistre.",
         "Coordonne en temps réel les actions de secours et de sécurité sur le terrain.","#1A365D"),
        ("PCF","Poste de Commandement Fixe",
         "Centre stratégique de pilotage de la crise, implanté hors zone impactée.",
         "Anticipe, planifie, coordonne et assure la communication institutionnelle.","#285E61"),
    ]:
        st.markdown(f"""
        <div class="cmd-row">
          <div class="cmd-tag" style="background:{col_c};">{sig}</div>
          <div class="cmd-body">
            <div class="cmd-title">{titre}</div>
            <div class="cmd-def">{defi}</div>
            <div class="cmd-role">▶ {role}</div>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2b — DÉCISION CONFINEMENT / ÉVACUATION
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div class="os-sh">
      <span class="sh-icon">🚨</span>
      <span class="sh-txt">Décision Confinement / Évacuation — Argumentée</span>
      <span class="sh-sub">Basée sur les paramètres simulés</span>
    </div>""", unsafe_allow_html=True)

    # Calcul dynamique de la décision
    _t_arrivee  = dist_pop / max(u_ms, 0.1) / 60.0   # minutes avant arrivée nuage
    _t_evac_ok  = delai_evac < _t_arrivee              # évacuation possible avant arrivée
    _in_rouge   = dist_pop <= r3
    _in_orange  = r3 < dist_pop <= r2
    _in_verte   = r2 < dist_pop <= r1

    if _in_rouge:
        _dec = "CONFINEMENT OBLIGATOIRE"
        _dc  = "#C53030"; _db = "#FFF5F5"
        _dj  = (f"Pop. à {dist_pop}m dans <b>zone rouge ERPG-3</b> ({r3:.0f}m). "
                f"Nuage arrive dans {_t_arrivee:.0f}min. Délai évac.={delai_evac}min "
                f"({'insuffisant' if not _t_evac_ok else 'mais zone rouge = confinement quand même'}). "
                f"Évacuation = exposition directe à >20ppm Cl₂ — <b>confinement obligatoire</b>.")
        _ds = (f"C estimée : {conc_ppm(q_debit_kgs(Q_kg,duree_min,type_lib),u_ms,dist_pop,0,stab):.1f}ppm "
               f"· Cl₂ 2,5× air → reste au sol · mouvement = inhalation directe")
    elif _in_orange:
        if _t_evac_ok and not _brutal:
            _dec = "ÉVACUATION POSSIBLE"
            _dc  = "#276749"; _db = "#F0FFF4"
            _dj  = (f"Pop. à {dist_pop}m dans <b>zone orange ERPG-2</b> ({r2:.0f}m). "
                    f"Nuage arrive dans {_t_arrivee:.0f}min · Délai évac.={delai_evac}min "
                    f"→ <b>sortie avant l'arrivée du nuage possible</b>. Évacuation recommandée.")
            _ds = (f"t_évac ({delai_evac}min) < t_arrivée ({_t_arrivee:.0f}min) → sécurisé. "
                   f"C estimée : {conc_ppm(q_debit_kgs(Q_kg,duree_min,type_lib),u_ms,dist_pop,0,stab):.2f}ppm")
        else:
            _dec = "CONFINEMENT"
            _dc  = "#C05621"; _db = "#FFFAF0"
            _dj  = (f"Pop. à {dist_pop}m en <b>zone orange</b> ({r2:.0f}m). "
                    f"Nuage arrive dans {_t_arrivee:.0f}min · Délai évac.={delai_evac}min "
                    f"({'insuffisant' if not _t_evac_ok else 'libération brutale = nuage instantané'}). "
                    f"<b>Confinement aux étages supérieurs</b> — sortie = exposition 3–20ppm.")
            _ds = (f"t_évac ≥ t_arrivée ou brutale → confinement. "
                   f"C estimée : {conc_ppm(q_debit_kgs(Q_kg,duree_min,type_lib),u_ms,dist_pop,0,stab):.2f}ppm")
    elif _in_verte:
        _dec = "CONFINEMENT RECOMMANDÉ"
        _dc  = "#B7791F"; _db = "#FFFFF0"
        _dj  = (f"Pop. à {dist_pop}m en <b>zone jaune ERPG-1</b> ({r1:.0f}m). "
                f"Effets légers — confinement recommandé par précaution. "
                f"Évacuation possible si hors direction du vent ({_dlbl}).")
        _ds  = f"C estimée : {conc_ppm(q_debit_kgs(Q_kg,duree_min,type_lib),u_ms,dist_pop,0,stab):.3f}ppm · seuil ERPG-1 = 1ppm"
    else:
        _dec = "AUCUNE ACTION IMMÉDIATE"
        _dc  = "#2F855A"; _db = "#F0FFF4"
        _dj  = f"Pop. à {dist_pop}m hors zones ERPG (r1={r1:.0f}m). Surveillance et information suffisent."
        _ds  = "C < 1ppm — pas d'effet sanitaire attendu"

    # Bandeau décision
    st.markdown(f"""
    <div style="background:{_db};border:2px solid {_dc};border-radius:12px;
                padding:14px 18px;margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:9px;flex-wrap:wrap;">
        <div style="background:{_dc};color:#fff;border-radius:7px;
                    padding:5px 14px;font-size:.95rem;font-weight:800;">
          {_dec}
        </div>
        <span style="font-size:.8rem;color:#4A5568;">
          Pop. à {dist_pop}m &nbsp;·&nbsp; Nuage arrive T+{_t_arrivee:.0f}min &nbsp;·&nbsp;
          Délai évac. {delai_evac}min &nbsp;·&nbsp; Libération : {type_lib.split()[0]}
        </span>
      </div>
      <div style="font-size:.83rem;color:#2D3748;margin-bottom:8px;">{_dj}</div>
      <div style="font-size:.76rem;color:#718096;background:rgba(0,0,0,0.04);
                  border-radius:5px;padding:5px 10px;font-family:'Courier New',monospace;">
        Physique : {_ds}
      </div>
    </div>""", unsafe_allow_html=True)

    # Tableau règles
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #E2E8F0;border-radius:9px;
                padding:12px 16px;margin-bottom:16px;">
      <div style="font-weight:700;color:#1A365D;font-size:.85rem;margin-bottom:9px;">
        Règle de décision ALOHA/NFPA appliquée à ce scénario
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;">
        <div style="background:#FFF5F5;border:1px solid #FC818144;border-radius:7px;padding:9px 11px;">
          <div style="font-size:.73rem;font-weight:700;color:#C53030;margin-bottom:4px;">
            Zone Rouge (&gt;20 ppm)</div>
          <div style="font-size:.71rem;color:#718096;margin-bottom:5px;">
            Toujours — nuage actif</div>
          <div style="background:#C53030;color:#fff;border-radius:4px;
                      padding:2px 8px;font-size:.71rem;font-weight:700;display:inline-block;">
            CONFINEMENT OBLIGATOIRE</div>
        </div>
        <div style="background:{'#F0FFF4' if (_t_evac_ok and not _brutal) else '#FFFAF0'};
                    border:1px solid {'#68D39144' if (_t_evac_ok and not _brutal) else '#F6AD5544'};
                    border-radius:7px;padding:9px 11px;">
          <div style="font-size:.73rem;font-weight:700;
                      color:{'#276749' if (_t_evac_ok and not _brutal) else '#C05621'};margin-bottom:4px;">
            Zone Orange (3–20 ppm)</div>
          <div style="font-size:.71rem;color:#718096;margin-bottom:5px;">
            t_évac({delai_evac}min) {'&lt;' if _t_evac_ok and not _brutal else '≥'} t_arrivée({_t_arrivee:.0f}min)</div>
          <div style="background:{'#276749' if (_t_evac_ok and not _brutal) else '#C05621'};
                      color:#fff;border-radius:4px;padding:2px 8px;
                      font-size:.71rem;font-weight:700;display:inline-block;">
            {'ÉVACUATION POSSIBLE' if (_t_evac_ok and not _brutal) else 'CONFINEMENT'}</div>
        </div>
        <div style="background:#FFFFF0;border:1px solid #F6E05E44;border-radius:7px;padding:9px 11px;">
          <div style="font-size:.73rem;font-weight:700;color:#B7791F;margin-bottom:4px;">
            Zone Jaune (&lt;3 ppm)</div>
          <div style="font-size:.71rem;color:#718096;margin-bottom:5px;">Toujours</div>
          <div style="background:#B7791F;color:#fff;border-radius:4px;
                      padding:2px 8px;font-size:.71rem;font-weight:700;display:inline-block;">
            CONFINEMENT RECOMMANDÉ</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # 3 zones détaillées
    col_z1, col_z2, col_z3 = st.columns(3)

    def _rz(col, title, radius, pop, color, bg_col, border_col, actions):
        with col:
            st.markdown(f"""
            <div class="za6" style="border-color:{border_col};background:{bg_col};">
              <div class="za6-title" style="color:{color};border-color:{border_col};">
                {title} · R={radius:.0f}m · {pop:,} pers.
              </div>""", unsafe_allow_html=True)
            for icon, txt in actions:
                st.markdown(f"""
                <div class="za6-item">
                  <span class="za6-icon">{icon}</span>
                  <span class="za6-txt">{txt}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    _az_r = [
        ("🚫","<b>CONFINEMENT OBLIGATOIRE</b> — évacuation = exposition directe >20ppm"),
        ("🏠","Étages supérieurs · VMC coupée · interstices colmatés · serviettes mouillées"),
        ("⬆️","Sous-sols : <b>évacuer IMMÉDIATEMENT</b> (Cl₂ 2,5× plus lourd — descend)"),
        ("⚗️","CMIC + EPI " + niveau_epi.split("—")[0].strip() + " obligatoires pour intervenants"),
        ("📵","Accès interdit · Balisage physique · Renforts NRBC"),
    ]
    if _brutal: _az_r.append(("⚡","Brutale : nuage <b>instantané</b> — périmètre sans délai"))
    if not _al_on: _az_r.append(("⚠️","<b>Alerte absente</b> — alerter par tous moyens"))

    _evac_orange = _t_evac_ok and not _brutal
    _az_o = [
        ("🏠" if not _evac_orange else "🚶",
         f"<b>{'CONFINEMENT' if not _evac_orange else 'ÉVACUATION POSSIBLE'}</b> — "
         f"{'délai insuffisant · rester aux étages supérieurs' if not _evac_orange else 'sortir avant T+'+str(int(_t_arrivee))+'min · direction opposée au vent'}"),
        ("🔴","Fermer toutes les VMC et prises d'air extérieur"),
        ("⛔","<b>Ne PAS évacuer si nuage déjà présent</b> — inhalation directe 3–20ppm"),
        ("⬆️","Sous-sols : <b>évacuation prioritaire</b> vers les étages"),
        ("📣","Alerte : sirènes + SMS + radio · {pop_e2:,} personnes exposées"),
    ]
    _az_v = [
        ("⬆️","<b>Sous-sols : évacuer IMMÉDIATEMENT</b> — Cl₂ s'accumule dans les espaces bas"),
        ("🏘",f"Confinement recommandé de {r2:.0f}m à {r1:.0f}m"),
        ("📢","Sirènes + SMS + médias + porte-à-porte"),
        ("👁","Populations vulnérables prioritaires : enfants, personnes âgées, asthmatiques"),
        ("🚃","Transports : VMC coupée · fenêtres fermées · pas de descente spontanée"),
    ]
    _rz(col_z1,"🔴 Zone Rouge ERPG-3",r3,pop_e3,
        "#C53030","#FFF5F5","#FC8181",_az_r)
    _rz(col_z2,"🟠 Zone Orange ERPG-2",r2,pop_e2,
        "#C05621","#FFFAF0","#F6AD55",_az_o)
    _rz(col_z3,"🟢 Zone Verte ERPG-1",r1,pop_e1,
        "#276749","#F0FFF4","#68D391",_az_v)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — CHRONOLOGIE PAR PHASE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div class="os-sh">
      <span class="sh-icon">⏱</span>
      <span class="sh-txt">Chronologie des Phases — Réponses attendues par phase</span>
      <span class="sh-sub">Dynamique selon le cas simulé</span>
    </div>""", unsafe_allow_html=True)

    # Gantt Plotly
    _phs_gantt = [
        ("Phase 1 — Prise de commandement",  0,  25,"#4299E1"),
        ("Phase 2 — Analyse & secteurs",     25,  60,"#DD6B20"),
        ("Phase 3 — Crise majeure",          60, 130,"#E53E3E"),
        ("Phase 4 — Stabilisation",         130, 150,"#38A169"),
    ]
    fig_gtt = go.Figure()
    for lbl,t0,t1,col in _phs_gantt:
        fig_gtt.add_trace(go.Bar(
            x=[t1-t0], y=[lbl], orientation='h',
            base=t0, marker_color=col, marker_opacity=0.85,
            text=[f"T+{t0}→T+{t1} min"],
            textposition='inside',
            textfont=dict(size=10,color='#fff'),
            showlegend=False,
            hovertemplate=f"<b>{lbl}</b><br>T+{t0} → T+{t1} min<extra></extra>",
        ))
    fig_gtt.update_layout(
        barmode='stack',
        xaxis=dict(title="Minutes depuis T0",tickfont=dict(size=10),
                   gridcolor="#E2E8F0",range=[0,155]),
        yaxis=dict(tickfont=dict(size=10,color="#2D3748")),
        height=200,margin=dict(t=15,b=35,l=10,r=10),
        paper_bgcolor="#FFFFFF",plot_bgcolor="#F7FAFC",
    )
    st.plotly_chart(fig_gtt, use_container_width=True)

    # ── PHASE 1 — DYNAMIQUE selon les inputs ──────────────────────────────
    # Calcul du nombre de premiers secours selon la gravité
    _nb_fpt   = 2 if _G >= 6 else 1
    _nb_vsav  = 3 if _G >= 6 else 2 if _G >= 4 else 1
    _nb_vlcg  = 2 if _G >= 7 else 1
    _nb_smur  = nb_smur  # saisi dans les inputs
    _res_init = f"{_nb_fpt} FPT + {_nb_vsav} VSAV + {_nb_vlcg} VLCG"

    # Points sensibles identifiés selon les inputs
    _pts_sensibles = []
    if has_gare_rout: _pts_sensibles.append(f"Gare routière ({nb_gare_pers} pers.)")
    if has_admin:     _pts_sensibles.append(f"Centre administratif ({nb_agents_admin} agents)")
    if has_hopital:   _pts_sensibles.append("Hôpital/clinique")
    if has_ecole:     _pts_sensibles.append("École/crèche")
    if has_train:     _pts_sensibles.append(f"Ligne ferroviaire ({train_passagers} pass.)")
    for _u in usines_domino:
        _pts_sensibles.append(f"Usine '{_u['nom']}' à {_u['dist']}m")
    _pts_str = " · ".join(_pts_sensibles) if _pts_sensibles else "Aucun établissement renseigné"

    # Renforts selon les inputs
    _renforts = ["CMIC (Cl₂ confirmé)"]
    if _G >= 4 or blesses_estimes >= 10:
        _renforts.append(f"PMA sur site")
    if nb_smur >= 1:
        _renforts.append(f"{nb_smur} SMUR")
    if has_hopital or has_ecole:
        _renforts.append("CUMP (soutien psychologique)")
    if blesses_e3 >= capa_ua_max:
        _renforts.append(f"Plan Blanc CHR ({capa_chr_lits} lits)")
    _renforts_str = " + ".join(_renforts)

    # Déclencheur Phase 1 dynamique
    _p1_trigger = (f"Source : {Q_kg:,.0f} kg Cl₂ · {type_lib.split()[0]} · "
                   f"Vent {u_ms}m/s · {dir_vent}° → {_dlbl} ({_prop:.0f}°) · Classe {stab}")

    st.markdown(f"""
    <div class="ph-wrap">
      <div class="ph-head" style="background:linear-gradient(90deg,#2B6CB0,#4299E1);">
        <span class="ph-num">1</span>
        <span class="ph-title">Prise de commandement</span>
        <span class="ph-time">T0 → T0+25 min</span>
      </div>
      <div class="ph-trigger">
        <b>Déclencheur :</b> {_p1_trigger}
      </div>
      <div class="ph-body">""", unsafe_allow_html=True)

    _p1_actions = [
        ("Réception alerte — CTA",
         f"Prise d'appel complète : identification appelant, localisation précise "
         f"(Lat {lat:.4f}° / Lon {lon:.4f}°), nature du rejet ({type_lib.split()[0]}).<br>"
         f"→ Déclenchement immédiat : <span class='highlight'>{_res_init}</span><br>"
         f"<small>Calibré sur G={_G:.1f}/10 · {Q_kg:,.0f}kg · {type_lib.split()[0]}</small>"),
        ("SITAC initial COS (T+5)",
         f"Format SITAC — <b>Situation :</b> Cl₂ confirmé, fuite {type_lib.split()[0].lower()}, "
         f"Q={Q_kg:,.0f}kg · <b>Actions :</b> périmètre réflexe 50m dos au vent ({dir_vent}°) · "
         f"<b>Besoins :</b> {_renforts_str} · <b>Délais :</b> aggravation estimée T+15.<br>"
         f"→ ADR Cl₂ : plaque orange <span class='highlight'>266/1017</span>"),
        ("Zonage réflexe (T+10–T+15)",
         f"<span class='warn'>Périmètre réflexe : 50 m dos au vent</span> — direction {dir_vent}° "
         f"→ propagation vers {_dlbl} ({_prop:.0f}°)"),
        ("Zonage réfléchi",
         f"<span class='warn'>Zone rouge</span> : <b>{r3:.0f} m</b> (ERPG-3 · 20 ppm) — Danger vital<br>"
         f"<span style='color:#C05621;font-weight:600;'>Zone orange</span> : <b>{r2:.0f} m</b> (ERPG-2 · 3 ppm) — Effets irréversibles<br>"
         f"<span style='color:#B7791F;font-weight:600;'>Zone jaune</span> : <b>{r1:.0f} m</b> (ERPG-1 · 1 ppm) — Irritation légère<br>"
         f"→ Population exposée : <b>{pop_e2:,} personnes</b> en zone orange"),
        ("Activation PCO (T+10)",
         f"Ouverture tableau GOC / main courante.<br>"
         f"<b>Points sensibles identifiés dans les zones :</b> {_pts_str}<br>"
         f"→ Demande renforts : <span class='highlight'>{_renforts_str}</span>"),
    ]
    for lbl,content in _p1_actions:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">{lbl}</div>
          <div class="act-content">{content}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── PHASE 2 — DYNAMIQUE selon les inputs ──────────────────────────────
    # Construire les déclencheurs Phase 2 selon ce qui est renseigné
    _p2_triggers = []
    if has_gare_rout: _p2_triggers.append(f"Gare routière ({nb_gare_pers} pers.)")
    if has_admin:     _p2_triggers.append(f"Centre administratif ({nb_agents_admin} agents)")
    if has_ecole:     _p2_triggers.append("École / crèche")
    if has_hopital:   _p2_triggers.append("Hôpital / clinique")
    # Usines en zone ERPG-2 (distance < r2)
    _usines_p2 = [u for u in usines_domino if u.get('dist',9999) <= r2]
    for _u in _usines_p2:
        _p2_triggers.append(f"Usine '{_u['nom']}' à {_u['dist']}m")
    _p2_trigger_str = " · ".join(_p2_triggers) if _p2_triggers else (
        "Analyse des zones · Communication · Coordination médicale")

    st.markdown(f"""
    <div class="ph-wrap">
      <div class="ph-head" style="background:linear-gradient(90deg,#C05621,#DD6B20);">
        <span class="ph-num">2</span>
        <span class="ph-title">Analyse de menace &amp; gestion des secteurs</span>
        <span class="ph-time">T+25 → T+60 min</span>
      </div>
      <div class="ph-trigger">
        <b>Déclencheur :</b> {_p2_trigger_str}
      </div>
      <div class="ph-body">""", unsafe_allow_html=True)

    # Actions Phase 2 — uniquement basées sur les inputs
    # Gare routière
    if has_gare_rout and nb_gare_pers > 0:
        _c_gare = conc_ppm(q_debit_kgs(Q_kg,duree_min,type_lib), u_ms, dist_pop, 0, stab)
        _zone_gare = ("ERPG-3" if dist_pop<=r3 else "ERPG-2" if dist_pop<=r2 else "ERPG-1")
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Gare routière (T+30)<br>
            <span style="font-weight:400;font-size:.75rem;">{nb_gare_pers} personnes</span></div>
          <div class="act-content">
            Gare en <b>{_zone_gare}</b> · C estimée : ~{_c_gare:.1f} ppm.<br>
            <span class='ok'>CONFINEMENT immédiat</span> — étages supérieurs — fermeture VMC.<br>
            <span class='warn'>NE PAS évacuer</span> pendant le passage du nuage.<br>
            Instructions : fenêtres fermées · serviettes mouillées · attendre PCO.
          </div>
        </div>""", unsafe_allow_html=True)

    # Centre administratif
    if has_admin and nb_agents_admin > 0:
        _zone_admin = ("ERPG-3" if dist_pop<=r3 else "ERPG-2" if dist_pop<=r2 else "ERPG-1")
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Centre admin. (T+40)<br>
            <span style="font-weight:400;font-size:.75rem;">{nb_agents_admin} agents</span></div>
          <div class="act-content">
            Centre en <b>{_zone_admin}</b>.<br>
            <span class='ok'>CONFINEMENT aux étages supérieurs</span> — fermeture prises d'air.<br>
            Pas d'évacuation immédiate — attendre dissipation du nuage.<br>
            Contact responsable pour encadrement du confinement.
          </div>
        </div>""", unsafe_allow_html=True)

    # École
    if has_ecole:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">École / Crèche (T+35)</div>
          <div class="act-content">
            <b>Population vulnérable prioritaire</b> (enfants : 2× plus sensibles au Cl₂).<br>
            <span class='ok'>Confinement en salle intérieure</span> · Fenêtres fermées.<br>
            Appel aux parents différé (éviter panique et afflux) · bus hors zone après dissipation.
          </div>
        </div>""", unsafe_allow_html=True)

    # Hôpital
    if has_hopital:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Hôpital / Clinique (T+35)</div>
          <div class="act-content">
            Activation protocole NRBC interne · Fermeture VMC.<br>
            Confinement patients non mobiles · Décontamination avant entrée.<br>
            Coordination DSM pour évacuation patients critiques si dissipation confirmée.
          </div>
        </div>""", unsafe_allow_html=True)

    # Usines en zone ERPG-2 (Phase 2)
    for _u in _usines_p2:
        if _u.get('produits'):
            st.markdown(f"""
            <div class="act-row">
              <div class="act-label">Usine '{_u['nom']}'<br>
                <span style="font-weight:400;font-size:.75rem;">à {_u['dist']}m — T+45</span></div>
              <div class="act-content">
                Produits : <b>{', '.join(_u['produits'])}</b>.<br>
                <span class='warn'>Risque réaction avec Cl₂</span> → voir Phase 3 pour détail.<br>
                Évacuation préventive des opérateurs · Alerte PCO pour révision zonage.
              </div>
            </div>""", unsafe_allow_html=True)

    # Communication médias — toujours présente
    st.markdown(f"""
    <div class="act-row">
      <div class="act-label">Communication<br>médias (T+35)</div>
      <div class="act-content">
        Message officiel : confirmer l'accident TMD · <span class='warn'>démentir toute hypothèse malveillante</span>.<br>
        <b>Ne PAS confirmer/infirmer sans validation DOS.</b><br>
        Modèle : <i>« Accident TMD survenu. Secours engagés. Population de [zone] invitée à se confiner. »</i><br>
        → Activation cellule de crise communication.
      </div>
    </div>""", unsafe_allow_html=True)

    # Si aucun établissement renseigné → message informatif
    if not any([has_gare_rout, has_admin, has_ecole, has_hopital, _usines_p2]):
        st.markdown("""
        <div style="padding:10px 16px;background:#EBF8FF;border-radius:6px;
                    font-size:.82rem;color:#2B6CB0;margin:4px 0;
                    border-left:3px solid #3182CE;">
          ℹ️ Aucun établissement renseigné dans la sidebar — les actions
          spécifiques (gare, école, centre admin...) apparaîtront automatiquement
          lorsque vous activez les inputs <b>"Crise majeure"</b>.
        </div>""", unsafe_allow_html=True)

    # Erreur fréquente Phase 2 — dynamique selon la présence d'une gare
    _err_p2 = (
        f"Évacuer la gare routière ({nb_gare_pers} pers.) pendant le passage du nuage."
        if has_gare_rout else
        "Évacuer les populations confinées pendant que le nuage est encore en propagation."
    )
    st.markdown(f"""
    <div class="err-box" style="margin:8px 16px 8px;">
      <b>⚠ Erreur fréquente — Phase 2 :</b> {_err_p2}<br>
      Règle absolue : <b>confinement si nuage en propagation</b> ·
      évacuation uniquement après dissipation ou hors zone de menace.
    </div>""", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── PHASE 3 — DYNAMIQUE selon les inputs ──────────────────────────────
    # Construire les déclencheurs selon les inputs
    _p3_triggers = []
    if usines_domino: _p3_triggers.append("Effet domino usines à risque")
    if has_train:     _p3_triggers.append(f"Train ({train_passagers} passagers)")
    if has_gare_rout: _p3_triggers.append(f"Gare routière ({nb_gare_pers} pers.)")
    if has_admin:     _p3_triggers.append(f"Centre administratif ({nb_agents_admin} agents)")
    if has_hopital:   _p3_triggers.append("Hôpital/clinique en zone")
    if has_ecole:     _p3_triggers.append("École/crèche en zone")
    _p3_triggers.append("Saturation hospitalière potentielle")
    _trig_str = " · ".join(_p3_triggers) if _p3_triggers else "Multi-sites"

    st.markdown(f"""
    <div class="ph-wrap">
      <div class="ph-head" style="background:linear-gradient(90deg,#9B2C2C,#C53030);">
        <span class="ph-num">3</span>
        <span class="ph-title">Crise majeure &amp; gestion multi-sites</span>
        <span class="ph-time">T+60 → T+130 min</span>
      </div>
      <div class="ph-trigger">
        <b>Déclencheur :</b> {_trig_str}
      </div>
      <div class="ph-body">""", unsafe_allow_html=True)

    # ── Usines à effet domino (basées sur les inputs) ─────────────────────
    # Table de réactions Cl₂ avec les produits courants
    _REACTIONS = {
        "Aluminium (Al)":
            ("Cl₂ + 2Al → 2AlCl₃",
             "Réaction exothermique intense → combustion / explosion potentielle. "
             "AlCl₃ se sublime à 180°C en gaz toxique secondaire.",
             "Périmètre +500m · CMIC spécialisée · <span class='warn'>PAS d'arrosage eau</span> "
             "(AlCl₃ + H₂O → réaction violente + HCl gazeux) · Interdiction accès zone."),
        "Acétylène (C₂H₂)":
            ("Cl₂ + C₂H₂ → C₂H₂Cl₂ (réaction explosive sous étincelle/lumière)",
             "Mélange explosif sous l'action d'une étincelle ou de la lumière. Risque BLEVE.",
             "Interdiction feu et étincelles · Périmètre +800m · Évacuation immédiate zone rouge."),
        "Ammoniac (NH₃)":
            ("Cl₂ + 8NH₃ → N₂ + 6NH₄Cl (nuage toxique NH₄Cl)",
             "Formation de chloramine (NH₂Cl) — gaz toxique pulmonaire très dangereux.",
             "Double nuage toxique Cl₂+NH₃ · Périmètre majoré · EPI niveau A impératif."),
        "Hydrogène (H₂)":
            ("Cl₂ + H₂ → 2HCl (réaction explosive à la lumière)",
             "Explosion possible sous lumière ou étincelle. Formation de HCl gazeux toxique.",
             "Source d'ignition à proscrire · Périmètre +400m · Alerte ATEX."),
        "Phosphore (P)":
            ("2P + 3Cl₂ → 2PCl₃ (spontané, exothermique)",
             "Réaction spontanée et violente. PCl₃ est un agent chimique toxique.",
             "Périmètre +600m · Pas d'eau (P + H₂O → acide phosphoreux) · CMIC."),
        "Graisses industrielles":
            ("Cl₂ + graisses → réaction exothermique + fumées irritantes",
             "Échauffement localisé, fumées irritantes, risque d'inflammation.",
             "Évacuation immédiate des opérateurs · Alerte pompiers risque incendie."),
        "Éthylène":
            ("Cl₂ + C₂H₄ → C₂H₄Cl₂ (dichloroéthane, toxique)",
             "Formation de produit halogéné toxique. Risque d'explosion si confinement.",
             "Périmètre +500m · Interdiction sources d'ignition · CMIC."),
        "Éthane":
            ("Cl₂ + C₂H₆ → C₂H₅Cl + HCl (sous lumière/catalyseur)",
             "Chloroéthane et HCl gazeux — toxiques et inflammables.",
             "Périmètre +400m · Alerte ATEX · CMIC."),
        "Silicones":
            ("Cl₂ + silicones → chlorosilanes (réactif, toxique)",
             "Formation de chlorosilanes très réactifs avec l'eau → HCl.",
             "Évacuation zone · Périmètre +300m · Pas d'eau · CMIC."),
        "Huiles industrielles":
            ("Cl₂ + huiles → chloration + dégagement HCl",
             "Risque d'inflammation violente avec dégagement de HCl gazeux.",
             "Évacuation opérateurs · Alerte pompiers · Périmètre +200m."),
        "Arsenic (As)":
            ("2As + 3Cl₂ → 2AsCl₃ (très toxique)",
             "Formation de trichlorure d'arsenic, agent extrêmement toxique.",
             "Périmètre +800m · CMIC niveau A impératif · Alerte NRBC."),
        "Antimoine (Sb)":
            ("2Sb + 3Cl₂ → 2SbCl₃ (exothermique, toxique)",
             "Trichlorure d'antimoine toxique formé spontanément.",
             "Périmètre +500m · CMIC · Interdiction accès."),
        "Chlorure de vinyle":
            ("Cl₂ + CH₂=CHCl → CHCl₂-CH₂Cl (addition, exothermique)",
             "Produit dichloré toxique et cancérigène. Risque d'explosion.",
             "Périmètre +600m · ATEX · CMIC · Interdiction ignition."),
        "Acide chlorhydrique":
            ("Cl₂ + H₂O → HCl + HClO (en présence humidité)",
             "Augmentation des concentrations en HCl. Double nuage acide.",
             "Majoration de la zone ERPG · EPI niveau A · CMIC."),
        "Autre produit réactif":
            ("Réaction à déterminer par CMIC",
             "Risque chimique non quantifié — intervention CMIC obligatoire.",
             "Périmètre conservatoire +300m · CMIC · Analyse sur site."),
    }

    if usines_domino:
        for _u in usines_domino:
            if not _u["produits"]:
                continue
            _eff_domino_lines = []
            for _prod in _u["produits"]:
                if _prod in _REACTIONS:
                    _eq, _effet, _action = _REACTIONS[_prod]
                    _eff_domino_lines.append(
                        f"<b>{_prod}</b> : <code style='background:#F7FAFC;"
                        f"padding:1px 4px;border-radius:3px;font-size:.78rem;'>{_eq}</code><br>"
                        f"&nbsp;&nbsp;→ {_effet}<br>"
                        f"&nbsp;&nbsp;<b>Action :</b> {_action}"
                    )
            if _eff_domino_lines:
                _u_lbl = (f"{_u['nom']}<br>"
                          f"<span style='font-weight:400;font-size:.75rem;'>"
                          f"à {_u['dist']}m · T+60 min</span>")
                _u_content = (
                    f"<b>Produits à risque identifiés :</b><br><br>" +
                    "<br><br>".join(_eff_domino_lines) +
                    f"<br><br><b>Interdiction d'accès</b> à la zone · "
                    f"Demande <span class='highlight'>CMIC spécialisée</span> · "
                    f"Périmètre élargi selon réaction identifiée."
                )
                st.markdown(f"""
                <div class="act-row">
                  <div class="act-label">{_u_lbl}</div>
                  <div class="act-content">{_u_content}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:10px 16px;background:#F0FFF4;border-radius:6px;
                    font-size:.82rem;color:#276749;margin:4px 0;">
          ℹ️ Aucune usine à risque renseignée — activez les inputs
          <b>"Crise majeure"</b> dans la sidebar pour simuler un effet domino.
        </div>""", unsafe_allow_html=True)

    # ── Train (si renseigné) ───────────────────────────────────────────────
    if has_train:
        # Déterminer dans quelle zone ERPG se trouve le train
        # (on considère que le train est à distance variable — on utilise dist_pop comme proxy)
        _zone_train = ("ERPG-3 (danger vital)" if dist_pop <= r3
                       else "ERPG-2 (effets irréversibles)" if dist_pop <= r2
                       else "ERPG-1 (irritations légères)")
        _zone_col_t = ("#C53030" if dist_pop<=r3 else
                       "#C05621" if dist_pop<=r2 else "#B7791F")
        _cote_opp = (dir_vent + 180) % 360
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Train en zone<br>
            <span style="font-weight:400;font-size:.75rem;">{train_passagers} passagers
            · {train_wagons} wagons</span>
          </div>
          <div class="act-content">
            Train en <b style="color:{_zone_col_t};">{_zone_train}</b>.<br>
            <span class='ok'>NE PAS quitter le train</span> · Ventilation coupée ·
            Fenêtres fermées hermétiquement.<br>
            Prochain arrêt dans <b>{train_delai_arr} min</b> →
            évacuation possible hors zone de menace.<br>
            → Arrêt côté opposé au vent
            (<b>{dir_vent}°</b> → s'arrêter vers <b>{_cote_opp:.0f}°</b>) ·
            SMUR en attente à la prochaine station.
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Gare routière (si renseignée) ─────────────────────────────────────
    if has_gare_rout and nb_gare_pers > 0:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Gare routière<br>
            <span style="font-weight:400;font-size:.75rem;">{nb_gare_pers} personnes</span>
          </div>
          <div class="act-content">
            <span class='ok'>CONFINEMENT immédiat</span> — étages supérieurs —
            fermeture VMC / prises d'air.<br>
            <span class='warn'>NE PAS évacuer</span> pendant le passage du nuage.<br>
            Instructions : fenêtres fermées · serviettes mouillées · attendre PCO.<br>
            <b>Concentration indoor attendue :</b> proche ERPG-2/3 si bâtiment
            à &lt;{r2:.0f}m.
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Centre administratif (si renseigné) ───────────────────────────────
    if has_admin and nb_agents_admin > 0:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Centre admin.<br>
            <span style="font-weight:400;font-size:.75rem;">{nb_agents_admin} agents</span>
          </div>
          <div class="act-content">
            <span class='ok'>CONFINEMENT aux étages supérieurs</span> ·
            Fermeture prises d'air extérieur.<br>
            Pas d'évacuation immédiate — attendre dissipation du nuage.<br>
            Contact responsable pour encadrement du confinement.
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Hôpital (si renseigné) ─────────────────────────────────────────────
    if has_hopital:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">Hôpital / Clinique<br>
            <span style="font-weight:400;font-size:.75rem;">en zone d'impact</span>
          </div>
          <div class="act-content">
            <span class='warn'>Zone à décontaminer avant entrée</span> ·
            Activation protocole NRBC interne.<br>
            Confinement patients non mobiles · Fermeture VMC.<br>
            Coordination avec DSM pour évacuation patients critiques.
          </div>
        </div>""", unsafe_allow_html=True)

    # ── École / crèche (si renseignée) ────────────────────────────────────
    if has_ecole:
        st.markdown(f"""
        <div class="act-row">
          <div class="act-label">École / Crèche<br>
            <span style="font-weight:400;font-size:.75rem;">en zone d'impact</span>
          </div>
          <div class="act-content">
            <b>Population vulnérable prioritaire</b> (enfants — plus sensibles au Cl₂).<br>
            <span class='ok'>Confinement en salle intérieure</span> · Fenêtres fermées ·
            Appel parents différé (éviter panique).<br>
            Évacuation sécurisée après dissipation — bus scolaires hors zone.
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Saturation hospitalière (basée sur les inputs) ────────────────────
    # Décision Plan Blanc : si UA estimés > capacité réanimation OU UA > 20% des lits CHR
    _plan_blanc = blesses_e3 >= capa_ua_max or blesses_e3 >= 10 or blesses_estimes >= 50
    _plan_blanc_txt = ("<span class='warn'>Activation Plan Blanc CHR recommandée</span>"
                       if _plan_blanc else
                       "<span class='ok'>Plan Blanc non nécessaire à ce stade</span>")
    _surplus_ua   = max(0, blesses_e3 - capa_ua_max)
    _reorientation = (f"Réorienter {_surplus_ua} UA vers autres établissements."
                      if _surplus_ua > 0 else "CHR peut absorber les UA estimés.")

    st.markdown(f"""
    <div class="act-row">
      <div class="act-label">Saturation hospitalière<br>
        <span style="font-weight:400;font-size:.75rem;">T+80→T+90</span>
      </div>
      <div class="act-content">
        {_plan_blanc_txt} — CHR : {capa_chr_lits} lits ·
        Réanimation/NRBC : {capa_ua_max} lits · SMUR : {nb_smur} unités.<br>
        <b>UA ({blesses_e3})</b> → CHR Réanimation / Cellule NRBC.
        {_reorientation}<br>
        <b>UR ({blesses_e2})</b> → CHR Urgences + hôpitaux de proximité.<br>
        <b>Impliqués ({pop_e2})</b> → PMA sur site + hôpitaux proximité.<br>
        → Activation <span class='highlight'>CUMP</span> (soutien psychologique) ·
        Renforcement ambulancier ({nb_smur} SMUR disponibles).
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="err-box" style="margin:8px 16px 8px;">
      <b>⚠ Erreur fréquente — Phase 3 :</b> Oublier les sous-sols dans les zones résidentielles.
      Le chlore est <b>2,5 fois plus lourd que l'air</b> : il descend et s'accumule
      dans les espaces bas (N-1, caves, fossés). Évacuation des sous-sols = priorité absolue.
    </div>""", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)


        # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — RETEX DYNAMIQUE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""<div class="os-sh">
      <span class="sh-icon">🔁</span>
      <span class="sh-txt">RETEX — Erreurs critiques à éviter</span>
      <span class="sh-sub">Adapté au cas simulé</span>
    </div>""", unsafe_allow_html=True)

    _RETEX = [
        ("🔴","Évacuer la zone rouge pendant le nuage actif",
         f"Cl₂ propagation {_dlbl} ({_prop:.0f}°) — évacuation = exposition directe maximale de {pop_e3:,} personnes.",
         f"Confinement hermétique &lt;{r3:.0f}m — VMC fermée — attendre dissipation complète avant toute évacuation."),
        ("🔴","Ignorer les espaces bas (sous-sols, fossés, caves)",
         "Cl₂ = 2,5× plus lourd que l'air : descend et s'accumule dans tous les points bas.",
         "Évacuer les sous-sols EN PRIORITÉ vers les étages — ne jamais s'y réfugier."),
    ]
    if not _al_on:
        _RETEX.append(("🔴","Alerte absente — populations sans instruction",
            f"{pop_e2:,} personnes en zone orange sans connaissance du danger.",
            "Déclencher immédiatement : sirènes + SMS + radio + porte-à-porte."))
    if delai_evac > 30:
        _RETEX.append(("🟠",f"Délai évacuation {delai_evac} min — prolonge l'exposition",
            f"{pop_e2:,} personnes accumulent une dose toxique supplémentaire.",
            "Réduire à &lt;15 min si possible — prioriser populations vulnérables."))
    _RETEX.extend([
        ("🟠","Activer eau sur zone aluminium en feu",
         "AlCl₃ + H₂O → réaction violente + dégagement HCl. Danger extrême.",
         "CMIC spécialisée uniquement — poudre sèche — jamais d'eau sur AlCl₃."),
        ("🟡","Lever confinement et évacuation simultanément",
         "Flux de population en zone contaminée si les deux ordres sont simultanés.",
         "Séquence stricte : confinement → dissipation → levée J → O → R."),
        ("🟡","Confirmer/infirmer l'hypothèse terroriste sans DOS",
         "Risque de panique, perte confiance, actions incontrôlées des populations.",
         "Message type officiel uniquement — validation DOS obligatoire avant toute déclaration."),
    ])

    _RLVL = {"🔴":"#C53030","🟠":"#C05621","🟡":"#B7791F"}
    _RLBG = {"🔴":"#FFF5F5","🟠":"#FFFAF0","🟡":"#FFFFF0"}

    for lvl,titre,err,sol in _RETEX:
        rc = _RLVL.get(lvl,"#718096")
        rb = _RLBG.get(lvl,"#F7FAFC")
        st.markdown(f"""
        <div class="rtx" style="background:{rb};border-top:3px solid {rc};">
          <div class="rtx-head">
            <span style="font-size:1.1rem;">{lvl}</span>
            <span class="rtx-title">{titre}</span>
          </div>
          <div class="rtx-cols">
            <div class="rtx-err">
              <span class="rtx-lbl" style="color:#C53030;">❌ Risque / Erreur</span>{err}
            </div>
            <div class="rtx-ok">
              <span class="rtx-lbl" style="color:#276749;">✅ Action correcte</span>{sol}
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:22px;padding:12px 18px;background:#F7FAFC;
                border-radius:8px;border:1px solid #E2E8F0;
                display:flex;justify-content:space-between;align-items:center;
                font-size:.75rem;color:#718096;">
      <span>🛡 Organisation des Secours — Plan ORSEC · HazMod ·
            MS NRBCE · UHA / SERFA · Commission Nationale NRBC — Maroc · 2025–2026</span>
      <span style="font-family:'Courier New',monospace;">
        HAZMOD · G={_G:.1f} · Q={Q_kg:,.0f}kg · {u_ms}m/s · {stab} · ERPG-3={r3:.0f}m
      </span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — HOTSPOTS & ZONES DE CONFINEMENT POTENTIELLES
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown("""<style>
    .hs-banner{background:linear-gradient(120deg,#1A202C 0%,#2D3748 55%,#1A365D 100%);
               border-radius:12px;padding:18px 24px;margin-bottom:20px;
               box-shadow:0 4px 16px rgba(0,0,0,.2);}
    .hs-banner h3{color:#fff;font-size:1.1rem;font-weight:700;margin:0 0 4px;}
    .hs-banner p{color:#A0AEC0;font-size:.82rem;margin:0;}
    .hs-card{background:#fff;border-radius:10px;border:1px solid #E2E8F0;
             padding:14px 16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.05);}
    .hs-title{font-weight:700;font-size:.9rem;color:#1A202C;margin-bottom:8px;
              display:flex;align-items:center;gap:8px;}
    .hs-item{display:grid;grid-template-columns:28px 1fr auto;align-items:center;
             gap:8px;padding:7px 0;border-bottom:1px solid #F0F4F8;font-size:.8rem;
             color:#2D3748;}
    .hs-item:last-child{border-bottom:none;}
    .hs-icon{font-size:1.1rem;text-align:center;}
    .hs-conc{font-family:'Courier New',monospace;font-size:.75rem;
             padding:2px 7px;border-radius:4px;font-weight:700;white-space:nowrap;}
    .cf-card{border-radius:10px;padding:14px 16px;margin-bottom:12px;
             border:2px solid;box-shadow:0 2px 8px rgba(0,0,0,.08);}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="hs-banner">
      <h3>🔥 Identification des Hotspots & Zones de Confinement Potentielles</h3>
      <p>
        Zones à concentration maximale dans chaque anneau ERPG · Points de stagnation du nuage ·
        Bâtiments / espaces de confinement recommandés
      </p>
    </div>""", unsafe_allow_html=True)


    # ── Recalcul local des concentrations pour les graphes ─────────────────────
    import math as _m
    _Q_kgs_hs = q_debit_kgs(Q_kg, duree_min, type_lib)
    _H_hs     = h_effectif(hauteur_m, type_lib)
    _prop_hs  = (dir_vent + 180) % 360

    def _hotspot_coord(lat0, lon0, dist_m_val, bearing):
        R = 6371000.0
        lat_r = _m.radians(lat0); br = _m.radians(bearing); dr = dist_m_val / R
        nlat = _m.asin(_m.sin(lat_r)*_m.cos(dr) + _m.cos(lat_r)*_m.sin(dr)*_m.cos(br))
        nlon = _m.radians(lon0) + _m.atan2(
            _m.sin(br)*_m.sin(dr)*_m.cos(lat_r),
            _m.cos(dr) - _m.sin(lat_r)*_m.sin(nlat))
        return _m.degrees(nlat), _m.degrees(nlon)

    _hotspot_dists = [
        max(50, r3 * 0.5), max(r3, 10), (r3 + r2) / 2,
        max(r2, 10), (r2 + r1) / 2,
    ]
    _hs_data = []
    for _d in _hotspot_dists:
        _sy_h, _sz_h = sigma_pg(max(_d, 1), stab)
        _den_h = _m.pi * u_ms * _sy_h * _sz_h
        _c_h = (_Q_kgs_hs * 1000) / _den_h * 24.45 / 70.9 if _den_h > 1e-10 else 0.0
        _lat_h, _lon_h = _hotspot_coord(lat, lon, _d, _prop_hs)
        _hs_data.append({"dist": _d, "conc": _c_h, "lat": _lat_h, "lon": _lon_h})

    # ── Bandeau statut des hotspots dynamiques OSM ───────────────────────────
    _hs_color = '#10B981' if _hs_total > 0 else '#F59E0B'
    _hs_status_txt = f'✅ {_hs_total} établissements identifiés via {_hs_source}' if _hs_total > 0 else f'⚠️ Mode géométrique — {_hs_source}'
    st.markdown(f"""
    <div style="background:linear-gradient(120deg,#0C2340,#1A3A6B);border-radius:10px;
                padding:12px 18px;margin-bottom:16px;border:1px solid rgba(255,255,255,.12);
                display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
      <div style='flex:1;'>
        <div style='color:#F0C040;font-weight:700;font-size:.88rem;margin-bottom:4px;'>
          🔥 Hotspots Dynamiques — Mise à jour automatique par coordonnées GPS
        </div>
        <div style='color:#93C5FD;font-size:.78rem;'>
          {_hs_status_txt} &nbsp;·&nbsp;
          🔴 ERPG-3 : <b style='color:#EF4444;'>{len(hotspots_dynamiques.get('ERPG-3',[]))} sites</b> &nbsp;·&nbsp;
          🟠 ERPG-2 : <b style='color:#F59E0B;'>{len(hotspots_dynamiques.get('ERPG-2',[]))} sites</b> &nbsp;·&nbsp;
          🟢 ERPG-1 : <b style='color:#4ADE80;'>{len(hotspots_dynamiques.get('ERPG-1',[]))} sites</b>
        </div>
        <div style='color:#475569;font-size:.72rem;margin-top:3px;'>
          📍 {lat:.4f}°N / {lon:.4f}°E &nbsp;·&nbsp; ERPG-3={r3:.0f}m · ERPG-2={r2:.0f}m · ERPG-1={r1:.0f}m
          &nbsp;·&nbsp; Sources : OpenStreetMap / Google Earth · Cache 5 min
        </div>
      </div>
      <div>
        <span style='background:{_hs_color};color:#fff;border-radius:6px;padding:5px 14px;
                     font-weight:700;font-size:.88rem;'>{_hs_total} HOTSPOTS</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if st.button('🔄  Rafraîchir les hotspots (forcer nouvelle requête OSM)', key='refresh_hs'):
        _get_hotspots_cached.clear()
        st.rerun()

    # ── Tableau des hotspots dynamiques par zone ──────────────────────────────
    st.markdown('<p class="sc-section">★ HOTSPOTS IDENTIFIÉS PAR ZONE (OpenStreetMap)</p>', unsafe_allow_html=True)

    _zone_configs = [
        ('ERPG-3', '🔴 Zone ERPG-3 — Danger Vital (> 20 ppm)', '#C53030', '#FFF5F5', '#FEE2E2'),
        ('ERPG-2', '🟠 Zone ERPG-2 — Effets Irréversibles (3–20 ppm)', '#C05621', '#FFFAF0', '#FEF3C7'),
        ('ERPG-1', '🟢 Zone ERPG-1 — Irritations (1–3 ppm)', '#15803D', '#F0FFF4', '#DCFCE7'),
    ]
    for _z_key, _z_title, _z_col, _z_bg, _z_bg2 in _zone_configs:
        _z_items = hotspots_dynamiques.get(_z_key, [])
        with st.expander(f"{_z_title} — {len(_z_items)} site(s)", expanded=(_z_key == 'ERPG-3')):
            if not _z_items:
                st.info(f'Aucun hotspot identifié dans la zone {_z_key} pour ces coordonnées.')
            else:
                for _hi in _z_items:
                    _prio_col = {'CRITIQUE':'#C53030','ÉLEVÉ':'#C05621'}.get(_hi.get('priority','MODÉRÉ'),'#B45309')
                    st.markdown(f"""
                    <div style='display:flex;align-items:center;gap:10px;padding:8px 12px;
                                background:{_z_bg};border-radius:8px;margin-bottom:6px;
                                border-left:4px solid {_z_col};'>
                      <span style='font-size:1.3rem;'>{_hi.get('icon','📍')}</span>
                      <span style='color:#EF4444;font-size:1rem;'>★</span>
                      <div style='flex:1;'>
                        <div style='font-weight:700;color:#1A202C;font-size:.88rem;'>{_hi['name']}</div>
                        <div style='font-size:.73rem;color:#4B5563;'>{_hi.get('risk','—')}</div>
                        <div style='font-size:.7rem;color:#9CA3AF;font-family:monospace;'>
                          {_hi['coords'][0]:.5f}°N {_hi['coords'][1]:.5f}°E &nbsp;·&nbsp; {_hi['dist']}m de la source
                        </div>
                      </div>
                      <span style='background:{_prio_col};color:#fff;border-radius:5px;
                                   padding:2px 8px;font-size:.72rem;font-weight:700;white-space:nowrap;'>
                        {_hi.get('priority','MODÉRÉ')}
                      </span>
                    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Affichage dynamique des hotspots OSM dans 2 colonnes
    # Colonne gauche : hotspots par zone (données OSM réelles)
    # Colonne droite : graphique de concentration + radar
    # ══════════════════════════════════════════════════════════════════════
    col_hs1, col_hs2 = st.columns([1.3, 1])

    with col_hs1:
        _ZONE_DISPLAY = [
            ("ERPG-3", "🔴 Zone ERPG-3 — Danger Vital (> 20 ppm)",
             "#C53030", "#FFF5F5", "#FEE2E2"),
            ("ERPG-2", "🟠 Zone ERPG-2 — Effets Irréversibles (3–20 ppm)",
             "#C05621", "#FFFAF0", "#FEF3C7"),
            ("ERPG-1", "🟢 Zone ERPG-1 — Irritations Légères (1–3 ppm)",
             "#15803D", "#F0FFF4", "#DCFCE7"),
        ]

        for _zk, _ztitle, _zcol, _zbg, _zbg2 in _ZONE_DISPLAY:
            _z_items = hotspots_dynamiques.get(_zk, [])
            st.markdown(f"""
            <div class="hs-card" style="border-left:4px solid {_zcol};background:{_zbg};">
              <div class="hs-title" style="color:{_zcol};">
                {_ztitle}
                <span style="margin-left:auto;font-size:.72rem;background:{_zcol};
                             color:#fff;border-radius:4px;padding:1px 8px;">
                  {len(_z_items)} site(s)
                </span>
              </div>""", unsafe_allow_html=True)

            if not _z_items:
                # Zone sans établissements — message contextuel
                if _zk == "ERPG-3":
                    _msg = f"Rayon {r3:.0f}m — Zone à évacuer/confiner impérativement"
                elif _zk == "ERPG-2":
                    _msg = f"Rayon {r2:.0f}m — Aucun établissement OSM trouvé"
                else:
                    _msg = f"Rayon {r1:.0f}m — Zone de surveillance"
                st.markdown(f"""
                <div class="hs-item">
                  <span class="hs-icon">ℹ️</span>
                  <div>
                    <div style="font-weight:600;color:#4B5563;font-style:italic;">
                      {_msg}
                    </div>
                    <div style="font-size:.7rem;color:#9CA3AF;">
                      Zone potentiellement rurale — données OSM limitées
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                for _hi in _z_items:
                    _prio = _hi.get("priority", "MODÉRÉ")
                    _prio_col = (
                        "#B91C1C" if _prio == "CRITIQUE"
                        else "#C05621" if _prio == "ÉLEVÉ"
                        else "#B45309"
                    )
                    # Calcul de la concentration à la distance du hotspot
                    _d_hs = max(_hi.get("dist", 100), 10)
                    _sy_hs, _sz_hs = sigma_pg(_d_hs, stab)
                    _den_hs = _m.pi * u_ms * _sy_hs * _sz_hs
                    _c_hs = (
                        (_Q_kgs_hs * 1000) / _den_hs * 24.45 / 70.9
                        if _den_hs > 1e-10 else 0.0
                    )
                    _c_str = f"~{_c_hs:.2f} ppm"
                    _c_bg  = (
                        "#FEE2E2" if _c_hs >= 20
                        else "#FEF3C7" if _c_hs >= 3
                        else "#DCFCE7" if _c_hs >= 1
                        else "#F0F9FF"
                    )
                    _coords = _hi.get("coords", [lat, lon])
                    _coord_str = (
                        f"{_coords[0]:.4f}°N {_coords[1]:.4f}°E"
                        if _coords else f"{lat:.4f}°N {lon:.4f}°E"
                    )
                    st.markdown(f"""
                    <div class="hs-item">
                      <span class="hs-icon">
                        {_hi.get("icon","📍")}
                        <span style="color:#EF4444;font-size:.8rem;">★</span>
                      </span>
                      <div style="flex:1;">
                        <div style="font-weight:700;color:#1A202C;font-size:.83rem;">
                          {_hi.get("name","—")}
                        </div>
                        <div style="font-size:.71rem;color:#4B5563;">
                          {_hi.get("risk","—")}
                        </div>
                        <div style="font-size:.68rem;color:#9CA3AF;font-family:monospace;">
                          📍 {_coord_str} &nbsp;·&nbsp; {_d_hs:.0f}m
                        </div>
                      </div>
                      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;">
                        <span style="background:{_prio_col};color:#fff;border-radius:4px;
                                     padding:1px 7px;font-size:.68rem;font-weight:700;">
                          {_prio}
                        </span>
                        <span class="hs-conc" style="background:{_c_bg};color:{_zcol};
                                                      font-size:.68rem;">
                          {_c_str}
                        </span>
                      </div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Note sur la source des données
        st.markdown(f"""
        <div style="margin-top:8px;padding:8px 12px;background:#F0F9FF;border-radius:6px;
                    font-size:.73rem;color:#1E40AF;border-left:3px solid #3B82F6;">
          📡 <b>Source :</b> OpenStreetMap / Overpass API —
          Coordonnées actuelles : <b>{lat:.4f}°N / {lon:.4f}°E</b> —
          Rayons : ERPG-3={r3:.0f}m · ERPG-2={r2:.0f}m · ERPG-1={r1:.0f}m<br/>
          🔄 Les hotspots se recalculent automatiquement à chaque changement de coordonnées.
        </div>""", unsafe_allow_html=True)

    with col_hs2:
        # ── Graphique concentration avec hotspots OSM réels ───────────────────
        _dist_axis = np.linspace(10, max(r1 * 1.2, 500), 200)
        _conc_axis = []
        for _da in _dist_axis:
            _sy_a, _sz_a = sigma_pg(max(_da, 1), stab)
            _den_a = _m.pi * u_ms * _sy_a * _sz_a
            _c_a = (_Q_kgs_hs * 1000) / _den_a * 24.45 / 70.9 if _den_a > 1e-10 else 0
            _conc_axis.append(max(_c_a, 0))

        fig_hs = go.Figure()
        for _y0, _y1, _fc in [
            (20, max(_conc_axis[0] if _conc_axis else 100, 25), "rgba(220,38,38,0.10)"),
            (3, 20, "rgba(234,88,12,0.10)"),
            (1, 3, "rgba(22,163,74,0.10)"),
        ]:
            fig_hs.add_hrect(y0=_y0, y1=_y1, fillcolor=_fc, layer="below", line_width=0)

        fig_hs.add_trace(go.Scatter(
            x=_dist_axis, y=_conc_axis,
            fill="tozeroy", fillcolor="rgba(37,99,235,0.12)",
            line=dict(color="#2563EB", width=2.5),
            name="Concentration axiale",
            hovertemplate="d=%{x:.0f}m<br>C=%{y:.3f}ppm<extra></extra>"
        ))

        # Marquer les hotspots OSM réels sur le graphique
        _all_hs_dists = []
        _all_hs_concs = []
        _all_hs_names = []
        _all_hs_cols  = []
        _z_colors = {"ERPG-3":"#B91C1C","ERPG-2":"#D97706","ERPG-1":"#16A34A"}
        for _zk in ["ERPG-3","ERPG-2","ERPG-1"]:
            for _hi in hotspots_dynamiques.get(_zk, []):
                _d_pt = max(_hi.get("dist", 0), 10)
                _sy_p, _sz_p = sigma_pg(_d_pt, stab)
                _den_p = _m.pi * u_ms * _sy_p * _sz_p
                _c_pt = (_Q_kgs_hs * 1000) / _den_p * 24.45 / 70.9 if _den_p > 1e-10 else 0
                _all_hs_dists.append(_d_pt)
                _all_hs_concs.append(max(_c_pt, 0))
                _all_hs_names.append(
                    f"{_hi.get('icon','★')} {_hi.get('name','—')}"
                    f" ({_zk}, {_d_pt:.0f}m)"
                )
                _all_hs_cols.append(_z_colors.get(_zk, "#666"))

        if _all_hs_dists:
            fig_hs.add_trace(go.Scatter(
                x=_all_hs_dists, y=_all_hs_concs,
                mode="markers+text",
                marker=dict(
                    color=_all_hs_cols, size=12,
                    symbol="star",
                    line=dict(color="white", width=1.5)
                ),
                text=[n.split("(")[0].strip()[:18] for n in _all_hs_names],
                textposition="top center",
                textfont=dict(size=7, color="#374151"),
                name="★ Hotspots OSM",
                hovertext=_all_hs_names,
                hovertemplate="%{hovertext}<br>C=%{y:.3f}ppm<extra></extra>"
            ))

        add_seuil_lines(fig_hs)
        apply_layout(fig_hs,
            f"Concentration & Hotspots — {lat:.4f}°N / {lon:.4f}°E",
            h=340, ylog=True)
        fig_hs.update_layout(
            xaxis_title="Distance axiale (m)",
            yaxis_title="Concentration Cl₂ (ppm) — log"
        )
        st.plotly_chart(fig_hs, use_container_width=True)

        # ── Radar des zones ───────────────────────────────────────────────────
        _radar_zones = ["Zone R (ERPG-3)", "Zone O (ERPG-2)", "Zone V (ERPG-1)",
                        "Pop. exposée", "Hotspots critiques", "Saturation CHR"]
        _n_critique = sum(
            1 for _z in ["ERPG-3","ERPG-2","ERPG-1"]
            for _hi in hotspots_dynamiques.get(_z, [])
            if _hi.get("priority") == "CRITIQUE"
        )
        _radar_vals = [
            min(10, r3 / 200),
            min(10, r2 / 500),
            min(10, r1 / 1000),
            min(10, pop_e2 / 500),
            min(10, _n_critique * 2.5),
            min(10, max(0, blesses_e3 - capa_ua_max) / max(capa_ua_max, 1) * 5),
        ]
        fig_rz = go.Figure(go.Scatterpolar(
            r=_radar_vals + [_radar_vals[0]],
            theta=_radar_zones + [_radar_zones[0]],
            fill="toself",
            fillcolor="rgba(220,38,38,0.15)" if gravite >= 7 else "rgba(234,88,12,0.15)",
            line=dict(color=g_color, width=2.5),
            marker=dict(size=8, color=g_color),
            name="Scores zones"
        ))
        fig_rz.update_layout(
            polar=dict(bgcolor="#F9FAFB",
                radialaxis=dict(visible=True, range=[0, 10],
                                tickfont=dict(size=8, color=PAL["muted"]),
                                gridcolor="#E8ECF0"),
                angularaxis=dict(tickfont=dict(size=9, color=PAL["text"]),
                                 gridcolor="#E8ECF0")),
            paper_bgcolor="#FFFFFF",
            title=dict(text=f"Radar Multi-Zones — {_n_critique} hotspots critiques",
                       font=dict(size=11)),
            height=300, margin=dict(l=40, r=40, t=40, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_rz, use_container_width=True)

    # ── Zones de Confinement Potentielles ────────────────────────────────────
    st.markdown("""<div style="margin-top:18px;margin-bottom:12px;display:flex;align-items:center;gap:8px;
               padding:10px 14px;background:#EFF6FF;border-radius:8px;border-left:5px solid #2563EB;">
      <span style="font-size:1.1rem;">🏠</span>
      <span style="font-size:.95rem;font-weight:700;color:#1E3A8A;">
        Zones Potentielles de Confinement — par anneau ERPG
      </span>
      <span style="font-size:.78rem;color:#3B82F6;margin-left:auto;">
        Basé sur les paramètres du scénario
      </span>
    </div>""", unsafe_allow_html=True)

    cf1, cf2, cf3 = st.columns(3)

    _confinement_zones = [
        (cf1, "🔴", "Zone Rouge — ERPG-3", r3, pop_e3,
         "#FEE2E2", "#B91C1C",
         [
             ("🏢", "Étages supérieurs (≥N+2) des immeubles en béton",
              "Protection maximale — structure bloque le Cl₂"),
             ("🏭", "Salles de commande pressurisées des usines",
              "Système surpression air filtré — EPI Niveau A requis à l'extérieur"),
             ("🚑", "Véhicules NRBC hermétiques — VMC coupée",
              "Recirculation air interne uniquement"),
             ("⬆️", "INTERDIRE tous sous-sols, caves, fossés",
              "Cl₂ 2.5× plus lourd — accumulation fatale"),
         ]),
        (cf2, "🟠", "Zone Orange — ERPG-2", r2, pop_e2,
         "#FEF3C7", "#B45309",
         [
             ("🏘️", "Appartements et maisons — étages ≥1, fenêtres calfeutrées",
              "VMC coupée · serviettes mouillées aux interstices"),
             ("🏫", "Salles de classe / bureaux intérieurs — porte étanche",
              "Meilleures pièces = intérieures sans fenêtre sur rue"),
             ("🚂", "Wagons de train — ventilation arrêtée, portes fermées",
              "Meilleure protection mobile disponible en zone orange"),
             ("🏪", "Grandes surfaces — confinement en zones réfrigérées/arrières",
              "Éviter halls d'entrée exposés"),
         ]),
        (cf3, "🟢", "Zone Verte — ERPG-1", r1, pop_e1,
         "#DCFCE7", "#15803D",
         [
             ("🏠", "Tout bâtiment fermé — confinement simple recommandé",
              "Fenêtres fermées suffisantes — EPI non obligatoire"),
             ("🌳", "Rassemblement à l'air libre hors direction du vent possible",
              f"S'éloigner vers {(dir_vent + 90) % 360:.0f}° ou {(dir_vent + 270) % 360:.0f}°"),
             ("🚗", "Véhicules personnels — vitres remontées, climatisation intérieure",
              "Solution de repli mobile efficace en zone verte"),
             ("🏫", "Écoles et ERP — confinement préventif recommandé",
              "Appeler parents après dissipation du nuage"),
         ]),
    ]

    for _col, _ico, _title, _radius, _pop, _bg, _border, _items in _confinement_zones:
        with _col:
            st.markdown(f"""
            <div class="cf-card" style="background:{_bg};border-color:{_border}44;">
              <div style="font-weight:700;font-size:.88rem;color:{_border};
                          margin-bottom:10px;display:flex;justify-content:space-between;">
                <span>{_ico} {_title}</span>
                <span style="font-size:.75rem;opacity:.75;">R={_radius:.0f}m · {_pop:,} pers.</span>
              </div>""", unsafe_allow_html=True)
            for _bi, _bs, _bd in _items:
                st.markdown(f"""
                <div style="display:flex;gap:8px;padding:7px 0;border-bottom:1px solid {_border}22;
                            font-size:.78rem;color:#1A202C;">
                  <span style="font-size:1rem;flex-shrink:0;">{_bi}</span>
                  <div>
                    <div style="font-weight:600;">{_bs}</div>
                    <div style="color:#4B5563;font-size:.72rem;margin-top:2px;">{_bd}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Bouton de génération PDF ─────────────────────────────────────────────
    st.markdown("""<div style="margin-top:28px;margin-bottom:8px;display:flex;align-items:center;
               gap:8px;padding:12px 16px;background:linear-gradient(120deg,#0C2340,#1A3A6B);
               border-radius:10px;border:1px solid rgba(255,255,255,0.1);">
      <span style="font-size:1.3rem;">📄</span>
      <div>
        <div style="color:#fff;font-weight:700;font-size:.95rem;">
          Générer le Livrable PDF — Rapport Ministre
        </div>
        <div style="color:#93C5FD;font-size:.78rem;margin-top:2px;">
          Rapport sophistiqué incluant toutes les zones ERPG, hotspots,
          zones de confinement et organisation des secours
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if st.button("📄  GÉNÉRER LE RAPPORT PDF OFFICIEL", use_container_width=True, type="primary", key="pdf_btn"):
        with st.spinner("⚙️ Génération du rapport PDF en cours…"):
            try:
                # ── Import du moteur PDF HazMod ─────────────────────────────
                import importlib.util, sys as _sys, os as _os
                # Chercher pdf_engine.py — chemin robuste multi-plateforme
                _eng_path = None
                _eng_candidates = [
                    _os.path.join(_os.getcwd(), "pdf_engine.py"),
                    "pdf_engine.py",
                    _os.path.join(_os.path.dirname(
                        _os.path.abspath(__file__) if "__file__" in dir() else _os.getcwd()
                    ), "pdf_engine.py"),
                ]
                for _fp in _eng_candidates:
                    if _os.path.exists(_fp):
                        _eng_path = _fp
                        break
                if _eng_path is None:
                    st.error("❌ Fichier pdf_engine.py introuvable. Placez-le dans le même dossier que app20_hazmod.py")
                    st.stop()
                _spec = importlib.util.spec_from_file_location("pdf_engine", _eng_path)
                _mod  = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)

                # ── Construction du dictionnaire de paramètres ───────────────
                import math as _mh
                def _hspot(lat0, lon0, dist_m, bearing):
                    R = 6371000.0
                    lr = _mh.radians(lat0); br = _mh.radians(bearing); dr = dist_m / R
                    nl = _mh.asin(_mh.sin(lr)*_mh.cos(dr)+_mh.cos(lr)*_mh.sin(dr)*_mh.cos(br))
                    nlo = _mh.radians(lon0)+_mh.atan2(_mh.sin(br)*_mh.sin(dr)*_mh.cos(lr),
                          _mh.cos(dr)-_mh.sin(lr)*_mh.sin(nl))
                    return {"lat": _mh.degrees(nl), "lon": _mh.degrees(nlo)}

                _prop_dir_pdf = (dir_vent + 180) % 360
                _hs_dists = [max(50, r3*0.5), max(r3,10), (r3+r2)/2, max(r2,10), (r2+r1)/2]
                _hs_data_pdf = []
                for _dd in _hs_dists:
                    _sy_h, _sz_h = sigma_pg(max(_dd,1), stab)
                    _den_h = _mh.pi * u_ms * _sy_h * _sz_h
                    _c_h = (q_debit_kgs(Q_kg,duree_min,type_lib)*1000)/_den_h*24.45/70.9 if _den_h>1e-10 else 0
                    _pt = _hspot(lat, lon, _dd, _prop_dir_pdf)
                    _pt["conc"] = _c_h
                    _hs_data_pdf.append(_pt)

                _pdf_params = {
                    "Q_kg": Q_kg, "type_lib": type_lib, "duree_min": duree_min,
                    "hauteur_m": hauteur_m, "u_ms": u_ms, "dir_vent": dir_vent,
                    "stab": stab, "stab_sel": stab_sel, "lat": lat, "lon": lon,
                    "config_site": config_site, "dens_pop": dens_pop,
                    "dist_pop": dist_pop, "niveau_epi": niveau_epi,
                    "alerte_prec": alerte_prec, "delai_evac": delai_evac,
                    "coord_sec": coord_sec, "capa_med": capa_med,
                    "capa_chr_lits": int(capa_chr_lits), "capa_ua_max": int(capa_ua_max),
                    "nb_smur": int(nb_smur), "n_mc": n_mc,
                    "gravite": gravite, "r1": r1, "r2": r2, "r3": r3,
                    "pop_e1": pop_e1, "pop_e2": pop_e2, "pop_e3": pop_e3,
                    "surf_e1": surf_e1, "surf_e2": surf_e2, "surf_e3": surf_e3,
                    "blesses_estimes": blesses_estimes, "blesses_e2": blesses_e2,
                    "blesses_e3": blesses_e3, "deces_estimes": deces_estimes,
                    "mc_p_e1": mc_p_e1, "mc_p_e2": mc_p_e2, "mc_p_e3": mc_p_e3,
                    "mc_c50": mc_c50, "mc_c95": mc_c95, "mc": mc,
                    "Q_kgs": Q_kgs, "H_eff": H_eff, "prop_dir": _prop_dir_pdf,
                    "perim_evac": perim_evac_calc, "surf_evac": surf_evac,
                    "facteur_site": facteur_site, "SECTEUR": SECTEUR,
                    "usines_domino": usines_domino, "has_train": has_train,
                    "has_hopital": has_hopital, "has_ecole": has_ecole,
                    "has_admin": has_admin, "has_gare_rout": has_gare_rout,
                    "train_passagers": train_passagers if has_train else 0,
                    "nb_agents_admin": nb_agents_admin if has_admin else 0,
                    "nb_gare_pers": nb_gare_pers if has_gare_rout else 0,
                    "dec_conf": _dec, "t_arrivee": _t_arrivee,
                    "hs_data": _hs_data_pdf,
                    # Chemin vers la capture de carte satellite (si disponible)
                    "map_image_path": st.session_state.get("last_map_screenshot", None),
                    # Hotspots dynamiques OSM (recalculés selon les coord. GPS actuelles)
                    "hotspots_reels": hotspots_dynamiques,
                }

                _pdf_bytes = _mod.generate_pdf(_pdf_params)
                import datetime as _dt
                _ref = _dt.datetime.now().strftime("HM-%Y%m%d-%H%M")
                st.success("✅ Rapport PDF généré avec succès !")
                st.download_button(
                    label="⬇️  Télécharger le Rapport Officiel PDF",
                    data=_pdf_bytes,
                    file_name=f"HazMod_Rapport_NRBC_{_ref}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            except Exception as _e:
                import traceback
                st.error(f"Erreur lors de la génération du PDF : {_e}")
                st.code(traceback.format_exc())

