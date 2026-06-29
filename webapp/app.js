/* ═══════════════════════════════════════════════════════════════════════
   HAZMOD — Interactive Web Application
   Three.js · GSAP · Leaflet · Physics Engine
   ═══════════════════════════════════════════════════════════════════════ */

// ── PHYSICS ENGINE ─────────────────────────────────────────────────────
const PG_COEFF = {
  A: { ay: 0.22, by: 0.89, az: 0.20, bz: 0.89 },
  B: { ay: 0.16, by: 0.87, az: 0.12, bz: 0.87 },
  C: { ay: 0.11, by: 0.87, az: 0.08, bz: 0.87 },
  D: { ay: 0.08, by: 0.85, az: 0.06, bz: 0.80 },
  E: { ay: 0.06, by: 0.80, az: 0.03, bz: 0.75 },
  F: { ay: 0.04, by: 0.75, az: 0.016, bz: 0.72 },
};
const SEUILS = { 'ERPG-1': 1.0, 'ERPG-2': 3.0, 'ERPG-3': 20.0 };
const K_DENSE = 5674366.0;
const EXP_Q = 0.80;
const EXP_X = 1.888;
const F_STAB_DENSE = { A: 0.35, B: 0.55, C: 0.82, D: 1.00, E: 1.25, F: 1.60 };

