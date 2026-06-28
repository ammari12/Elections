const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
  TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

// ─── Couleurs ─────────────────────────────────────────────────────────────────
const C = {
  primary:   "1B3A6B",   // Bleu marine foncé
  accent:    "C0392B",   // Rouge professionnel
  light:     "D6E4F0",   // Bleu très clair
  header:    "1B3A6B",
  tableHead: "1B3A6B",
  tableRow:  "EBF5FB",
  text:      "1A1A1A",
  gray:      "7F8C8D",
  white:     "FFFFFF",
};

// ─── Bordures helpers ──────────────────────────────────────────────────────────
const border1 = (color="CCCCCC") => ({ style: BorderStyle.SINGLE, size: 1, color });
const borders = (c="CCCCCC") => ({ top:border1(c),bottom:border1(c),left:border1(c),right:border1(c) });
const noBorder = { style: BorderStyle.NIL, size: 0, color: "FFFFFF" };
const noBorders = { top:noBorder,bottom:noBorder,left:noBorder,right:noBorder };

// ─── Helpers texte ─────────────────────────────────────────────────────────────
const run = (text, opts={}) => new TextRun({ text, font:"Arial", size: opts.size||22, ...opts });
const bold = (text, size=22, color=C.text) => run(text,{bold:true,size,color});
const accent = (text) => run(text,{bold:true,color:C.accent,size:22});

const heading1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  pageBreakBefore: true,
  spacing: { before: 480, after: 240 },
  children: [new TextRun({ text, font:"Arial", size:36, bold:true, color:C.primary })],
});

const heading2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 360, after: 180 },
  children: [new TextRun({ text, font:"Arial", size:28, bold:true, color:C.primary })],
  border: { bottom: { style:BorderStyle.SINGLE, size:4, color:C.primary, space:2 } },
});

const heading3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 240, after: 120 },
  children: [new TextRun({ text, font:"Arial", size:24, bold:true, color:C.accent })],
});

const para = (children, opts={}) => new Paragraph({
  spacing: { before:120, after:120, line:320 },
  alignment: AlignmentType.JUSTIFIED,
  ...opts,
  children: Array.isArray(children) ? children : [run(children)],
});

const bullet = (text, level=0) => new Paragraph({
  numbering: { reference:"bullets", level },
  spacing: { before:60, after:60 },
  children: [run(text)],
});

const lineRule = () => new Paragraph({
  spacing: { before:120, after:120 },
  border: { bottom: { style:BorderStyle.SINGLE, size:8, color:C.primary, space:2 } },
  children: [],
});

// ─── Table helpers ─────────────────────────────────────────────────────────────
const W = 9026; // A4 content width in DXA (1" margins)

const tblCell = (children, opts={}) => new TableCell({
  borders: opts.borders || borders(),
  width: opts.width ? { size: opts.width, type:WidthType.DXA } : undefined,
  shading: opts.fill ? { fill:opts.fill, type:ShadingType.CLEAR } : undefined,
  margins: { top:80, bottom:80, left:150, right:150 },
  verticalAlign: opts.va || VerticalAlign.CENTER,
  children: Array.isArray(children) ? children : [para([run(children, opts.run||{})])],
});

const tblHeaderRow = (cells, widths) => new TableRow({
  tableHeader: true,
  children: cells.map((c,i) => tblCell(
    [para([bold(c, 20, C.white)])],
    { fill:C.tableHead, width:widths[i], borders:borders(C.primary) }
  ))
});

const tblRow = (cells, widths, fill=C.white) => new TableRow({
  children: cells.map((c,i) => tblCell(c, { fill, width:widths[i] }))
});

const table = (rows, widths) => new Table({
  width: { size:W, type:WidthType.DXA },
  columnWidths: widths,
  rows,
});

