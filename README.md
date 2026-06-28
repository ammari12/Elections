# 🧪 SYSCHLORE — Système d'Aide à la Décision NRBC
## Simulation et Cartographie des Risques liés aux Incidents au Chlore (Cl₂)

> **Mémoire de Thèse Professionnelle** — Spécialité : Gestion des Risques Industriels & Sécurité Civile  
> Commission Nationale NRBC — Ministère de l'Intérieur, Maroc — Année 2025–2026

---

## 📋 Présentation

**SysChlore** est une application Python interactive d'aide à la décision destinée à :
- **Simuler** la dispersion atmosphérique du chlore gazeux (Cl₂)
- **Quantifier** les zones d'impact et les populations exposées
- **Prédire** la gravité des incidents par Machine Learning
- **Visualiser** les risques sur une carte interactive

---

## 🗂️ Structure du Projet

```
chlore_app/
│
├── app.py                          ← Application principale (Streamlit)
├── requirements.txt                ← Dépendances Python
├── run.sh                          ← Script de lancement
├── README.md                       ← Ce fichier
│
└── data/
    └── accidents_chlore_rectifie.xlsx  ← Base de données (81 accidents)
```

---

## ⚙️ Installation

```bash
# 1. Cloner / décompresser le projet
cd chlore_app/

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
bash run.sh
# OU directement :
streamlit run app.py
```

**Prérequis** : Python 3.9+

---

## 🎯 Fonctionnalités

### 1. Modèle de Dispersion Gaussien (Pasquill-Gifford)
- Modèle de panache gaussien adapté au chlore gazeux (densité > air)
- 6 classes de stabilité atmosphérique (A à F, Turner 1994)
- Calcul des concentrations en tout point de la grille
- Seuils toxicologiques : ERPG-1 (1 ppm), ERPG-2 (3 ppm), ERPG-3 (20 ppm), IDLH (10 ppm)

### 2. Simulation Monte Carlo
- N = 1 000 à 10 000 itérations (paramétrable)
- Incertitude sur la quantité émise : loi log-normale (CV = 30%)
- Incertitude sur la vitesse du vent : loi log-normale (CV = 20%)
- Sorties : distribution de concentration, probabilités de dépassement, intervalles de crédibilité 90%

### 3. Machine Learning (Random Forest)
- Entraînement sur 81 accidents historiques réels
- 4 cibles prédites : Indice de gravité, Blessés totaux, Zone d'impact, Décès
- Validation croisée 5-fold avec score R²
- Analyse d'importance des variables (Gini)

### 4. Cartographie Interactive (Folium + OpenStreetMap)
- Sélection du lieu d'incident sur la carte
- Zones d'impact en couleur (rouge/orange/vert)
- Direction et vitesse du vent
- Périmètre d'évacuation recommandé

### 5. Tableau de Bord Opérationnel
- Niveau d'alerte (Rouge/Orange/Jaune)
- KPIs : rayon d'impact, population exposée, indice de gravité
- Profil de concentration axiale
- Consignes opérationnelles (santé, intervention, communications)

### 6. Base de Données Historique
- 81 accidents au chlore (1929–2022), monde entier
- Filtres par pays, type de libération, période
- Visualisations : scatter, histogramme, timeline

---

## 📊 Base de Données

| Champ | Description | Plage |
|-------|-------------|-------|
| `Quantité_Cl2_kg` | Masse de Cl₂ émise | 20 – 60 000 kg |
| `Vitesse_vent_ms` | Vitesse du vent | 1 – 4 m/s |
| `Type_libération` | Brutale / Progressive | — |
| `Indice_gravité` | Score composite 0-11 | 0 – 10.7 |
| `Blessés_total` | Victimes totales | 0 – 529 |
| `Zone_impact_km2` | Surface impactée | 0.02 – 4.2 km² |

---

## 🔬 Modèles Scientifiques

### Modèle Gaussien
```
C(x, y) = Q / (π · u · σy(x) · σz(x)) · exp(-y² / 2σy²)
```
Où σy et σz sont les coefficients de Pasquill-Gifford.

### Conversion mg/m³ → ppm
```
ppm = C_mg/m³ × 24.45 / 70.9   (Cl₂ à 25°C, 1 atm)
```

### Monte Carlo
```
Q ~ LogNormal(ln(Q0), 0.30)
u ~ LogNormal(ln(u0), 0.20)
→ Distribution de C(x) sur N itérations
```

---

## 📚 Références

- Turner, D.B. (1994). *Workbook of atmospheric dispersion estimates*. CRC Press.
- Pasquill, F. (1961). The estimation of the dispersion of windborne material. *Met. Mag.*, 90, 33-49.
- ERPG values: AIHA (2023). *Emergency Response Planning Guidelines*.
- Base ARIA, BARPI, France (1992-2023).
- Kaplan, S. & Garrick, B.J. (1981). On the quantitative definition of risk. *Risk Analysis*, 1(1), 11-27.

---

## ⚠️ Avertissement

> Cette application est développée à des fins **académiques et opérationnelles de planification**.  
> Les résultats doivent être interprétés par des experts en sécurité industrielle.  
> Ne pas utiliser comme seul outil de décision en situation réelle sans validation terrain.

---

*SysChlore v1.0 — Thèse NRBC 2025-2026 — Commission Nationale NRBC, Maroc*
