"""
HazMod — Moteur de détection dynamique des hotspots
Sources (par ordre de priorité) :
  1. Base locale Maroc  : hazmod_maroc_hotspots.json  (instantané)
  2. Overpass API OSM   : requête temps réel           (30s, si disponible)
  3. Fallback géométrique : calcul directionnel        (toujours disponible)

La base locale est pré-chargée en mémoire au démarrage (< 1 ms par requête).
Overpass est interrogé uniquement si la base locale ne couvre pas la zone.
"""

import math, json, os, time, urllib.request, urllib.parse
from typing import Dict, List, Optional, Tuple

# ── Cache en mémoire ──────────────────────────────────────────────────────────
_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 300   # 5 min

# ── Base locale Maroc (chargée une seule fois) ───────────────────────────────
_LOCAL_DB: Optional[List[dict]] = None
_LOCAL_DB_PATH = None

def _find_db_path() -> Optional[str]:
    """Cherche le fichier hazmod_maroc_hotspots.json."""
    try:
        _here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        _here = os.getcwd()
    candidates = [
        os.path.join(_here, "hazmod_maroc_hotspots.json"),
        os.path.join(os.getcwd(), "hazmod_maroc_hotspots.json"),
        "hazmod_maroc_hotspots.json",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

def _load_local_db() -> List[dict]:
    """Charge la base locale en mémoire (appelée une seule fois)."""
    global _LOCAL_DB, _LOCAL_DB_PATH
    if _LOCAL_DB is not None:
        return _LOCAL_DB
    path = _find_db_path()
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            _LOCAL_DB = data.get("features", [])
            _LOCAL_DB_PATH = path
            return _LOCAL_DB
        except Exception:
            pass
    _LOCAL_DB = []
    return _LOCAL_DB

# ── Helpers géo ───────────────────────────────────────────────────────────────
def _dist_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(min(a, 1.0)))

def _zone(dist: float, r3: float, r2: float, r1: float) -> Optional[str]:
    if dist <= r3: return "ERPG-3"
    if dist <= r2: return "ERPG-2"
    if dist <= r1: return "ERPG-1"
    return None

