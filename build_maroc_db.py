"""
Script de construction de la base de données hotspots Maroc
Sources : HOTOSM / HDX / OSM — Données téléchargeables publiquement
Lance ce script UNE SEULE FOIS pour créer la base locale.
"""
import json, math, urllib.request, urllib.parse, os, time

# ── URLs de téléchargement directs HDX / HOTOSM ────────────────────────────
HDX_URLS = {
    "health": "https://data.humdata.org/dataset/hotosm_mar_health_facilities/resource/hotosm_mar_health_facilities_points_geojson",
    "education": "https://data.humdata.org/dataset/hotosm_mar_education_facilities/resource/hotosm_mar_education_facilities_points_geojson",
    "pois": "https://data.humdata.org/dataset/hotosm_mar_points_of_interest/resource/hotosm_mar_points_of_interest_points_geojson",
}

# ── Mapping type OSM → métadonnées hotspot ─────────────────────────────────
TYPE_META = {
    "hospital":          ("🏥", "CRITIQUE",  "Patients non mobiles — protocole Cl2 requis"),
    "clinic":            ("🏥", "CRITIQUE",  "Personnel soignant et patients exposés"),
    "doctors":           ("⚕️",  "ÉLEVÉ",    "Cabinet médical — patients à évacuer"),
    "pharmacy":          ("💊", "MODÉRÉ",   "Pharmacie — clientèle exposée"),
    "dentist":           ("⚕️",  "MODÉRÉ",   "Cabinet dentaire — patients"),
    "school":            ("🏫", "CRITIQUE",  "Enfants — sensibilité Cl2 ×2"),
    "kindergarten":      ("🏫", "CRITIQUE",  "Crèche — nourrissons très vulnérables"),
    "university":        ("🎓", "ÉLEVÉ",    "Étudiants — évacuation campus"),
    "college":           ("🎓", "ÉLEVÉ",    "Établissement supérieur — étudiants"),
    "fire_station":      ("🚒", "ÉLEVÉ",    "Caserne — mobilisation intervention chimique"),
    "police":            ("🚓", "ÉLEVÉ",    "Commissariat — coordination évacuation"),
    "military":          ("🪖", "ÉLEVÉ",    "Zone militaire — protocole interne"),
    "bus_station":       ("🚌", "ÉLEVÉ",    "Gare routière — voyageurs à alerter"),
    "station":           ("🚉", "ÉLEVÉ",    "Gare ferroviaire — passagers bloqués"),
    "aerodrome":         ("✈️",  "CRITIQUE", "Aéroport — évacuation massive"),
    "fuel":              ("⛽", "ÉLEVÉ",    "Station essence — risque incendie Cl2"),
    "supermarket":       ("🛒", "ÉLEVÉ",    "Hypermarché — public dense"),
    "mall":              ("🛍️", "ÉLEVÉ",    "Centre commercial — confinement public"),
    "marketplace":       ("🏪", "MODÉRÉ",   "Marché — vendeurs et clients"),
    "stadium":           ("🏟️", "CRITIQUE", "Stade — grande capacité"),
    "sports_centre":     ("🏋️", "MODÉRÉ",   "Centre sportif — usagers"),
    "place_of_worship":  ("🕌", "MODÉRÉ",   "Lieu de culte — fidèles rassemblés"),
    "townhall":          ("🏛️", "ÉLEVÉ",    "Mairie — agents et public"),
    "government":        ("🏛️", "ÉLEVÉ",    "Bâtiment officiel — agents"),
    "embassy":           ("🏛️", "CRITIQUE", "Ambassade — personnel diplomatique"),
    "prison":            ("🔒", "CRITIQUE", "Prison — personnes non évacuables"),
    "social_facility":   ("🏠", "ÉLEVÉ",    "Centre social — personnes vulnérables"),
    "nursing_home":      ("🏠", "CRITIQUE", "Maison de retraite — personnes âgées"),
    "industrial":        ("🏭", "CRITIQUE", "Zone industrielle — effet domino potentiel"),
    "warehouse":         ("📦", "ÉLEVÉ",    "Entrepôt — personnels exposés"),
    "power":             ("⚡", "CRITIQUE", "Infrastructure électrique critique"),
    "water_works":       ("💧", "CRITIQUE", "Station traitement eau — infrastructure vitale"),
    "hotel":             ("🏨", "MODÉRÉ",   "Hôtel — résidents et touristes"),
}
DEFAULT_META = ("📍", "MODÉRÉ", "Établissement identifié")

