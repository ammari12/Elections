"""
osm_hotspots.py — HazMod NRBC
Détection exhaustive des établissements sensibles autour d'un incident Cl₂.

Sources (cascade prioritaire) :
  1. Base locale Maroc vérifiée (129+ sites, < 1ms)
  2. Overpass API OSM temps réel — 120+ catégories
  3. Fallback géométrique (toujours disponible)

Catégories couvertes :
  Santé, Éducation, Sport & Loisirs, Industrie, Transport,
  Administration, Culture, Social, Tourisme, Infrastructure,
  Commerce & Marchés, Sécurité, Culte, Environnement
"""

import math, json, os, requests, time
from typing import Dict, List

# ── Constantes ────────────────────────────────────────────────────────────────
_OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
_TIMEOUT = 28

# ── Catalogue exhaustif des types OSM ─────────────────────────────────────────
# Format : tag_key -> {tag_value: (icône, priorité, risque_description)}
# Priorités : CRITIQUE > ÉLEVÉ > MODÉRÉ > FAIBLE

_OSM_CATALOG = {

    # ══════════════════════════════════════════════════════
    # SANTÉ
    # ══════════════════════════════════════════════════════
    "amenity": {
        "hospital":            ("🏥", "CRITIQUE", "Patients vulnérables, évacuation complexe"),
        "clinic":              ("🏥", "CRITIQUE", "Personnel et patients, évacuation urgente"),
        "doctors":             ("🩺", "ÉLEVÉ",    "Cabinet médical — patients en consultation"),
        "dentist":             ("🦷", "MODÉRÉ",   "Cabinet dentaire"),
        "pharmacy":            ("💊", "ÉLEVÉ",    "Pharmacie — affluence publique"),
        "nursing_home":        ("🏠", "CRITIQUE", "Maison de retraite — personnes âgées"),
        "social_facility":     ("🤝", "CRITIQUE", "Centre social — populations vulnérables"),
        "baby_hatch":          ("👶", "CRITIQUE", "Structure petite enfance"),
        "veterinary":          ("🐾", "MODÉRÉ",   "Clinique vétérinaire"),
        "blood_bank":          ("🩸", "ÉLEVÉ",    "Banque de sang"),
        "dialysis":            ("💉", "CRITIQUE", "Centre de dialyse — patients dépendants"),
        "rehabilitation":      ("♿", "CRITIQUE", "Centre de rééducation"),

        # ══════════════════════════════════════════════════
        # ÉDUCATION
        # ══════════════════════════════════════════════════
        "school":              ("🏫", "CRITIQUE", "École — enfants en milieu confiné"),
        "kindergarten":        ("🧒", "CRITIQUE", "Crèche/Maternelle — très jeunes enfants"),
        "university":          ("🎓", "ÉLEVÉ",    "Université — forte densité étudiante"),
        "college":             ("🏫", "ÉLEVÉ",    "Lycée/Collège — jeunes, confinement"),
        "language_school":     ("📖", "MODÉRÉ",   "École de langues"),
        "music_school":        ("🎵", "MODÉRÉ",   "Conservatoire / École de musique"),
        "driving_school":      ("🚗", "FAIBLE",   "Auto-école"),
        "library":             ("📚", "MODÉRÉ",   "Bibliothèque — public nombreux"),

        # ══════════════════════════════════════════════════
        # ADMINISTRATION & GOUVERNEMENT
        # ══════════════════════════════════════════════════
        "townhall":            ("🏛", "ÉLEVÉ",    "Mairie / Commune — personnel et public"),
        "embassy":             ("🏛", "ÉLEVÉ",    "Ambassade / Consulat"),
        "courthouse":          ("⚖️",  "ÉLEVÉ",   "Tribunal — personnel et justiciables"),
        "post_office":         ("📮", "MODÉRÉ",   "Bureau de poste — affluence publique"),
        "customs":             ("🛃", "MODÉRÉ",   "Douane / Contrôle frontalier"),
        "register_office":     ("📋", "MODÉRÉ",   "Bureau d'état civil"),
        "prison":              ("🔒", "CRITIQUE", "Prison — évacuation très complexe"),
        "police":              ("👮", "ÉLEVÉ",    "Commissariat / Gendarmerie"),
        "fire_station":        ("🚒", "ÉLEVÉ",    "Caserne pompiers — premiers intervenants"),
        "ranger_station":      ("🌲", "FAIBLE",   "Poste forestier"),

        # ══════════════════════════════════════════════════
        # TRANSPORT & MOBILITÉ
        # ══════════════════════════════════════════════════
        "bus_station":         ("🚌", "ÉLEVÉ",    "Gare routière — forte concentration"),
        "taxi":                ("🚕", "FAIBLE",   "Station de taxis"),
        "parking":             ("🅿️",  "FAIBLE",  "Parking public"),
        "ferry_terminal":      ("⛴️",  "ÉLEVÉ",   "Terminal ferry — passagers nombreux"),
        "fuel":                ("⛽", "ÉLEVÉ",    "Station essence — inflammable, public"),

        # ══════════════════════════════════════════════════
        # LOISIRS, CULTURE & RASSEMBLEMENT
        # ══════════════════════════════════════════════════
        "theatre":             ("🎭", "ÉLEVÉ",    "Théâtre — public confiné en représentation"),
        "cinema":              ("🎬", "ÉLEVÉ",    "Cinéma — public confiné dans l'obscurité"),
        "arts_centre":         ("🎨", "MODÉRÉ",   "Centre artistique / culturel"),
        "community_centre":    ("🏘", "ÉLEVÉ",    "Centre communautaire — rassemblement"),
        "social_centre":       ("🤝", "ÉLEVÉ",    "Centre social"),
        "conference_centre":   ("🏢", "ÉLEVÉ",    "Centre de congrès — grands rassemblements"),
        "events_venue":        ("🎪", "ÉLEVÉ",    "Salle de spectacles / événements"),
        "nightclub":           ("🎵", "MODÉRÉ",   "Boîte de nuit — public en milieu fermé"),
        "bar":                 ("🍺", "FAIBLE",   "Bar / Café"),
        "restaurant":          ("🍽", "FAIBLE",   "Restaurant"),
        "fast_food":           ("🍔", "FAIBLE",   "Restauration rapide — fort trafic"),
        "cafe":                ("☕", "FAIBLE",   "Café / Salon de thé"),
        "marketplace":         ("🛒", "ÉLEVÉ",    "Marché public — rassemblement dense"),
        "food_court":          ("🛒", "MODÉRÉ",   "Galerie alimentaire"),
        "bank":                ("🏦", "FAIBLE",   "Banque / Agence"),
        "atm":                 ("💳", "FAIBLE",   "Distributeur automatique"),

        # ══════════════════════════════════════════════════
        # CULTE
        # ══════════════════════════════════════════════════
        "place_of_worship":    ("🕌", "ÉLEVÉ",    "Lieu de culte — rassemblement massif (prière)"),
        "mosque":              ("🕌", "ÉLEVÉ",    "Mosquée — rassemblement massif"),
        "church":              ("⛪", "ÉLEVÉ",    "Église — rassemblement"),
        "synagogue":           ("✡️",  "ÉLEVÉ",   "Synagogue — rassemblement"),

        # ══════════════════════════════════════════════════
        # REFUGES & HÉBERGEMENT D'URGENCE
        # ══════════════════════════════════════════════════
        "shelter":             ("🏕", "CRITIQUE", "Abri d'urgence — populations précaires"),
        "refugee_site":        ("⛺", "CRITIQUE", "Camp de réfugiés — populations vulnérables"),
        "homeless_shelter":    ("🏠", "CRITIQUE", "Hébergement sans-abri"),
        "orphanage":           ("👶", "CRITIQUE", "Orphelinat — enfants"),
        "childcare":           ("🧒", "CRITIQUE", "Garderie / Centre de jour enfants"),
        "daycare":             ("🧒", "CRITIQUE", "Crèche de jour"),

        # ══════════════════════════════════════════════════
        # INFRASTRUCTURE & SERVICES
        # ══════════════════════════════════════════════════
        "recycling":           ("♻️",  "FAIBLE",  "Centre de tri / recyclage"),
        "waste_transfer":      ("🗑", "MODÉRÉ",   "Centre de transfert déchets"),
        "internet_cafe":       ("💻", "FAIBLE",   "Cybercafé"),
        "charging_station":    ("⚡", "FAIBLE",   "Borne de recharge"),
    },

    # ══════════════════════════════════════════════════════
    # LOISIRS & SPORT (tag leisure)
    # ══════════════════════════════════════════════════════
    "leisure": {
        "stadium":             ("🏟", "CRITIQUE", "Stade — dizaines de milliers de personnes"),
        "sports_centre":       ("🏋", "ÉLEVÉ",    "Complexe sportif — nombreux pratiquants"),
        "sports_hall":         ("🏀", "ÉLEVÉ",    "Salle de sport / Gymnase"),
        "swimming_pool":       ("🏊", "ÉLEVÉ",    "Piscine publique — baigneurs exposés"),
        "water_park":          ("💦", "CRITIQUE", "Parc aquatique — grande affluence"),
        "fitness_centre":      ("🏋", "MODÉRÉ",   "Salle de fitness / Gym"),
        "ice_rink":            ("⛸️",  "ÉLEVÉ",   "Patinoire — public confiné"),
        "golf_course":         ("⛳", "MODÉRÉ",   "Terrain de golf — espace ouvert"),
        "pitch":               ("⚽", "MODÉRÉ",   "Terrain de sport — activité en plein air"),
        "track":               ("🏃", "MODÉRÉ",   "Piste d'athlétisme"),
        "playground":          ("🛝", "CRITIQUE", "Aire de jeux — enfants en plein air"),
        "park":                ("🌳", "MODÉRÉ",   "Parc public — rassemblement loisirs"),
        "garden":              ("🌸", "FAIBLE",   "Jardin public"),
        "nature_reserve":      ("🌿", "FAIBLE",   "Réserve naturelle"),
        "marina":              ("⛵", "MODÉRÉ",   "Port de plaisance"),
        "slipway":             ("🚤", "FAIBLE",   "Cale de mise à l'eau"),
        "horse_riding":        ("🐎", "MODÉRÉ",   "Centre équestre"),
        "miniature_golf":      ("⛳", "FAIBLE",   "Mini-golf"),
        "amusement_arcade":    ("🎮", "MODÉRÉ",   "Salle de jeux — adolescents"),
        "escape_game":         ("🗝", "MODÉRÉ",   "Escape game — confiné"),
        "bowling_alley":       ("🎳", "MODÉRÉ",   "Bowling — public confiné"),
        "dog_park":            ("🐕", "FAIBLE",   "Parc canin"),
        "sauna":               ("🧖", "MODÉRÉ",   "Sauna / Hammam"),
        "spa":                 ("💆", "MODÉRÉ",   "Spa / Centre de bien-être"),
        "dance":               ("💃", "MODÉRÉ",   "École de danse"),
        "hackerspace":         ("💻", "FAIBLE",   "FabLab / Hackerspace"),
    },

    # ══════════════════════════════════════════════════════
    # TOURISME
    # ══════════════════════════════════════════════════════
    "tourism": {
        "hotel":               ("🏨", "ÉLEVÉ",    "Hôtel — touristes en chambres"),
        "hostel":              ("🛏", "ÉLEVÉ",    "Auberge de jeunesse — occupation dense"),
        "motel":               ("🏩", "MODÉRÉ",   "Motel"),
        "guest_house":         ("🏠", "MODÉRÉ",   "Maison d'hôtes / Riad"),
        "camp_site":           ("⛺", "MODÉRÉ",   "Camping — tentes exposées"),
        "caravan_site":        ("🚐", "MODÉRÉ",   "Camping-cars"),
        "museum":              ("🏛", "MODÉRÉ",   "Musée — visiteurs"),
        "gallery":             ("🖼", "FAIBLE",   "Galerie d'art"),
        "theme_park":          ("🎡", "CRITIQUE", "Parc d'attractions — grande affluence"),
        "zoo":                 ("🦁", "ÉLEVÉ",    "Zoo — visiteurs et animaux"),
        "aquarium":            ("🐟", "ÉLEVÉ",    "Aquarium — public confiné"),
        "viewpoint":           ("👁", "FAIBLE",   "Point de vue"),
        "picnic_site":         ("🧺", "MODÉRÉ",   "Aire de pique-nique"),
        "attraction":          ("📍", "MODÉRÉ",   "Site touristique"),
        "information":         ("ℹ️",  "FAIBLE",  "Office de tourisme"),
        "apartment":           ("🏢", "MODÉRÉ",   "Résidence touristique"),
    },

    # ══════════════════════════════════════════════════════
    # BUREAUX & ADMINISTRATION
    # ══════════════════════════════════════════════════════
    "office": {
        "government":          ("🏛", "ÉLEVÉ",    "Bureau gouvernemental — fonctionnaires et public"),
        "administrative":      ("🏢", "MODÉRÉ",   "Administration publique"),
        "diplomatic":          ("🏛", "ÉLEVÉ",    "Mission diplomatique"),
        "ngo":                 ("🤝", "MODÉRÉ",   "ONG / Association"),
        "company":             ("🏢", "MODÉRÉ",   "Siège social entreprise"),
        "insurance":           ("📋", "FAIBLE",   "Compagnie d'assurances"),
        "lawyer":              ("⚖️",  "FAIBLE",  "Cabinet d'avocats"),
        "accountant":          ("💼", "FAIBLE",   "Cabinet comptable"),
        "research":            ("🔬", "MODÉRÉ",   "Centre de recherche"),
        "telecommunication":   ("📡", "MODÉRÉ",   "Opérateur télécom — infrastructure"),
        "newspaper":           ("📰", "FAIBLE",   "Rédaction de presse"),
        "political_party":     ("🗳", "MODÉRÉ",   "Siège de parti politique"),
        "religion":            ("🕌", "MODÉRÉ",   "Bureau religieux"),
        "quango":              ("🏢", "MODÉRÉ",   "Organisme semi-public"),
    },

    # ══════════════════════════════════════════════════════
    # INDUSTRIE & INFRASTRUCTURE CRITIQUE
    # ══════════════════════════════════════════════════════
    "man_made": {
        "water_tower":         ("🗼", "ÉLEVÉ",    "Château d'eau — infrastructure eau potable"),
        "pumping_station":     ("⚙️",  "ÉLEVÉ",   "Station de pompage"),
        "wastewater_plant":    ("🏭", "ÉLEVÉ",    "Station d'épuration"),
        "water_works":         ("💧", "ÉLEVÉ",    "Usine de traitement eau"),
        "storage_tank":        ("🛢", "CRITIQUE", "Réservoir de stockage industriel"),
        "oil_refinery":        ("🏭", "CRITIQUE", "Raffinerie — risque chimique majeur"),
        "chimney":             ("🏭", "MODÉRÉ",   "Cheminée industrielle"),
        "gasometer":           ("⛽", "CRITIQUE", "Gazomètre — stockage gaz sous pression"),
        "tower":               ("🗼", "MODÉRÉ",   "Tour / Pylône — infrastructure"),
        "mast":                ("📡", "MODÉRÉ",   "Antenne relais"),
        "pipeline":            ("🔧", "ÉLEVÉ",    "Conduite / Pipeline industriel"),
        "silo":                ("🌾", "MODÉRÉ",   "Silo agricole / industriel"),
        "cooling_tower":       ("🏭", "ÉLEVÉ",    "Tour de refroidissement industrielle"),
        "crane":               ("🏗", "FAIBLE",   "Grue — site de construction actif"),
        "works":               ("🏭", "ÉLEVÉ",    "Site industriel / usine"),
        "street_cabinet":      ("📦", "FAIBLE",   "Armoire technique réseau"),
        "reservoir":           ("💧", "ÉLEVÉ",    "Réservoir d'eau"),
        "bridge":              ("🌉", "MODÉRÉ",   "Pont — axe de circulation"),
    },

    # ══════════════════════════════════════════════════════
    # ÉLECTRICITÉ & ÉNERGIE
    # ══════════════════════════════════════════════════════
    "power": {
        "substation":          ("⚡", "CRITIQUE", "Sous-station électrique — infrastructure critique"),
        "transformer":         ("⚡", "ÉLEVÉ",    "Transformateur électrique"),
        "plant":               ("🏭", "CRITIQUE", "Centrale électrique"),
        "generator":           ("⚙️",  "MODÉRÉ",  "Groupe électrogène"),
        "pole":                ("⚡", "FAIBLE",   "Pylône électrique"),
        "tower":               ("🗼", "MODÉRÉ",   "Tour électrique haute tension"),
        "cable":               ("⚡", "FAIBLE",   "Câble électrique"),
    },

    # ══════════════════════════════════════════════════════
    # TRANSPORTS PUBLICS
    # ══════════════════════════════════════════════════════
    "public_transport": {
        "station":             ("🚇", "ÉLEVÉ",    "Station metro/tram — fort afflux"),
        "stop_position":       ("🚌", "MODÉRÉ",   "Arrêt de bus / transport en commun"),
        "platform":            ("🚉", "ÉLEVÉ",    "Quai — concentration de passagers"),
        "stop_area":           ("🚌", "MODÉRÉ",   "Zone d'arrêt transport"),
    },

    # ══════════════════════════════════════════════════════
    # FERROVIAIRE
    # ══════════════════════════════════════════════════════
    "railway": {
        "station":             ("🚉", "ÉLEVÉ",    "Gare ferroviaire — voyageurs nombreux"),
        "halt":                ("🚉", "MODÉRÉ",   "Halte ferroviaire"),
        "tram_stop":           ("🚊", "MODÉRÉ",   "Arrêt tramway"),
        "subway_entrance":     ("🚇", "ÉLEVÉ",    "Entrée métro — confiné sous-terrain"),
        "platform":            ("🚉", "MODÉRÉ",   "Quai ferroviaire"),
        "depot":               ("🏭", "MODÉRÉ",   "Dépôt ferroviaire"),
        "yard":                ("🚂", "MODÉRÉ",   "Triage ferroviaire"),
    },

    # ══════════════════════════════════════════════════════
    # AÉRIEN
    # ══════════════════════════════════════════════════════
    "aeroway": {
        "aerodrome":           ("✈️",  "CRITIQUE", "Aéroport — milliers de passagers"),
        "terminal":            ("✈️",  "CRITIQUE", "Terminal aéroportuaire"),
        "helipad":             ("🚁", "MODÉRÉ",   "Héliport / Hélipad"),
        "heliport":            ("🚁", "ÉLEVÉ",    "Héliport — transport médical ou civil"),
        "apron":               ("✈️",  "ÉLEVÉ",   "Aire de trafic aéroportuaire"),
        "hangar":              ("🛩", "MODÉRÉ",   "Hangar aéronautique"),
    },

    # ══════════════════════════════════════════════════════
    # COMMERCE & GRANDE SURFACE
    # ══════════════════════════════════════════════════════
    "shop": {
        "supermarket":         ("🛒", "ÉLEVÉ",    "Supermarché — forte affluence"),
        "mall":                ("🏬", "ÉLEVÉ",    "Centre commercial — milliers de visiteurs"),
        "department_store":    ("🏬", "ÉLEVÉ",    "Grand magasin"),
        "convenience":         ("🏪", "FAIBLE",   "Épicerie de proximité"),
        "clothes":             ("👗", "FAIBLE",   "Magasin de vêtements"),
        "electronics":         ("📱", "MODÉRÉ",   "Magasin d'électronique — affluence"),
        "hardware":            ("🔧", "MODÉRÉ",   "Quincaillerie"),
        "chemist":             ("🧪", "ÉLEVÉ",    "Droguerie / Parapharmacie — produits chimiques"),
        "gas":                 ("⛽", "CRITIQUE", "Dépôt de gaz — stockage inflammable"),
        "kiosk":               ("🗞", "FAIBLE",   "Kiosque"),
        "bakery":              ("🥖", "FAIBLE",   "Boulangerie — clientèle régulière"),
        "butcher":             ("🥩", "FAIBLE",   "Boucherie"),
        "market":              ("🛒", "ÉLEVÉ",    "Marché couvert — rassemblement dense"),
    },

    # ══════════════════════════════════════════════════════
    # BÂTIMENTS (fallback tag building)
    # ══════════════════════════════════════════════════════
    "building": {
        "hospital":            ("🏥", "CRITIQUE", "Bâtiment hospitalier"),
        "school":              ("🏫", "CRITIQUE", "Établissement scolaire"),
        "university":          ("🎓", "ÉLEVÉ",    "Bâtiment universitaire"),
        "church":              ("⛪", "ÉLEVÉ",    "Édifice religieux"),
        "mosque":              ("🕌", "ÉLEVÉ",    "Mosquée"),
        "stadium":             ("🏟", "CRITIQUE", "Stade"),
        "sports_hall":         ("🏋", "ÉLEVÉ",    "Halle sportive"),
        "train_station":       ("🚉", "ÉLEVÉ",    "Gare"),
        "transportation":      ("🚌", "ÉLEVÉ",    "Hub de transport"),
        "retail":              ("🏬", "MODÉRÉ",   "Commerce / Centre commercial"),
        "commercial":          ("🏢", "MODÉRÉ",   "Bâtiment commercial"),
        "industrial":          ("🏭", "ÉLEVÉ",    "Bâtiment industriel"),
        "warehouse":           ("🏭", "MODÉRÉ",   "Entrepôt"),
        "government":          ("🏛", "ÉLEVÉ",    "Bâtiment administratif"),
        "dormitory":           ("🛏", "ÉLEVÉ",    "Dortoir / Résidence étudiante"),
        "apartments":          ("🏢", "MODÉRÉ",   "Immeuble résidentiel — population dense"),
        "residential":         ("🏘", "MODÉRÉ",   "Zone résidentielle"),
        "hotel":               ("🏨", "ÉLEVÉ",    "Hôtel"),
        "prison":              ("🔒", "CRITIQUE", "Établissement pénitentiaire"),
        "military":            ("🪖", "ÉLEVÉ",    "Installation militaire"),
        "fire_station":        ("🚒", "ÉLEVÉ",    "Caserne de pompiers"),
        "civic":               ("🏛", "ÉLEVÉ",    "Bâtiment civique"),
        "public":              ("🏢", "MODÉRÉ",   "Bâtiment public"),
        "kindergarten":        ("🧒", "CRITIQUE", "Crèche / Maternelle"),
        "college":             ("🏫", "ÉLEVÉ",    "Lycée / Collège"),
    },

    # ══════════════════════════════════════════════════════
    # MILITAIRE
    # ══════════════════════════════════════════════════════
    "military": {
        "base":                ("🪖", "ÉLEVÉ",    "Base militaire — personnel nombreux"),
        "barracks":            ("🪖", "ÉLEVÉ",    "Caserne militaire"),
        "bunker":              ("🛡", "MODÉRÉ",   "Bunker / Abri militaire"),
        "checkpoint":          ("🚧", "MODÉRÉ",   "Point de contrôle"),
        "training_area":       ("🪖", "MODÉRÉ",   "Zone d'entraînement militaire"),
        "airfield":            ("✈️",  "ÉLEVÉ",   "Terrain d'aviation militaire"),
        "naval_base":          ("⚓", "ÉLEVÉ",    "Base navale"),
    },

    # ══════════════════════════════════════════════════════
    # FRONTIÈRES & SÉCURITÉ
    # ══════════════════════════════════════════════════════
    "barrier": {
        "border_control":      ("🛃", "ÉLEVÉ",    "Poste frontière — flux intense"),
        "toll_booth":          ("🚧", "MODÉRÉ",   "Péage — concentration de véhicules"),
    },

    # ══════════════════════════════════════════════════════
    # ENVIRONNEMENT & EAU
    # ══════════════════════════════════════════════════════
    "natural": {
        "water":               ("💧", "ÉLEVÉ",    "Plan d'eau — contamination possible"),
        "beach":               ("🏖", "ÉLEVÉ",    "Plage — rassemblement estival"),
        "wetland":             ("🌿", "MODÉRÉ",   "Zone humide — écosystème sensible"),
        "spring":              ("💧", "ÉLEVÉ",    "Source d'eau potable"),
    },

    # ══════════════════════════════════════════════════════
    # LANDUSE — ZONES À RISQUE
    # ══════════════════════════════════════════════════════
    "landuse": {
        "industrial":          ("🏭", "ÉLEVÉ",    "Zone industrielle — usines et entrepôts"),
        "commercial":          ("🏬", "MODÉRÉ",   "Zone commerciale — forte fréquentation"),
        "retail":              ("🛒", "MODÉRÉ",   "Zone de commerce de détail"),
        "residential":         ("🏘", "MODÉRÉ",   "Zone résidentielle — population dense"),
        "military":            ("🪖", "ÉLEVÉ",    "Zone militaire"),
        "port":                ("⚓", "ÉLEVÉ",    "Zone portuaire — activités industrielles"),
        "railway":             ("🚉", "MODÉRÉ",   "Zone ferroviaire"),
        "garages":             ("🚗", "FAIBLE",   "Zone de garages"),
        "allotments":          ("🌱", "FAIBLE",   "Jardins familiaux"),
        "recreation_ground":   ("⚽", "MODÉRÉ",   "Terrain de sport / loisirs"),
        "fairground":          ("🎡", "ÉLEVÉ",    "Champ de foire / fête foraine"),
        "cemetery":            ("🪦", "FAIBLE",   "Cimetière"),
        "quarry":              ("⛏", "MODÉRÉ",   "Carrière"),
        "landfill":            ("🗑", "MODÉRÉ",   "Décharge / Centre d'enfouissement"),
        "brownfield":          ("🏗", "MODÉRÉ",   "Friche industrielle"),
        "greenhouse_horticulture": ("🌿", "FAIBLE", "Serres horticoles"),
    },
}