// ─── Page de titre ─────────────────────────────────────────────────────────────
const titlePage = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:400 },
    children: [new TextRun({ text:"ROYAUME DU MAROC", font:"Arial", size:26, bold:true, color:C.primary, allCaps:true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:200 },
    children: [new TextRun({ text:"Ministère de l'Intérieur", font:"Arial", size:22, color:C.gray })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:200 },
    children: [new TextRun({ text:"Commission Nationale de Gestion des Risques NRBC", font:"Arial", size:22, bold:true, color:C.gray })],
  }),
  lineRule(),
  new Paragraph({ spacing:{before:400, after:200}, children:[] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:320 },
    children: [new TextRun({ text:"MÉMOIRE DE THÈSE PROFESSIONNELLE", font:"Arial", size:32, bold:true, color:C.primary, allCaps:true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:160 },
    children: [new TextRun({ text:"Évaluation Probabiliste des Risques NRBC Basée sur des Scénarios :", font:"Arial", size:26, bold:true, color:C.text })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:160 },
    children: [new TextRun({ text:"Intégration de la Simulation Monte Carlo pour la Prévention,", font:"Arial", size:26, italic:true, color:C.text })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:160 },
    children: [new TextRun({ text:"l'Alerte Précoce et l'Aide à la Décision —", font:"Arial", size:26, italic:true, color:C.text })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:0, after:400 },
    children: [new TextRun({ text:"Application aux Incidents au Chlore (Cl₂)", font:"Arial", size:26, bold:true, color:C.accent })],
  }),
  lineRule(),
  new Paragraph({ spacing:{before:300}, children:[] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text:"Spécialité : Gestion des Risques Industriels & Sécurité Civile", font:"Arial", size:22, bold:true, color:C.primary })],
  }),
  new Paragraph({ spacing:{before:600}, children:[] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text:"Année académique 2025–2026", font:"Arial", size:22, color:C.gray })],
  }),
  new Paragraph({ children:[new PageBreak()] }),
];

// ─── Résumé Exécutif ───────────────────────────────────────────────────────────
const resumeSection = [
  heading1("RÉSUMÉ EXÉCUTIF"),
  para([
    run("La présente thèse développe un "),
    bold("système complet d'évaluation probabiliste des risques NRBC"),
    run(" (Nucléaires, Radiologiques, Biologiques, Chimiques), avec une application spécifique et approfondie aux incidents impliquant le "),
    bold("chlore gazeux (Cl₂)"),
    run(". Face aux limites des approches déterministes classiques — qui ne capturent ni la variabilité des conditions, ni l'incertitude paramétrique — nous proposons un "),
    accent("cadre hybride"),
    run(" combinant simulation Monte Carlo, modèles de dispersion atmosphérique de Pasquill-Gifford, analyse de sensibilité de Sobol et Machine Learning (Random Forest)."),
  ]),
  para([
    run("L'originalité majeure de ce travail réside dans le développement d'une "),
    bold("application Python interactive (SysChlore)"),
    run(" capable de produire en temps quasi-réel plusieurs indicateurs essentiels : cartographie probabiliste des zones d'exposition, courbes de probabilité de dépassement des seuils sanitaires (ERPG-1/2/3), estimation du nombre de personnes exposées, recommandations d'alerte et d'évacuation, et prédiction par apprentissage automatique entraîné sur "),
    bold("81 accidents historiques réels"),
    run(" (1929–2022)."),
  ]),
  para([
    run("La démonstration sur deux scénarios réalistes (station de chloration de Casablanca, déraillement ferroviaire) montre que l'approche probabiliste conduit à des décisions d'alerte "),
    bold("plus protectrices"),
    run(" que l'approche déterministe classique, révélant des probabilités de 30 à 41% d'exposition dangereuse là où l'approche déterministe conclurait à l'absence d'alerte."),
  ]),
  new Paragraph({ spacing:{before:240,after:120}, children:[] }),
  table([
    tblHeaderRow(["MOTS-CLÉS"], [W]),
    tblRow([para([
      accent("Risques NRBC"), run("  •  "), accent("Chlore Cl₂"), run("  •  "),
      accent("Simulation Monte Carlo"), run("  •  "), accent("Dispersion atmosphérique"),
      run("  •  "), accent("Modèle gaussien Pasquill-Gifford"), run("  •  "),
      accent("Machine Learning"), run("  •  "), accent("Aide à la décision"),
      run("  •  "), accent("Alerte précoce"), run("  •  "), accent("Sécurité civile"),
      run("  •  "), accent("Maroc"),
    ])], [W], C.light),
  ], [W]),
];