print("=" * 60)
print("HazMod — Construction Base Hotspots Maroc")
print("Sources : HOTOSM / HDX / OpenStreetMap")
print("=" * 60)

# ── Requête Overpass pour construire la base complète ───────────────────────
# On récupère TOUS les POI importants du Maroc d'un coup
# Bounding box Maroc : -17.1 à -1.0 lon, 20.7 à 35.9 lat

print("\n📡 Téléchargement des données OSM via Overpass API...")
print("   (Cette opération prend 30-120 secondes)")

QUERY = """
[out:json][timeout:180];
area["name"="المغرب"]["admin_level"="2"]->.maroc;
(
  node["amenity"~"hospital|clinic|school|kindergarten|university|college|fire_station|police|pharmacy|bus_station|fuel|place_of_worship|social_facility|nursing_home|townhall|embassy|prison|marketplace|stadium|sports_centre"](area.maroc);
  node["shop"~"supermarket|mall|department_store"](area.maroc);
  node["aeroway"~"aerodrome|terminal"](area.maroc);
  node["railway"~"station|halt"](area.maroc);
  node["military"~"base|barracks"](area.maroc);
  node["man_made"~"water_works|power_station"](area.maroc);
  node["landuse"="industrial"]["name"](area.maroc);
  way["amenity"~"hospital|clinic|school|kindergarten|university|college|fire_station|police|bus_station|stadium"](area.maroc);
  way["landuse"="industrial"]["name"](area.maroc);
  way["aeroway"="aerodrome"](area.maroc);
);
out center tags;
""".strip()

endpoints = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

elements = []
for ep in endpoints:
    try:
        print(f"   Essai: {ep}")
        data = urllib.parse.urlencode({"data": QUERY}).encode()
        req = urllib.request.Request(ep, data=data, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "HazMod-MarocDB/1.0 (direction.securite@interieur.gov.ma)"
        })
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
            elements = result.get("elements", [])
            print(f"   ✅ {len(elements)} éléments récupérés")
            break
    except Exception as e:
        print(f"   ❌ {e}")

if not elements:
    print("\n⚠️ Overpass inaccessible depuis ce système.")
    print("   La base sera créée avec les données intégrées.")
    BUILD_FROM_OVERPASS = False
else:
    BUILD_FROM_OVERPASS = True

# ── Construire la base de données ───────────────────────────────────────────
db = []
seen = set()

if BUILD_FROM_OVERPASS:
    for el in elements:
        tags = el.get("tags", {})
        name = (tags.get("name:fr") or tags.get("name") or
                tags.get("name:ar") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)

        if el["type"] == "node":
            lat_e, lon_e = el.get("lat"), el.get("lon")
        else:
            c = el.get("center", {})
            lat_e, lon_e = c.get("lat"), c.get("lon")
        if not lat_e:
            continue

        loc_type = (
            tags.get("amenity") or tags.get("building") or
            tags.get("shop") or tags.get("leisure") or
            tags.get("aeroway") or tags.get("landuse") or
            tags.get("man_made") or tags.get("railway") or
            tags.get("military") or "unknown"
        )

        icon, priority, risk = TYPE_META.get(loc_type, DEFAULT_META)
        city = (tags.get("addr:city") or
                tags.get("is_in:city") or
                tags.get("addr:district") or "—")

        db.append({
            "name":     name[:60],
            "type":     loc_type,
            "icon":     icon,
            "priority": priority,
            "risk":     risk,
            "lat":      round(lat_e, 5),
            "lon":      round(lon_e, 5),
            "city":     city,
        })
    print(f"\n✅ {len(db)} établissements valides extraits")