# ── Mapping type OSM ─────────────────────────────────────────────────────────
_TYPE_META = {
    "hospital":        ("🏥", "CRITIQUE",  "Patients non mobiles — protocole Cl2 requis"),
    "clinic":          ("🏥", "CRITIQUE",  "Personnel soignant et patients exposés"),
    "doctors":         ("⚕️",  "ÉLEVÉ",    "Cabinet médical — patients à évacuer"),
    "pharmacy":        ("💊", "MODÉRÉ",   "Pharmacie — clientèle exposée"),
    "school":          ("🏫", "CRITIQUE",  "Enfants — sensibilité Cl2 ×2"),
    "kindergarten":    ("🏫", "CRITIQUE",  "Crèche — nourrissons très vulnérables"),
    "university":      ("🎓", "ÉLEVÉ",    "Étudiants — évacuation campus"),
    "college":         ("🎓", "ÉLEVÉ",    "Établissement supérieur"),
    "fire_station":    ("🚒", "ÉLEVÉ",    "Caserne — mobilisation intervention chimique"),
    "police":          ("🚓", "ÉLEVÉ",    "Commissariat — coordination évacuation"),
    "military":        ("🪖", "ÉLEVÉ",    "Zone militaire — protocole interne"),
    "bus_station":     ("🚌", "ÉLEVÉ",    "Gare routière — voyageurs à alerter"),
    "station":         ("🚉", "ÉLEVÉ",    "Gare ferroviaire — passagers bloqués"),
    "aerodrome":       ("✈️",  "CRITIQUE", "Aéroport — évacuation massive"),
    "fuel":            ("⛽", "ÉLEVÉ",    "Station essence — risque incendie"),
    "supermarket":     ("🛒", "ÉLEVÉ",    "Hypermarché — public dense"),
    "mall":            ("🛍️", "ÉLEVÉ",    "Centre commercial — confinement"),
    "marketplace":     ("🏪", "MODÉRÉ",   "Marché — vendeurs et clients"),
    "stadium":         ("🏟️", "CRITIQUE", "Stade — grande capacité"),
    "sports_centre":   ("🏋️", "MODÉRÉ",   "Centre sportif — usagers"),
    "place_of_worship":("🕌", "MODÉRÉ",   "Lieu de culte — fidèles rassemblés"),
    "townhall":        ("🏛️", "ÉLEVÉ",    "Mairie — agents et public"),
    "government":      ("🏛️", "ÉLEVÉ",    "Bâtiment officiel — agents"),
    "embassy":         ("🏛️", "CRITIQUE", "Ambassade — personnel diplomatique"),
    "prison":          ("🔒", "CRITIQUE", "Prison — personnes non évacuables"),
    "nursing_home":    ("🏠", "CRITIQUE", "Maison de retraite — personnes âgées"),
    "industrial":      ("🏭", "CRITIQUE", "Zone industrielle — effet domino potentiel"),
    "warehouse":       ("📦", "ÉLEVÉ",    "Entrepôt — personnels exposés"),
    "power":           ("⚡", "CRITIQUE", "Infrastructure électrique critique"),
    "water_works":     ("💧", "CRITIQUE", "Station traitement eau — vitale"),
    "hotel":           ("🏨", "MODÉRÉ",   "Hôtel — résidents et touristes"),
    # ── Établissements supplémentaires ─────────────────────────────────────
    "theatre":         ("🎭", "MODÉRÉ",   "Théâtre — spectateurs rassemblés"),
    "cinema":          ("🎬", "MODÉRÉ",   "Cinéma — public confiné"),
    "library":         ("📚", "MODÉRÉ",   "Bibliothèque — usagers présents"),
    "community_centre":("🏘️", "MODÉRÉ",   "Centre communautaire — population locale"),
    "social_centre":   ("🤝", "MODÉRÉ",   "Centre social — personnes fragiles"),
    "social_facility": ("♿", "CRITIQUE",  "Établissement médico-social — handicapés"),
    "courthouse":      ("⚖️",  "ÉLEVÉ",    "Tribunal — personnel et justiciables"),
    "post_office":     ("📮", "FAIBLE",   "Bureau de poste — file d'attente"),
    "bank":            ("🏦", "FAIBLE",   "Banque — clients présents"),
    "restaurant":      ("🍽️", "FAIBLE",   "Restaurant — clientèle exposée"),
    "bar":             ("🍺", "FAIBLE",   "Bar — clientèle exposée"),
    "nightclub":       ("🎵", "MODÉRÉ",   "Discothèque — clientèle dense nuit"),
    "charging_station":("🔌", "FAIBLE",   "Borne recharge — passage"),
    "college_secondary":("🏫","CRITIQUE", "Lycée — adolescents à évacuer"),
    "training":        ("📋", "MODÉRÉ",   "Centre de formation — stagiaires"),
    "conference_centre":("🏢","ÉLEVÉ",    "Centre de congrès — participants"),
    "office_government":("🏛️","ÉLEVÉ",    "Bureau administratif — agents publics"),
    "refugee":         ("⛺", "CRITIQUE",  "Camp réfugiés — population vulnérable"),
    "shelter":         ("🏚️", "CRITIQUE",  "Hébergement d'urgence — sans-abri"),
    "hospital_primary":("🏥", "CRITIQUE",  "CHU/CHR — centre de référence régional"),
    "blood_bank":      ("🩸", "ÉLEVÉ",    "Banque du sang — ressource critique"),
    "daycare":         ("👶", "CRITIQUE",  "Garderie — nourrissons très vulnérables"),
    "veterinary":      ("🐾", "FAIBLE",   "Vétérinaire — personnel et animaux"),
    "car_wash":        ("🚗", "FAIBLE",   "Station lavage — personnel exposé"),
    "recycling":       ("♻️",  "MODÉRÉ",   "Centre recyclage — ouvriers exposés"),
    "customs":         ("🛃", "MODÉRÉ",   "Douane — agents et voyageurs"),
    "border_control":  ("🛂", "MODÉRÉ",   "Contrôle frontière"),
    "lighthouse":      ("🔦", "FAIBLE",   "Phare — personnel technique"),
    "tower":           ("📡", "FAIBLE",   "Tour de communication — techniciens"),
    "water_tower":     ("💧", "ÉLEVÉ",    "Château d'eau — infrastructure vitale"),
    "pumping_station": ("⚙️",  "CRITIQUE", "Station pompage — eau potable"),
    "substation":      ("⚡", "CRITIQUE",  "Sous-station électrique — réseau"),
    "transformer":     ("🔌", "ÉLEVÉ",    "Transformateur — réseau électrique"),
    "gas_station":     ("⛽", "ÉLEVÉ",    "Station gaz — risque explosion Cl2"),
    "oil_refinery":    ("🏭", "CRITIQUE",  "Raffinerie — effet domino chimique"),
    "chemical":        ("⚗️",  "CRITIQUE",  "Usine chimique — réaction possible Cl2"),
    "cold_storage":    ("❄️",  "MODÉRÉ",   "Entrepôt frigorifique — personnel"),
    "logistics":       ("📦", "MODÉRÉ",   "Centre logistique — travailleurs"),
    "port":            ("⚓", "ÉLEVÉ",    "Port — marins et dockers"),
    "ferry_terminal":  ("⛴️",  "ÉLEVÉ",    "Terminal ferry — passagers"),
    "bus_stop":        ("🚏", "MODÉRÉ",   "Arrêt bus — passagers en attente"),
    "metro_station":   ("🚇", "CRITIQUE",  "Station métro — concentration importante"),
    "tram_stop":       ("🚊", "MODÉRÉ",   "Arrêt tramway — usagers"),
    "park":            ("🌳", "FAIBLE",   "Parc public — promeneurs"),
    "beach":           ("🏖️", "MODÉRÉ",   "Plage — baigneurs et familles"),
    "camp_site":       ("⛺", "MODÉRÉ",   "Camping — campeurs exposés"),
    "sports_hall":     ("🏋️", "MODÉRÉ",   "Salle de sport — sportifs"),
    "swimming_pool":   ("🏊", "MODÉRÉ",   "Piscine — nageurs et enfants"),
    "museum":          ("🏛️", "MODÉRÉ",   "Musée — visiteurs et personnel"),
    "art_gallery":     ("🖼️",  "FAIBLE",   "Galerie d'art — visiteurs"),
}
_DEFAULT_META = ("📍", "MODÉRÉ", "Établissement identifié")