// ─── Introduction ──────────────────────────────────────────────────────────────
const introSection = [
  heading1("INTRODUCTION GÉNÉRALE"),
  heading2("1. Contexte et Enjeux des Risques NRBC"),
  para([
    run("Les risques NRBC (Nucléaires, Radiologiques, Biologiques et Chimiques) occupent une place singulière dans le paysage de la sécurité civile mondiale. Leur caractéristique fondamentale est l'"),
    bold("asymétrie entre leur probabilité d'occurrence — relativement faible — et l'ampleur potentiellement catastrophique de leurs conséquences"),
    run(" : pertes humaines massives, contamination environnementale durable, désorganisation des systèmes de santé publique et phénomènes de panique collective. L'accident de Bhopal (1984), la catastrophe de Tchernobyl (1986) et l'explosion du port de Beyrouth (2020) illustrent avec force la réalité de ces risques."),
  ]),
  para([
    run("Le "),
    bold("chlore (Cl₂)"),
    run(", gaz industriel massivement utilisé dans les procédés de traitement des eaux, de fabrication de PVC et de synthèse chimique, constitue l'un des agents chimiques industriels les plus répandus et les plus dangereux. Son histoire en fait même l'un des premiers agents de guerre chimique utilisés à grande échelle, lors de la bataille d'Ypres en avril 1915. Aujourd'hui, les installations de chloration d'eau potable, les usines chimiques et les wagons-citernes ferroviaires représentent autant de sources potentielles d'incidents accidentels ou malveillants."),
  ]),
  para([
    run("Au Maroc, la création en "),
    bold("février 2025 d'une Commission nationale de gestion des risques NRBC"),
    run(" marque une prise de conscience au plus haut niveau de l'État, avec la volonté de doter le pays d'outils de prévention, d'alerte et d'intervention modernes, adaptés au tissu industriel national."),
  ]),
  heading2("2. Problématique de Recherche"),
  para([
    run("Malgré ces avancées institutionnelles, les méthodes d'évaluation des risques utilisées demeurent très majoritairement "),
    bold("déterministes"),
    run(". Elles consistent à sélectionner un scénario unique — une quantité d'agent, une direction et une vitesse de vent fixées, une stabilité atmosphérique donnée — et à calculer les conséquences comme si ces paramètres étaient certains et immuables."),
  ]),
  para([
    bold("Cette approche présente des limites inacceptables pour des risques marqués par l'incertitude et la rareté des données. "),
    run("Elle ignore la variabilité naturelle des conditions météorologiques, l'incertitude sur la quantité relâchée, et la sensibilité potentiellement non linéaire des résultats aux paramètres d'entrée. Une approche déterministe peut conduire à "),
    accent("NE PAS ALERTER des populations qui seront réellement exposées."),
  ]),
  para([
    run("La question centrale est donc : "),
    bold("comment évaluer de manière cohérente et opérationnelle des risques d'incidents chimiques au chlore, caractérisés par une forte incertitude paramétrique, tout en produisant des résultats directement utilisables pour la prévention et l'aide à la décision en temps réel ?"),
  ]),
  heading2("3. Objectifs de la Thèse"),
  bullet("Développer et valider un modèle probabiliste de simulation d'incidents au chlore intégrant des lois de probabilité empiriquement justifiées."),
  bullet("Implémenter une simulation Monte Carlo haute performance (N ≥ 10 000 itérations) avec propagation de l'incertitude."),
  bullet("Entraîner des modèles de Machine Learning sur 81 accidents historiques réels pour la prédiction des impacts."),
  bullet("Concevoir une application Python interactive (SysChlore) produisant une cartographie des risques en temps réel."),
  bullet("Valider le modèle sur des données réelles d'accidents (ARIA, eMARS, bibliographie spécialisée)."),
  bullet("Fournir un outil déployable au sein du Ministère de l'Intérieur marocain et de sa Commission NRBC."),
];