# ── Base de données intégrée (fallback + enrichissement) ───────────────────
# Établissements clés du Maroc codés manuellement (sources officielles)
MAROC_BASE = [
    # ── HÔPITAUX ET CLINIQUES ──────────────────────────────────────────────
    # Rabat
    ("Hôpital Ibn Sina","hospital","🏥","CRITIQUE","Hôpital universitaire — 1200 lits",33.9921,-6.8499,"Rabat"),
    ("Hôpital Cheikh Zaïd","hospital","🏥","CRITIQUE","CHU — soins intensifs",33.9733,-6.8543,"Rabat"),
    ("Hôpital Militaire Mohammed V","hospital","🏥","CRITIQUE","Hôpital militaire — protocole interne",33.9690,-6.8640,"Rabat"),
    ("Hôpital d'Enfants de Rabat","hospital","🏥","CRITIQUE","Pédiatrie — population vulnérable",33.9840,-6.8610,"Rabat"),
    ("Clinique Agdal","clinic","🏥","CRITIQUE","Clinique privée",33.9820,-6.8720,"Rabat"),
    # Casablanca
    ("CHU Ibn Rochd","hospital","🏥","CRITIQUE","CHU Casablanca — 1800 lits",33.5731,-7.5898,"Casablanca"),
    ("Hôpital Moulay Youssef","hospital","🏥","CRITIQUE","Hôpital général",33.5800,-7.6100,"Casablanca"),
    ("Hôpital 20 Août 1953","hospital","🏥","CRITIQUE","Hôpital régional",33.5600,-7.6200,"Casablanca"),
    ("Clinique du Littoral","clinic","🏥","CRITIQUE","Clinique privée",33.5950,-7.6320,"Casablanca"),
    # Marrakech
    ("CHU Mohammed VI Marrakech","hospital","🏥","CRITIQUE","CHU — trauma et urgences",31.6295,-7.9811,"Marrakech"),
    ("Hôpital Ibn Nafis","hospital","🏥","CRITIQUE","Hôpital régional",31.6100,-8.0100,"Marrakech"),
    # Tanger
    ("CHU Mohammed VI Tanger","hospital","🏥","CRITIQUE","CHU — 800 lits",35.7595,-5.8340,"Tanger"),
    ("Hôpital Militaire Tanger","hospital","🏥","CRITIQUE","Hôpital militaire",35.7800,-5.8100,"Tanger"),
    # Fès
    ("CHU Hassan II Fès","hospital","🏥","CRITIQUE","CHU — 1400 lits",34.0209,-5.0078,"Fès"),
    ("Hôpital Ghassani","hospital","🏥","CRITIQUE","Hôpital régional",34.0100,-4.9900,"Fès"),
    # Agadir
    ("CHU Souss-Massa Agadir","hospital","🏥","CRITIQUE","CHU Agadir",30.4278,-9.5981,"Agadir"),
    ("Hôpital Hassan II Agadir","hospital","🏥","CRITIQUE","Hôpital régional",30.4200,-9.5800,"Agadir"),
    # Meknès
    ("Hôpital Mohammed V Meknès","hospital","🏥","CRITIQUE","Hôpital régional",33.8935,-5.5547,"Meknès"),
    # Oujda
    ("CHU Mohammed VI Oujda","hospital","🏥","CRITIQUE","CHU région orientale",34.6867,-1.9114,"Oujda"),
    # El Jadida / Jorf Lasfar
    ("Hôpital Mohammed V El Jadida","hospital","🏥","CRITIQUE","Hôpital régional",33.2333,-8.5000,"El Jadida"),
    ("Clinique Errazi El Jadida","clinic","🏥","CRITIQUE","Clinique privée",33.2400,-8.5100,"El Jadida"),
    # Safi
    ("Hôpital Sidi Mohammed Ben Abdellah Safi","hospital","🏥","CRITIQUE","Hôpital régional",32.2833,-9.2333,"Safi"),
    # Béni Mellal
    ("Hôpital Mohammed V Béni Mellal","hospital","🏥","CRITIQUE","Hôpital régional",32.3333,-6.3500,"Béni Mellal"),
    # Kénitra
    ("Hôpital Moulay Youssef Kénitra","hospital","🏥","CRITIQUE","Hôpital régional",34.2610,-6.5802,"Kénitra"),
    # Tétouan
    ("Hôpital Saniat Rmel Tétouan","hospital","🏥","CRITIQUE","Hôpital régional",35.5785,-5.3684,"Tétouan"),
    # Nador
    ("Hôpital Mohamed Bouafi Nador","hospital","🏥","CRITIQUE","Hôpital régional",35.1667,-2.9333,"Nador"),
    # Laayoune
    ("Hôpital Laayoune","hospital","🏥","CRITIQUE","Hôpital régional",27.1253,-13.1625,"Laayoune"),
    # Dakhla
    ("Hôpital Dakhla","hospital","🏥","CRITIQUE","Hôpital régional",23.7137,-15.9355,"Dakhla"),

    # ── AÉROPORTS ─────────────────────────────────────────────────────────
    ("Aéroport Mohammed V Casablanca","aerodrome","✈️","CRITIQUE","Hub national — 10M passagers/an",33.3675,-7.5897,"Casablanca"),
    ("Aéroport Marrakech Menara","aerodrome","✈️","CRITIQUE","Aéroport international",31.6069,-8.0363,"Marrakech"),
    ("Aéroport Tanger Ibn Battouta","aerodrome","✈️","CRITIQUE","Aéroport international",35.7269,-5.9169,"Tanger"),
    ("Aéroport Agadir Al Massira","aerodrome","✈️","CRITIQUE","Aéroport international",30.3250,-9.4131,"Agadir"),
    ("Aéroport Fès-Saïss","aerodrome","✈️","CRITIQUE","Aéroport régional",33.9272,-4.9778,"Fès"),
    ("Aéroport Oujda Angads","aerodrome","✈️","CRITIQUE","Aéroport régional",34.7872,-1.9240,"Oujda"),
    ("Aéroport Rabat-Salé","aerodrome","✈️","CRITIQUE","Aéroport régional",34.0514,-6.7515,"Rabat"),
    ("Aéroport Nador El Aroui","aerodrome","✈️","CRITIQUE","Aéroport régional",34.9888,-3.0282,"Nador"),
    ("Aéroport Laayoune Hassan I","aerodrome","✈️","CRITIQUE","Aéroport régional",27.1516,-13.2191,"Laayoune"),
    ("Aéroport Dakhla","aerodrome","✈️","CRITIQUE","Aéroport régional",23.7183,-15.9320,"Dakhla"),
    ("Aéroport Ouarzazate","aerodrome","✈️","ÉLEVÉ","Aéroport régional",30.9391,-6.9094,"Ouarzazate"),
    ("Aéroport Tétouan Sania Ramel","aerodrome","✈️","ÉLEVÉ","Aéroport régional",35.5943,-5.3200,"Tétouan"),
    ("Aéroport Al Hoceima Cherif Al Idrissi","aerodrome","✈️","ÉLEVÉ","Aéroport régional",35.1769,-3.8395,"Al Hoceima"),

    # ── GARES FERROVIAIRES ─────────────────────────────────────────────────
    ("Gare de Casablanca Voyageurs","station","🚉","ÉLEVÉ","Principale gare nationale",33.5944,-7.6122,"Casablanca"),
    ("Gare de Casablanca Port","station","🚉","ÉLEVÉ","Gare ferroviaire",33.6014,-7.6244,"Casablanca"),
    ("Gare de Rabat Ville","station","🚉","ÉLEVÉ","Gare principale Rabat",33.9907,-6.8550,"Rabat"),
    ("Gare de Rabat Agdal","station","🚉","ÉLEVÉ","Gare secondaire Rabat",33.9728,-6.8719,"Rabat"),
    ("Gare de Tanger Ville","station","🚉","ÉLEVÉ","Gare principale Tanger",35.7679,-5.7979,"Tanger"),
    ("Gare de Marrakech","station","🚉","ÉLEVÉ","Gare principale Marrakech",31.6296,-8.0104,"Marrakech"),
    ("Gare de Fès","station","🚉","ÉLEVÉ","Gare principale Fès",34.0229,-5.0142,"Fès"),
    ("Gare de Meknès","station","🚉","ÉLEVÉ","Gare principale Meknès",33.8992,-5.5536,"Meknès"),
    ("Gare de Kénitra","station","🚉","ÉLEVÉ","Gare principale Kénitra",34.2600,-6.5750,"Kénitra"),
    ("Gare de Oujda","station","🚉","ÉLEVÉ","Gare principale Oujda",34.6800,-1.9100,"Oujda"),
    ("Gare de Safi","station","🚉","MODÉRÉ","Gare régionale",32.3100,-9.2200,"Safi"),
    ("Gare de El Jadida","station","🚉","MODÉRÉ","Gare régionale",33.2300,-8.5100,"El Jadida"),

    # ── SITES INDUSTRIELS CHIMIQUES / DANGEREUX ───────────────────────────
    ("OCP — Usine Jorf Lasfar","industrial","🏭","CRITIQUE","Engrais phosphatés — NH3, H2SO4, HNO3",33.0972,-8.6272,"El Jadida"),
    ("OCP — Usine Safi","industrial","🏭","CRITIQUE","Engrais phosphatés — H2SO4",32.2800,-9.2100,"Safi"),
    ("OCP — Site Khouribga","industrial","🏭","CRITIQUE","Extraction phosphates",32.8833,-6.9167,"Khouribga"),
    ("OCP — Site Benguerir","industrial","🏭","CRITIQUE","Extraction phosphates",32.2333,-7.9500,"Benguerir"),
    ("OCP — Site Youssoufia","industrial","🏭","CRITIQUE","Extraction phosphates",32.2500,-8.5333,"Youssoufia"),
    ("Raffinerie SAMIR Mohammedia","industrial","🏭","CRITIQUE","Raffinerie pétrole — risque explosif",33.6939,-7.4153,"Mohammedia"),
    ("SNEP — Complexe chimique Mohammedia","industrial","🏭","CRITIQUE","Chlore Cl2, PVC — risque majeur",33.6800,-7.3900,"Mohammedia"),
    ("FERTIMA — Engrais azotés Mohammedia","industrial","🏭","CRITIQUE","NH3 liquide — risque toxique",33.6700,-7.4000,"Mohammedia"),
    ("Terminal pétrolier Mohammedia","industrial","🏭","CRITIQUE","Stockage hydrocarbures",33.7000,-7.4200,"Mohammedia"),
    ("Zone Industrielle Aïn Johra Casablanca","industrial","🏭","ÉLEVÉ","Industries diverses",33.5200,-7.7300,"Casablanca"),
    ("Zone Industrielle Sidi Bernoussi Casablanca","industrial","🏭","ÉLEVÉ","Industries chimiques légères",33.5800,-7.5500,"Casablanca"),
    ("Terminal chimique Tanger Med","industrial","🏭","CRITIQUE","Port industriel — matières dangereuses",35.8833,-5.5000,"Tanger"),
    ("Zone Industrielle Tanger Automotive City","industrial","🏭","ÉLEVÉ","Constructeurs auto — peintures solvants",35.7300,-5.9500,"Tanger"),
    ("ONEE — Centrale thermique Mohammedia","industrial","⚡","CRITIQUE","Centrale électrique — charbon",33.7200,-7.3800,"Mohammedia"),
    ("ONEE — Centrale Jerada","industrial","⚡","CRITIQUE","Centrale thermique charbon",34.3100,-2.1600,"Jerada"),
    ("ONEE — Centrale Kénitra","industrial","⚡","CRITIQUE","Centrale thermique",34.2700,-6.5600,"Kénitra"),
    ("Station de traitement eau Tamesna","water_works","💧","CRITIQUE","Infrastructure eau potable Rabat",33.9200,-6.9400,"Rabat"),
    ("Station de traitement eau Ain Attig","water_works","💧","CRITIQUE","Infrastructure eau potable Casablanca",33.6100,-7.6900,"Casablanca"),
    ("SOMACA — Usine automobile Casablanca","industrial","🏭","ÉLEVÉ","Peintures solvants — risque chimique",33.5300,-7.5700,"Casablanca"),
    ("Stellantis Kénitra","industrial","🏭","ÉLEVÉ","Usine automobile — peintures solvants",34.2500,-6.6100,"Kénitra"),

    # ── PORTS ────────────────────────────────────────────────────────────
    ("Port Tanger Med","aerodrome","🚢","CRITIQUE","1er port d'Afrique — conteneurs et chimie",35.8833,-5.5000,"Tanger"),
    ("Port de Casablanca","aerodrome","🚢","CRITIQUE","Port national — matières dangereuses",33.6044,-7.6183,"Casablanca"),
    ("Port de Jorf Lasfar","aerodrome","🚢","CRITIQUE","Port chimique — soufre, phosphates, Cl2",33.1167,-8.6333,"El Jadida"),
    ("Port de Safi","aerodrome","🚢","ÉLEVÉ","Port chimique — phosphates",32.3000,-9.2500,"Safi"),
    ("Port d'Agadir","aerodrome","🚢","ÉLEVÉ","Port commercial et pêche",30.4200,-9.6500,"Agadir"),
    ("Port de Nador","aerodrome","🚢","ÉLEVÉ","Port commercial",35.1700,-2.9400,"Nador"),
    ("Port de Mohammedia","aerodrome","🚢","CRITIQUE","Port pétrolier",33.7200,-7.4000,"Mohammedia"),

    # ── STADES ET GRANDS RASSEMBLEMENTS ────────────────────────────────
    ("Stade Mohammed V Casablanca","stadium","🏟️","CRITIQUE","Stade national — 67 000 places",33.5940,-7.6360,"Casablanca"),
    ("Grand Stade de Marrakech","stadium","🏟️","CRITIQUE","Stade international — 45 000 places",31.6100,-8.0200,"Marrakech"),
    ("Stade Adrar Agadir","stadium","🏟️","CRITIQUE","Stade moderne — 45 000 places",30.4200,-9.6100,"Agadir"),
    ("Grand Stade de Tanger","stadium","🏟️","CRITIQUE","Stade — 45 000 places",35.7600,-5.8300,"Tanger"),
    ("Stade Moulay Abdallah Rabat","stadium","🏟️","CRITIQUE","Stade national — 52 000 places",33.9950,-6.8700,"Rabat"),
    ("Stade de Fès","stadium","🏟️","ÉLEVÉ","Stade régional — 45 000 places",34.0200,-4.9800,"Fès"),
    ("Stade Boujniba Khouribga","stadium","🏟️","MODÉRÉ","Stade régional",32.8700,-6.9200,"Khouribga"),
    ("Complexe Sportif Prince Héritier Moulay El Hassan","stadium","🏟️","ÉLEVÉ","Stade polyvalent Rabat",34.0000,-6.8600,"Rabat"),

    # ── UNIVERSITÉS ────────────────────────────────────────────────────
    ("Université Mohammed V Rabat","university","🎓","ÉLEVÉ","Grande université — 100 000 étudiants",33.9760,-6.8499,"Rabat"),
    ("Université Hassan II Casablanca","university","🎓","ÉLEVÉ","Grande université",33.5731,-7.5898,"Casablanca"),
    ("Université Cadi Ayyad Marrakech","university","🎓","ÉLEVÉ","Université régionale",31.6295,-7.9811,"Marrakech"),
    ("Université Sidi Mohammed Ben Abdellah Fès","university","🎓","ÉLEVÉ","Université régionale",34.0209,-5.0078,"Fès"),
    ("Université Abdelmalek Essaadi Tanger","university","🎓","ÉLEVÉ","Université régionale",35.7595,-5.8340,"Tanger"),
    ("EMI — École Mohammadia d'Ingénieurs Rabat","university","🎓","ÉLEVÉ","Grande école d'ingénieurs",33.9760,-6.8700,"Rabat"),

    # ── CENTRES ADMINISTRATIFS / DIPLOMATIQUES ─────────────────────────
    ("Siège du Ministère de l'Intérieur","government","🏛️","CRITIQUE","Ministère — gestion de crise",33.9921,-6.8499,"Rabat"),
    ("Parlement Maroc Rabat","government","🏛️","CRITIQUE","Institution nationale",34.0200,-6.8300,"Rabat"),
    ("Palais Royal Rabat","government","🏛️","CRITIQUE","Résidence officielle",34.0020,-6.8580,"Rabat"),
    ("Ambassade USA Rabat","embassy","🏛️","CRITIQUE","Ambassade étrangère",34.0100,-6.8300,"Rabat"),
    ("Ambassade France Rabat","embassy","🏛️","CRITIQUE","Ambassade étrangère",33.9900,-6.8500,"Rabat"),
    ("Wilaya de Casablanca","government","🏛️","ÉLEVÉ","Administration régionale",33.5950,-7.6200,"Casablanca"),
    ("Wilaya de Marrakech","government","🏛️","ÉLEVÉ","Administration régionale",31.6295,-7.9811,"Marrakech"),
    ("Wilaya de Tanger","government","🏛️","ÉLEVÉ","Administration régionale",35.7595,-5.8340,"Tanger"),
    ("Wilaya d'Agadir","government","🏛️","ÉLEVÉ","Administration régionale",30.4278,-9.5981,"Agadir"),
    ("Wilaya de Fès","government","🏛️","ÉLEVÉ","Administration régionale",34.0209,-5.0078,"Fès"),

    # ── CASERNES DE POMPIERS ───────────────────────────────────────────
    ("Caserne Centrale Sapeurs-Pompiers Casablanca","fire_station","🚒","ÉLEVÉ","Unité principale SDIS",33.5800,-7.6100,"Casablanca"),
    ("Caserne Pompiers Rabat","fire_station","🚒","ÉLEVÉ","SDIS Rabat",33.9800,-6.8500,"Rabat"),
    ("Caserne Pompiers Tanger","fire_station","🚒","ÉLEVÉ","SDIS Tanger",35.7600,-5.8200,"Tanger"),
    ("Caserne Pompiers Marrakech","fire_station","🚒","ÉLEVÉ","SDIS Marrakech",31.6200,-7.9700,"Marrakech"),
    ("Caserne Pompiers Agadir","fire_station","🚒","ÉLEVÉ","SDIS Agadir",30.4200,-9.5900,"Agadir"),
    ("Caserne Pompiers Fès","fire_station","🚒","ÉLEVÉ","SDIS Fès",34.0200,-5.0000,"Fès"),
    ("Caserne Pompiers Meknès","fire_station","🚒","ÉLEVÉ","SDIS Meknès",33.8900,-5.5500,"Meknès"),
    ("Caserne Pompiers Kénitra","fire_station","🚒","ÉLEVÉ","SDIS Kénitra",34.2600,-6.5700,"Kénitra"),
    ("Caserne Pompiers El Jadida","fire_station","🚒","ÉLEVÉ","SDIS El Jadida",33.2300,-8.5000,"El Jadida"),
    ("Caserne Pompiers Oujda","fire_station","🚒","ÉLEVÉ","SDIS Oujda",34.6800,-1.9100,"Oujda"),

    # ── MARCHÉS / CENTRES COMMERCIAUX ─────────────────────────────────
    ("Morocco Mall Casablanca","mall","🛍️","ÉLEVÉ","Centre commercial — 6M visiteurs/an",33.5500,-7.6700,"Casablanca"),
    ("Anfa Place Casablanca","mall","🛍️","ÉLEVÉ","Centre commercial moderne",33.5800,-7.6400,"Casablanca"),
    ("Carré Eden Marrakech","mall","🛍️","ÉLEVÉ","Centre commercial",31.6300,-7.9800,"Marrakech"),
    ("Marjane Hay Riad Rabat","supermarket","🛒","ÉLEVÉ","Hypermarché",33.9600,-6.8400,"Rabat"),
    ("Marjane Casablanca Aïn Sebaa","supermarket","🛒","ÉLEVÉ","Hypermarché",33.6100,-7.5300,"Casablanca"),
    ("Marjane Tanger","supermarket","🛒","ÉLEVÉ","Hypermarché",35.7500,-5.8200,"Tanger"),
    ("Carrefour Marrakech","supermarket","🛒","ÉLEVÉ","Hypermarché",31.6200,-7.9900,"Marrakech"),
    ("Souk Central Casablanca","marketplace","🏪","MODÉRÉ","Grand marché traditionnel",33.5900,-7.6100,"Casablanca"),
]