# ── Requête Overpass optimisée ────────────────────────────────────────────────

def _build_overpass_query(lat: float, lon: float, radius_m: float) -> str:
    """
    Construit la requête Overpass QL couvrant toutes les catégories du catalogue.
    Inclut nodes ET ways pour capturer les grands bâtiments (stades, complexes...).
    """
    r = int(radius_m)

    # Construire les filtres par tag
    tag_filters = []
    for tag_key, tag_vals in _OSM_CATALOG.items():
        vals = "|".join(tag_vals.keys())
        tag_filters.append(
            f'  node["{tag_key}"~"{vals}"](around:{r},{lat},{lon});'
        )
        tag_filters.append(
            f'  way["{tag_key}"~"{vals}"](around:{r},{lat},{lon});'
        )
        tag_filters.append(
            f'  relation["{tag_key}"~"{vals}"](around:{r},{lat},{lon});'
        )

    q = "[out:json][timeout:28];\n(\n"
    q += "\n".join(tag_filters)
    q += "\n);\nout center tags;"
    return q


def _classify_element(tags: dict) -> tuple:
    """
    Retourne (icône, priorité, description) pour un élément OSM donné.
    Cherche dans tous les tags dans l'ordre de priorité.
    """
    priority_order = ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE"]
    best = None

    for tag_key, tag_vals in _OSM_CATALOG.items():
        if tag_key not in tags:
            continue
        tag_val = tags[tag_key]
        if tag_val in tag_vals:
            icon, prio, risk = tag_vals[tag_val]
            if best is None or priority_order.index(prio) < priority_order.index(best[1]):
                best = (icon, prio, risk)

    return best or ("📍", "MODÉRÉ", "Établissement public")