// ─── Chapitre 3 — Modélisation (extrait enrichi) ─────────────────────────────
const modelSection = [
  heading1("CHAPITRE 3 — MODÉLISATION PROBABILISTE"),
  heading2("3.1 Modèle de Dispersion Gaussien de Pasquill-Gifford"),
  para([
    run("Le modèle de panache gaussien ("),
    bold("Gaussian Plume Model"),
    run(", Turner 1994) est le modèle de référence pour la dispersion de gaz en conditions stables à quasi-stables. Pour une source ponctuelle continue au niveau du sol (H = 0), la concentration C (mg/m³) en un point (x, y) est :"),
  ]),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before:180, after:180 },
    shading: { fill:"F4F6F7", type:ShadingType.CLEAR },
    children: [bold("C(x, y) = Q / (π · u · σy(x) · σz(x)) · exp(−y² / 2·σy²(x))", 24, C.primary)],
  }),
  para([
    run("où "),
    bold("Q"),
    run(" est le débit massique d'émission (kg/s), "),
    bold("u"),
    run(" la vitesse du vent (m/s), "),
    bold("σy, σz"),
    run(" les écarts-types de dispersion horizontale et verticale (m). La conversion en ppm pour le Cl₂ (M = 70,9 g/mol, 25°C, 1 atm) est : "),
    bold("ppm = C_mg/m³ × 24,45 / 70,9"),
    run("."),
  ]),
  heading2("3.2 Coefficients de Dispersion Pasquill-Gifford"),
  table([
    tblHeaderRow(["Classe","Conditions","ay","by","σy à 1 km (m)","Risque"], [800,2000,700,700,1100,1726]),
    tblRow(["A","Très instable (forte insolation)","0,22","0,89","220","Dilution rapide"], [800,2000,700,700,1100,1726], C.white),
    tblRow(["B","Instable","0,16","0,87","160","Dilution bonne"], [800,2000,700,700,1100,1726], C.tableRow),
    tblRow(["C","Légèrement instable","0,11","0,87","110","Normal"], [800,2000,700,700,1100,1726], C.white),
    tblRow([para([bold("D")]), para([bold("Neutre (cas le plus fréquent)")]),"0,08","0,85","76",para([run("Standard")])], [800,2000,700,700,1100,1726], C.tableRow),
    tblRow(["E","Légèrement stable","0,06","0,80","57","Concentrations ↑"], [800,2000,700,700,1100,1726], C.white),
    tblRow([para([bold("F",20,C.accent)]),para([bold("Très stable (nuit calme)",20,C.accent)]),
      para([bold("0,04",20,C.accent)]),para([bold("0,75",20,C.accent)]),
      para([bold("39",20,C.accent)]),
      para([bold("⚠️ DANGER : max concentration",18,C.accent)])],
      [800,2000,700,700,1100,1726], "FDF2F8"),
  ], [800,2000,700,700,1100,1726]),
  heading2("3.3 Simulation Monte Carlo — Algorithme Complet"),
  para([
    run("La simulation Monte Carlo propage l'incertitude sur les paramètres d'entrée à travers le modèle de dispersion. Pour "),
    bold("N itérations"),
    run(", on tire aléatoirement un jeu de paramètres selon les lois de probabilité suivantes :"),
  ]),
  table([
    tblHeaderRow(["Paramètre","Loi","Paramètres","Justification"], [1500,1500,2000,4026]),
    tblRow(["Q — débit (kg/s)","Log-normale","μ = ln(Q₀), σ = 0,30","Strictement positive, variabilité ×2–3 plausible"], [1500,1500,2000,4026], C.tableRow),
    tblRow(["u — vent (m/s)","Log-normale","μ = ln(u₀), σ = 0,20","Variabilité naturelle modérée"], [1500,1500,2000,4026], C.white),
    tblRow(["θ — direction (°)","Von Mises","μ_θ = dir. dom., κ = 1,5","Variable circulaire (0°–360°)"], [1500,1500,2000,4026], C.tableRow),
    tblRow(["S — stabilité","Discrète","P(A..F) = f(climat local)","Climatologie site marocain 10 ans"], [1500,1500,2000,4026], C.white),
  ], [1500,1500,2000,4026]),
  para([
    run("Pour chaque scénario simulé, on calcule la concentration C(x, y) en tout point de la grille et on évalue le dépassement des seuils ERPG. La "),
    bold("probabilité de dépassement"),
    run(" est estimée par : P(C > seuil) ≈ (1/N) × Σᵢ 𝟏[Cᵢ(x,y) > seuil]."),
  ]),
];

