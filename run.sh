#!/usr/bin/env bash
# =============================================================================
#  SYSCHLORE — Script de lancement de l'application
#  Système d'Aide à la Décision NRBC — Incidents au Chlore
# =============================================================================

echo "╔══════════════════════════════════════════════════════╗"
echo "║   SYSCHLORE — Simulation Chlore & Aide à la Décision ║"
echo "║   Commission Nationale NRBC — Maroc 2025-2026        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Vérification Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 requis. Installez Python 3.9+ depuis python.org"
    exit 1
fi

# Vérification que le fichier de données est présent
if [ ! -f "data/accidents_chlore_rectifie.xlsx" ]; then
    echo "❌ Fichier de données manquant : data/accidents_chlore_rectifie.xlsx"
    echo "   Placez le fichier Excel dans le dossier data/"
    exit 1
fi

# Installation des dépendances si nécessaire
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Installation des dépendances..."
    pip install -r requirements.txt
fi

echo "🚀 Lancement de l'application..."
echo "📍 Accessible sur : http://localhost:8501"
echo ""
echo "   Appuyez sur CTRL+C pour arrêter"
echo ""

streamlit run app.py \
    --server.port=8501 \
    --server.headless=false \
    --theme.base=dark \
    --theme.primaryColor="#ff6400" \
    --theme.backgroundColor="#050a15" \
    --theme.secondaryBackgroundColor="#0a1020" \
    --theme.textColor="#e0e0e0"