const MAROC_BASE = [
  {name:"Hôpital Ibn Sina",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital universitaire — 1200 lits",lat:33.9921,lon:-6.8499,city:"Rabat"},
  {name:"Hôpital Cheikh Zaïd",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU — soins intensifs",lat:33.9733,lon:-6.8543,city:"Rabat"},
  {name:"Hôpital Militaire Mohammed V",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital militaire — protocole interne",lat:33.9690,lon:-6.8640,city:"Rabat"},
  {name:"Hôpital d'Enfants de Rabat",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Pédiatrie — population vulnérable",lat:33.9840,lon:-6.8610,city:"Rabat"},
  {name:"Clinique Agdal",type:"clinic",icon:"🏥",priority:"CRITIQUE",risk:"Clinique privée",lat:33.9820,lon:-6.8720,city:"Rabat"},
  {name:"CHU Ibn Rochd",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU Casablanca — 1800 lits",lat:33.5731,lon:-7.5898,city:"Casablanca"},
  {name:"Hôpital Moulay Youssef",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital général",lat:33.5800,lon:-7.6100,city:"Casablanca"},
  {name:"Hôpital 20 Août 1953",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:33.5600,lon:-7.6200,city:"Casablanca"},
  {name:"Clinique du Littoral",type:"clinic",icon:"🏥",priority:"CRITIQUE",risk:"Clinique privée",lat:33.5950,lon:-7.6320,city:"Casablanca"},
  {name:"CHU Mohammed VI Marrakech",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU — trauma et urgences",lat:31.6295,lon:-7.9811,city:"Marrakech"},
  {name:"Hôpital Ibn Nafis",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:31.6100,lon:-8.0100,city:"Marrakech"},
  {name:"CHU Mohammed VI Tanger",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU — 800 lits",lat:35.7595,lon:-5.8340,city:"Tanger"},
  {name:"Hôpital Militaire Tanger",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital militaire",lat:35.7800,lon:-5.8100,city:"Tanger"},
  {name:"CHU Hassan II Fès",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU — 1400 lits",lat:34.0209,lon:-5.0078,city:"Fès"},
  {name:"Hôpital Ghassani",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:34.0100,lon:-4.9900,city:"Fès"},
  {name:"CHU Souss-Massa Agadir",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU Agadir",lat:30.4278,lon:-9.5981,city:"Agadir"},
  {name:"Hôpital Hassan II Agadir",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:30.4200,lon:-9.5800,city:"Agadir"},
  {name:"Hôpital Mohammed V Meknès",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:33.8935,lon:-5.5547,city:"Meknès"},
  {name:"CHU Mohammed VI Oujda",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"CHU région orientale",lat:34.6867,lon:-1.9114,city:"Oujda"},
  {name:"Hôpital Mohammed V El Jadida",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:33.2333,lon:-8.5000,city:"El Jadida"},
  {name:"Clinique Errazi El Jadida",type:"clinic",icon:"🏥",priority:"CRITIQUE",risk:"Clinique privée",lat:33.2400,lon:-8.5100,city:"El Jadida"},
  {name:"Hôpital Sidi Mohammed Ben Abdellah Safi",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:32.2833,lon:-9.2333,city:"Safi"},
  {name:"Hôpital Mohammed V Béni Mellal",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:32.3333,lon:-6.3500,city:"Béni Mellal"},
  {name:"Hôpital Moulay Youssef Kénitra",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:34.2610,lon:-6.5802,city:"Kénitra"},
  {name:"Hôpital Saniat Rmel Tétouan",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:35.5785,lon:-5.3684,city:"Tétouan"},
  {name:"Hôpital Mohamed Bouafi Nador",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:35.1667,lon:-2.9333,city:"Nador"},
  {name:"Hôpital Laayoune",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:27.1253,lon:-13.1625,city:"Laayoune"},
  {name:"Hôpital Dakhla",type:"hospital",icon:"🏥",priority:"CRITIQUE",risk:"Hôpital régional",lat:23.7137,lon:-15.9355,city:"Dakhla"},
  {name:"Aéroport Mohammed V Casablanca",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Hub national — 10M passagers/an",lat:33.3675,lon:-7.5897,city:"Casablanca"},
  {name:"Aéroport Marrakech Menara",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport international",lat:31.6069,lon:-8.0363,city:"Marrakech"},
  {name:"Aéroport Tanger Ibn Battouta",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport international",lat:35.7269,lon:-5.9169,city:"Tanger"},
  {name:"Aéroport Agadir Al Massira",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport international",lat:30.3250,lon:-9.4131,city:"Agadir"},
  {name:"Aéroport Fès-Saïss",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport régional",lat:33.9272,lon:-4.9778,city:"Fès"},
  {name:"Aéroport Oujda Angads",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport régional",lat:34.7872,lon:-1.9240,city:"Oujda"},
  {name:"Aéroport Rabat-Salé",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport régional",lat:34.0514,lon:-6.7515,city:"Rabat"},
  {name:"Aéroport Nador El Aroui",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport régional",lat:34.9888,lon:-3.0282,city:"Nador"},
  {name:"Aéroport Laayoune Hassan I",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport régional",lat:27.1516,lon:-13.2191,city:"Laayoune"},
  {name:"Aéroport Dakhla",type:"aerodrome",icon:"✈️",priority:"CRITIQUE",risk:"Aéroport régional",lat:23.7183,lon:-15.9320,city:"Dakhla"},
  {name:"Aéroport Ouarzazate",type:"aerodrome",icon:"✈️",priority:"ELEVE",risk:"Aéroport régional",lat:30.9391,lon:-6.9094,city:"Ouarzazate"},
  {name:"Aéroport Tétouan Sania Ramel",type:"aerodrome",icon:"✈️",priority:"ELEVE",risk:"Aéroport régional",lat:35.5943,lon:-5.3200,city:"Tétouan"},
  {name:"Aéroport Al Hoceima Cherif Al Idrissi",type:"aerodrome",icon:"✈️",priority:"ELEVE",risk:"Aéroport régional",lat:35.1769,lon:-3.8395,city:"Al Hoceima"},
  {name:"Gare de Casablanca Voyageurs",type:"station",icon:"🚉",priority:"ELEVE",risk:"Principale gare nationale",lat:33.5944,lon:-7.6122,city:"Casablanca"},
  {name:"Gare de Casablanca Port",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare ferroviaire",lat:33.6014,lon:-7.6244,city:"Casablanca"},
  {name:"Gare de Rabat Ville",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Rabat",lat:33.9907,lon:-6.8550,city:"Rabat"},
  {name:"Gare de Rabat Agdal",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare secondaire Rabat",lat:33.9728,lon:-6.8719,city:"Rabat"},
  {name:"Gare de Tanger Ville",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Tanger",lat:35.7679,lon:-5.7979,city:"Tanger"},
  {name:"Gare de Marrakech",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Marrakech",lat:31.6296,lon:-8.0104,city:"Marrakech"},
  {name:"Gare de Fès",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Fès",lat:34.0229,lon:-5.0142,city:"Fès"},
  {name:"Gare de Meknès",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Meknès",lat:33.8992,lon:-5.5536,city:"Meknès"},
  {name:"Gare de Kénitra",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Kénitra",lat:34.2600,lon:-6.5750,city:"Kénitra"},
  {name:"Gare de Oujda",type:"station",icon:"🚉",priority:"ELEVE",risk:"Gare principale Oujda",lat:34.6800,lon:-1.9100,city:"Oujda"},
  {name:"Gare de Safi",type:"station",icon:"🚉",priority:"MODERE",risk:"Gare régionale",lat:32.3100,lon:-9.2200,city:"Safi"},
  {name:"Gare de El Jadida",type:"station",icon:"🚉",priority:"MODERE",risk:"Gare régionale",lat:33.2300,lon:-8.5100,city:"El Jadida"},
  {name:"OCP — Usine Jorf Lasfar",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Engrais phosphatés — NH3, H2SO4, HNO3",lat:33.0972,lon:-8.6272,city:"El Jadida"},
  {name:"OCP — Usine Safi",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Engrais phosphatés — H2SO4",lat:32.2800,lon:-9.2100,city:"Safi"},
  {name:"OCP — Site Khouribga",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Extraction phosphates",lat:32.8833,lon:-6.9167,city:"Khouribga"},
  {name:"OCP — Site Benguerir",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Extraction phosphates",lat:32.2333,lon:-7.9500,city:"Benguerir"},
  {name:"OCP — Site Youssoufia",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Extraction phosphates",lat:32.2500,lon:-8.5333,city:"Youssoufia"},
  {name:"Raffinerie SAMIR Mohammedia",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Raffinerie pétrole — risque explosif",lat:33.6939,lon:-7.4153,city:"Mohammedia"},
  {name:"SNEP — Complexe chimique Mohammedia",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Chlore Cl2, PVC — risque majeur",lat:33.6800,lon:-7.3900,city:"Mohammedia"},
  {name:"FERTIMA — Engrais azotés Mohammedia",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"NH3 liquide — risque toxique",lat:33.6700,lon:-7.4000,city:"Mohammedia"},
  {name:"Terminal pétrolier Mohammedia",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Stockage hydrocarbures",lat:33.7000,lon:-7.4200,city:"Mohammedia"},
  {name:"Zone Industrielle Aïn Johra Casablanca",type:"industrial",icon:"🏭",priority:"ELEVE",risk:"Industries diverses",lat:33.5200,lon:-7.7300,city:"Casablanca"},
  {name:"Zone Industrielle Sidi Bernoussi Casablanca",type:"industrial",icon:"🏭",priority:"ELEVE",risk:"Industries chimiques légères",lat:33.5800,lon:-7.5500,city:"Casablanca"},
  {name:"Terminal chimique Tanger Med",type:"industrial",icon:"🏭",priority:"CRITIQUE",risk:"Port industriel — matières dangereuses",lat:35.8833,lon:-5.5000,city:"Tanger"},
  {name:"Zone Industrielle Tanger Automotive City",type:"industrial",icon:"🏭",priority:"ELEVE",risk:"Constructeurs auto — peintures solvants",lat:35.7300,lon:-5.9500,city:"Tanger"},
  {name:"ONEE — Centrale thermique Mohammedia",type:"industrial",icon:"⚡",priority:"CRITIQUE",risk:"Centrale électrique — charbon",lat:33.7200,lon:-7.3800,city:"Mohammedia"},
  {name:"ONEE — Centrale Jerada",type:"industrial",icon:"⚡",priority:"CRITIQUE",risk:"Centrale thermique charbon",lat:34.3100,lon:-2.1600,city:"Jerada"},
  {name:"ONEE — Centrale Kénitra",type:"industrial",icon:"⚡",priority:"CRITIQUE",risk:"Centrale thermique",lat:34.2700,lon:-6.5600,city:"Kénitra"},
  {name:"Station de traitement eau Tamesna",type:"water_works",icon:"💧",priority:"CRITIQUE",risk:"Infrastructure eau potable Rabat",lat:33.9200,lon:-6.9400,city:"Rabat"},
  {name:"Station de traitement eau Ain Attig",type:"water_works",icon:"💧",priority:"CRITIQUE",risk:"Infrastructure eau potable Casablanca",lat:33.6100,lon:-7.6900,city:"Casablanca"},
  {name:"SOMACA — Usine automobile Casablanca",type:"industrial",icon:"🏭",priority:"ELEVE",risk:"Peintures solvants — risque chimique",lat:33.5300,lon:-7.5700,city:"Casablanca"},
  {name:"Stellantis Kénitra",type:"industrial",icon:"🏭",priority:"ELEVE",risk:"Usine automobile — peintures solvants",lat:34.2500,lon:-6.6100,city:"Kénitra"},
  {name:"Port Tanger Med",type:"aerodrome",icon:"🚢",priority:"CRITIQUE",risk:"1er port d'Afrique — conteneurs et chimie",lat:35.8833,lon:-5.5000,city:"Tanger"},
  {name:"Port de Casablanca",type:"aerodrome",icon:"🚢",priority:"CRITIQUE",risk:"Port national — matières dangereuses",lat:33.6044,lon:-7.6183,city:"Casablanca"},
  {name:"Port de Jorf Lasfar",type:"aerodrome",icon:"🚢",priority:"CRITIQUE",risk:"Port chimique — soufre, phosphates, Cl2",lat:33.1167,lon:-8.6333,city:"El Jadida"},
  {name:"Port de Safi",type:"aerodrome",icon:"🚢",priority:"ELEVE",risk:"Port chimique — phosphates",lat:32.3000,lon:-9.2500,city:"Safi"},
  {name:"Port d'Agadir",type:"aerodrome",icon:"🚢",priority:"ELEVE",risk:"Port commercial et pêche",lat:30.4200,lon:-9.6500,city:"Agadir"},
  {name:"Port de Nador",type:"aerodrome",icon:"🚢",priority:"ELEVE",risk:"Port commercial",lat:35.1700,lon:-2.9400,city:"Nador"},
  {name:"Port de Mohammedia",type:"aerodrome",icon:"🚢",priority:"CRITIQUE",risk:"Port pétrolier",lat:33.7200,lon:-7.4000,city:"Mohammedia"},
  {name:"Stade Mohammed V Casablanca",type:"stadium",icon:"🏟️",priority:"CRITIQUE",risk:"Stade national — 67 000 places",lat:33.5940,lon:-7.6360,city:"Casablanca"},
  {name:"Grand Stade de Marrakech",type:"stadium",icon:"🏟️",priority:"CRITIQUE",risk:"Stade international — 45 000 places",lat:31.6100,lon:-8.0200,city:"Marrakech"},
  {name:"Stade Adrar Agadir",type:"stadium",icon:"🏟️",priority:"CRITIQUE",risk:"Stade moderne — 45 000 places",lat:30.4200,lon:-9.6100,city:"Agadir"},
  {name:"Grand Stade de Tanger",type:"stadium",icon:"🏟️",priority:"CRITIQUE",risk:"Stade — 45 000 places",lat:35.7600,lon:-5.8300,city:"Tanger"},
  {name:"Stade Moulay Abdallah Rabat",type:"stadium",icon:"🏟️",priority:"CRITIQUE",risk:"Stade national — 52 000 places",lat:33.9950,lon:-6.8700,city:"Rabat"},
  {name:"Stade de Fès",type:"stadium",icon:"🏟️",priority:"ELEVE",risk:"Stade régional — 45 000 places",lat:34.0200,lon:-4.9800,city:"Fès"},
  {name:"Stade Boujniba Khouribga",type:"stadium",icon:"🏟️",priority:"MODERE",risk:"Stade régional",lat:32.8700,lon:-6.9200,city:"Khouribga"},
  {name:"Complexe Sportif Prince Héritier Moulay El Hassan",type:"stadium",icon:"🏟️",priority:"ELEVE",risk:"Stade polyvalent Rabat",lat:34.0000,lon:-6.8600,city:"Rabat"},
  {name:"Université Mohammed V Rabat",type:"university",icon:"🎓",priority:"ELEVE",risk:"Grande université — 100 000 étudiants",lat:33.9760,lon:-6.8499,city:"Rabat"},
  {name:"Université Hassan II Casablanca",type:"university",icon:"🎓",priority:"ELEVE",risk:"Grande université",lat:33.5731,lon:-7.5898,city:"Casablanca"},
  {name:"Université Cadi Ayyad Marrakech",type:"university",icon:"🎓",priority:"ELEVE",risk:"Université régionale",lat:31.6295,lon:-7.9811,city:"Marrakech"},
  {name:"Université Sidi Mohammed Ben Abdellah Fès",type:"university",icon:"🎓",priority:"ELEVE",risk:"Université régionale",lat:34.0209,lon:-5.0078,city:"Fès"},
  {name:"Université Abdelmalek Essaadi Tanger",type:"university",icon:"🎓",priority:"ELEVE",risk:"Université régionale",lat:35.7595,lon:-5.8340,city:"Tanger"},
  {name:"EMI — École Mohammadia d'Ingénieurs Rabat",type:"university",icon:"🎓",priority:"ELEVE",risk:"Grande école d'ingénieurs",lat:33.9760,lon:-6.8700,city:"Rabat"},
  {name:"Siège du Ministère de l'Intérieur",type:"government",icon:"🏛️",priority:"CRITIQUE",risk:"Ministère — gestion de crise",lat:33.9921,lon:-6.8499,city:"Rabat"},
  {name:"Parlement Maroc Rabat",type:"government",icon:"🏛️",priority:"CRITIQUE",risk:"Institution nationale",lat:34.0200,lon:-6.8300,city:"Rabat"},
  {name:"Palais Royal Rabat",type:"government",icon:"🏛️",priority:"CRITIQUE",risk:"Résidence officielle",lat:34.0020,lon:-6.8580,city:"Rabat"},
  {name:"Ambassade USA Rabat",type:"embassy",icon:"🏛️",priority:"CRITIQUE",risk:"Ambassade étrangère",lat:34.0100,lon:-6.8300,city:"Rabat"},
  {name:"Ambassade France Rabat",type:"embassy",icon:"🏛️",priority:"CRITIQUE",risk:"Ambassade étrangère",lat:33.9900,lon:-6.8500,city:"Rabat"},
  {name:"Wilaya de Casablanca",type:"government",icon:"🏛️",priority:"ELEVE",risk:"Administration régionale",lat:33.5950,lon:-7.6200,city:"Casablanca"},
  {name:"Wilaya de Marrakech",type:"government",icon:"🏛️",priority:"ELEVE",risk:"Administration régionale",lat:31.6295,lon:-7.9811,city:"Marrakech"},
  {name:"Wilaya de Tanger",type:"government",icon:"🏛️",priority:"ELEVE",risk:"Administration régionale",lat:35.7595,lon:-5.8340,city:"Tanger"},
  {name:"Wilaya d'Agadir",type:"government",icon:"🏛️",priority:"ELEVE",risk:"Administration régionale",lat:30.4278,lon:-9.5981,city:"Agadir"},
  {name:"Wilaya de Fès",type:"government",icon:"🏛️",priority:"ELEVE",risk:"Administration régionale",lat:34.0209,lon:-5.0078,city:"Fès"},
  {name:"Caserne Centrale Sapeurs-Pompiers Casablanca",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"Unité principale SDIS",lat:33.5800,lon:-7.6100,city:"Casablanca"},
  {name:"Caserne Pompiers Rabat",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Rabat",lat:33.9800,lon:-6.8500,city:"Rabat"},
  {name:"Caserne Pompiers Tanger",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Tanger",lat:35.7600,lon:-5.8200,city:"Tanger"},
  {name:"Caserne Pompiers Marrakech",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Marrakech",lat:31.6200,lon:-7.9700,city:"Marrakech"},
  {name:"Caserne Pompiers Agadir",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Agadir",lat:30.4200,lon:-9.5900,city:"Agadir"},
  {name:"Caserne Pompiers Fès",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Fès",lat:34.0200,lon:-5.0000,city:"Fès"},
  {name:"Caserne Pompiers Meknès",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Meknès",lat:33.8900,lon:-5.5500,city:"Meknès"},
  {name:"Caserne Pompiers Kénitra",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Kénitra",lat:34.2600,lon:-6.5700,city:"Kénitra"},
  {name:"Caserne Pompiers El Jadida",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS El Jadida",lat:33.2300,lon:-8.5000,city:"El Jadida"},
  {name:"Caserne Pompiers Oujda",type:"fire_station",icon:"🚒",priority:"ELEVE",risk:"SDIS Oujda",lat:34.6800,lon:-1.9100,city:"Oujda"},
  {name:"Morocco Mall Casablanca",type:"mall",icon:"🛍️",priority:"ELEVE",risk:"Centre commercial — 6M visiteurs/an",lat:33.5500,lon:-7.6700,city:"Casablanca"},
  {name:"Anfa Place Casablanca",type:"mall",icon:"🛍️",priority:"ELEVE",risk:"Centre commercial moderne",lat:33.5800,lon:-7.6400,city:"Casablanca"},
  {name:"Carré Eden Marrakech",type:"mall",icon:"🛍️",priority:"ELEVE",risk:"Centre commercial",lat:31.6300,lon:-7.9800,city:"Marrakech"},
  {name:"Marjane Hay Riad Rabat",type:"supermarket",icon:"🛒",priority:"ELEVE",risk:"Hypermarché",lat:33.9600,lon:-6.8400,city:"Rabat"},
  {name:"Marjane Casablanca Aïn Sebaa",type:"supermarket",icon:"🛒",priority:"ELEVE",risk:"Hypermarché",lat:33.6100,lon:-7.5300,city:"Casablanca"},
  {name:"Marjane Tanger",type:"supermarket",icon:"🛒",priority:"ELEVE",risk:"Hypermarché",lat:35.7500,lon:-5.8200,city:"Tanger"},
  {name:"Carrefour Marrakech",type:"supermarket",icon:"🛒",priority:"ELEVE",risk:"Hypermarché",lat:31.6200,lon:-7.9900,city:"Marrakech"},
  {name:"Souk Central Casablanca",type:"marketplace",icon:"🏪",priority:"MODERE",risk:"Grand marché traditionnel",lat:33.5900,lon:-7.6100,city:"Casablanca"},
];

const HCP_ZONES = {
  casablanca: {pop:4330000,area:386,density:11218,lat:33.5731,lon:-7.5898,type:"metrop"},
  rabat: {pop:1230000,area:117,density:10513,lat:33.9716,lon:-6.8498,type:"metrop"},
  sale: {pop:950000,area:180,density:5278,lat:34.0531,lon:-6.7986,type:"metrop"},
  fes: {pop:1220000,area:320,density:3813,lat:34.0209,lon:-5.0078,type:"metrop"},
  marrakech: {pop:1070000,area:230,density:4652,lat:31.6295,lon:-7.9811,type:"metrop"},
  tanger: {pop:950000,area:352,density:2699,lat:35.7595,lon:-5.8340,type:"metrop"},
  agadir: {pop:620000,area:260,density:2385,lat:30.4278,lon:-9.5981,type:"ville"},
  meknes: {pop:700000,area:220,density:3182,lat:33.8935,lon:-5.5547,type:"ville"},
  oujda: {pop:600000,area:180,density:3333,lat:34.6867,lon:-1.9114,type:"ville"},
  kenitra: {pop:500000,area:190,density:2632,lat:34.2610,lon:-6.5802,type:"ville"},
  tetouan: {pop:400000,area:60,density:6667,lat:35.5785,lon:-5.3684,type:"ville"},
  temara: {pop:370000,area:100,density:3700,lat:33.9250,lon:-6.9083,type:"ville"},
  safi: {pop:330000,area:90,density:3667,lat:32.2833,lon:-9.2333,type:"ville"},
  mohammedia: {pop:210000,area:55,density:3818,lat:33.6867,lon:-7.3831,type:"ville"},
  nador: {pop:220000,area:70,density:3143,lat:35.1667,lon:-2.9333,type:"ville"},
  beni_mellal: {pop:290000,area:80,density:3625,lat:32.3333,lon:-6.3500,type:"ville"},
  khouribga: {pop:210000,area:65,density:3231,lat:32.8833,lon:-6.9167,type:"ville"},
  el_jadida: {pop:200000,area:120,density:1667,lat:33.2333,lon:-8.5000,type:"ville"},
  laayoune: {pop:220000,area:65,density:3385,lat:27.1253,lon:-13.1625,type:"ville_moy"},
  berrechid: {pop:150000,area:45,density:3333,lat:33.2656,lon:-7.5874,type:"ville_moy"},
  settat: {pop:180000,area:55,density:3273,lat:32.9942,lon:-7.6225,type:"ville_moy"},
  ksar_el_kebir: {pop:120000,area:38,density:3158,lat:35.0022,lon:-5.9031,type:"ville_moy"},
  larache: {pop:130000,area:45,density:2889,lat:35.1932,lon:-6.1571,type:"ville_moy"},
  khemisset: {pop:140000,area:40,density:3500,lat:33.8228,lon:-6.0639,type:"ville_moy"},
  taza: {pop:170000,area:55,density:3091,lat:34.2105,lon:-3.9946,type:"ville_moy"},
  ouarzazate: {pop:85000,area:40,density:2125,lat:30.9391,lon:-6.9094,type:"ville_moy"},
  dakhla: {pop:120000,area:45,density:2667,lat:23.7137,lon:-15.9355,type:"ville_moy"},
  al_hoceima: {pop:100000,area:40,density:2500,lat:35.2517,lon:-3.9372,type:"ville_moy"},
  jorf_lasfar: {pop:50000,area:25,density:2000,lat:33.1167,lon:-8.6333,type:"bourg"},
  tanger_med: {pop:15000,area:12,density:1250,lat:35.8833,lon:-5.5000,type:"bourg"},
  gharb: {pop:8000,area:50,density:160,lat:34.5000,lon:-6.0000,type:"rural"},
  doukk_abda: {pop:5000,area:45,density:111,lat:32.5000,lon:-8.8000,type:"rural"},
  tadla: {pop:3000,area:60,density:50,lat:32.5000,lon:-6.5000,type:"rural"},
  haouz: {pop:2500,area:80,density:31,lat:31.5000,lon:-8.0000,type:"rural"},
  souss_rural: {pop:2000,area:70,density:29,lat:30.2000,lon:-9.3000,type:"rural"},
  rif: {pop:4000,area:55,density:73,lat:35.0000,lon:-4.5000,type:"rural"},
  atlas_moyen: {pop:1500,area:100,density:15,lat:31.5000,lon:-5.5000,type:"rural"},
  pre_sahara: {pop:400,area:300,density:1,lat:30.0000,lon:-6.0000,type:"desert"},
  sahara: {pop:200,area:800,density:0.2,lat:25.0000,lon:-12.0000,type:"desert"},
};

function sigmaPG(x, stab) {
  x = Math.max(x, 1.0);
  const c = PG_COEFF[stab] || PG_COEFF.D;
  const fac = Math.pow(1 + 0.0001 * x, -0.5);
  return {
    sy: c.ay * Math.pow(x, c.by) * fac,
    sz: Math.max(c.az * Math.pow(x, c.bz) * fac, 0.5),
  };
}

function qDebit(Q_kg, dureeMin, typeBrutal) {
  const durEff = typeBrutal ? Math.min(dureeMin, 10) : dureeMin;
  return Q_kg / Math.max(durEff, 1) / 60;
}

function concPPM(Q_kgs, u, x, y, stab, H = 0) {
  x = Math.max(x, 1);
  const { sy, sz } = sigmaPG(x, stab);
  const denom = Math.PI * u * sy * sz;
  if (denom < 1e-10) return 0;
  let C = (Q_kgs * 1000) / denom * Math.exp(-0.5 * (y / sy) ** 2);
  if (H > 0) C *= 2 * Math.exp(-0.5 * (H / sz) ** 2);
  return Math.max(C * 24.45 / 70.9, 0);
}

function rayonSeuil(Q_kg, u, stab, H, seuil, dureeMin, typeBrutal) {
  const Q_kgs = qDebit(Q_kg, dureeMin, typeBrutal);
  const H_eff = typeBrutal ? 0 : H;

  if (!typeBrutal) {
    const F = F_STAB_DENSE[stab] || 1.0;
    const R = Math.pow(K_DENSE * Math.pow(Q_kgs, EXP_Q) * F / (u * seuil), 1.0 / EXP_X);
    return Math.min(Math.max(R, 1), 30000);
  }

  const hiMax = 20000;
  let lo = 1, hi = hiMax;
  if (concPPM(Q_kgs, u, lo, 0, stab, H_eff) <= seuil) return 1;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (concPPM(Q_kgs, u, mid, 0, stab, H_eff) > seuil) lo = mid;
    else hi = mid;
  }
  const R_plume = hi;
  const durEff = Math.min(dureeMin, 10);
  if (durEff < 30) {
    const dur_s = Math.max(durEff, 1) * 60;
    const T_transit = R_plume / Math.max(u, 0.1);
    if (dur_s < T_transit) return Math.min(Math.sqrt(R_plume * u * dur_s), R_plume);
  }
  return R_plume;
}

function monteCarlo(Q_kg, u, stab, H, N, dureeMin, typeBrutal) {
  const Q_kgs = qDebit(Q_kg, dureeMin, typeBrutal);
  const H_eff = typeBrutal ? 0 : H;
  const distances = [100, 200, 300, 500, 750, 1000, 1500, 2000, 3000];
  const result = {};

  for (const d of distances) {
    const { sy, sz } = sigmaPG(d, stab);
    const samples = [];
    for (let i = 0; i < N; i++) {
      const Qv = Q_kgs * Math.exp((Math.random() + Math.random() + Math.random() - 1.5) * 0.3 * 2);
      const uv = Math.max(0.3, Math.min(15, u * Math.exp((Math.random() + Math.random() + Math.random() - 1.5) * 0.2 * 2)));
      const denom = Math.PI * uv * sy * sz;
      let c = denom > 0 ? (Qv * 1000) / denom * 24.45 / 70.9 : 0;
      if (H_eff > 0) c *= 2 * Math.exp(-0.5 * (H_eff / sz) ** 2);
      samples.push(Math.max(c, 0));
    }
    samples.sort((a, b) => a - b);
    const mean = samples.reduce((a, b) => a + b, 0) / N;
    result[d] = {
      mean,
      p50: samples[Math.floor(N * 0.5)],
      p95: samples[Math.floor(N * 0.95)],
      p_e1: samples.filter(s => s > SEUILS['ERPG-1']).length / N,
      p_e2: samples.filter(s => s > SEUILS['ERPG-2']).length / N,
      p_e3: samples.filter(s => s > SEUILS['ERPG-3']).length / N,
    };
  }
  return result;
}

// ── HOTSPOT DETECTION ──────────────────────────────────────────────────
function distMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2-lat1)*Math.PI/180;
  const dLon = (lon2-lon1)*Math.PI/180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.asin(Math.sqrt(Math.min(a,1)));
}

function findHotspots(lat, lon, r3, r2, r1) {
  const zones = {'ERPG-3':[], 'ERPG-2':[], 'ERPG-1':[]};
  for (const h of MAROC_BASE) {
    const d = distMeters(lat, lon, h.lat, h.lon);
    let zone = null;
    if (d <= r3) zone = 'ERPG-3';
    else if (d <= r2) zone = 'ERPG-2';
    else if (d <= r1) zone = 'ERPG-1';
    if (zone) {
      zones[zone].push({...h, dist: Math.round(d), zone});
    }
  }
  for (const z of Object.keys(zones)) {
    zones[z].sort((a,b) => a.dist - b.dist);
    zones[z] = zones[z].slice(0, 12);
  }
  return zones;
}

// ── POPULATION DENSITY ─────────────────────────────────────────────────
function getPopulationDensity(lat, lon) {
  let bestD = 999, bestZone = 'unknown', bestDens = 1000;
  for (const [zid, z] of Object.entries(HCP_ZONES)) {
    const d = Math.sqrt((lat-z.lat)**2 + (lon-z.lon)**2);
    if (d < bestD) { bestD = d; bestZone = zid; bestDens = z.density; }
  }
  const decay = Math.exp(-0.06 * bestD * 111);
  return Math.max(1, Math.round(bestDens * decay));
}

// ── STATE ──────────────────────────────────────────────────────────────
const state = {
  Q_kg: 9000, dureeMin: 60, hauteur: 2, typeBrutal: true,
  u_ms: 5, dirVent: 280, stab: 'C',
  lat: 33.9716, lon: -6.8498,
  densPop: 2000, distPop: 300,
  ppeLevel: 2, earlyWarning: false, delaiEvac: 30, coordSec: 2,
  mcIter: 2000,
  r1: 0, r2: 0, r3: 0,
  gravite: 0,
  mc: null,
  capaMed: 1,
  dominoEffect: false,
  hasTrain: false, hasHopital: false, hasEcole: false, hasAdmin: false, hasGare: false,
  hotspots: null,
  simulated: false,
};

// ── THREE.JS PARTICLE SYSTEM ───────────────────────────────────────────
let scene, camera, renderer, particles;

function initThree() {
  const canvas = document.getElementById('three-canvas');
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 50;

  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const particleCount = 3000;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  const sizes = new Float32Array(particleCount);
  const velocities = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 120;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 80;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 60;
    velocities[i * 3] = (Math.random() - 0.3) * 0.02;
    velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.01;
    velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.005;

    const zone = Math.random();
    if (zone < 0.15) {
      colors[i * 3] = 0.93; colors[i * 3 + 1] = 0.27; colors[i * 3 + 2] = 0.27;
      sizes[i] = Math.random() * 1.5 + 0.5;
    } else if (zone < 0.35) {
      colors[i * 3] = 0.96; colors[i * 3 + 1] = 0.62; colors[i * 3 + 2] = 0.04;
      sizes[i] = Math.random() * 1.2 + 0.3;
    } else {
      colors[i * 3] = 0.23; colors[i * 3 + 1] = 0.51; colors[i * 3 + 2] = 0.96;
      sizes[i] = Math.random() * 0.8 + 0.2;
    }
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
  geometry._velocities = velocities;

  const material = new THREE.PointsMaterial({
    size: 0.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  particles = new THREE.Points(geometry, material);
  scene.add(particles);

  animateThree();
}

function animateThree() {
  requestAnimationFrame(animateThree);
  const positions = particles.geometry.attributes.position.array;
  const velocities = particles.geometry._velocities;
  const time = Date.now() * 0.0005;

  for (let i = 0; i < positions.length / 3; i++) {
    positions[i * 3] += velocities[i * 3] + Math.sin(time + i) * 0.003;
    positions[i * 3 + 1] += velocities[i * 3 + 1] + Math.cos(time + i * 0.7) * 0.002;
    positions[i * 3 + 2] += velocities[i * 3 + 2];

    if (positions[i * 3] > 60) positions[i * 3] = -60;
    if (positions[i * 3] < -60) positions[i * 3] = 60;
    if (Math.abs(positions[i * 3 + 1]) > 40) velocities[i * 3 + 1] *= -1;
  }

  particles.geometry.attributes.position.needsUpdate = true;
  particles.rotation.y = time * 0.05;
  particles.rotation.x = Math.sin(time * 0.3) * 0.05;
  renderer.render(scene, camera);
}

// ── LOADING ANIMATION ──────────────────────────────────────────────────
function animateLoader() {
  const steps = document.querySelectorAll('.loader-step');
  const fills = document.querySelectorAll('.step-fill');
  const gradients = ['#3B82F6', '#7C3AED', '#059669', '#DC2626', '#D97706'];

  gsap.timeline()
    .to(fills[0], { width: '100%', duration: 0.6, ease: 'power2.out', delay: 0.3 })
    .to(fills[1], { width: '100%', duration: 0.5, ease: 'power2.out' }, '-=0.1')
    .to(fills[2], { width: '100%', duration: 0.4, ease: 'power2.out' }, '-=0.1')
    .to(fills[3], { width: '100%', duration: 0.5, ease: 'power2.out' }, '-=0.1')
    .to(fills[4], { width: '100%', duration: 0.4, ease: 'power2.out' }, '-=0.1')
    .to('#loader', {
      opacity: 0,
      duration: 0.8,
      ease: 'power2.inOut',
      delay: 0.4,
      onComplete: () => {
        document.getElementById('loader').classList.add('hidden');
        initApp();
      },
    });
}

// ── APP INITIALIZATION ─────────────────────────────────────────────────
function initApp() {
  document.querySelector('.navbar').classList.add('visible');

  gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

  // Hero animations
  const heroTl = gsap.timeline({ delay: 0.2 });
  heroTl
    .from('.hero-badge-row', { opacity: 0, y: 20, duration: 0.6, ease: 'power3.out' })
    .from('.hero-title .hero-line', {
      opacity: 0, y: 40, duration: 0.8, ease: 'power3.out', stagger: 0.15,
    }, '-=0.3')
    .from('.hero-desc', { opacity: 0, y: 20, duration: 0.6, ease: 'power3.out' }, '-=0.4')
    .from('.hero-actions', { opacity: 0, y: 20, duration: 0.6, ease: 'power3.out' }, '-=0.3')
    .from('.hero-stat', {
      opacity: 0, y: 30, scale: 0.9, duration: 0.5, ease: 'back.out(1.4)', stagger: 0.1,
    }, '-=0.3');

  // Counter animations
  animateCounter('statAccidents', 81, 1.5);
  animateCounter('statHotspots', 122, 1.8);
  animateCounter('statMC', 2000, 2);
  animateCounter('statStab', 6, 1.2);

  // Scroll reveal
  document.querySelectorAll('[data-reveal]').forEach((el, i) => {
    ScrollTrigger.create({
      trigger: el,
      start: 'top 85%',
      onEnter: () => {
        gsap.to(el, {
          opacity: 1, y: 0, duration: 0.8,
          delay: i % 4 * 0.1,
          ease: 'power3.out',
          onStart: () => el.classList.add('revealed'),
        });
      },
      once: true,
    });
  });

  // Nav tabs
  setupNavTabs();
  setupInputs();
  setupMap();
}

function animateCounter(id, target, duration) {
  const el = document.getElementById(id);
  gsap.to({ val: 0 }, {
    val: target,
    duration,
    delay: 0.5,
    ease: 'power2.out',
    onUpdate: function () {
      el.textContent = Math.round(this.targets()[0].val).toLocaleString();
    },
  });
}

// ── NAV TABS ───────────────────────────────────────────────────────────
function setupNavTabs() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.section);
      if (target) {
        gsap.to(window, { scrollTo: { y: target, offsetY: 60 }, duration: 1, ease: 'power3.inOut' });
      }
    });
  });

  // Update active tab on scroll
  const sections = ['hero', 'simulation', 'map-section', 'dashboard', 'monte-carlo', 'operations'];
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    ScrollTrigger.create({
      trigger: el,
      start: 'top center',
      end: 'bottom center',
      onEnter: () => setActiveTab(id),
      onEnterBack: () => setActiveTab(id),
    });
  });

  // Hero buttons
  document.getElementById('startSimBtn')?.addEventListener('click', () => {
    gsap.to(window, { scrollTo: { y: '#simulation', offsetY: 60 }, duration: 1.2, ease: 'power3.inOut' });
  });
  document.getElementById('viewDashBtn')?.addEventListener('click', () => {
    gsap.to(window, { scrollTo: { y: '#dashboard', offsetY: 60 }, duration: 1.2, ease: 'power3.inOut' });
  });
}

function setActiveTab(id) {
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.section === id);
  });
}

// ── INPUT BINDINGS ─────────────────────────────────────────────────────
function setupInputs() {
  const bind = (id, key, outputId, fmt) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      state[key] = parseFloat(el.value);
      if (outputId) document.getElementById(outputId).textContent = fmt(el.value);
      onParamChange();
    });
  };

  bind('inputQ', 'Q_kg', 'outputQ', v => Number(v).toLocaleString() + ' kg');
  bind('inputDuration', 'dureeMin', 'outputDuration', v => v + ' min');
  bind('inputHeight', 'hauteur', 'outputHeight', v => v + ' m');
  bind('inputWind', 'u_ms', 'outputWind', v => parseFloat(v).toFixed(1) + ' m/s');
  bind('inputDir', 'dirVent', 'outputDir', v => v + '°');
  bind('inputDens', 'densPop', 'outputDens', v => Number(v).toLocaleString());
  bind('inputEvac', 'delaiEvac', 'outputEvac', v => v + ' min');
  bind('inputCoord', 'coordSec', 'outputCoord', v => v);
  bind('inputDistPop', 'distPop', 'outputDistPop', v => v + ' m');

  // Wind compass
  const dirInput = document.getElementById('inputDir');
  if (dirInput) {
    dirInput.addEventListener('input', () => {
      const needle = document.getElementById('compassNeedle');
      if (needle) needle.style.transform = `translate(-50%, -100%) rotate(${dirInput.value}deg)`;
    });
  }

  // Toggle groups
  document.querySelectorAll('.toggle-group').forEach(group => {
    group.querySelectorAll('.toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        gsap.from(btn, { scale: 0.9, duration: 0.2, ease: 'back.out(2)' });

        if (group.id === 'releaseType') state.typeBrutal = btn.dataset.value === 'brutal';
        if (group.id === 'ppeLevel') state.ppeLevel = parseInt(btn.dataset.value);
        if (group.id === 'mcIter') state.mcIter = parseInt(btn.dataset.value);
        if (group.id === 'capaMed') state.capaMed = parseInt(btn.dataset.value);
        onParamChange();
      });
    });
  });

  // Stability
  document.querySelectorAll('.stab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.stab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.stab = btn.dataset.stab;
      gsap.from(btn, { scale: 0.85, duration: 0.25, ease: 'back.out(2)' });
      onParamChange();
    });
  });

  // Switch
  document.getElementById('earlyWarning')?.addEventListener('change', (e) => {
    state.earlyWarning = e.target.checked;
    onParamChange();
  });
  document.getElementById('dominoEffect')?.addEventListener('change', e => { state.dominoEffect = e.target.checked; });
  document.getElementById('hasTrain')?.addEventListener('change', e => { state.hasTrain = e.target.checked; });
  document.getElementById('hasHopital')?.addEventListener('change', e => { state.hasHopital = e.target.checked; });
  document.getElementById('hasEcole')?.addEventListener('change', e => { state.hasEcole = e.target.checked; });
  document.getElementById('hasAdmin')?.addEventListener('change', e => { state.hasAdmin = e.target.checked; });
  document.getElementById('hasGare')?.addEventListener('change', e => { state.hasGare = e.target.checked; });

  // Coords
  document.getElementById('inputLat')?.addEventListener('change', (e) => {
    state.lat = parseFloat(e.target.value);
    onParamChange();
  });
  document.getElementById('inputLon')?.addEventListener('change', (e) => {
    state.lon = parseFloat(e.target.value);
    onParamChange();
  });

  // Launch button
  document.getElementById('launchBtn')?.addEventListener('click', runSimulation);
}

function onParamChange() {
  // Update debit
  const debit = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const debitEl = document.getElementById('debitValue');
  if (debitEl) debitEl.textContent = debit.toFixed(2) + ' kg/s';
}

// ── SIMULATION ─────────────────────────────────────────────────────────
function runSimulation() {
  const btn = document.getElementById('launchBtn');
  const text = btn.querySelector('.launch-text');
  text.textContent = 'SIMULATION EN COURS...';
  gsap.to(btn, { scale: 0.96, duration: 0.1, yoyo: true, repeat: 1 });

  // Compute radii
  state.r1 = rayonSeuil(state.Q_kg, state.u_ms, state.stab, state.hauteur, SEUILS['ERPG-1'], state.dureeMin, state.typeBrutal);
  state.r2 = rayonSeuil(state.Q_kg, state.u_ms, state.stab, state.hauteur, SEUILS['ERPG-2'], state.dureeMin, state.typeBrutal);
  state.r3 = rayonSeuil(state.Q_kg, state.u_ms, state.stab, state.hauteur, SEUILS['ERPG-3'], state.dureeMin, state.typeBrutal);

  // Auto-detect population density
  const autoDens = getPopulationDensity(state.lat, state.lon);
  state.densPop = autoDens;
  document.getElementById('inputDens').value = autoDens;
  document.getElementById('outputDens').textContent = autoDens.toLocaleString();

  // Find hotspots
  state.hotspots = findHotspots(state.lat, state.lon, state.r3, state.r2, state.r1);

  // Monte Carlo
  state.mc = monteCarlo(state.Q_kg, state.u_ms, state.stab, state.hauteur, Math.min(state.mcIter, 2000), state.dureeMin, state.typeBrutal);

  // Gravity
  state.gravite = computeGravity();
  state.simulated = true;

  setTimeout(() => {
    text.textContent = 'LANCER LA SIMULATION';
    updateUI();
    updateMap();
    updateHotspotsUI();
    gsap.to(window, { scrollTo: { y: '#map-section', offsetY: 60 }, duration: 1.2, ease: 'power3.inOut' });
  }, 600);
}

function computeGravity() {
  const Q_kgs = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const d = Math.max(state.distPop, 20);
  const { sy, sz } = sigmaPG(d, state.stab);
  const denom = Math.PI * state.u_ms * sy * sz;
  const C_pop = denom > 1e-10 ? Math.min(Math.max((Q_kgs * 1000) / denom * 24.45 / 70.9, 1e-4), 500) : 1e-4;

  const expo = Math.max(Math.log10(C_pop + 0.01) / Math.log10(500.01), 0);
  const q_score = Math.max(0, Math.min(1, (Math.log10(state.Q_kg) - 1) / (Math.log10(60000) - 1)));
  const dur_sc = Math.min(state.dureeMin / 120, 1);
  let raw = expo * 5.5 + q_score * 2.5 + dur_sc * 1.0;

  const brutM = state.typeBrutal ? 1.3 : 1.0;
  const stabM = { A: 0.7, B: 0.85, C: 0.95, D: 1.0, E: 1.1, F: 1.2 }[state.stab] || 1.0;
  const densM = 0.8 + 0.4 * Math.min(Math.log10(Math.max(state.densPop, 1)) / Math.log10(15001), 1);
  const siteM = 1.0;
  const alerteM = state.earlyWarning ? 0.78 : 1.0;
  const epiM = Math.max(0.6, 1.0 - (state.ppeLevel - 1) * 0.1);
  const evacM = Math.max(0.75, 1.0 - Math.max(0, state.delaiEvac - 15) / 200);
  const coordM = Math.max(0.72, 1.0 - (state.coordSec - 1) * 0.09);
  const capaM = {1: 1.15, 2: 1.0, 3: 0.9}[state.capaMed] || 1.0;

  const dominoM = state.dominoEffect ? 1.15 : 1.0;
  const trainM = state.hasTrain ? 1.06 : 1.0;
  let vulnM = 1.0;
  if (state.hasHopital) vulnM += 0.05;
  if (state.hasEcole) vulnM += 0.06;
  if (state.hasGare) vulnM += 0.03;
  if (state.hasAdmin) vulnM += 0.02;
  vulnM = Math.min(1.15, vulnM);

  let score = raw * brutM * stabM * densM * siteM;
  score *= alerteM * epiM * evacM * coordM * capaM;
  score *= dominoM * trainM * vulnM;
  return Math.min(10, Math.max(0, score));
}

// ── UPDATE UI ──────────────────────────────────────────────────────────
function updateUI() {
  if (!state.simulated) return;

  // Zone cards
  animateValue('zoneR3', state.r3, ' m');
  animateValue('zoneR2', state.r2, ' m');
  animateValue('zoneR1', state.r1, ' m');
  animateValue('zoneEvac', Math.max(state.r2, 200), ' m');

  // Legend
  setText('legR3', Math.round(state.r3) + ' m');
  setText('legR2', Math.round(state.r2) + ' m');
  setText('legR1', Math.round(state.r1) + ' m');
  setText('legEvac', Math.round(Math.max(state.r2, 200)) + ' m');

  // KPIs
  const SECTEUR = 1 / 6;
  const surfE2 = Math.PI * (state.r2/1000)**2 * SECTEUR;
  const surfE3 = Math.PI * (state.r3/1000)**2 * SECTEUR;
  const surfEvac = Math.PI * (Math.max(state.r2, 200)/1000)**2;
  const popE2 = Math.round(surfE2 * state.densPop);
  const popE3 = Math.round(surfE3 * state.densPop);

  const TAUX_B = 0.028;
  const capaMultB = {1:1.0, 2:0.85, 3:0.75}[state.capaMed] || 1.0;
  const dominoMultB = state.dominoEffect ? 1.12 : 1.0;
  let vulnMultB = 1.0;
  if (state.hasEcole) vulnMultB += 0.07;
  if (state.hasHopital) vulnMultB += 0.05;
  if (state.hasGare) vulnMultB += 0.04;
  vulnMultB = Math.min(1.18, vulnMultB);

  const blesses = Math.max(0, Math.round(surfEvac * state.densPop * TAUX_B / 0.12 * capaMultB * dominoMultB * vulnMultB));
  const blessesE3 = Math.round(blesses * 0.31);
  const blessesE2 = blesses - blessesE3;

  let deaths = 0;
  if (state.gravite >= 7) {
    deaths = Math.round(surfEvac * state.densPop * 0.0014 / 0.12 * (state.gravite - 6) / 3);
  } else if (state.gravite >= 5) {
    deaths = Math.round(blesses * 0.005 * (state.gravite - 4));
  }
  deaths = Math.min(deaths, blessesE3);

  const arrival = state.distPop / Math.max(state.u_ms, 0.1) / 60;

  animateValue('kpiGravity', state.gravite, '/10', 1);
  animateValue('kpiPop', popE2, '');
  animateValue('kpiInjuries', blesses, '');
  animateValue('kpiArrival', arrival, ' min', 1);

  // MC at population distance
  const dRef = Object.keys(state.mc).map(Number).reduce((a, b) =>
    Math.abs(b - state.distPop) < Math.abs(a - state.distPop) ? b : a
  );
  const mcData = state.mc[dRef];
  animateValue('kpiMC', mcData.p_e2 * 100, '%', 1);

  animateValue('kpiDeaths', deaths, '');

  // Gravity bar
  const gravFill = document.getElementById('kpiGravityFill');
  if (gravFill) {
    gravFill.style.width = (state.gravite * 10) + '%';
    gravFill.style.background = state.gravite >= 7 ? '#EF4444' : state.gravite >= 4 ? '#F59E0B' : '#10B981';
  }

  // Decision banner
  const banner = document.getElementById('decisionBanner');
  const label = document.getElementById('decisionLabel');
  const detail = document.getElementById('decisionDetail');
  const physics = document.getElementById('decisionPhysics');
  banner.className = 'decision-banner';

  if (state.distPop <= state.r3) {
    banner.classList.add('red');
    label.textContent = 'CONFINEMENT OBLIGATOIRE';
    label.style.color = '#EF4444';
    detail.textContent = `Population a ${state.distPop}m en zone ROUGE ERPG-3 (${Math.round(state.r3)}m). Evacuation = exposition directe a >20ppm Cl2.`;
  } else if (state.distPop <= state.r2) {
    banner.classList.add('amber');
    label.textContent = arrival * 60 > state.delaiEvac ? 'EVACUATION POSSIBLE' : 'CONFINEMENT';
    label.style.color = '#F59E0B';
    detail.textContent = `Population a ${state.distPop}m en zone ORANGE ERPG-2 (${Math.round(state.r2)}m).`;
  } else {
    banner.classList.add('green');
    label.textContent = 'PAS D\'ACTION IMMEDIATE';
    label.style.color = '#10B981';
    detail.textContent = `Population a ${state.distPop}m en dehors des zones ERPG.`;
  }

  const Q_kgs = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const cPop = concPPM(Q_kgs, state.u_ms, state.distPop, 0, state.stab);
  physics.textContent = `C estimated: ${cPop.toFixed(3)} ppm · Q=${Q_kgs.toFixed(2)} kg/s · u=${state.u_ms} m/s · Stab=${state.stab}`;

  // MC stats
  setText('mcP50', mcData.p50.toFixed(3) + ' ppm');
  setText('mcP95', mcData.p95.toFixed(3) + ' ppm');
  setText('mcPE1', (mcData.p_e1 * 100).toFixed(1) + '%');
  setText('mcPE2', (mcData.p_e2 * 100).toFixed(1) + '%');
  setText('mcPE3', (mcData.p_e3 * 100).toFixed(1) + '%');
  setText('mcMean', mcData.mean.toFixed(3) + ' ppm');

  setText('legMC', (mcData.p_e2 * 100).toFixed(0) + '%');
  setText('legG', state.gravite.toFixed(1) + '/10');

  const legMC = document.getElementById('legMC');
  const legG = document.getElementById('legG');
  if (legMC) legMC.style.background = mcData.p_e2 >= 0.7 ? '#B91C1C' : mcData.p_e2 >= 0.3 ? '#B45309' : '#15803D';
  if (legG) legG.style.background = state.gravite >= 7 ? '#DC2626' : state.gravite >= 4 ? '#D97706' : '#16A34A';

  // MC alert
  const mcAlert = document.getElementById('mcAlert');
  const mcAlertText = document.getElementById('mcAlertText');
  if (mcData.p_e2 >= 0.7) {
    mcAlert.className = 'mc-alert red';
    mcAlertText.textContent = `RISQUE ELEVE : ${(mcData.p_e2*100).toFixed(0)}% de probabilite de depassement ERPG-2 a ${dRef}m. Action immediate requise.`;
  } else if (mcData.p_e2 >= 0.3) {
    mcAlert.className = 'mc-alert amber';
    mcAlertText.textContent = `RISQUE MODERE : ${(mcData.p_e2*100).toFixed(0)}% de probabilite de depassement ERPG-2 a ${dRef}m.`;
  } else {
    mcAlert.className = 'mc-alert';
    mcAlertText.textContent = `RISQUE FAIBLE : ${(mcData.p_e2*100).toFixed(0)}% de probabilite de depassement ERPG-2 a ${dRef}m.`;
  }

  setText('mcIterCount', `N=${state.mcIter.toLocaleString()}`);

  drawConcChart();
  drawMCChart();
}

function animateValue(id, target, suffix = '', decimals = 0) {
  const el = document.getElementById(id);
  if (!el) return;
  gsap.to({ val: 0 }, {
    val: target,
    duration: 1.2,
    ease: 'power2.out',
    onUpdate: function () {
      const v = this.targets()[0].val;
      el.textContent = (decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString()) + suffix;
    },
  });
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ── CHARTS (Canvas 2D) ────────────────────────────────────────────────
function drawConcChart() {
  const canvas = document.getElementById('concChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.parentElement.clientWidth - 32;
  const H = 300;
  canvas.width = W * 2;
  canvas.height = H * 2;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(2, 2);

  const Q_kgs = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const maxDist = Math.max(state.r1 * 1.2, 500);
  const pad = { t: 20, r: 20, b: 40, l: 60 };
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;

  const points = [];
  for (let i = 0; i <= 200; i++) {
    const x = 10 + (maxDist - 10) * i / 200;
    const c = concPPM(Q_kgs, state.u_ms, x, 0, state.stab, state.typeBrutal ? 0 : state.hauteur);
    points.push({ x, c: Math.max(c, 0.001) });
  }

  const maxC = Math.max(...points.map(p => p.c), 25);
  const logMax = Math.log10(maxC);
  const logMin = Math.log10(0.001);

  ctx.clearRect(0, 0, W, H);

  // Background zones
  const zones = [
    { min: 20, max: maxC, color: 'rgba(239,68,68,0.06)' },
    { min: 3, max: 20, color: 'rgba(245,158,11,0.06)' },
    { min: 1, max: 3, color: 'rgba(16,185,129,0.06)' },
  ];
  zones.forEach(z => {
    const y1 = pad.t + (1 - (Math.log10(z.max) - logMin) / (logMax - logMin)) * ph;
    const y2 = pad.t + (1 - (Math.log10(z.min) - logMin) / (logMax - logMin)) * ph;
    ctx.fillStyle = z.color;
    ctx.fillRect(pad.l, Math.max(y1, pad.t), pw, Math.min(y2, H - pad.b) - Math.max(y1, pad.t));
  });

  // Grid
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 0.5;
  [0.01, 0.1, 1, 3, 10, 20, 100].forEach(v => {
    if (v > maxC) return;
    const y = pad.t + (1 - (Math.log10(v) - logMin) / (logMax - logMin)) * ph;
    if (y < pad.t || y > H - pad.b) return;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText(v >= 1 ? v : v.toFixed(2), pad.l - 6, y + 3);
  });

  // Threshold lines
  [{ v: 1, c: '#10B981', l: 'ERPG-1' }, { v: 3, c: '#F59E0B', l: 'ERPG-2' }, { v: 20, c: '#EF4444', l: 'ERPG-3' }].forEach(({ v, c, l }) => {
    const y = pad.t + (1 - (Math.log10(v) - logMin) / (logMax - logMin)) * ph;
    if (y < pad.t || y > H - pad.b) return;
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = c;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = c;
    ctx.font = '8px JetBrains Mono';
    ctx.textAlign = 'left';
    ctx.fillText(l, W - pad.r - 40, y - 4);
  });

  // Curve
  ctx.beginPath();
  points.forEach((p, i) => {
    const px = pad.l + (p.x / maxDist) * pw;
    const py = pad.t + (1 - (Math.log10(p.c) - logMin) / (logMax - logMin)) * ph;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.strokeStyle = '#3B82F6';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Fill under
  const lastP = points[points.length - 1];
  ctx.lineTo(pad.l + (lastP.x / maxDist) * pw, H - pad.b);
  ctx.lineTo(pad.l, H - pad.b);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
  grad.addColorStop(0, 'rgba(59,130,246,0.15)');
  grad.addColorStop(1, 'rgba(59,130,246,0)');
  ctx.fillStyle = grad;
  ctx.fill();

  // Axes labels
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = '10px Inter';
  ctx.textAlign = 'center';
  ctx.fillText('Distance (m)', W / 2, H - 6);

  // X ticks
  const xTicks = [100, 500, 1000, 2000, 5000, 10000].filter(v => v <= maxDist);
  xTicks.forEach(v => {
    const px = pad.l + (v / maxDist) * pw;
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText(v >= 1000 ? (v / 1000) + 'k' : v, px, H - pad.b + 14);
  });
}

function drawMCChart() {
  if (!state.mc) return;
  const canvas = document.getElementById('mcChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.parentElement.clientWidth - 32;
  const H = 350;
  canvas.width = W * 2;
  canvas.height = H * 2;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(2, 2);

  const pad = { t: 20, r: 20, b: 40, l: 60 };
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;
  const distances = Object.keys(state.mc).map(Number).sort((a, b) => a - b);

  ctx.clearRect(0, 0, W, H);

  // Grid
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 0.5;
  [0, 20, 40, 60, 80, 100].forEach(v => {
    const y = pad.t + (1 - v / 100) * ph;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText(v + '%', pad.l - 6, y + 3);
  });

  const maxD = distances[distances.length - 1];
  const xScale = d => pad.l + (d / maxD) * pw;
  const yScale = v => pad.t + (1 - v) * ph;

  // Draw lines for each ERPG
  const series = [
    { key: 'p_e3', color: '#EF4444', label: 'P(C>ERPG-3)' },
    { key: 'p_e2', color: '#F59E0B', label: 'P(C>ERPG-2)' },
    { key: 'p_e1', color: '#10B981', label: 'P(C>ERPG-1)' },
  ];

  series.forEach(({ key, color }) => {
    // Fill
    ctx.beginPath();
    distances.forEach((d, i) => {
      const px = xScale(d);
      const py = yScale(state.mc[d][key]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.lineTo(xScale(maxD), yScale(0));
    ctx.lineTo(xScale(distances[0]), yScale(0));
    ctx.closePath();
    ctx.fillStyle = color.replace(')', ',0.08)').replace('rgb', 'rgba');
    ctx.fill();

    // Line
    ctx.beginPath();
    distances.forEach((d, i) => {
      const px = xScale(d);
      const py = yScale(state.mc[d][key]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Dots
    distances.forEach(d => {
      const px = xScale(d);
      const py = yScale(state.mc[d][key]);
      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });
  });

  // Legend
  series.forEach(({ color, label }, i) => {
    const lx = W - pad.r - 130;
    const ly = pad.t + 15 + i * 16;
    ctx.fillStyle = color;
    ctx.fillRect(lx, ly - 4, 10, 10);
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'left';
    ctx.fillText(label, lx + 14, ly + 5);
  });

  // X labels
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = '10px Inter';
  ctx.textAlign = 'center';
  ctx.fillText('Distance (m)', W / 2, H - 6);
  distances.forEach(d => {
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText(d >= 1000 ? (d / 1000) + 'k' : d, xScale(d), H - pad.b + 14);
  });
}

// ── LEAFLET MAP ────────────────────────────────────────────────────────
let map, zoneLayers = [];

function setupMap() {
  map = L.map('map', {
    center: [state.lat, state.lon],
    zoom: 13,
    zoomControl: false,
  });

  L.control.zoom({ position: 'topright' }).addTo(map);

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'ESRI World Imagery',
    maxZoom: 18,
  }).addTo(map);

  // Map tile controls
  document.querySelectorAll('.map-ctrl').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.map-ctrl').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Source marker with pulse
  const pulseIcon = L.divIcon({
    className: '',
    html: `<div style="position:relative;width:28px;height:28px;">
      <div style="position:absolute;inset:0;border-radius:50%;background:rgba(239,68,68,0.3);animation:mapPulse 2s ease-in-out infinite;"></div>
      <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;background:#EF4444;border:2px solid #fff;box-shadow:0 0 12px rgba(239,68,68,0.5);"></div>
    </div>
    <style>@keyframes mapPulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.8);opacity:0.3}}</style>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
  L.marker([state.lat, state.lon], { icon: pulseIcon }).addTo(map);

  setText('mapCoord', `${state.lat.toFixed(4)}°N, ${Math.abs(state.lon).toFixed(4)}°W`);
}

function updateMap() {
  if (!map || !state.simulated) return;

  // Clear old zones
  zoneLayers.forEach(l => map.removeLayer(l));
  zoneLayers = [];

  const propDir = (state.dirVent + 180) % 360;

  const zones = [
    { r: state.r1, fill: '#86EFAC', border: '#16A34A', opacity: 0.3, label: 'ERPG-1' },
    { r: state.r2, fill: '#FDB168', border: '#D97706', opacity: 0.35, label: 'ERPG-2' },
    { r: state.r3, fill: '#FC8181', border: '#C53030', opacity: 0.4, label: 'ERPG-3' },
  ];

  zones.forEach(z => {
    const pts = conePolygon(state.lat, state.lon, z.r, state.dirVent);
    const poly = L.polygon(pts, {
      color: z.border,
      weight: 3,
      fillColor: z.fill,
      fillOpacity: z.opacity,
    }).addTo(map);
    poly.bindTooltip(`${z.label}: ${Math.round(z.r)}m`, { sticky: true });
    zoneLayers.push(poly);
  });

  // Evacuation perimeter
  const evac = Math.max(state.r2, 200);
  const evacPts = conePolygon(state.lat, state.lon, evac, state.dirVent, 42);
  const evacPoly = L.polygon(evacPts, {
    color: '#F59E0B',
    weight: 2,
    dashArray: '10 5',
    fillColor: '#FEF3C7',
    fillOpacity: 0.05,
  }).addTo(map);
  zoneLayers.push(evacPoly);

  // Wind arrow
  const tipLatLon = geoPoint(state.lat, state.lon, Math.max(state.r2 * 0.3, 300), propDir);
  const arrow = L.polyline([[state.lat, state.lon], tipLatLon], {
    color: '#3B82F6',
    weight: 3,
    opacity: 0.8,
  }).addTo(map);
  zoneLayers.push(arrow);

  // Fit bounds
  const allPts = conePolygon(state.lat, state.lon, state.r1, state.dirVent, 40);
  const bounds = L.latLngBounds(allPts);
  map.fitBounds(bounds.pad(0.15));
}

function geoPoint(lat, lon, dist, bearing) {
  const R = 6371000;
  const latR = lat * Math.PI / 180;
  const bearR = bearing * Math.PI / 180;
  const dR = dist / R;
  const newLat = Math.asin(Math.sin(latR) * Math.cos(dR) + Math.cos(latR) * Math.sin(dR) * Math.cos(bearR));
  const newLon = lon * Math.PI / 180 + Math.atan2(
    Math.sin(bearR) * Math.sin(dR) * Math.cos(latR),
    Math.cos(dR) - Math.sin(latR) * Math.sin(newLat)
  );
  return [newLat * 180 / Math.PI, newLon * 180 / Math.PI];
}

function conePolygon(lat, lon, radius, windFrom, halfAngle = 36) {
  const propDir = (windFrom + 180) % 360;
  const pts = [];
  const nArc = 80;

  for (let i = 0; i <= nArc; i++) {
    const t = -1 + 2 * i / nArc;
    const bearing = (propDir + t * halfAngle + 360) % 360;
    const rMod = radius * Math.exp(-0.5 * (t * 1.8) ** 2);
    pts.push(geoPoint(lat, lon, Math.max(rMod, radius * 0.04), bearing));
  }

  const backR = radius * 0.06;
  const backDir = (propDir + 180) % 360;
  for (let i = 0; i <= 16; i++) {
    const angle = (backDir - 90 + 180 * i / 16 + 360) % 360;
    pts.push(geoPoint(lat, lon, backR, angle));
  }

  pts.push(pts[0]);
  return pts;
}

// ── HOTSPOTS UI ───────────────────────────────────────────────────────
function updateHotspotsUI() {
  const table = document.getElementById('hotspotsTable');
  if (!table) return;
  const hs = state.hotspots || { 'ERPG-3': [], 'ERPG-2': [], 'ERPG-1': [] };
  let html = `<thead><tr>
    <th>Site</th><th>Type</th><th>Zone</th><th>Distance</th><th>Priorite</th><th>Risque</th>
  </tr></thead><tbody>`;
  let count = 0;
  for (const zone of ['ERPG-3', 'ERPG-2', 'ERPG-1']) {
    const cls = zone === 'ERPG-3' ? 'erpg3' : zone === 'ERPG-2' ? 'erpg2' : 'erpg1';
    for (const h of (hs[zone] || [])) {
      const prioCls = h.priority === 'CRITIQUE' ? 'critique' : h.priority === 'ELEVE' ? 'eleve' : 'modere';
      html += `<tr>
        <td><strong>${h.icon} ${h.name}</strong></td>
        <td>${h.type}</td>
        <td><span class="zone-badge ${cls}">${zone}</span></td>
        <td>${h.dist} m</td>
        <td><span class="priority-badge ${prioCls}">${h.priority}</span></td>
        <td>${h.risk}</td>
      </tr>`;
      count++;
    }
  }
  if (count === 0) {
    html += '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">Aucun hotspot detecte dans les zones d\'impact</td></tr>';
  }
  html += '</tbody>';
  table.innerHTML = html;

  const countEl = document.getElementById('hotspotsCount');
  if (countEl) countEl.textContent = count;

  // Add hotspot markers to map
  if (map && state.simulated) {
    for (const zone of ['ERPG-3', 'ERPG-2', 'ERPG-1']) {
      const color = zone === 'ERPG-3' ? '#EF4444' : zone === 'ERPG-2' ? '#F59E0B' : '#3B82F6';
      for (const h of (hs[zone] || [])) {
        const icon = L.divIcon({
          className: '',
          html: `<div style="background:${color};color:#fff;font-size:14px;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 8px ${color}80;">${h.icon}</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });
        L.marker([h.lat, h.lon], { icon })
          .bindPopup(`<b>${h.icon} ${h.name}</b><br>${zone} — ${h.dist} m<br><em>${h.risk}</em>`)
          .addTo(map);
      }
    }
  }
}

// ── PDF GENERATION ────────────────────────────────────────────────────
function generatePDF() {
  if (!state.simulated) {
    alert('Veuillez lancer une simulation d\'abord.');
    return;
  }
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF('p', 'mm', 'a4');
  const W = 210, H = 297;
  const now = new Date();
  const dateStr = now.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  const refStr = 'HM-' + now.toISOString().slice(0,10).replace(/-/g,'') + '-' + now.toTimeString().slice(0,5).replace(':','');

  const NAVY = [12, 35, 64];
  const GOLD = [201, 162, 39];
  const RED = [185, 28, 28];
  const BLUE = [59, 130, 246];

  // ── PAGE 1: COVER ──────────────────────────────────────────────
  doc.setFillColor(...NAVY);
  doc.rect(0, 0, W, H, 'F');

  // Gold bar top
  doc.setFillColor(...GOLD);
  doc.rect(0, 0, W, 10, 'F');

  // Institution
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.text('ROYAUME DU MAROC', 18, 22);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(147, 197, 253);
  doc.text('Ministere de l\'Interieur', 18, 28);
  doc.text('Direction Generale des Affaires Interieures', 18, 33);
  doc.text('Direction de la Securite et de la Documentation', 18, 38);

  // HAZMOD title
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(36);
  doc.setFont('helvetica', 'bold');
  doc.text('HAZMOD', W / 2, 70, { align: 'center' });
  doc.setFontSize(10);
  doc.setTextColor(147, 197, 253);
  doc.text('Hazardous Materials Modeling System', W / 2, 78, { align: 'center' });

  // Gold line
  doc.setDrawColor(...GOLD);
  doc.setLineWidth(0.8);
  doc.line(25, 84, W - 25, 84);

  // Report title
  doc.setFontSize(14);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.text('RAPPORT OFFICIEL D\'ANALYSE DES RISQUES', W / 2, 96, { align: 'center' });
  doc.setFontSize(11);
  doc.setTextColor(...GOLD);
  doc.text('Dispersion Atmospherique — Chlore (Cl2)', W / 2, 104, { align: 'center' });

  // Scenario box
  doc.setFillColor(0, 0, 0, 90);
  doc.roundedRect(20, 120, W - 40, 50, 4, 4, 'F');
  doc.setDrawColor(...BLUE);
  doc.setLineWidth(0.5);
  doc.roundedRect(20, 120, W - 40, 50, 4, 4, 'S');

  doc.setFontSize(9);
  doc.setTextColor(...GOLD);
  doc.setFont('helvetica', 'bold');
  doc.text('PARAMETRES DU SCENARIO', W / 2, 130, { align: 'center' });

  const propDir = (state.dirVent + 180) % 360;
  const DIRS = ['N','NE','E','SE','S','SO','O','NO'];
  const propLbl = DIRS[Math.round(propDir / 45) % 8];

  doc.setFontSize(7.5);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'normal');
  const infos = [
    [`Quantite Cl2 : ${state.Q_kg.toLocaleString()} kg`, `Type : ${state.typeBrutal ? 'Brutal' : 'Continu'}`],
    [`Vent : ${state.u_ms} m/s — ${state.dirVent}deg vers ${propDir.toFixed(0)}deg (${propLbl})`, `Stabilite : Classe ${state.stab}`],
    [`Zone ERPG-3 : ${state.r3.toFixed(0)} m`, `Zone ERPG-2 : ${state.r2.toFixed(0)} m`],
    [`Coord. : ${state.lat.toFixed(4)}N / ${state.lon.toFixed(4)}E`, `Gravite G : ${state.gravite.toFixed(1)} / 10`],
  ];
  infos.forEach(([l, r], i) => {
    const y = 138 + i * 7;
    doc.text(l, 28, y);
    doc.text(r, W / 2 + 5, y);
  });

  // Alert badge
  const g = state.gravite;
  const alertLabel = g >= 7 ? 'ALERTE ROUGE — Danger Vital' : g >= 4 ? 'ALERTE ORANGE — Risque Significatif' : 'ALERTE JAUNE — Risque Modere';
  const alertColor = g >= 7 ? [220, 38, 38] : g >= 4 ? [217, 119, 6] : [146, 64, 14];
  doc.setFillColor(...alertColor);
  doc.roundedRect(30, 178, W - 60, 10, 3, 3, 'F');
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text(alertLabel, W / 2, 185, { align: 'center' });

  // Date & ref
  doc.setFontSize(8);
  doc.setTextColor(203, 213, 225);
  doc.setFont('helvetica', 'normal');
  doc.text('Etabli le ' + dateStr, W / 2, 200, { align: 'center' });
  doc.setTextColor(...GOLD);
  doc.setFont('helvetica', 'bold');
  doc.text('Ref. ' + refStr, W / 2, 208, { align: 'center' });

  // Footer
  doc.setFillColor(...GOLD);
  doc.rect(0, H - 12, W, 3, 'F');
  doc.setFillColor(...NAVY);
  doc.rect(0, H - 9, W, 9, 'F');
  doc.setFontSize(6);
  doc.setTextColor(100, 116, 139);
  doc.text('DOCUMENT A DIFFUSION RESTREINTE — Usage operationnel uniquement', W / 2, H - 3, { align: 'center' });

  // ── PAGE 2: PARAMETRES ─────────────────────────────────────────
  doc.addPage();
  addPageHeader(doc, 2, refStr);

  doc.setFontSize(12);
  doc.setTextColor(...NAVY);
  doc.setFont('helvetica', 'bold');
  doc.text('01  PARAMETRES DU SCENARIO SIMULE', 15, 25);
  doc.setDrawColor(...GOLD);
  doc.setLineWidth(1);
  doc.line(15, 27, W - 15, 27);

  doc.autoTable({
    startY: 32,
    head: [['Parametre', 'Valeur', 'Parametre', 'Valeur']],
    body: [
      ['Localisation', `${state.lat.toFixed(4)}N / ${state.lon.toFixed(4)}E`, 'Densite population', `${state.densPop.toLocaleString()} hab/km2`],
      ['Quantite Cl2', `${state.Q_kg.toLocaleString()} kg`, 'Distance population', `${state.distPop} m`],
      ['Type liberation', state.typeBrutal ? 'Brutal (instantane)' : 'Continu (fuite)', 'Duree liberation', `${state.dureeMin} min`],
      ['Vitesse vent', `${state.u_ms} m/s`, 'Direction vent', `${state.dirVent}deg vers ${propLbl}`],
      ['Stabilite atm.', `Classe ${state.stab}`, 'Hauteur source', `${state.hauteur} m`],
      ['Niveau EPI', `Niveau ${state.ppeLevel}`, 'Alerte precoce', state.earlyWarning ? 'Oui' : 'Non'],
      ['Delai evacuation', `${state.delaiEvac} min`, 'Coordination secours', `${state.coordSec}/4`],
      ['Iterations MC', `${state.mcIter.toLocaleString()}`, 'Indice de gravite', `${state.gravite.toFixed(1)}/10`],
    ],
    theme: 'grid',
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontSize: 7.5, fontStyle: 'bold' },
    bodyStyles: { fontSize: 7, textColor: [30, 30, 30] },
    alternateRowStyles: { fillColor: [240, 249, 255] },
    margin: { left: 15, right: 15 },
  });

  // ── PAGE 3: RESULTATS ──────────────────────────────────────────
  doc.addPage();
  addPageHeader(doc, 3, refStr);

  doc.setFontSize(12);
  doc.setTextColor(...NAVY);
  doc.setFont('helvetica', 'bold');
  doc.text('02  RESULTATS DE LA SIMULATION PHYSIQUE', 15, 25);
  doc.setDrawColor(...GOLD);
  doc.line(15, 27, W - 15, 27);
  doc.setFontSize(7);
  doc.setTextColor(100, 100, 100);
  doc.setFont('helvetica', 'italic');
  doc.text('Modele Pasquill-Gifford (Briggs 1973) — Gaz lourd calibre ALOHA (erreur <= 11%)', 15, 32);

  const SECTEUR = 1 / 6;
  const surfE2 = Math.PI * (state.r2/1000)**2 * SECTEUR;
  const surfE3 = Math.PI * (state.r3/1000)**2 * SECTEUR;
  const surfE1 = Math.PI * (state.r1/1000)**2 * SECTEUR;
  const surfEvac = Math.PI * (Math.max(state.r2, 200)/1000)**2;
  const popE2 = Math.round(surfE2 * state.densPop);
  const popE3 = Math.round(surfE3 * state.densPop);
  const popE1 = Math.round(surfE1 * state.densPop);
  const blesses = Math.max(0, Math.round(surfEvac * state.densPop * 0.028 / 0.12));
  const blessesE3 = Math.round(blesses * 0.31);
  const blessesE2 = blesses - blessesE3;
  let deaths = 0;
  if (g >= 7) deaths = Math.round(surfEvac * state.densPop * 0.0014 / 0.12 * (g - 6) / 3);
  else if (g >= 5) deaths = Math.round(blesses * 0.005 * (g - 4));

  doc.autoTable({
    startY: 36,
    head: [['Zone NRBC', 'Seuil', 'Rayon axial', 'Surface', 'Pop. exposee', 'Blesses est.', 'Decision']],
    body: [
      ['ERPG-3', '> 20 ppm', `${state.r3.toFixed(0)} m`, `${surfE3.toFixed(3)} km2`, `${popE3.toLocaleString()}`, `${blessesE3.toLocaleString()}`, 'Evacuation totale + EPI A'],
      ['ERPG-2', '3 - 20 ppm', `${state.r2.toFixed(0)} m`, `${surfE2.toFixed(3)} km2`, `${popE2.toLocaleString()}`, `${blessesE2.toLocaleString()}`, 'Evacuation partielle'],
      ['ERPG-1', '1 - 3 ppm', `${state.r1.toFixed(0)} m`, `${surfE1.toFixed(3)} km2`, `${popE1.toLocaleString()}`, '—', 'Confinement preventif'],
    ],
    theme: 'grid',
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontSize: 7, fontStyle: 'bold' },
    bodyStyles: { fontSize: 7 },
    margin: { left: 15, right: 15 },
    didParseCell: (data) => {
      if (data.section === 'body') {
        if (data.row.index === 0) data.cell.styles.fillColor = [255, 241, 242];
        if (data.row.index === 1) data.cell.styles.fillColor = [255, 251, 235];
        if (data.row.index === 2) data.cell.styles.fillColor = [240, 255, 244];
      }
    },
  });

  let y = doc.lastAutoTable.finalY + 8;
  doc.setFontSize(10);
  doc.setTextColor(...NAVY);
  doc.setFont('helvetica', 'bold');
  doc.text('Bilan humain estime', 15, y);
  y += 5;

  doc.autoTable({
    startY: y,
    head: [['Indicateur', 'Valeur', 'Methode']],
    body: [
      ['Blesses totaux', blesses.toLocaleString(), `TAUX=2.8‰ x surf=${surfEvac.toFixed(2)} km2 x densite`],
      ['Urgences Absolues (ERPG-3)', blessesE3.toLocaleString(), '31% des blesses — exposition > 20 ppm'],
      ['Urgences Relatives (ERPG-2)', blessesE2.toLocaleString(), '69% des blesses — effets irreversibles'],
      ['Deces estimes', deaths.toString(), `G=${g.toFixed(1)} — Modele probit simplifie`],
      ['Population ERPG-2', popE2.toLocaleString(), `Secteur ${(SECTEUR*100).toFixed(0)}% x surf orange x ${state.densPop} hab/km2`],
    ],
    theme: 'grid',
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontSize: 7 },
    bodyStyles: { fontSize: 7 },
    margin: { left: 15, right: 15 },
  });

  // ── PAGE 4: MONTE CARLO ────────────────────────────────────────
  doc.addPage();
  addPageHeader(doc, 4, refStr);

  doc.setFontSize(12);
  doc.setTextColor(...NAVY);
  doc.setFont('helvetica', 'bold');
  doc.text('03  ANALYSE PROBABILISTE — MONTE CARLO', 15, 25);
  doc.setDrawColor(...GOLD);
  doc.line(15, 27, W - 15, 27);

  if (state.mc) {
    const mcRows = [];
    for (const [d, r] of Object.entries(state.mc).sort((a, b) => Number(a[0]) - Number(b[0]))) {
      const risk = r.p_e3 > 0.15 ? 'CRITIQUE' : r.p_e2 > 0.20 ? 'ELEVE' : r.p_e1 > 0.30 ? 'MODERE' : 'FAIBLE';
      mcRows.push([
        `${d} m`,
        `${r.p50.toFixed(4)} ppm`,
        `${r.p95.toFixed(4)} ppm`,
        `${(r.p_e1 * 100).toFixed(1)}%`,
        `${(r.p_e2 * 100).toFixed(1)}%`,
        `${(r.p_e3 * 100).toFixed(1)}%`,
        risk,
      ]);
    }
    doc.autoTable({
      startY: 32,
      head: [['Distance', 'Mediane P50', 'P95 Pire cas', 'P(>ERPG-1)', 'P(>ERPG-2)', 'P(>ERPG-3)', 'Risque']],
      body: mcRows,
      theme: 'grid',
      headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontSize: 7 },
      bodyStyles: { fontSize: 6.5 },
      margin: { left: 15, right: 15 },
    });
  }

  // ── PAGE 5: HOTSPOTS ───────────────────────────────────────────
  const hs = state.hotspots || {};
  const allHs = [...(hs['ERPG-3'] || []), ...(hs['ERPG-2'] || []), ...(hs['ERPG-1'] || [])];
  if (allHs.length > 0) {
    doc.addPage();
    addPageHeader(doc, 5, refStr);

    doc.setFontSize(12);
    doc.setTextColor(...NAVY);
    doc.setFont('helvetica', 'bold');
    doc.text('04  INVENTAIRE DES HOTSPOTS IDENTIFIES', 15, 25);
    doc.setDrawColor(...GOLD);
    doc.line(15, 27, W - 15, 27);

    const hsRows = [];
    for (const zone of ['ERPG-3', 'ERPG-2', 'ERPG-1']) {
      for (const h of (hs[zone] || [])) {
        hsRows.push([
          h.icon,
          h.name,
          zone,
          `${h.dist} m`,
          h.priority,
          h.risk,
          `${h.lat.toFixed(4)}N ${h.lon.toFixed(4)}E`,
        ]);
      }
    }
    doc.autoTable({
      startY: 32,
      head: [['', 'Etablissement', 'Zone', 'Distance', 'Priorite', 'Risque', 'Coordonnees']],
      body: hsRows,
      theme: 'grid',
      headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontSize: 7 },
      bodyStyles: { fontSize: 6.5 },
      columnStyles: { 0: { cellWidth: 8 }, 6: { fontSize: 5.5 } },
      margin: { left: 15, right: 15 },
      didParseCell: (data) => {
        if (data.section === 'body') {
          const zone = data.row.raw[2];
          if (zone === 'ERPG-3') data.cell.styles.fillColor = [255, 241, 242];
          else if (zone === 'ERPG-2') data.cell.styles.fillColor = [255, 251, 235];
          else data.cell.styles.fillColor = [240, 255, 244];
        }
      },
    });
  }

  // ── PAGE 6: OPERATIONS ─────────────────────────────────────────
  doc.addPage();
  addPageHeader(doc, allHs.length > 0 ? 6 : 5, refStr);

  doc.setFontSize(12);
  doc.setTextColor(...NAVY);
  doc.setFont('helvetica', 'bold');
  const opNum = allHs.length > 0 ? '05' : '04';
  doc.text(`${opNum}  ORGANISATION DES SECOURS — PLAN ORSEC`, 15, 25);
  doc.setDrawColor(...GOLD);
  doc.line(15, 27, W - 15, 27);

  doc.autoTable({
    startY: 32,
    head: [['Phase', 'Periode', 'Actions', 'Responsable']],
    body: [
      ['1 — Prise en main', 'T0 → T+25 min', 'Alerte CTA, zonage reflexe 50m, activation PCO, identification SITAC', 'COS / Chef SDIS'],
      ['2 — Analyse menace', 'T+25 → T+60 min', 'Deploiement CMIC, confirmation chimique, ordres confinement, VMC coupees', 'CMIC / Prefet'],
      ['3 — Crise majeure', 'T+60 → T+130 min', 'Gestion effet domino, saturation hopitaux, Plan Blanc, populations vulnerables', 'DOS / Prefet'],
      ['4 — Stabilisation', 'T+130 → T+150 min', 'Dissipation confirmee, levee progressive zones, decontamination, RETEX', 'DOS / COS'],
    ],
    theme: 'grid',
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontSize: 7.5 },
    bodyStyles: { fontSize: 7 },
    margin: { left: 15, right: 15 },
    columnStyles: { 2: { cellWidth: 80 } },
  });

  // Confidential footer on all pages
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 2; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(6);
    doc.setTextColor(150, 150, 150);
    doc.text(`HAZMOD — Rapport Confidentiel — Ref. ${refStr} — DIFFUSION RESTREINTE`, 15, H - 5);
    doc.setTextColor(...GOLD);
    doc.setFont('helvetica', 'bold');
    doc.text(`Page ${i - 1} / ${totalPages - 1}`, W - 15, H - 5, { align: 'right' });
    doc.setFont('helvetica', 'normal');
  }

  doc.save(`HazMod_Rapport_${refStr}.pdf`);
}

function addPageHeader(doc, pageNum, refStr) {
  const W = 210;
  doc.setFillColor(12, 35, 64);
  doc.rect(0, 0, W, 14, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.text('ROYAUME DU MAROC — MINISTERE DE L\'INTERIEUR', 15, 6);
  doc.setFontSize(6);
  doc.setFont('helvetica', 'normal');
  doc.text('Direction Generale des Affaires Interieures — Direction de la Securite', 15, 11);
  doc.setDrawColor(201, 162, 39);
  doc.setLineWidth(0.8);
  doc.line(0, 14, W, 14);
}

// ── WINDOW RESIZE ──────────────────────────────────────────────────────
window.addEventListener('resize', () => {
  if (renderer) {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
  if (state.simulated) {
    drawConcChart();
    drawMCChart();
  }
});

// ── INIT ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initThree();
  animateLoader();
});