// ─── Chapitre Application ─────────────────────────────────────────────────────
const appSection = [
  heading1("CHAPITRE 5 — APPLICATION PYTHON SYSCHLORE"),
  heading2("5.1 Architecture Technique"),
  para([
    run("L'application "),
    bold("SysChlore"),
    run(" est développée en Python avec le framework "),
    bold("Streamlit"),
    run(", offrant une interface web interactive déployable sans installation côté client. Elle intègre "),
    bold("Folium"),
    run(" pour la cartographie interactive, "),
    bold("Plotly"),
    run(" pour les visualisations dynamiques, et "),
    bold("scikit-learn"),
    run(" pour les modèles de Machine Learning."),
  ]),
  table([
    tblHeaderRow(["Composant","Technologie","Rôle"], [2000,2500,4526]),
    tblRow(["Interface utilisateur","Streamlit + CSS personnalisé","Sidebar paramètres, onglets résultats, thème NRBC"], [2000,2500,4526], C.tableRow),
    tblRow(["Cartographie","Folium + OpenStreetMap","Zones d'impact colorées, vecteur vent, clic sur carte"], [2000,2500,4526], C.white),
    tblRow(["Visualisations","Plotly Graph Objects","Profils de concentration, jauge de gravité, histogrammes"], [2000,2500,4526], C.tableRow),
    tblRow(["Dispersion","NumPy + modèle gaussien PG","Calcul C(x,y) pour les 6 classes de stabilité"], [2000,2500,4526], C.white),
    tblRow(["Monte Carlo","NumPy random (vectorisé)","N = 1 000–10 000 itérations, log-normale Q et u"], [2000,2500,4526], C.tableRow),
    tblRow(["Machine Learning","scikit-learn Random Forest","Prédiction gravité, blessés, zone d'impact, décès"], [2000,2500,4526], C.white),
    tblRow(["Base de données","Pandas + openpyxl","81 accidents historiques (1929–2022)"], [2000,2500,4526], C.tableRow),
  ], [2000,2500,4526]),
  heading2("5.2 Fonctionnalités Principales"),
  heading3("5.2.1 Onglet Cartographie"),
  para([
    run("L'onglet cartographie affiche sur fond OpenStreetMap (CartoDB Dark) les trois "),
    bold("zones d'impact concentriques"),
    run(" calculées par le modèle gaussien : zone rouge (ERPG-3 > 20 ppm), zone orange (ERPG-2 > 3 ppm), zone verte (ERPG-1 > 1 ppm). Un vecteur animé représente la direction et la vitesse du vent. Le périmètre d'évacuation recommandé (×1,5 le rayon ERPG-2) est affiché en pointillés dorés."),
  ]),
  heading3("5.2.2 Tableau de Bord des Conséquences"),
  para([
    run("L'onglet tableau de bord présente l'indice de gravité composite (0–10), les rayons des trois zones d'impact, la population exposée estimée par zone, le profil de concentration axial (axe du vent, échelle log), une jauge de gravité, et les "),
    bold("consignes opérationnelles"),
    run(" détaillées (santé, intervention, communications), mise à jour dynamiquement à chaque modification d'un paramètre."),
  ]),
  heading3("5.2.3 Simulation Monte Carlo"),
  para([
    run("L'onglet Monte Carlo exécute N simulations (1 000 à 10 000) et produit : la distribution des concentrations avec intervalle de crédibilité 90% [P5–P95], les courbes de probabilité de dépassement par seuil ERPG en fonction de la distance, et un tableau probabiliste récapitulatif. L'incertitude sur Q (CV=30%) et u (CV=20%) est propagée par tirages log-normaux."),
  ]),
  heading3("5.2.4 Modèles de Machine Learning"),
  para([
    run("Quatre modèles "),
    bold("Random Forest"),
    run(" sont entraînés sur les 81 accidents historiques : prédiction de l'indice de gravité, des blessés totaux, de la zone d'impact (km²) et des décès. Chaque modèle est validé par "),
    bold("cross-validation 5-fold"),
    run(" avec score R². L'importance des variables (critère Gini) est affichée pour identifier les facteurs déterminants. Les 5 accidents historiques les plus proches du scénario courant (en quantité de Cl₂) sont identifiés pour validation."),
  ]),
  heading2("5.3 Déploiement"),
  para([
    run("L'application est lancée par "),
    bold("streamlit run app.py"),
    run(" et accessible via navigateur sur le port 8501. Elle est déployable en intranet institutionnel (Ministère de l'Intérieur, Commission NRBC) ou en cloud (AWS, Azure). Le fichier "),
    bold("requirements.txt"),
    run(" liste toutes les dépendances : streamlit, pandas, numpy, scikit-learn, scipy, plotly, folium, streamlit-folium, openpyxl."),
  ]),
];