# ── Requête base locale ───────────────────────────────────────────────────────
def _query_local(lat: float, lon: float,
                 r3: float, r2: float, r1: float) -> Tuple[Dict, int]:
    """
    Interroge la base locale Maroc.
    Retourne (zones_dict, nombre_total_trouvés).
    Rapide : O(n) sur ~120-500 entrées.
    """
    db = _load_local_db()
    zones: Dict[str, List[dict]] = {"ERPG-3": [], "ERPG-2": [], "ERPG-1": []}

    for rec in db:
        d = _dist_m(lat, lon, rec["lat"], rec["lon"])
        z = _zone(d, r3, r2, r1)
        if z is None:
            continue
        icon, priority, risk = _TYPE_META.get(rec.get("type",""), _DEFAULT_META)
        # Utiliser les données de la base (plus précises) si disponibles
        zones[z].append({
            "name":     rec["name"],
            "type":     rec.get("type", "unknown"),
            "icon":     rec.get("icon", icon),
            "priority": rec.get("priority", priority),
            "risk":     rec.get("risk", risk),
            "coords":   [rec["lat"], rec["lon"]],
            "dist":     int(d),
            "zone":     z,
            "city":     rec.get("city", "—"),
            "source":   "HazMod Maroc DB",
        })

    total = sum(len(v) for v in zones.values())

    # Trier par distance
    for z in zones:
        zones[z].sort(key=lambda x: x["dist"])
        zones[z] = zones[z][:12]  # max 12 par zone

    return zones, total