def _get_name(tags: dict) -> str:
    """Extrait le meilleur nom disponible."""
    for key in ["name", "name:fr", "name:ar", "official_name",
                "short_name", "brand", "operator", "ref"]:
        if key in tags and tags[key].strip():
            return tags[key].strip()
    # Fallback : type
    for k in ["amenity", "leisure", "tourism", "office", "building",
              "shop", "man_made", "power", "military", "public_transport"]:
        if k in tags:
            return tags[k].replace("_", " ").title()
    return "Établissement sans nom"


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance en mètres entre deux points GPS."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _bearing(lat1, lon1, lat2, lon2) -> float:
    """Cap en degrés (0=N, 90=E) de (lat1,lon1) vers (lat2,lon2)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlam)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _assign_zone(dist: float, r3: float, r2: float, r1: float) -> str:
    if dist <= r3:
        return "ERPG-3"
    elif dist <= r2:
        return "ERPG-2"
    elif dist <= r1:
        return "ERPG-1"
    return None


def _query_overpass(lat: float, lon: float, radius_m: float) -> list:
    """Requête Overpass avec fallback sur plusieurs serveurs."""
    query = _build_overpass_query(lat, lon, radius_m)
    for url in _OVERPASS_URLS:
        try:
            resp = requests.post(
                url, data={"data": query},
                timeout=_TIMEOUT,
                headers={"User-Agent": "HazMod-NRBC/2.0 (hazmat-decision-support)"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("elements", [])
        except Exception:
            continue
    return []


def _load_local_base() -> list:
    """Charge la base locale Maroc JSON si disponible."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "hazmod_maroc_hotspots.json"),
        os.path.join(os.getcwd(), "hazmod_maroc_hotspots.json"),
        "hazmod_maroc_hotspots.json",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return []