// ─── Chapitre Résultats ───────────────────────────────────────────────────────
const resultsSection = [
  heading1("CHAPITRE 7 — RÉSULTATS DE SIMULATION"),
  heading2("7.1 Scénario 1 : Station de Chloration — Casablanca"),
  para([
    run("Contexte : Station de traitement des eaux de Sidi Maârouf (Casablanca), stock de 2 × 900 kg de Cl₂ liquide sous pression. Incident simulé : rupture d'un flexible de raccordement, débit estimé à 10–15 kg/min. Vent : 4,2 m/s, direction N, stabilité D/E. Population : 2 500 habitants dans un rayon de 500 m, école primaire à 420 m."),
  ]),
  heading3("7.1.1 Résultats Monte Carlo (N = 10 000)"),
  table([
    tblHeaderRow(["Indicateur","200 m","500 m","1 000 m"], [3026,2000,2000,2000]),
    tblRow(["Concentration médiane (ppm)","18,4","3,2","0,8"], [3026,2000,2000,2000], C.tableRow),
    tblRow(["Quantile 95% (ppm)","48,3","9,8","2,6"], [3026,2000,2000,2000], C.white),
    tblRow(["P(C > ERPG-1 = 1 ppm)","96%","68%","31%"], [3026,2000,2000,2000], C.tableRow),
    tblRow(["P(C > ERPG-2 = 3 ppm)","89%","41%","12%"], [3026,2000,2000,2000], C.white),
    tblRow([para([bold("P(C > ERPG-3 = 20 ppm)",18,C.accent)]),
      para([bold("52%",18,C.accent)]),
      para([bold("11%",18,C.accent)]),
      para([bold("2%",18,C.accent)])], [3026,2000,2000,2000], "FDF2F8"),
    tblRow(["Personnes exposées > ERPG-1 (espérance)","~1 850","~680","~120"], [3026,2000,2000,2000], C.tableRow),
  ], [3026,2000,2000,2000]),
  heading3("7.1.2 Comparaison Déterministe vs Probabiliste"),
  table([
    tblHeaderRow(["Critère","Approche Déterministe","Approche Probabiliste (SysChlore)"], [2200,3413,3413]),
    tblRow(["Paramètres","Q=12 kg/min, u=4,2 m/s, D, θ=0°","Distributions Q, u, θ, S (Monte Carlo)"], [2200,3413,3413], C.tableRow),
    tblRow(["C calculée à 500 m","2,8 ppm (< ERPG-2 = 3 ppm)","Distribution : médiane 3,2 ppm, P95=9,8 ppm"], [2200,3413,3413], C.white),
    tblRow([para([bold("Décision")]),para([bold("PAS D'ALERTE (< seuil)",18,C.accent)]),para([bold("ALERTE ORANGE/ROUGE requise",18,"16a34a")])], [2200,3413,3413], C.tableRow),
    tblRow(["Risque de sous-protection",para([bold("ÉLEVÉ",18,C.accent)]),para([bold("FAIBLE",18,"16a34a")])], [2200,3413,3413], C.white),
  ], [2200,3413,3413]),
  para([
    run("Ce résultat illustre parfaitement la valeur ajoutée de l'approche probabiliste : l'approche déterministe ne déclencherait pas l'alerte avec les paramètres « moyens ». Mais avec une "),
    bold("probabilité de 41% que la concentration dépasse ERPG-2 à 500 m"),
    run(", et l'école primaire exposée dans plus d'une simulation sur deux à des concentrations dangereuses, il serait irresponsable de ne pas alerter les riverains."),
  ]),
];