# ── Requête Overpass (temps réel) ─────────────────────────────────────────────
_OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

def _query_overpass(lat: float, lon: float,
                    r3: float, r2: float, r1: float) -> Optional[Dict]:
    """Requête Overpass temps réel. Retourne None si indisponible."""
    radius = int(r1 * 1.10) + 50
    query = f"""
[out:json][timeout:28];
(
  node["amenity"~"hospital|clinic|school|kindergarten|university|college|fire_station|police|pharmacy|bus_station|fuel|place_of_worship|social_facility|nursing_home|townhall|embassy|prison|marketplace|stadium|sports_centre|theatre|cinema|library|community_centre|social_centre|courthouse|post_office|bank|restaurant|bar|nightclub|conference_centre|refugee|shelter|blood_bank|daycare|veterinary|recycling|customs|border_control|swimming_pool|arts_centre|museum"](around:{radius},{lat},{lon});
  node["shop"~"supermarket|mall"](around:{radius},{lat},{lon});
  node["aeroway"~"aerodrome|terminal"](around:{radius},{lat},{lon});
  node["railway"~"station|halt"](around:{radius},{lat},{lon});
  node["military"](around:{radius},{lat},{lon});
  node["landuse"="industrial"]["name"](around:{radius},{lat},{lon});
  node["office"~"government|administration|diplomatic|ngo|association"](around:{radius},{lat},{lon});
  node["tourism"~"hotel|hostel|camp_site|museum|theme_park"](around:{radius},{lat},{lon});
  node["leisure"~"stadium|sports_centre|swimming_pool|park|beach_resort"](around:{radius},{lat},{lon});
  node["man_made"~"water_tower|pumping_station|water_works|tower|lighthouse"](around:{radius},{lat},{lon});
  node["power"~"substation|transformer|plant"](around:{radius},{lat},{lon});
  node["public_transport"~"station|stop_position"](around:{radius},{lat},{lon});
  way["office"~"government|administration"](around:{radius},{lat},{lon});
  way["tourism"~"hotel|museum"](around:{radius},{lat},{lon});
  way["leisure"~"stadium|sports_centre|swimming_pool"](around:{radius},{lat},{lon});
  way["amenity"~"hospital|clinic|school|kindergarten|university|college|fire_station|police|stadium|theatre|cinema|library|community_centre|courthouse|conference_centre|museum|swimming_pool|arts_centre"](around:{radius},{lat},{lon});
  way["landuse"="industrial"]["name"](around:{radius},{lat},{lon});
  way["aeroway"="aerodrome"](around:{radius},{lat},{lon});
);
out center tags;
""".strip()

    encoded = urllib.parse.urlencode({"data": query}).encode("utf-8")
    for ep in _OVERPASS_ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=encoded, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent":   "HazMod-DSD/2.0 (direction.securite@interieur.gov.ma)",
                "Accept":       "application/json",
            })
            with urllib.request.urlopen(req, timeout=28) as resp:
                elements = json.loads(resp.read().decode()).get("elements", [])

            zones: Dict[str, List[dict]] = {"ERPG-3": [], "ERPG-2": [], "ERPG-1": []}
            seen: set = set()
            for el in elements:
                tags = el.get("tags", {})
                name = (tags.get("name:fr") or tags.get("name") or
                        tags.get("name:ar") or "").strip()
                if not name or name.lower() in seen:
                    continue
                seen.add(name.lower())
                if el["type"] == "node":
                    elat, elon = el.get("lat"), el.get("lon")
                else:
                    c = el.get("center", {})
                    elat, elon = c.get("lat"), c.get("lon")
                if not elat:
                    continue
                d = _dist_m(lat, lon, elat, elon)
                z = _zone(d, r3, r2, r1)
                if not z:
                    continue
                loc_type = (tags.get("amenity") or tags.get("building") or
                            tags.get("shop") or tags.get("leisure") or
                            tags.get("aeroway") or tags.get("landuse") or
                            tags.get("railway") or tags.get("military") or "unknown")
                icon, priority, risk = _TYPE_META.get(loc_type, _DEFAULT_META)
                zones[z].append({
                    "name":     name[:55],
                    "type":     loc_type,
                    "icon":     icon,
                    "priority": priority,
                    "risk":     risk,
                    "coords":   [round(elat,5), round(elon,5)],
                    "dist":     int(d),
                    "zone":     z,
                    "city":     tags.get("addr:city","—"),
                    "source":   "OpenStreetMap temps réel",
                })

            for z in zones:
                zones[z].sort(key=lambda x: x["dist"])
                zones[z] = zones[z][:12]
            return zones
        except Exception:
            continue
    return None