def _local_hotspots(lat: float, lon: float, radius_m: float) -> list:
    """Cherche dans la base locale les sites dans le rayon."""
    base = _load_local_base()
    results = []
    for site in base:
        slat = site.get("lat", 0)
        slon = site.get("lon", 0)
        dist = _haversine(lat, lon, slat, slon)
        if dist <= radius_m:
            results.append({
                "name":     site.get("name", "Site local"),
                "icon":     site.get("icon", "📍"),
                "priority": site.get("priority", "MODÉRÉ"),
                "risk":     site.get("risk", "Établissement sensible"),
                "coords":   [slat, slon],
                "dist":     int(dist),
                "source":   "base_locale",
                "tags":     site.get("tags", {}),
            })
    return results


def get_hotspots(
    lat: float, lon: float,
    r3: float, r2: float, r1: float,
    prop_dir: float
) -> Dict[str, List[dict]]:
    """
    Point d'entrée principal.
    Retourne {"ERPG-3": [...], "ERPG-2": [...], "ERPG-1": [...]}
    chaque item : {name, icon, priority, risk, coords, dist, source}
    """
    result = {"ERPG-3": [], "ERPG-2": [], "ERPG-1": []}
    seen_coords = set()
    max_radius = max(r1, 500)

    # ── 1. Base locale Maroc ──────────────────────────────────────────────────
    local_sites = _local_hotspots(lat, lon, max_radius)

    # ── 2. Overpass OSM temps réel ────────────────────────────────────────────
    osm_elements = _query_overpass(lat, lon, max_radius)

    # ── 3. Fusionner et déduplication ─────────────────────────────────────────
    all_items = []

    # Traiter éléments OSM
    for el in osm_elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        # Coordonnées (node ou way/relation avec center)
        if el.get("type") == "node":
            elat, elon = el.get("lat", 0), el.get("lon", 0)
        else:
            center = el.get("center", {})
            elat = center.get("lat", 0)
            elon = center.get("lon", 0)

        if not elat or not elon:
            continue

        dist = _haversine(lat, lon, elat, elon)
        zone = _assign_zone(dist, r3, r2, r1)
        if not zone:
            continue

        # Déduplication par coordonnées arrondies
        coord_key = (round(elat, 4), round(elon, 4))
        if coord_key in seen_coords:
            continue
        seen_coords.add(coord_key)

        icon, priority, risk = _classify_element(tags)
        name = _get_name(tags)
        bear = _bearing(lat, lon, elat, elon)

        all_items.append({
            "name":     name,
            "icon":     icon,
            "priority": priority,
            "risk":     risk,
            "coords":   [round(elat, 5), round(elon, 5)],
            "dist":     int(dist),
            "bearing":  round(bear, 1),
            "zone":     zone,
            "source":   "osm",
            "tags":     tags,
        })

    # Traiter base locale (priorité si pas déjà dans OSM)
    for site in local_sites:
        coord_key = (round(site["coords"][0], 4), round(site["coords"][1], 4))
        if coord_key in seen_coords:
            continue
        seen_coords.add(coord_key)

        dist = site["dist"]
        zone = _assign_zone(dist, r3, r2, r1)
        if not zone:
            continue

        bear = _bearing(lat, lon, site["coords"][0], site["coords"][1])
        site["zone"] = zone
        site["bearing"] = round(bear, 1)
        all_items.append(site)

    # ── 4. Tri par priorité puis distance ─────────────────────────────────────
    _prio_rank = {"CRITIQUE": 0, "ÉLEVÉ": 1, "MODÉRÉ": 2, "FAIBLE": 3}
    all_items.sort(key=lambda x: (_prio_rank.get(x["priority"], 3), x["dist"]))

    # ── 5. Répartition par zone ───────────────────────────────────────────────
    for item in all_items:
        zone = item.get("zone")
        if zone in result:
            result[zone].append(item)

    # ── 6. Fallback géométrique si aucun résultat ─────────────────────────────
    if not any(result.values()):
        result = _geometric_fallback(lat, lon, r3, r2, r1, prop_dir)

    return result