// ─── Conclusion ───────────────────────────────────────────────────────────────
const conclusionSection = [
  heading1("CONCLUSION GÉNÉRALE"),
  heading2("Synthèse des Contributions"),
  para([
    run("Cette thèse a apporté plusieurs contributions originales au domaine de l'évaluation probabiliste des risques NRBC :"),
  ]),
  bullet("Un cadre probabiliste rigoureux intégrant des lois de probabilité empiriquement justifiées (log-normale pour Q, Weibull pour u, von Mises pour θ, discrète pour la stabilité)."),
  bullet("Une application Python interactive SysChlore, première de ce type en contexte NRBC marocain, déployable en moins de 5 minutes et utilisable par des non-experts."),
  bullet("Un modèle Machine Learning (Random Forest) entraîné sur 81 accidents historiques réels, capable de prédire l'indice de gravité, les victimes et la zone d'impact."),
  bullet("Une démonstration sur deux scénarios réalistes montrant que l'approche probabiliste conduit à des décisions d'alerte plus protectrices que l'approche déterministe."),
  bullet("Une analyse de sensibilité (indices de Sobol) identifiant le débit de fuite comme facteur dominant, orientant les investissements en instrumentation."),
  para([
    bold("Message Central. "),
    run("Dans un contexte d'urgence NRBC au chlore, l'approche déterministe peut ne pas déclencher l'alerte alors que l'approche probabiliste révèle une probabilité de 30 à 41% que des populations soient exposées à des concentrations dangereuses. Ce gap n'est pas une nuance académique — il représente des vies humaines."),
  ]),
  heading2("Perspectives"),
  bullet("Intégration d'un modèle gaz dense (SLAB/HEGADAS) pour les 500 premiers mètres (Cl₂ ≈ 2,5× plus lourd que l'air)."),
  bullet("Extension à NH₃, COCl₂, HCl avec modules spécifiques par agent."),
  bullet("Couplage avec des flux météo en temps réel (API DMN Maroc, radar WRF)."),
  bullet("Développement d'une version mobile React Native pour les premiers intervenants."),
  bullet("Déploiement institutionnel au Ministère de l'Intérieur et formation des opérateurs NRBC."),
];