# ── Fallback géométrique ──────────────────────────────────────────────────────
def _fallback_geo(lat: float, lon: float,
                  r3: float, r2: float, r1: float,
                  prop_dir: float) -> Dict:
    """Hotspots géométriques si aucune donnée disponible."""
    def mv(dist_m_v, bearing):
        R = 6371000.0
        lr = math.radians(lat); br = math.radians(bearing); dr = dist_m_v / R
        nl = math.asin(math.sin(lr)*math.cos(dr)+math.cos(lr)*math.sin(dr)*math.cos(br))
        nlo = math.radians(lon) + math.atan2(
            math.sin(br)*math.sin(dr)*math.cos(lr),
            math.cos(dr)-math.sin(lr)*math.sin(nl))
        return [round(math.degrees(nl),5), round(math.degrees(nlo),5)]

    pd = prop_dir
    return {
        "ERPG-3": [
            {"name":"Zone industrielle proximate","icon":"🏭","priority":"CRITIQUE",
             "risk":"Effet domino potentiel","coords":mv(int(r3*0.5),pd),
             "dist":int(r3*0.5),"zone":"ERPG-3","source":"Géométrique"},
            {"name":"Infrastructure routière","icon":"🛣️","priority":"ÉLEVÉ",
             "risk":"Trafic bloqué","coords":mv(int(r3*0.85),(pd+30)%360),
             "dist":int(r3*0.85),"zone":"ERPG-3","source":"Géométrique"},
        ],
        "ERPG-2": [
            {"name":"Établissement de santé estimé","icon":"🏥","priority":"CRITIQUE",
             "risk":"Population vulnérable","coords":mv(int((r3+r2)*0.4),pd),
             "dist":int((r3+r2)*0.4),"zone":"ERPG-2","source":"Géométrique"},
            {"name":"Zone résidentielle","icon":"🏘️","priority":"ÉLEVÉ",
             "risk":"Population exposée","coords":mv(int(r2*0.7),(pd-20)%360),
             "dist":int(r2*0.7),"zone":"ERPG-2","source":"Géométrique"},
            {"name":"Établissement scolaire estimé","icon":"🏫","priority":"CRITIQUE",
             "risk":"Enfants — Cl2 ×2","coords":mv(int(r2*0.85),(pd+25)%360),
             "dist":int(r2*0.85),"zone":"ERPG-2","source":"Géométrique"},
        ],
        "ERPG-1": [
            {"name":"Centre hospitalier estimé","icon":"🏥","priority":"ÉLEVÉ",
             "risk":"Plan Blanc potentiel","coords":mv(int(r2+250),pd),
             "dist":int(r2+250),"zone":"ERPG-1","source":"Géométrique"},
            {"name":"Centre commercial estimé","icon":"🛒","priority":"ÉLEVÉ",
             "risk":"Public dense","coords":mv(int(r2+500),(pd-15)%360),
             "dist":int(r2+500),"zone":"ERPG-1","source":"Géométrique"},
            {"name":"Équipement sportif estimé","icon":"🏟️","priority":"MODÉRÉ",
             "risk":"Grande capacité","coords":mv(int(r1*0.75),(pd+12)%360),
             "dist":int(r1*0.75),"zone":"ERPG-1","source":"Géométrique"},
            {"name":"Gare / Transport estimé","icon":"🚌","priority":"ÉLEVÉ",
             "risk":"Voyageurs exposés","coords":mv(int(r1*0.92),(pd-10)%360),
             "dist":int(r1*0.92),"zone":"ERPG-1","source":"Géométrique"},
        ],
    }