def _geometric_fallback(lat, lon, r3, r2, r1, prop_dir) -> Dict[str, List[dict]]:
    """
    Fallback : génère des points types le long de l'axe de dispersion.
    Utilisé quand OSM et la base locale ne retournent rien.
    """
    def geo_point(d, bearing):
        R = 6371000.0
        lat_r = math.radians(lat)
        br = math.radians(bearing)
        dr = d / R
        nlat = math.asin(math.sin(lat_r)*math.cos(dr) +
                         math.cos(lat_r)*math.sin(dr)*math.cos(br))
        nlon = math.radians(lon) + math.atan2(
            math.sin(br)*math.sin(dr)*math.cos(lat_r),
            math.cos(dr) - math.sin(lat_r)*math.sin(nlat))
        return round(math.degrees(nlat), 5), round(math.degrees(nlon), 5)

    result = {"ERPG-3": [], "ERPG-2": [], "ERPG-1": []}

    templates = [
        ("ERPG-3", r3*0.6,  "🏥", "CRITIQUE", "Zone de danger vital — établissement critique probable"),
        ("ERPG-3", r3*0.9,  "🏫", "CRITIQUE", "Zone de danger vital — école ou rassemblement possible"),
        ("ERPG-2", r2*0.55, "🏋", "ÉLEVÉ",    "Zone d'effets irréversibles — complexe sportif probable"),
        ("ERPG-2", r2*0.80, "🏘", "MODÉRÉ",   "Zone d'effets irréversibles — zone habitée"),
        ("ERPG-1", r1*0.50, "🕌", "ÉLEVÉ",    "Zone d'irritation — lieu de culte ou rassemblement"),
        ("ERPG-1", r1*0.80, "🏬", "MODÉRÉ",   "Zone d'irritation — commerce ou administration"),
    ]

    for i, (zone, dist, icon, prio, risk) in enumerate(templates):
        bear = (prop_dir + (i * 15 - 30)) % 360
        clat, clon = geo_point(max(dist, 10), bear)
        result[zone].append({
            "name":     f"Zone sensible estimée ({zone})",
            "icon":     icon,
            "priority": prio,
            "risk":     risk,
            "coords":   [clat, clon],
            "dist":     int(dist),
            "bearing":  round(bear, 1),
            "zone":     zone,
            "source":   "geometrique",
            "tags":     {},
        })

    return result


# ── Statistiques pour debug ───────────────────────────────────────────────────
def get_stats(result: dict) -> dict:
    total = sum(len(v) for v in result.values())
    by_prio = {}
    for items in result.values():
        for it in items:
            p = it.get("priority", "MODÉRÉ")
            by_prio[p] = by_prio.get(p, 0) + 1
    return {
        "total": total,
        "by_zone": {k: len(v) for k, v in result.items()},
        "by_priority": by_prio,
    }