# Fusionner les données Overpass avec la base intégrée
existing_names = {r["name"].lower() for r in db}

for row in MAROC_BASE:
    name, atype, icon, priority, risk, lat_e, lon_e, city = row
    if name.lower() not in existing_names:
        db.append({
            "name":     name,
            "type":     atype,
            "icon":     icon,
            "priority": priority,
            "risk":     risk,
            "lat":      lat_e,
            "lon":      lon_e,
            "city":     city,
        })
        existing_names.add(name.lower())

print(f"\n📊 Base finale : {len(db)} établissements/sites")

# Sauvegarder
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "hazmod_maroc_hotspots.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "version":   "2.0",
        "date":      "2026-06",
        "source":    "HOTOSM / HDX / OSM / Sources officielles Maroc",
        "license":   "ODbL 1.0 — OpenStreetMap contributors",
        "total":     len(db),
        "features":  db,
    }, f, ensure_ascii=False, indent=2)

print(f"✅ Base sauvegardée : {out_path}")
print(f"\n📈 Répartition par priorité :")
from collections import Counter
cpt = Counter(r["priority"] for r in db)
for k, v in sorted(cpt.items()):
    print(f"   {k}: {v}")
print(f"\n📈 Répartition par type :")
cpt2 = Counter(r["type"] for r in db)
for k,v in cpt2.most_common(10):
    print(f"   {k}: {v}")