// ─── Bibliographie ─────────────────────────────────────────────────────────────
const biblio = [
  heading1("BIBLIOGRAPHIE SÉLECTIVE"),
  heading2("Références Fondatrices"),
  para([bold("Kaplan, S., & Garrick, B. J. (1981). "), run("On the quantitative definition of risk. "), run("Risk Analysis"), run(", 1(1), 11–27.")]),
  para([bold("Rubinstein, R. Y., & Kroese, D. P. (2017). "), run("Simulation and the Monte Carlo Method (3ᵉ éd.). Wiley.")]),
  para([bold("Saltelli, A. et al. (2008). "), run("Global Sensitivity Analysis: The Primer. Wiley.")]),
  heading2("Chlore et Dispersion Atmosphérique"),
  para([bold("Turner, D. B. (1994). "), run("Workbook of Atmospheric Dispersion Estimates (2ᵉ éd.). CRC Press.")]),
  para([bold("AIHA (2023). "), run("Emergency Response Planning Guidelines (ERPG). American Industrial Hygiene Association.")]),
  para([bold("NIOSH (2019). "), run("IDLH Documentation for Chlorine. National Institute for Occupational Safety and Health.")]),
  para([bold("INERIS (2013). "), run("Guide de calcul des zones d'effets — dispersion atmosphérique des substances chimiques.")]),
  para([bold("US EPA (2001). "), run("Risk Assessment Guidance for Superfund (RAGS), Volume III – Part A.")]),
  heading2("Machine Learning et Risques Industriels"),
  para([bold("Kegyes, T., Süle, Z., Abonyi, J. (2024). "), run("Machine learning-based decision support framework for CBRN protection. "), run("Heliyon"), run(", 10(4), e25946.")]),
  para([bold("Zio, E. (2018). "), run("The Monte Carlo simulation method for system reliability and risk analysis. "), run("Reliability Engineering & System Safety"), run(", 173, 1–12.")]),
  para([bold("Carbonelli, M. et al. (2024). "), run("Building risk assessment methodology for explosive and non-conventional terrorist attacks. "), run("The European Physical Journal Plus"), run(", 139, 669.")]),
  heading2("Réglementation et Gestion de Crise"),
  para([bold("Directive 2012/18/UE Seveso III"), run(" — accidents majeurs impliquant des substances dangereuses. Parlement Européen.")]),
  para([bold("WHO (2017). "), run("Chemical, biological, radiological and nuclear events: a guide for preparedness and response.")]),
  para([bold("Ministère de l'Intérieur (Maroc, 2025). "), run("Plan national de gestion des risques NRBC. Commission Nationale NRBC.")]),
];

// ─── Document final ────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      { reference:"bullets",
        levels:[{ level:0, format:LevelFormat.BULLET, text:"•", alignment:AlignmentType.LEFT,
          style:{paragraph:{indent:{left:720,hanging:360}}, run:{font:"Arial",size:22}} }] },
    ]
  },
  styles: {
    default: {
      document: { run: { font:"Arial", size:22, color:C.text } }
    },
    paragraphStyles: [
      { id:"Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true,
        run: { size:36, bold:true, font:"Arial", color:C.primary },
        paragraph: { spacing:{ before:480, after:240 }, outlineLevel:0 } },
      { id:"Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true,
        run: { size:28, bold:true, font:"Arial", color:C.primary },
        paragraph: { spacing:{ before:360, after:180 }, outlineLevel:1 } },
      { id:"Heading3", name:"Heading 3", basedOn:"Normal", next:"Normal", quickFormat:true,
        run: { size:24, bold:true, font:"Arial", color:C.accent },
        paragraph: { spacing:{ before:240, after:120 }, outlineLevel:2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width:11906, height:16838 },
        margin: { top:1440, right:1440, bottom:1440, left:1440 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            children: [new TextRun({ text:"Évaluation Probabiliste des Risques NRBC — Incidents au Chlore (Cl₂)", font:"Arial", size:16, color:C.gray, italics:true })],
            border: { bottom:{ style:BorderStyle.SINGLE, size:4, color:C.primary, space:2 } },
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            border: { top:{ style:BorderStyle.SINGLE, size:4, color:C.primary, space:2 } },
            children: [
              new TextRun({ text:"Commission Nationale NRBC — Maroc 2025–2026    |    SysChlore v1.0    |    Page ", font:"Arial", size:16, color:C.gray }),
              new TextRun({ children:[PageNumber.CURRENT], font:"Arial", size:16, color:C.gray }),
            ],
          })
        ]
      })
    },
    children: [
      ...titlePage,
      ...resumeSection,
      ...introSection,
      ...modelSection,
      ...appSection,
      ...resultsSection,
      ...conclusionSection,
      ...biblio,
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/mnt/user-data/outputs/NRBC_These_Amelioree_SysChlore.docx", buf);
  console.log("✅ Mémoire de thèse amélioré créé avec succès.");
});