# ── Point d'entrée principal ──────────────────────────────────────────────────
def get_hotspots(lat: float, lon: float,
                 r3: float, r2: float, r1: float,
                 prop_dir: float,
                 force_refresh: bool = False) -> Dict[str, List[dict]]:
    """
    Retourne les hotspots pour (lat, lon) classés par zone ERPG.

    Stratégie :
      1. Cache 5 min (évite recalcul à chaque rerun Streamlit)
      2. Base locale Maroc (instantané, ~120 entrées vérifiées)
      3. Si zone non couverte OU hors Maroc → Overpass temps réel
      4. Fallback géométrique si tout échoue

    Args :
        lat, lon    : coordonnées GPS de la source
        r3, r2, r1  : rayons ERPG-3, ERPG-2, ERPG-1 en mètres
        prop_dir    : direction de propagation (degrés)
        force_refresh : forcer nouvelle requête
    """
    cache_key = f"{lat:.3f}_{lon:.3f}_{int(r1)}"
    now = time.time()

    # Cache
    if not force_refresh and cache_key in _CACHE:
        if now - _CACHE[cache_key]["ts"] < _CACHE_TTL:
            return _CACHE[cache_key]["data"]

    # 1. Base locale Maroc
    local_zones, local_count = _query_local(lat, lon, r3, r2, r1)

    # Maroc bounding box : lat [20.7-36.0], lon [-17.1 à -1.0]
    IS_MOROCCO = (20.7 <= lat <= 36.0) and (-17.1 <= lon <= -1.0)

    if local_count > 0 and IS_MOROCCO:
        # La base locale couvre — utiliser directement
        _CACHE[cache_key] = {"ts": now, "data": local_zones,
                              "source": "DB Maroc locale"}
        return local_zones

    # 2. Overpass temps réel (zones non couvertes ou hors Maroc)
    overpass_result = _query_overpass(lat, lon, r3, r2, r1)
    if overpass_result:
        # Fusionner avec la base locale si Maroc
        if IS_MOROCCO and local_count > 0:
            merged: Dict[str, List[dict]] = {"ERPG-3":[],"ERPG-2":[],"ERPG-1":[]}
            seen_names = set()
            for z in ["ERPG-3","ERPG-2","ERPG-1"]:
                for item in local_zones.get(z,[]) + overpass_result.get(z,[]):
                    k = item["name"].lower()
                    if k not in seen_names:
                        seen_names.add(k)
                        merged[z].append(item)
                merged[z].sort(key=lambda x: x["dist"])
                merged[z] = merged[z][:12]
            _CACHE[cache_key] = {"ts": now, "data": merged,
                                  "source": "DB Maroc + OSM temps réel"}
            return merged

        _CACHE[cache_key] = {"ts": now, "data": overpass_result,
                              "source": "OSM temps réel"}
        return overpass_result

    # 3. Fallback géométrique
    if local_count > 0:
        _CACHE[cache_key] = {"ts": now, "data": local_zones,
                              "source": "DB Maroc locale (partielle)"}
        return local_zones

    result = _fallback_geo(lat, lon, r3, r2, r1, prop_dir)
    _CACHE[cache_key] = {"ts": now, "data": result, "source": "Géométrique"}
    return result

def get_db_stats() -> dict:
    """Retourne des statistiques sur la base locale."""
    db = _load_local_db()
    from collections import Counter
    return {
        "total":        len(db),
        "path":         _LOCAL_DB_PATH or "Non trouvé",
        "by_type":      dict(Counter(r.get("type","?") for r in db)),
        "by_priority":  dict(Counter(r.get("priority","?") for r in db)),
        "cache_entries": len(_CACHE),
    }
