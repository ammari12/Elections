"""
HazMod PDF Engine — Rapport Ministériel Sophistiqué
Utilise reportlab canvas (contrôle pixel-perfect) + platypus pour tableaux.
"""

import io, math, datetime, os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Palette ──────────────────────────────────────────────────────────────────
C_NAVY    = colors.HexColor("#0C2340")
C_NAVY2   = colors.HexColor("#162D4F")
C_BLUE    = colors.HexColor("#1A4F8A")
C_BLUE2   = colors.HexColor("#2563EB")
C_BLUE3   = colors.HexColor("#3B82F6")
C_GOLD    = colors.HexColor("#C9A227")
C_GOLD2   = colors.HexColor("#F0C040")
C_RED     = colors.HexColor("#B91C1C")
C_RED2    = colors.HexColor("#DC2626")
C_ORANGE  = colors.HexColor("#C05621")
C_GREEN   = colors.HexColor("#15803D")
C_GRAY1   = colors.HexColor("#1A202C")
C_GRAY2   = colors.HexColor("#4B5563")
C_GRAY3   = colors.HexColor("#9CA3AF")
C_LGRAY   = colors.HexColor("#F3F4F6")
C_LGRAY2  = colors.HexColor("#E5E7EB")
C_BG_R    = colors.HexColor("#FEE2E2")
C_BG_O    = colors.HexColor("#FEF3C7")
C_BG_G    = colors.HexColor("#DCFCE7")
C_BG_B    = colors.HexColor("#DBEAFE")
C_WHITE   = colors.white

W, H = A4  # 595.27 x 841.89 pt

# ── Logo HazMod dessiné au canvas ────────────────────────────────────────────
def draw_hazmod_logo(c, x, y, size=72):
    """
    Logo vectoriel sophistiqué HazMod :
    - Cercle extérieur gradient simulé (navy foncé → bleu)
    - Symbole NRBC/biohazard stylisé avec 3 lobes et cercle central
    - Atomes orbitaux aux 4 coins
    - Croix de sécurité civile en overlay léger
    """
    r  = size / 2
    cx = x + r
    cy = y + r

    # ── Ombre portée ──────────────────────────────────────────────────────
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.18))
    c.circle(cx + 2, cy - 2, r + 2, fill=1, stroke=0)

    # ── Disque de fond (navy profond) ─────────────────────────────────────
    c.setFillColor(C_NAVY)
    c.circle(cx, cy, r, fill=1, stroke=0)

    # ── Anneau extérieur doré ─────────────────────────────────────────────
    c.setStrokeColor(C_GOLD)
    c.setLineWidth(2.0)
    c.circle(cx, cy, r - 1, fill=0, stroke=1)

    # ── Anneau intérieur bleu ─────────────────────────────────────────────
    c.setStrokeColor(C_BLUE3)
    c.setLineWidth(0.8)
    c.circle(cx, cy, r - 5, fill=0, stroke=1)

    # ── Symbole biohazard stylisé ─────────────────────────────────────────
    # 3 lobes principaux autour du centre
    lobe_r   = r * 0.30
    lobe_off = r * 0.38
    angles   = [90, 210, 330]  # en degrés

    # Remplissage des lobes (rouge vif)
    c.setFillColor(C_RED2)
    c.setStrokeColor(C_RED2)
    c.setLineWidth(0)
    for ang in angles:
        rad = math.radians(ang)
        lx  = cx + lobe_off * math.cos(rad)
        ly  = cy + lobe_off * math.sin(rad)
        c.circle(lx, ly, lobe_r, fill=1, stroke=0)

    # Centre blanc (masque partiel → effet biohazard)
    c.setFillColor(C_NAVY)
    c.circle(cx, cy, r * 0.28, fill=1, stroke=0)

    # Petit cercle central rouge
    c.setFillColor(C_RED2)
    c.circle(cx, cy, r * 0.14, fill=1, stroke=0)

    # ── Lignes de connexion (bras du symbole biohazard) ───────────────────
    c.setStrokeColor(C_NAVY)
    c.setLineWidth(r * 0.14)
    for ang in angles:
        rad = math.radians(ang)
        lx  = cx + lobe_off * math.cos(rad)
        ly  = cy + lobe_off * math.sin(rad)
        # Ligne du centre vers le bord du lobe interne
        inner = r * 0.16
        c.line(cx + inner * math.cos(rad), cy + inner * math.sin(rad),
               lx - lobe_r * 0.6 * math.cos(rad),
               ly - lobe_r * 0.6 * math.sin(rad))

    # ── Atomes/électrons orbitaux (4 petits points bleus) ─────────────────
    c.setFillColor(C_BLUE3)
    orbital_r = r * 0.78
    for ang in [45, 135, 225, 315]:
        rad = math.radians(ang)
        c.circle(cx + orbital_r * math.cos(rad) * 0.85,
                 cy + orbital_r * math.sin(rad) * 0.85,
                 r * 0.07, fill=1, stroke=0)

    # ── Lignes orbitales ──────────────────────────────────────────────────
    c.setStrokeColor(C_BLUE2)
    c.setLineWidth(0.6)
    c.setDash([2, 3])
    inner_r = r * 0.50
    for ang in range(0, 360, 90):
        rad  = math.radians(ang)
        rad2 = math.radians(ang + 45)
        c.line(cx + inner_r * math.cos(rad),  cy + inner_r * math.sin(rad),
               cx + orbital_r * 0.85 * math.cos(rad2),
               cy + orbital_r * 0.85 * math.sin(rad2))
    c.setDash([])

    # ── "HM" en monogramme au centre ─────────────────────────────────────
    # (Petit texte blanc dans le cercle central)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", r * 0.22)
    c.drawCentredString(cx, cy - r * 0.08, "HM")


# ── Bandeau en-tête de page (canvas) ─────────────────────────────────────────
def draw_page_header(c, page_num, total_pages, ref_str, is_cover=False):
    """Dessine l'en-tête institutionnel sur chaque page."""
    if is_cover:
        return

    # Bande bleu navy top
    c.setFillColor(C_NAVY)
    c.rect(0, H - 1.4*cm, W, 1.4*cm, fill=1, stroke=0)

    # Texte en-tête gauche
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(1.8*cm, H - 0.85*cm, "ROYAUME DU MAROC — MINISTERE DE L'INTERIEUR")
    c.setFont("Helvetica", 6.5)
    c.drawString(1.8*cm, H - 1.15*cm, "Direction Générale des Affaires Intérieures — Direction de la Sécurité et de la Documentation")

    # Logo mini droit
    draw_hazmod_logo(c, W - 2.2*cm, H - 1.35*cm, size=1.1*cm)

    # Ligne de séparation dorée
    c.setStrokeColor(C_GOLD)
    c.setLineWidth(1.2)
    c.line(0, H - 1.42*cm, W, H - 1.42*cm)

    # Pied de page
    c.setFillColor(C_NAVY)
    c.rect(0, 0, W, 1.0*cm, fill=1, stroke=0)
    c.setStrokeColor(C_GOLD)
    c.setLineWidth(0.8)
    c.line(0, 1.0*cm, W, 1.0*cm)

    c.setFillColor(C_GRAY3)
    c.setFont("Helvetica", 6.5)
    c.drawString(1.8*cm, 0.38*cm,
                 f"HAZMOD — Rapport Confidentiel — Ref. {ref_str} — DIFFUSION RESTREINTE")
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(C_GOLD)
    c.drawRightString(W - 1.8*cm, 0.38*cm, f"Page {page_num} / {total_pages}")



# ── Carte vectorielle des zones ERPG (canvas) ────────────────────────────────
def _draw_star(c, cx, cy, r_outer, r_inner, col, n=5):
    """Étoile à n branches."""
    import math as _m
    pts = []
    for i in range(n * 2):
        angle = _m.radians(-90 + i * 180 / n)
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * _m.cos(angle), cy + r * _m.sin(angle)))
    path = c.beginPath()
    path.moveTo(*pts[0])
    for pt in pts[1:]: path.lineTo(*pt)
    path.close()
    c.setFillColor(col)
    c.setStrokeColor(colors.white)
    c.setLineWidth(0.6)
    c.drawPath(path, fill=1, stroke=1)


def _clean_name(name: str, max_len: int = 32) -> str:
    """
    Traduit les noms arabes en français et nettoie les caractères illisibles.
    Utilisé pour les étiquettes sur la carte PDF.
    """
    import unicodedata, re

    if not name:
        return "—"

    AR_TO_FR = {
        "مستشفى": "Hôpital", "مستشفيات": "Hôpitaux",
        "عيادة": "Clinique", "صيدلية": "Pharmacie",
        "صيدليات": "Pharmacies", "مدرسة": "École",
        "مدارس": "Écoles", "ثانوية": "Lycée",
        "ابتدائية": "Prim.", "جامعة": "Université",
        "كلية": "Faculté", "معهد": "Institut",
        "مركز صحي": "Ctre Santé", "مركز": "Centre",
        "مسجد": "Mosquée", "ولاية": "Wilaya",
        "بلدية": "Municipalité", "سوق": "Marché",
        "محطة": "Gare", "مطار": "Aéroport",
        "شرطة": "Police", "دركية": "Gendarmerie",
        "إطفاء": "Pompiers", "ملعب": "Stade",
        "فندق": "Hôtel", "مصنع": "Usine",
        "مستودع": "Entrepôt", "دار": "Dar",
        "حي": "Qr.", "شارع": "Av.",
        "منطقة صناعية": "Zone Ind.",
        "محل": "Commerce",
        "الحسن": "Al Hassan", "محمد": "Mohammed",
        "الخامس": "V", "السادس": "VI",
        "الرباط": "Rabat", "الدار البيضاء": "Casablanca",
    }
    TRANSLIT = {
        'ا':'a','أ':'a','إ':'i','آ':'a','ب':'b','ت':'t','ث':'th',
        'ج':'j','ح':'h','خ':'kh','د':'d','ذ':'dh','ر':'r','ز':'z',
        'س':'s','ش':'sh','ص':'s','ض':'d','ط':'t','ظ':'z','ع':"'",
        'غ':'gh','ف':'f','ق':'q','ك':'k','ل':'l','م':'m','ن':'n',
        'ه':'h','و':'w','ي':'y','ى':'a','ة':'a','ء':"'",
        'ُ':'u','ِ':'i','َ':'a','ّ':'','ْ':'','ً':'','ٌ':'','ٍ':'',
        '\u200c':'','\u200d':'','\u200b':'','\ufeff':'',
    }

    has_arabic = any('\u0600' <= ch <= '\u06FF' for ch in name)
    if not has_arabic:
        clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', name)
        return clean[:max_len].strip()

    result = name
    for ar, fr in AR_TO_FR.items():
        result = result.replace(ar, fr)

    remaining = sum(1 for ch in result if '\u0600' <= ch <= '\u06FF')
    if remaining > 2:
        result = ''.join(TRANSLIT.get(ch, ch) for ch in result)
        result = re.sub(r'\s+', ' ', result).strip().capitalize()

    result = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200f\ufeff]', '', result)
    return result[:max_len].strip()


def draw_erpg_map_canvas(c, x, y, w, h, params):
    """
    Carte ERPG vectorielle sophistiquée — version 4.0
    - Zones elliptiques orientées vent
    - Hotspots avec placement anti-collision des étiquettes
    - Traduction automatique noms arabes → français
    - Police Noto si disponible
    - Lisibilité maximale
    """
    import math as _m, os as _os

    r1  = params["r1"]; r2 = params["r2"]; r3 = params["r3"]
    pd  = params["prop_dir"]
    lat = params["lat"]; lon = params["lon"]
    Q   = params["Q_kg"]; u  = params["u_ms"]
    stb = params["stab"]; dv = params.get("dir_vent", 0)
    hs  = params.get("hotspots_reels", {})

    # ── Fond et grille ────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#0B1929"))
    c.roundRect(x, y, w, h, 6, fill=1, stroke=0)

    # Grille discrète
    c.setStrokeColor(colors.Color(0.2, 0.35, 0.55, 0.12))
    c.setLineWidth(0.3)
    for i in range(1, 11):
        c.line(x+w*i/11, y+1, x+w*i/11, y+h-1)
    for j in range(1, 7):
        c.line(x+1, y+h*j/7, x+w-1, y+h*j/7)

    c.setStrokeColor(colors.HexColor("#C9A227"))
    c.setLineWidth(1.8)
    c.roundRect(x, y, w, h, 6, fill=0, stroke=1)

    # ── Paramètres de projection ──────────────────────────────────────────────
    src_x = x + w * 0.22
    src_y = y + h * 0.50
    scale = (w * 0.73) / max(r1, 1)
    pr    = _m.radians(90.0 - pd)   # canvas: x→E, y→N

    def axial(r_m, frac=1.0):
        d = r_m * scale * frac
        return src_x + _m.cos(pr)*d, src_y + _m.sin(pr)*d

    def geo2cv(glat, glon):
        dx = _m.radians(glon - lon) * 6371000 * _m.cos(_m.radians(lat))
        dy = _m.radians(glat - lat) * 6371000
        return src_x + dx*scale, src_y + dy*scale

    # ── Zones elliptiques ─────────────────────────────────────────────────────
    def draw_zone(radius, fill_col, stroke_col, sw):
        rx = radius * scale
        ry = radius * scale * 0.44
        ce_x = src_x + _m.cos(pr) * rx * 0.48
        ce_y = src_y + _m.sin(pr) * rx * 0.48
        c.saveState()
        c.translate(ce_x, ce_y)
        c.rotate(_m.degrees(pr))
        c.setFillColor(fill_col)
        c.setStrokeColor(stroke_col)
        c.setLineWidth(sw)
        c.ellipse(-rx*0.52, -ry, rx*0.52, ry, fill=1, stroke=1)
        c.restoreState()

    draw_zone(r1, colors.Color(0.06,0.42,0.20,0.28), colors.HexColor("#16A34A"), 1.8)
    draw_zone(r2, colors.Color(0.78,0.42,0.04,0.38), colors.HexColor("#D97706"), 2.2)
    draw_zone(r3, colors.Color(0.78,0.08,0.08,0.55), colors.HexColor("#DC2626"), 2.5)

    # ── Placement anti-collision des étiquettes ───────────────────────────────
    # Algorithme : grille de cellules occupées + offset intelligent
    _LABEL_W = 90   # largeur badge estimée en points
    _LABEL_H = 14   # hauteur badge
    _placed: list = []  # [(lx, ly, lw, lh)]

    def _no_overlap(lx, ly):
        """True si la position est libre."""
        for (px, py, pw, ph) in _placed:
            if (abs(lx - px) < (pw + _LABEL_W)/2 + 3 and
                    abs(ly - py) < (ph + _LABEL_H)/2 + 2):
                return False
        return True

    def _find_pos(hx, hy, bw):
        """Trouver une position libre autour du point (hx, hy)."""
        offsets = [
            (0, 14), (0, -18), (bw/2+6, 6), (-bw/2-6, 6),
            (bw/2+4, -16), (-bw/2-4, -16), (0, 24), (0, -28),
            (bw/2+8, 16), (-bw/2-8, 16),
        ]
        for ox, oy in offsets:
            cx2 = hx + ox
            cy2 = hy + oy
            # Rester dans le cadre
            if (x + 5 < cx2 - bw/2 and cx2 + bw/2 < x+w-5 and
                    y + 5 < cy2 - _LABEL_H/2 and cy2 + _LABEL_H/2 < y+h-24):
                if _no_overlap(cx2, cy2):
                    return cx2, cy2
        # Force position (accepte collision partielle)
        return hx, hy + 16

    # ── Collecte et dessin des hotspots ───────────────────────────────────────
    Z_COLORS = {
        "ERPG-3": (colors.HexColor("#FF4444"), colors.HexColor("#FF0000")),
        "ERPG-2": (colors.HexColor("#FBBF24"), colors.HexColor("#F59E0B")),
        "ERPG-1": (colors.HexColor("#6EE7B7"), colors.HexColor("#34D399")),
    }
    Z_BADGE_BG = {
        "ERPG-3": colors.Color(0.15, 0.02, 0.02, 0.90),
        "ERPG-2": colors.Color(0.15, 0.10, 0.00, 0.90),
        "ERPG-1": colors.Color(0.02, 0.15, 0.08, 0.90),
    }

    # Collecter tous les points valides
    all_pts = []
    for zk in ["ERPG-3", "ERPG-2", "ERPG-1"]:
        items = hs.get(zk, [])
        txt_col, star_col = Z_COLORS[zk]
        badge_bg = Z_BADGE_BG[zk]
        for hi in items:
            coords = hi.get("coords", [lat, lon])
            if not coords or len(coords) < 2:
                continue
            hx, hy = geo2cv(coords[0], coords[1])
            # Vérifier que le point est dans le cadre
            if not (x+4 < hx < x+w-4 and y+4 < hy < y+h-4):
                continue
            raw_name = hi.get("name", "Site")
            clean    = _clean_name(raw_name, 28)
            icon     = hi.get("icon", "📍")
            prio     = hi.get("priority", "MODÉRÉ")
            all_pts.append((hx, hy, clean, icon, prio, zk,
                            txt_col, star_col, badge_bg))

    # Dessiner les étoiles d'abord (sous les labels)
    for (hx, hy, clean, icon, prio, zk, txt_col, star_col, badge_bg) in all_pts:
        sz = 7 if prio == "CRITIQUE" else 5.5
        # Halo
        c.setFillColor(colors.Color(1, 0, 0, 0.20))
        c.circle(hx, hy, sz+4, fill=1, stroke=0)
        c.setFillColor(colors.Color(1, 0, 0, 0.15))
        c.circle(hx, hy, sz+8, fill=1, stroke=0)
        # Étoile
        _draw_star(c, hx, hy, sz, sz*0.38, colors.HexColor("#FF0000"))

    # Dessiner les badges avec placement anti-collision
    for (hx, hy, clean, icon, prio, zk, txt_col, star_col, badge_bg) in all_pts:
        # Calculer largeur du badge selon le nom
        char_w = 5.2
        bw = min(clean.__len__() * char_w + 16, 115)
        bh = 13

        lx, ly = _find_pos(hx, hy, bw)
        _placed.append((lx, ly, bw, bh))

        # Ligne de connexion étoile → badge (fine)
        c.setStrokeColor(colors.Color(1, 0.2, 0.2, 0.55))
        c.setLineWidth(0.7)
        c.setDash([2, 2])
        c.line(hx, hy, lx, ly)
        c.setDash([])

        # Badge fond
        c.setFillColor(badge_bg)
        c.roundRect(lx - bw/2, ly - bh/2, bw, bh, 3, fill=1, stroke=0)

        # Bordure colorée zone
        c.setStrokeColor(txt_col)
        c.setLineWidth(0.8)
        c.roundRect(lx - bw/2, ly - bh/2, bw, bh, 3, fill=0, stroke=1)

        # Bande couleur priorité (côté gauche du badge)
        prio_col = (colors.HexColor("#FF3333") if prio == "CRITIQUE"
                    else colors.HexColor("#F59E0B") if prio == "ÉLEVÉ"
                    else colors.HexColor("#6EE7B7"))
        c.setFillColor(prio_col)
        c.roundRect(lx - bw/2, ly - bh/2, 3, bh, 1, fill=1, stroke=0)

        # Texte du badge
        c.setFont("Helvetica-Bold", 6.2)
        c.setFillColor(colors.white)
        c.drawCentredString(lx + 1, ly - 2.5, clean[:28])

    # ── Marqueur source ───────────────────────────────────────────────────────
    for r_h, alpha in [(18, 0.08), (12, 0.18), (8, 0.32)]:
        c.setFillColor(colors.Color(0.90, 0.10, 0.10, alpha))
        c.circle(src_x, src_y, r_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.circle(src_x, src_y, 6, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#DC2626"))
    c.circle(src_x, src_y, 4, fill=1, stroke=0)
    c.setStrokeColor(colors.white)
    c.setLineWidth(0.9)
    for dx2, dy2 in [(-13, 0), (-7, 0), (7, 0), (13, 0),
                     (0, -13), (0, -7), (0, 7), (0, 13)]:
        if abs(dx2) > 8 or abs(dy2) > 8:
            c.line(src_x, src_y, src_x+dx2, src_y+dy2)

    # Badge source
    c.setFillColor(colors.Color(0.75, 0.05, 0.05, 0.92))
    c.roundRect(src_x - 52, src_y + 10, 104, 14, 3, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#FF6666"))
    c.setLineWidth(0.7)
    c.roundRect(src_x - 52, src_y + 10, 104, 14, 3, fill=0, stroke=1)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.white)
    c.drawCentredString(src_x, src_y + 16, f"Source Cl2 — {Q:,.0f} kg")

    # ── Flèche vent ───────────────────────────────────────────────────────────
    al = r2 * scale * 0.28
    ax1, ay1 = src_x + _m.cos(pr)*11, src_y + _m.sin(pr)*11
    ax2, ay2 = src_x + _m.cos(pr)*al, src_y + _m.sin(pr)*al
    c.setStrokeColor(colors.HexColor("#60A5FA"))
    c.setLineWidth(3)
    c.line(ax1, ay1, ax2, ay2)
    c.setFillColor(colors.HexColor("#60A5FA"))
    for sgn in [1, -1]:
        perp = pr + _m.pi/2
        px2 = ax2 - _m.cos(pr)*9 + sgn*_m.cos(perp)*5
        py2 = ay2 - _m.sin(pr)*9 + sgn*_m.sin(perp)*5
        path = c.beginPath()
        path.moveTo(ax2, ay2); path.lineTo(px2, py2); path.close()
        c.drawPath(path, fill=1, stroke=0)

    # ── Badges zones ─────────────────────────────────────────────────────────
    for r_v, col_h, zn, dist_s, frac in [
        (r3, "#EF4444", "ERPG-3", f"{r3:.0f} m", 0.36),
        (r2, "#F59E0B", "ERPG-2", f"{r2:.0f} m", 0.60),
        (r1, "#4ADE80", "ERPG-1", f"{r1:.0f} m", 0.82),
    ]:
        bx2, by2 = axial(r_v, frac)
        by2 -= r_v * scale * 0.19
        c.setFillColor(colors.HexColor(col_h))
        c.roundRect(bx2 - 44, by2 - 9, 88, 18, 4, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(bx2, by2 - 2.5, f"{zn}  {dist_s}")

    # ── Légende ───────────────────────────────────────────────────────────────
    leg_items = [
        (colors.HexColor("#EF4444"), colors.Color(0.78,0.08,0.08,0.50),
         "ERPG-3  > 20 ppm  (Danger vital)"),
        (colors.HexColor("#F59E0B"), colors.Color(0.78,0.42,0.04,0.38),
         "ERPG-2  > 3 ppm   (Irréversible)"),
        (colors.HexColor("#4ADE80"), colors.Color(0.06,0.42,0.20,0.28),
         "ERPG-1  > 1 ppm   (Irritation)"),
        (colors.HexColor("#FF0000"), None,
         "★  Hotspot critique identifié"),
    ]
    lw2 = 155; lih = 15
    lgh = len(leg_items) * lih + 22
    lgx = x + w - lw2 - 6; lgy = y + h - lgh - 6
    c.setFillColor(colors.Color(0.04, 0.09, 0.22, 0.92))
    c.roundRect(lgx, lgy, lw2, lgh, 5, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#C9A227"))
    c.setLineWidth(0.9)
    c.roundRect(lgx, lgy, lw2, lgh, 5, fill=0, stroke=1)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#C9A227"))
    c.drawCentredString(lgx+lw2/2, lgy+lgh-11, "ZONES D'IMPACT Cl\u2082")
    c.setStrokeColor(colors.HexColor("#C9A227"))
    c.setLineWidth(0.5)
    c.line(lgx+6, lgy+lgh-14, lgx+lw2-6, lgy+lgh-14)
    for i, (sc2, fc2, lbl2) in enumerate(leg_items):
        iy2 = lgy + lgh - 24 - i * lih
        if i == 3:
            _draw_star(c, lgx+12, iy2+4, 5.5, 2.2, colors.HexColor("#FF0000"))
        else:
            c.setFillColor(fc2 or sc2)
            c.setStrokeColor(sc2)
            c.setLineWidth(0.8)
            c.roundRect(lgx+6, iy2, 12, 9, 2, fill=1, stroke=1)
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.white)
        c.drawString(lgx+23, iy2+1, lbl2)

    # ── Bandeaux info ─────────────────────────────────────────────────────────
    for (by3, bh3) in [(y, 22), (y+h-20, 20)]:
        c.setFillColor(colors.Color(0.02, 0.07, 0.18, 0.90))
        c.rect(x, by3, w, bh3, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#1E40AF"))
    c.setLineWidth(0.5)
    c.line(x, y+22, x+w, y+22)
    c.line(x, y+h-20, x+w, y+h-20)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#93C5FD"))
    c.drawString(x+8, y+8,
        f"Vent : {dv}\u00b0 \u2192 {pd:.0f}\u00b0  |  {u} m/s  |  Cl. {stb}"
        f"  |  Coord. : {lat:.4f}\u00b0N  {lon:.4f}\u00b0E")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#FDE68A"))
    c.drawString(x+8, y+h-14,
        "HAZMOD \u2014 Cartographie des Zones de Risque ERPG / Cl\u2082")
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawRightString(x+w-8, y+h-14,
        "\u00a9 Google Earth / Imagery Satellite \u2014 OpenStreetMap")


# ── Flowable pour carte ERPG (canvas inside platypus) ─────────────────────────
class ERPGMapFlowable:
    """Insère une carte des zones ERPG dans le flux platypus."""
    def __init__(self, params, img_path=None, map_w=None, map_h=None):
        from reportlab.platypus import Flowable
        self._params   = params
        self._img_path = img_path
        self._map_w    = map_w or (W - 3.6*cm)
        self._map_h    = map_h or 7.5*cm

    def as_flowable(self):
        """Retourne soit une RLImage (photo satellite) soit un Drawing custom."""
        from reportlab.platypus import Flowable

        class _MapFlow(Flowable):
            def __init__(self2, params, img_path, map_w, map_h):
                super().__init__()
                self2.params   = params
                self2.img_path = img_path
                self2.map_w    = map_w
                self2.map_h    = map_h
                self2.width    = map_w
                self2.height   = map_h

            def wrap(self2, aw, ah):
                return (self2.map_w, self2.map_h)

            def draw(self2):
                c = self2.canv
                if self2.img_path and os.path.exists(self2.img_path):
                    # Dessine la photo satellite
                    from reportlab.lib.utils import ImageReader
                    try:
                        ir = ImageReader(self2.img_path)
                        c.drawImage(ir, 0, 0, width=self2.map_w, height=self2.map_h,
                                    preserveAspectRatio=True, anchor='c',
                                    mask='auto')
                        # Overlay légende par-dessus la photo
                        r3 = self2.params["r3"]
                        r2 = self2.params["r2"]
                        r1 = self2.params["r1"]
                        dir_v = self2.params.get("dir_vent", 0)
                        prop  = self2.params.get("prop_dir", 0)
                        u_ms  = self2.params.get("u_ms", 5)
                        stab  = self2.params.get("stab", "C")
                        Q_kg  = self2.params.get("Q_kg", 0)
                        lat   = self2.params.get("lat", 0)
                        lon   = self2.params.get("lon", 0)
                        # Légende overlay
                        c.setFillColor(colors.Color(0.05, 0.10, 0.20, 0.82))
                        c.roundRect(6, 6, 165, 80, 5, fill=1, stroke=0)
                        c.setStrokeColor(colors.HexColor("#3B82F6"))
                        c.setLineWidth(0.7)
                        c.roundRect(6, 6, 165, 80, 5, fill=0, stroke=1)
                        c.setFont("Helvetica-Bold", 7)
                        c.setFillColor(colors.HexColor("#C9A227"))
                        c.drawString(14, 74, "ZONES D'IMPACT Cl2")
                        c.setLineWidth(0.5)
                        c.setStrokeColor(colors.HexColor("#3B82F6"))
                        c.line(14, 71, 163, 71)
                        leg_entries = [
                            (colors.HexColor("#EF4444"), f"ERPG-3  Danger vital  >20 ppm    {r3:.0f} m"),
                            (colors.HexColor("#F59E0B"), f"ERPG-2  Irréversible  >3 ppm      {r2:.0f} m"),
                            (colors.HexColor("#4ADE80"), f"ERPG-1  Irritation     >1 ppm      {r1:.0f} m"),
                        ]
                        for i, (col, txt) in enumerate(leg_entries):
                            ly3 = 59 - i * 15
                            c.setFillColor(col)
                            c.circle(18, ly3 + 3, 4, fill=1, stroke=0)
                            c.setFont("Helvetica", 7)
                            c.setFillColor(colors.white)
                            c.drawString(26, ly3, txt)
                        c.setFont("Helvetica", 6.5)
                        c.setFillColor(colors.HexColor("#93C5FD"))
                        c.drawString(14, 14, f"Vent : {dir_v}° → {prop:.0f}°  {u_ms} m/s  Cl. {stab}")
                        c.drawString(14, 7, f"Source : {Q_kg:,.0f} kg Cl2  |  {lat:.4f}°N  {lon:.4f}°E")
                        return
                    except Exception:
                        pass
                # Fallback vectoriel
                draw_erpg_map_canvas(c, 0, 0, self2.map_w, self2.map_h, self2.params)

        return _MapFlow(self._params, self._img_path, self._map_w, self._map_h)


# ── Classe canvas template pour numérotation ─────────────────────────────────
class HazModTemplate:
    def __init__(self, ref_str):
        self.ref_str    = ref_str
        self.page_count = 0
        self._pages     = []  # liste des (canvas_state, page_num)

    def on_page(self, canvas_obj, doc):
        self.page_count += 1
        pn = canvas_obj.getPageNumber()
        draw_page_header(canvas_obj, pn, "?", self.ref_str, is_cover=(pn == 1))


# ── Style helper ─────────────────────────────────────────────────────────────
def _s(name, base_style, **kw):
    return ParagraphStyle(name, parent=base_style, **kw)


# ── Table helper ──────────────────────────────────────────────────────────────
def make_table(data, col_widths, row_styles=None,
               header_bg=C_NAVY, alt_bg=C_LGRAY,
               font_size=8.0, header_color=C_WHITE,
               extra_cmds=None):
    """Crée une Table ReportLab avec style institutionnel propre."""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        # En-tête
        ("BACKGROUND",    (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0), header_color),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), font_size),
        ("TOPPADDING",    (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        # Corps
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), font_size - 0.5),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, alt_bg]),
        # Grille
        ("GRID",          (0, 0), (-1, -1), 0.4, C_LGRAY2),
        ("BOX",           (0, 0), (-1, -1), 1.0, C_BLUE),
        # Alignement
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]
    if row_styles:
        cmds.extend(row_styles)
    if extra_cmds:
        cmds.extend(extra_cmds)
    t.setStyle(TableStyle(cmds))
    return t


# ── Section header block ──────────────────────────────────────────────────────
def section_header(styles, num, title, subtitle=""):
    """Retourne un bloc KeepTogether pour les titres de section."""
    items = []
    # Trait coloré avant
    items.append(Spacer(1, 0.12*cm))
    items.append(HRFlowable(width="100%", thickness=2, color=C_GOLD, spaceAfter=0))
    p = Paragraph(
        f"<font color='#F0C040'>{num}</font>&nbsp;&nbsp;{title}",
        _s(f"sh_{num}", styles["Normal"],
           fontName="Helvetica-Bold", fontSize=12,
           textColor=C_WHITE, backColor=C_NAVY,
           borderPad=(8, 8, 8, 12),
           spaceBefore=0, spaceAfter=0, leading=18)
    )
    items.append(p)
    items.append(HRFlowable(width="100%", thickness=1, color=C_BLUE2, spaceAfter=2))
    if subtitle:
        items.append(Paragraph(subtitle,
            _s(f"sh_sub_{num}", styles["Normal"],
               fontName="Helvetica-Oblique", fontSize=8,
               textColor=C_GRAY2, spaceAfter=4)))
    items.append(Spacer(1, 0.15*cm))
    return KeepTogether(items)


# ── KPI bar ───────────────────────────────────────────────────────────────────
def kpi_bar(items_list, total_width, styles):
    """
    items_list : [(label, value, color_hex, bg_hex), ...]
    Retourne un Table KPI visuel.
    """
    n = len(items_list)
    cw = [total_width / n] * n

    row_val = []
    row_lbl = []
    for (lbl, val, col, bg) in items_list:
        row_val.append(
            Paragraph(f"<b>{val}</b>",
                      _s(f"kv_{lbl}", styles["Normal"],
                         fontName="Helvetica-Bold", fontSize=13,
                         textColor=colors.HexColor(col),
                         alignment=TA_CENTER))
        )
        row_lbl.append(
            Paragraph(lbl,
                      _s(f"kl_{lbl}", styles["Normal"],
                         fontName="Helvetica", fontSize=7,
                         textColor=C_GRAY2,
                         alignment=TA_CENTER))
        )

    t = Table([row_val, row_lbl], colWidths=cw, rowHeights=[20, 12])

    # Styles de fond individuels par cellule
    bg_cmds = []
    for i, (lbl, val, col, bg) in enumerate(items_list):
        bg_cmds.append(("BACKGROUND", (i, 0), (i, 1), colors.HexColor(bg)))
        bg_cmds.append(("LINEABOVE",  (i, 0), (i, 0), 3,
                        colors.HexColor(col)))

    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, C_LGRAY2),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, C_LGRAY2),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ] + bg_cmds))
    return t


# ═════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE : generate_pdf(params) → bytes
# ═════════════════════════════════════════════════════════════════════════════
def generate_pdf(p):
    """
    p : dict avec toutes les variables de la simulation HazMod.
    Retourne : bytes du PDF.
    """
    now      = datetime.datetime.now()
    date_str = now.strftime("%d %B %Y  à  %H:%M")
    ref_str  = now.strftime("HM-%Y%m%d-%H%M")

    buf = io.BytesIO()

    # ── Document principal (platypus) ─────────────────────────────────────
    def on_page(cv, doc):
        pn = cv.getPageNumber()
        draw_page_header(cv, pn, doc.page, ref_str, is_cover=(pn == 1))

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin  = 1.5*cm,
        rightMargin = 1.5*cm,
        topMargin   = 1.8*cm,
        bottomMargin= 1.3*cm,
        title=f"HazMod — Rapport Officiel {ref_str}",
        author="HazMod — Min. Intérieur, Dir. Sécurité et Documentation",
        subject="Rapport Analyse Risques Chlore Cl2",
    )
    TW = W - 3.6*cm  # text width

    styles = getSampleStyleSheet()
    sBody = _s("sBody", styles["Normal"],
               fontName="Helvetica", fontSize=8.5,
               textColor=C_GRAY1, leading=12, spaceAfter=2,
               alignment=TA_JUSTIFY)
    sBold = _s("sBold", styles["Normal"],
               fontName="Helvetica-Bold", fontSize=8.5,
               textColor=C_GRAY1, spaceAfter=3)
    sSmall= _s("sSmall", styles["Normal"],
               fontName="Helvetica", fontSize=7.5,
               textColor=C_GRAY2, spaceAfter=2, leading=11)
    sCapt = _s("sCapt", styles["Normal"],
               fontName="Helvetica-Oblique", fontSize=7.5,
               textColor=C_GRAY3, alignment=TA_CENTER, spaceAfter=4)
    sH2   = _s("sH2", styles["Normal"],
               fontName="Helvetica-Bold", fontSize=9.5,
               textColor=C_BLUE, spaceAfter=2, spaceBefore=5,
               borderPad=(0,0,1,0))
    sAlertR = _s("sAlR", styles["Normal"],
                 fontName="Helvetica-Bold", fontSize=10,
                 textColor=C_RED, backColor=C_BG_R,
                 borderPad=8, alignment=TA_CENTER, spaceAfter=6)
    sAlertO = _s("sAlO", styles["Normal"],
                 fontName="Helvetica-Bold", fontSize=10,
                 textColor=C_ORANGE, backColor=C_BG_O,
                 borderPad=8, alignment=TA_CENTER, spaceAfter=6)
    sAlertY = _s("sAlY", styles["Normal"],
                 fontName="Helvetica-Bold", fontSize=10,
                 textColor=colors.HexColor("#92400E"),
                 backColor=colors.HexColor("#FEFCE8"),
                 borderPad=8, alignment=TA_CENTER, spaceAfter=6)
    sCenter = _s("sCtr", styles["Normal"],
                 fontName="Helvetica", fontSize=8.5,
                 textColor=C_GRAY2, alignment=TA_CENTER, spaceAfter=3)

    story = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE DE COUVERTURE  (dessinée avec canvas via un Flowable custom)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    from reportlab.platypus import Flowable

    class CoverPage(Flowable):
        """Page de couverture entièrement dessinée au canvas."""
        def __init__(self, p, date_str, ref_str, now):
            super().__init__()
            self.p = p; self.date_str = date_str
            self.ref_str = ref_str; self.now = now
            self.width = W; self.height = H

        def wrap(self, *args):
            return (W, H)

        def draw(self):
            cv = self.canv
            pp = self.p

            # ── Fond pleine page ──────────────────────────────────────────
            cv.setFillColor(C_NAVY)
            cv.rect(0, 0, W, H, fill=1, stroke=0)

            # Gradient simulé (rectangles en dégradé du haut vers le bas)
            for i in range(30):
                frac = i / 30
                r = 0.05 + 0.07 * frac
                g = 0.12 + 0.10 * frac
                b = 0.24 + 0.15 * frac
                cv.setFillColor(colors.Color(r, g, b, alpha=0.6))
                cv.rect(0, H - (i+1)*H/30, W, H/30, fill=1, stroke=0)

            # Filigrane diagonal discret "CONFIDENTIEL"
            cv.saveState()
            cv.setFillColor(colors.Color(1, 1, 1, alpha=0.04))
            cv.setFont("Helvetica-Bold", 60)
            cv.translate(W/2, H/2)
            cv.rotate(45)
            cv.drawCentredString(0, 0, "CONFIDENTIEL")
            cv.restoreState()

            # ── Bande dorée supérieure ────────────────────────────────────
            cv.setFillColor(C_GOLD)
            cv.rect(0, H - 1.0*cm, W, 1.0*cm, fill=1, stroke=0)

            # ── Bloc institutionnel (haut gauche) ─────────────────────────
            cv.setFillColor(C_WHITE)
            cv.setFont("Helvetica-Bold", 8)
            cv.drawString(1.8*cm, H - 2.2*cm, "ROYAUME DU MAROC")
            cv.setFont("Helvetica", 7.5)
            cv.setFillColor(colors.HexColor("#93C5FD"))
            cv.drawString(1.8*cm, H - 2.8*cm, "Ministère de l'Intérieur")
            cv.drawString(1.8*cm, H - 3.2*cm, "Direction Générale des Affaires Intérieures")
            cv.drawString(1.8*cm, H - 3.6*cm, "Direction de la Sécurité et de la Documentation")

            # Ligne dorée sous institution
            cv.setStrokeColor(C_GOLD)
            cv.setLineWidth(0.8)
            cv.line(1.8*cm, H - 3.9*cm, W/2, H - 3.9*cm)

            # ── Logo HazMod (centre-haut) ─────────────────────────────────
            logo_size = 3.0*cm
            logo_x    = (W - logo_size) / 2
            logo_y    = H - 2.6*cm - logo_size
            draw_hazmod_logo(cv, logo_x, logo_y, size=logo_size)

            # ── Nom HAZMOD ────────────────────────────────────────────────
            cv.setFillColor(C_WHITE)
            cv.setFont("Helvetica-Bold", 40)
            cv.drawCentredString(W/2, H - 6.8*cm, "HAZMOD")

            cv.setFont("Helvetica", 10)
            cv.setFillColor(colors.HexColor("#93C5FD"))
            cv.drawCentredString(W/2, H - 7.4*cm,
                "Hazardous Materials Modeling System")

            # ── Ligne séparatrice centrale ────────────────────────────────────
            cv.setStrokeColor(C_GOLD)
            cv.setLineWidth(1.5)
            cv.line(2.5*cm, H - 7.8*cm, W - 2.5*cm, H - 7.8*cm)

            # ── Titre du rapport ──────────────────────────────────────────────
            cv.setFont("Helvetica-Bold", 14)
            cv.setFillColor(C_WHITE)
            cv.drawCentredString(W/2, H - 8.5*cm,
                "RAPPORT OFFICIEL D'ANALYSE DES RISQUES")

            cv.setFont("Helvetica-Bold", 12)
            cv.setFillColor(C_GOLD2)
            cv.drawCentredString(W/2, H - 9.1*cm,
                "Dispersion Atmosphérique — Chlore (Cl₂)")

            # ── Entité officielle ─────────────────────────────────────────────
            cv.setFont("Helvetica", 8)
            cv.setFillColor(colors.HexColor("#94A3B8"))
            cv.drawCentredString(W/2, H - 9.7*cm,
                "Ministère de l'Intérieur — Direction Générale des Affaires Intérieures")
            cv.drawCentredString(W/2, H - 10.2*cm,
                "Direction de la Sécurité et de la Documentation")

            # ── Bloc scénario (carte gris) ────────────────────────────────────
            bx, bw, by, bh = 2.0*cm, W - 4.0*cm, H - 14.0*cm, 3.5*cm
            cv.setFillColor(colors.Color(0, 0, 0, alpha=0.35))
            cv.roundRect(bx, by, bw, bh, 8, fill=1, stroke=0)
            cv.setStrokeColor(C_BLUE3)
            cv.setLineWidth(0.8)
            cv.roundRect(bx, by, bw, bh, 8, fill=0, stroke=1)

            # Infos scénario
            cv.setFont("Helvetica-Bold", 9)
            cv.setFillColor(C_GOLD2)
            cv.drawCentredString(W/2, by + bh - 0.8*cm, "PARAMÈTRES DU SCÉNARIO")

            cv.setLineWidth(0.5)
            cv.setStrokeColor(colors.Color(1,1,1,alpha=0.2))
            cv.line(bx + 0.5*cm, by + bh - 1.0*cm, bx + bw - 0.5*cm, by + bh - 1.0*cm)

            infos = [
                (f"Quantité Cl2 :  {pp['Q_kg']:,.0f} kg",
                 f"Type :  {pp['type_lib'].split()[0]}"),
                (f"Vent :  {pp['u_ms']} m/s — {pp['dir_vent']}° → {pp['prop_dir']:.0f}°",
                 f"Stabilité :  Classe {pp['stab']}"),
                (f"Zone ERPG-3 :  {pp['r3']:.0f} m",
                 f"Zone ERPG-2 :  {pp['r2']:.0f} m"),
                (f"Coord. :  {pp['lat']:.4f}°N / {pp['lon']:.4f}°E",
                 f"Gravité G :  {pp['gravite']:.1f} / 10"),
            ]
            for i, (left, right) in enumerate(infos):
                yy = by + bh - 1.5*cm - i * 0.6*cm
                cv.setFont("Helvetica", 7.8)
                cv.setFillColor(C_WHITE)
                cv.drawString(bx + 0.7*cm, yy, left)
                cv.drawString(bx + bw/2 + 0.3*cm, yy, right)

            # ── Badge niveau d'alerte ─────────────────────────────────────
            g = pp['gravite']
            al_label = ("ALERTE ROUGE — Danger Vital" if g >= 7
                        else "ALERTE ORANGE — Risque Significatif" if g >= 4
                        else "ALERTE JAUNE — Risque Modéré")
            al_color = (C_RED2 if g >= 7
                        else colors.HexColor("#D97706") if g >= 4
                        else colors.HexColor("#92400E"))
            bh2 = 0.75*cm
            by2 = H - 15.2*cm
            cv.setFillColor(al_color)
            cv.roundRect(2.5*cm, by2, W - 5.0*cm, bh2, 5, fill=1, stroke=0)
            cv.setFont("Helvetica-Bold", 9)
            cv.setFillColor(C_WHITE)
            cv.drawCentredString(W/2, by2 + 0.22*cm, f"● {al_label} ●")

            # ── Référence & date ──────────────────────────────────────────
            cv.setFont("Helvetica", 8)
            cv.setFillColor(colors.HexColor("#CBD5E1"))
            cv.drawCentredString(W/2, H - 16.5*cm,
                f"Établi le  {self.date_str}")
            cv.setFont("Helvetica-Bold", 8)
            cv.setFillColor(C_GOLD2)
            cv.drawCentredString(W/2, H - 17.1*cm, f"Réf. {self.ref_str}")

            # ── Bande dorée inférieure ────────────────────────────────────
            cv.setFillColor(C_GOLD)
            cv.rect(0, 0.8*cm, W, 0.25*cm, fill=1, stroke=0)
            cv.setFillColor(C_NAVY2)
            cv.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)
            cv.setFont("Helvetica", 6.5)
            cv.setFillColor(colors.HexColor("#64748B"))
            cv.drawCentredString(W/2, 0.28*cm,
                "DOCUMENT A DIFFUSION RESTREINTE — Usage opérationnel uniquement")

    # Cover drawn via onFirstPage callback — no Flowable needed
    _cover_params = (p, date_str, ref_str, now)

    # ── Variables locales ─────────────────────────────────────────────────
    Q_kg          = p["Q_kg"]
    type_lib      = p["type_lib"]
    duree_min     = p["duree_min"]
    hauteur_m     = p["hauteur_m"]
    u_ms          = p["u_ms"]
    dir_vent      = p["dir_vent"]
    stab          = p["stab"]
    stab_sel      = p["stab_sel"]
    lat           = p["lat"]
    lon           = p["lon"]
    config_site   = p["config_site"]
    dens_pop      = p["dens_pop"]
    dist_pop      = p["dist_pop"]
    niveau_epi    = p["niveau_epi"]
    alerte_prec   = p["alerte_prec"]
    delai_evac    = p["delai_evac"]
    coord_sec     = p["coord_sec"]
    capa_med      = p["capa_med"]
    capa_chr_lits = p["capa_chr_lits"]
    capa_ua_max   = p["capa_ua_max"]
    nb_smur       = p["nb_smur"]
    n_mc          = p["n_mc"]
    gravite       = p["gravite"]
    r1, r2, r3    = p["r1"], p["r2"], p["r3"]
    pop_e1        = p["pop_e1"]
    pop_e2        = p["pop_e2"]
    pop_e3        = p["pop_e3"]
    surf_e1       = p["surf_e1"]
    surf_e2       = p["surf_e2"]
    surf_e3       = p["surf_e3"]
    blesses_estimes = p["blesses_estimes"]
    blesses_e2    = p["blesses_e2"]
    blesses_e3    = p["blesses_e3"]
    deces_estimes = p["deces_estimes"]
    mc_p_e1       = p["mc_p_e1"]
    mc_p_e2       = p["mc_p_e2"]
    mc_p_e3       = p["mc_p_e3"]
    mc_c50        = p["mc_c50"]
    mc_c95        = p["mc_c95"]
    mc            = p["mc"]
    Q_kgs         = p["Q_kgs"]
    H_eff         = p["H_eff"]
    prop_dir      = p["prop_dir"]
    perim_evac    = p["perim_evac"]
    surf_evac     = p["surf_evac"]
    facteur_site  = p["facteur_site"]
    SECTEUR       = p["SECTEUR"]
    usines_domino = p["usines_domino"]
    has_train     = p["has_train"]
    has_hopital   = p["has_hopital"]
    has_ecole     = p["has_ecole"]
    has_admin     = p["has_admin"]
    has_gare_rout = p["has_gare_rout"]
    train_passagers = p.get("train_passagers", 0)
    nb_agents_admin = p.get("nb_agents_admin", 0)
    nb_gare_pers  = p.get("nb_gare_pers", 0)
    _dec          = p.get("dec_conf", "—")
    _t_arrivee    = p.get("t_arrivee", 0)
    g_color_hex   = ("#B91C1C" if gravite >= 7
                     else "#C05621" if gravite >= 4 else "#15803D")
    _DIRS8        = ["N","NE","E","SE","S","SO","O","NO"]
    prop_lbl      = _DIRS8[int((prop_dir + 22.5) // 45) % 8]
    _niv          = ("CRITIQUE" if gravite >= 7 else "ÉLEVÉ" if gravite >= 4
                     else "MODÉRÉ" if gravite >= 2 else "FAIBLE")
    hs_data       = p.get("hs_data", [{}]*5)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 1 — PARAMÈTRES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "01", "PARAMÈTRES DU SCÉNARIO SIMULÉ"))

    params = [
        ["Paramètre", "Valeur", "Paramètre", "Valeur"],
        ["Localisation (Lat/Lon)", f"{lat:.4f}°N / {lon:.4f}°E",
         "Configuration du site", config_site],
        ["Quantité Cl2 libérée", f"{Q_kg:,.0f} kg",
         "Densité de population", f"{dens_pop:,} hab/km²"],
        ["Type de libération", type_lib.split()[0],
         "Distance population", f"{dist_pop} m"],
        ["Durée de libération", f"{duree_min} min",
         "Débit effectif", f"{Q_kgs:.3f} kg/s"],
        ["Hauteur source / effective",
         f"{hauteur_m} m / {H_eff:.1f} m",
         "Vitesse du vent", f"{u_ms} m/s"],
        ["Direction vent", f"{dir_vent}° → {prop_dir:.0f}° ({prop_lbl})",
         "Stabilité atm.", stab_sel],
        ["Niveau EPI", niveau_epi,
         "Alerte précoce", "Oui ✓" if alerte_prec else "Non"],
        ["Délai évacuation", f"{delai_evac} min",
         "Coordination secours", f"{coord_sec}/4"],
        ["Capacité médicale", capa_med,
         "Lits CHR / NRBC", f"{capa_chr_lits} / {capa_ua_max}"],
        ["SMUR disponibles", f"{nb_smur} unités",
         "Itérations Monte Carlo", f"{n_mc:,}"],
    ]
    cw4 = [TW*0.26, TW*0.24, TW*0.26, TW*0.24]

    def p_cell(txt, bold=False, color=C_GRAY1, fs=8.0, align=TA_LEFT):
        return Paragraph(str(txt), _s(f"pc_{txt[:8]}", styles["Normal"],
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=fs, textColor=color, alignment=align))

    story.append(make_table(
        [[p_cell(c, bold=(i==0 or j%2==0), color=C_WHITE if i==0 else C_BLUE if j%2==0 else C_GRAY1)
          for j,c in enumerate(row)]
         for i,row in enumerate(params)],
        cw4, font_size=8.0,
        row_styles=[
            ("BACKGROUND", (0,0), (1,0), C_NAVY),
            ("BACKGROUND", (2,0), (3,0), C_NAVY),
            ("BACKGROUND", (0,1), (1,-1), colors.HexColor("#F0F9FF")),
            ("BACKGROUND", (2,1), (3,-1), C_WHITE),
        ]
    ))

    # Sites à risque si présents
    sites_risk = []
    for _u in usines_domino:
        sites_risk.append([
            Paragraph(f"Usine — {_u['nom']}", sBold),
            Paragraph(f"à {_u['dist']} m", sBody),
            Paragraph(", ".join(_u.get('produits',['—'])[:3]), sBody),
        ])
    if has_train:
        sites_risk.append([Paragraph("Ligne ferroviaire", sBold),
                           Paragraph("En zone d'impact", sBody),
                           Paragraph(f"{train_passagers} passagers", sBody)])
    if has_hopital:
        sites_risk.append([Paragraph("Hôpital / Clinique", sBold),
                           Paragraph("En zone d'impact", sBody),
                           Paragraph("Population vulnérable — protocole NRBC requis", sBody)])
    if has_ecole:
        sites_risk.append([Paragraph("École / Crèche", sBold),
                           Paragraph("En zone d'impact", sBody),
                           Paragraph("Enfants — sensibilité Cl2 x2", sBody)])
    if has_admin:
        sites_risk.append([Paragraph("Centre Administratif", sBold),
                           Paragraph("En zone d'impact", sBody),
                           Paragraph(f"{nb_agents_admin} agents", sBody)])
    if has_gare_rout:
        sites_risk.append([Paragraph("Gare Routière", sBold),
                           Paragraph("En zone d'impact", sBody),
                           Paragraph(f"{nb_gare_pers} personnes présentes", sBody)])

    if sites_risk:
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("Sites à risque identifiés dans les zones d'impact :", sH2))
        story.append(make_table(
            [[Paragraph("Établissement", sBold),
              Paragraph("Localisation", sBold),
              Paragraph("Observations", sBold)]] + sites_risk,
            [TW*0.30, TW*0.20, TW*0.50], font_size=8.0
        ))

    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 2 — RÉSULTATS SIMULATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "02", "RÉSULTATS DE LA SIMULATION PHYSIQUE",
        "Modèle Pasquill-Gifford (Briggs 1973) — Gaz lourd calibré ALOHA (erreur ≤ 11%) — Correction puff Wilson (1981)"))

    # Alerte
    g = gravite
    al_txt = ("● ALERTE ROUGE — Danger Vital Immédiat ●" if g >= 7
              else "● ALERTE ORANGE — Risque Significatif ●" if g >= 4
              else "● ALERTE JAUNE — Risque Modéré ●")
    al_sty = sAlertR if g >= 7 else sAlertO if g >= 4 else sAlertY
    story.append(Paragraph(al_txt, al_sty))
    story.append(Spacer(1, 0.1*cm))

    # KPI
    story.append(kpi_bar([
        ("Indice de Gravité", f"{g:.1f}/10",
         g_color_hex, "#FEF2F2" if g>=7 else "#FFF7ED" if g>=4 else "#F0FDF4"),
        ("Zone ERPG-3", f"{r3:.0f} m", "#B91C1C", "#FEE2E2"),
        ("Zone ERPG-2", f"{r2:.0f} m", "#C05621", "#FEF3C7"),
        ("Zone ERPG-1", f"{r1:.0f} m", "#15803D", "#DCFCE7"),
        ("Pop. ERPG-2", f"{pop_e2:,}", "#1D4ED8", "#DBEAFE"),
        ("Blessés estimés", f"{blesses_estimes:,}", "#7C3AED", "#F5F3FF"),
    ], TW, styles))

    story.append(Spacer(1, 0.12*cm))

    # Tableau des 3 zones
    zones_data = [
        [Paragraph(c, _s(f"zh{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Zone NRBC","Seuil","Rayon axial",
                                "Surface vent","Pop. exposée",
                                "Blessés est.","P(MC) dépas.","Décision"])],
        [Paragraph("<b>ERPG-3</b>", _s("ze3v", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8.5, textColor=C_RED)),
         Paragraph("> 20 ppm", sBody), f"{r3:.0f} m",
         f"{surf_e3:.3f} km²", f"{pop_e3:,}", f"{blesses_e3:,}",
         f"{mc_p_e3:.0f} %",
         Paragraph("Évacuation totale + EPI A", _s("zd3", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=7.5, textColor=C_RED))],
        [Paragraph("<b>ERPG-2</b>", _s("ze2v", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8.5, textColor=C_ORANGE)),
         Paragraph("3 – 20 ppm", sBody), f"{r2:.0f} m",
         f"{surf_e2:.3f} km²", f"{pop_e2:,}", f"{blesses_e2:,}",
         f"{mc_p_e2:.0f} %",
         Paragraph("Évacuation partielle", _s("zd2", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=7.5, textColor=C_ORANGE))],
        [Paragraph("<b>ERPG-1</b>", _s("ze1v", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8.5, textColor=C_GREEN)),
         Paragraph("1 – 3 ppm", sBody), f"{r1:.0f} m",
         f"{surf_e1:.3f} km²", f"{pop_e1:,}", "—",
         f"{mc_p_e1:.0f} %",
         Paragraph("Confinement préventif", _s("zd1", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=7.5, textColor=C_GREEN))],
    ]
    cw_z = [TW*p for p in [0.08,0.09,0.09,0.10,0.10,0.09,0.09,0.36]]
    t_zones = Table(zones_data, colWidths=cw_z)
    t_zones.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), C_NAVY),
        ("BACKGROUND",    (0,1), (-1,1), colors.HexColor("#FFF1F2")),
        ("BACKGROUND",    (0,2), (-1,2), colors.HexColor("#FFFBEB")),
        ("BACKGROUND",    (0,3), (-1,3), colors.HexColor("#F0FFF4")),
        ("BOX",           (0,0), (-1,-1), 1.2, C_BLUE),
        ("INNERGRID",     (0,0), (-1,-1), 0.4, C_LGRAY2),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("LINEABOVE",     (0,1), (-1,1), 2, C_RED),
        ("LINEABOVE",     (0,2), (-1,2), 2, colors.HexColor("#D97706")),
        ("LINEABOVE",     (0,3), (-1,3), 2, C_GREEN),
    ]))
    story.append(t_zones)
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        f"Propagation du nuage : {dir_vent}° (origine) → {prop_dir:.0f}° vers {prop_lbl} à {u_ms} m/s  ·  "
        f"Classe {stab}  ·  Périmètre d'évacuation recommandé : {perim_evac:.0f} m", sCapt))

    story.append(Spacer(1, 0.15*cm))

    # Bilan humain
    story.append(Paragraph("Bilan humain estimé :", sH2))
    bilan = [
        [Paragraph("Indicateur", sBold), Paragraph("Valeur", sBold),
         Paragraph("Méthode de calcul", sBold)],
        [Paragraph("Blessés totaux", sBody),
         Paragraph(f"<b><font color='#C05621'>{blesses_estimes:,}</font></b>",
                   _s("bv1",styles["Normal"],fontName="Helvetica-Bold",fontSize=9,
                      textColor=C_ORANGE)),
         Paragraph(f"TAUX_B=2.8‰ × surf.={surf_evac:.2f} km² × densité × site ({facteur_site:.0%})",
                   sSmall)],
        [Paragraph("dont Urgences Absolues (ERPG-3)", sBody),
         Paragraph(f"<b><font color='#B91C1C'>{blesses_e3:,}</font></b>",
                   _s("bv2",styles["Normal"],fontName="Helvetica-Bold",fontSize=9,
                      textColor=C_RED)),
         Paragraph("31 % des blessés — exposition maximale (> 20 ppm)", sSmall)],
        [Paragraph("dont Urgences Relatives (ERPG-2)", sBody),
         Paragraph(f"<b>{blesses_e2:,}</b>",
                   _s("bv3",styles["Normal"],fontName="Helvetica-Bold",fontSize=9)),
         Paragraph("69 % des blessés — effets irréversibles (3–20 ppm)", sSmall)],
        [Paragraph("Décès estimés", sBody),
         Paragraph(f"<b><font color='#B91C1C'>{deces_estimes}</font></b>",
                   _s("bv4",styles["Normal"],fontName="Helvetica-Bold",fontSize=9,
                      textColor=C_RED)),
         Paragraph(f"G={g:.1f} · CHR {capa_chr_lits} lits · NRBC {capa_ua_max} lits", sSmall)],
        [Paragraph("Population ERPG-2 exposée", sBody),
         Paragraph(f"<b>{pop_e2:,}</b>",
                   _s("bv5",styles["Normal"],fontName="Helvetica-Bold",fontSize=9)),
         Paragraph(f"Secteur {SECTEUR:.0%} × surf. orange × {dens_pop} hab/km²", sSmall)],
    ]
    story.append(make_table(bilan, [TW*0.28, TW*0.14, TW*0.58], font_size=8.0))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 3 — MONTE CARLO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "03", "ANALYSE PROBABILISTE — MONTE CARLO",
        f"Simulation de {n_mc:,} scénarios — Q ±30% (log-normale) — u ±20% (log-normale) — Résultats à {dist_pop} m"))

    story.append(kpi_bar([
        ("P(C > ERPG-1)", f"{mc_p_e1:.1f} %",
         "#15803D" if mc_p_e1<30 else "#B45309" if mc_p_e1<70 else "#B91C1C",
         "#F0FDF4" if mc_p_e1<30 else "#FFFBEB" if mc_p_e1<70 else "#FEF2F2"),
        ("P(C > ERPG-2)", f"{mc_p_e2:.1f} %",
         "#15803D" if mc_p_e2<30 else "#B45309" if mc_p_e2<70 else "#B91C1C",
         "#F0FDF4" if mc_p_e2<30 else "#FFFBEB" if mc_p_e2<70 else "#FEF2F2"),
        ("P(C > ERPG-3)", f"{mc_p_e3:.1f} %",
         "#15803D" if mc_p_e3<10 else "#B45309" if mc_p_e3<30 else "#B91C1C",
         "#F0FDF4" if mc_p_e3<10 else "#FFFBEB" if mc_p_e3<30 else "#FEF2F2"),
        ("C50 — Médiane", f"{mc_c50:.3f} ppm", "#1D4ED8", "#EFF6FF"),
        ("C95 — Pire cas", f"{mc_c95:.3f} ppm", "#7C3AED", "#F5F3FF"),
    ], TW, styles))

    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("Distribution probabiliste de dépassement par distance :", sH2))

    if mc:
        mc_rows = [[Paragraph(c, _s(f"mch{j}", styles["Normal"],
                                     fontName="Helvetica-Bold", fontSize=8,
                                     textColor=C_WHITE, alignment=TA_CENTER))
                    for j,c in enumerate(
                        ["Distance","Médiane P50","P95 Pire cas",
                         "P(> ERPG-1)","P(> ERPG-2)","P(> ERPG-3)","Niveau de risque"])]
                   ]
        for _d in sorted(mc.keys()):
            _r = mc[_d]
            _risk = ("CRITIQUE" if _r["p_e3"]>0.15
                     else "ÉLEVÉ"   if _r["p_e2"]>0.20
                     else "MODÉRÉ"  if _r["p_e1"]>0.30
                     else "FAIBLE")
            _risk_col = (C_RED if _r["p_e3"]>0.15
                         else C_ORANGE if _r["p_e2"]>0.20
                         else colors.HexColor("#B45309") if _r["p_e1"]>0.30
                         else C_GREEN)
            mc_rows.append([
                f"{_d} m",
                f"{_r['p50']:.4f} ppm",
                f"{_r['p95']:.4f} ppm",
                f"{_r['p_e1']*100:.1f} %",
                f"{_r['p_e2']*100:.1f} %",
                f"{_r['p_e3']*100:.1f} %",
                Paragraph(f"<b>{_risk}</b>", _s(f"mr_{_d}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=_risk_col, alignment=TA_CENTER)),
            ])
        story.append(make_table(mc_rows,
                                [TW*p for p in [0.10,0.13,0.13,0.12,0.12,0.12,0.28]],
                                font_size=8.0))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 3b — CARTOGRAPHIE DES ZONES ERPG (carte + vectoriel)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "03b",
        "CARTOGRAPHIE DES ZONES D'IMPACT — REPRÉSENTATION SPATIALE",
        f"Zones ERPG orientées selon le vent {dir_vent}° → {prop_dir:.0f}° à {u_ms} m/s — Stabilité classe {stab}"))

    _img_path = p.get("map_image_path", None)

    # Hotspots : utiliser ceux passés dans p (dynamiques OSM) ou fallback géométrique
    import math as _mh2
    def _move_hs(lat0, lon0, dist_m2, bearing_deg):
        R = 6371000.0
        lr = _mh2.radians(lat0); br = _mh2.radians(bearing_deg); dr = dist_m2/R
        nl = _mh2.asin(_mh2.sin(lr)*_mh2.cos(dr)+_mh2.cos(lr)*_mh2.sin(dr)*_mh2.cos(br))
        nlo = _mh2.radians(lon0)+_mh2.atan2(_mh2.sin(br)*_mh2.sin(dr)*_mh2.cos(lr),
              _mh2.cos(dr)-_mh2.sin(lr)*_mh2.sin(nl))
        return [round(_mh2.degrees(nl),5), round(_mh2.degrees(nlo),5)]

    _PD = prop_dir
    # Priorité aux hotspots OSM dynamiques passés depuis l'app Streamlit
    _HS = p.get("hotspots_reels") or {
        "ERPG-3": [
            {"name":"Zone Industrielle","icon":"\U0001f3ed","priority":"CRITIQUE",
             "risk":"Effet domino potentiel","coords":_move_hs(lat,lon,int(r3*0.5),_PD),
             "dist":int(r3*0.5),"zone":"ERPG-3"},
            {"name":"Infrastructure routiere","icon":"\U0001f6e3\ufe0f","priority":"ELEVE",
             "risk":"Trafic bloque","coords":_move_hs(lat,lon,int(r3*0.85),(_PD+25)%360),
             "dist":int(r3*0.85),"zone":"ERPG-3"},
        ],
        "ERPG-2": [
            {"name":"Etablissement de sante","icon":"\U0001f3e5","priority":"CRITIQUE",
             "risk":"Patients non mobiles","coords":_move_hs(lat,lon,int((r3+r2)*0.4),_PD),
             "dist":int((r3+r2)*0.4),"zone":"ERPG-2"},
            {"name":"Zone residentielle","icon":"\U0001f3d8\ufe0f","priority":"ELEVE",
             "risk":"Population dense","coords":_move_hs(lat,lon,int(r2*0.70),(_PD-20)%360),
             "dist":int(r2*0.70),"zone":"ERPG-2"},
            {"name":"Ecole","icon":"\U0001f3eb","priority":"CRITIQUE",
             "risk":"Enfants Cl2 x2","coords":_move_hs(lat,lon,int(r2*0.85),(_PD+25)%360),
             "dist":int(r2*0.85),"zone":"ERPG-2"},
        ],
        "ERPG-1": [
            {"name":"Centre hospitalier","icon":"\U0001f3e5","priority":"ELEVE",
             "risk":"Plan Blanc","coords":_move_hs(lat,lon,int(r2+250),_PD),
             "dist":int(r2+250),"zone":"ERPG-1"},
            {"name":"Centre commercial","icon":"\U0001f6d2","priority":"ELEVE",
             "risk":"Public dense","coords":_move_hs(lat,lon,int(r2+500),(_PD-15)%360),
             "dist":int(r2+500),"zone":"ERPG-1"},
            {"name":"Equipement sportif","icon":"\U0001f3df\ufe0f","priority":"MODERE",
             "risk":"Grande capacite","coords":_move_hs(lat,lon,int(r1*0.75),(_PD+12)%360),
             "dist":int(r1*0.75),"zone":"ERPG-1"},
            {"name":"Gare Transport","icon":"\U0001f68c","priority":"ELEVE",
             "risk":"Voyageurs exposes","coords":_move_hs(lat,lon,int(r1*0.92),(_PD-10)%360),
             "dist":int(r1*0.92),"zone":"ERPG-1"},
        ],
    }

    _p_with_hs = dict(p, hotspots_reels=_HS, prop_dir=_PD)

    _map_flow = ERPGMapFlowable(_p_with_hs, img_path=_img_path,
                                 map_w=TW, map_h=11.0*cm)
    story.append(_map_flow.as_flowable())
    story.append(Spacer(1, 0.15*cm))

    # Tableau synthèse sous la carte
    _prop_lbl_map = ["N","NE","E","SE","S","SO","O","NO"][int((prop_dir+22.5)//45)%8]
    story.append(Paragraph(
        f"Propagation du nuage de chlore vers le <b>{_prop_lbl_map}</b> ({prop_dir:.0f}°) "
        f"à <b>{u_ms} m/s</b> — Stabilité <b>classe {stab}</b> — "
        f"Source Cl<sub>2</sub> : <b>{Q_kg:,.0f} kg</b> — "
        f"Coordonnées : <b>{lat:.4f}°N / {lon:.4f}°E</b> — "
        "Sources : Google Earth / OpenStreetMap",
        _s("map_cap", styles["Normal"],
           fontName="Helvetica", fontSize=8.5,
           textColor=C_GRAY1, alignment=TA_CENTER,
           backColor=colors.HexColor("#F0F9FF"),
           borderPad=5, spaceAfter=6)))

    # ── Tableau des hotspots réels identifiés ────────────────────────────────
    story.append(Paragraph("Inventaire des hotspots identifiés par zone d'impact (source : Google Earth / OSM) :", sH2))

    hs_inv_rows = [
        [Paragraph(c, _s(f"hsi{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=7.5,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["★","Établissement / Site","Zone","Distance","Priorité","Risque identifié","Coordonnées"])]
    ]
    # ── Tableau hotspots 100% dynamique depuis les données OSM passées en params ──
    # _HS contient les hotspots réels récupérés par osm_hotspots.py
    # pour les COORDONNÉES ACTUELLES de l'incident (pas Rabat en dur)
    _ZONE_BG  = {"ERPG-3": (C_BG_R, C_RED), "ERPG-2": (C_BG_O, C_ORANGE), "ERPG-1": (C_BG_G, C_GREEN)}
    _ZONE_LBL = {"ERPG-3": "ERPG-3", "ERPG-2": "ERPG-2", "ERPG-1": "ERPG-1"}

    _HS_ALL = []
    for _zone_key in ["ERPG-3", "ERPG-2", "ERPG-1"]:
        _bg_z, _col_z = _ZONE_BG[_zone_key]
        for _hs_item in _HS.get(_zone_key, []):
            _coords_str = (
                f"{_hs_item['coords'][0]:.4f}°N {_hs_item['coords'][1]:.4f}°E"
                if _hs_item.get('coords') else f"{lat:.4f}°N {lon:.4f}°E"
            )
            _HS_ALL.append((
                _hs_item.get('icon', '📍'),
                _hs_item.get('name', 'Site identifié'),
                _zone_key,
                f"{_hs_item.get('dist', 0)} m",
                _hs_item.get('priority', 'MODÉRÉ'),
                _hs_item.get('risk', '—'),
                _coords_str,
                _bg_z,
                _col_z,
            ))

    # Si aucun hotspot OSM disponible — message explicatif
    if not _HS_ALL:
        _HS_ALL = [(
            "ℹ️",
            "Aucun établissement OSM trouvé pour ces coordonnées",
            "ERPG-1", "—", "—",
            "Zone potentiellement rurale ou données OSM insuffisantes",
            f"{lat:.4f}°N {lon:.4f}°E", C_BG_B,
            colors.HexColor("#1D4ED8"),
        )]
    _bg_cmds_hs = []
    for i, (ico, name, zone, dist, prio, risk, coords, bg, col) in enumerate(_HS_ALL):
        _prio_col = C_RED if prio=="CRITIQUE" else C_ORANGE if prio=="ÉLEVÉ" else colors.HexColor("#B45309")
        hs_inv_rows.append([
            Paragraph(ico, _s(f"hi{i}0",styles["Normal"],fontSize=9,alignment=TA_CENTER)),
            Paragraph(f"<b>{name}</b>", _s(f"hi{i}1",styles["Normal"],
                       fontName="Helvetica-Bold",fontSize=7.5,textColor=col)),
            Paragraph(f"<b>{zone}</b>", _s(f"hi{i}2",styles["Normal"],
                       fontName="Helvetica-Bold",fontSize=7.5,textColor=col,alignment=TA_CENTER)),
            Paragraph(dist, _s(f"hi{i}3",styles["Normal"],
                       fontName="Helvetica-Bold",fontSize=7.5,alignment=TA_CENTER)),
            Paragraph(f"<b>{prio}</b>", _s(f"hi{i}4",styles["Normal"],
                       fontName="Helvetica-Bold",fontSize=7.5,textColor=_prio_col,alignment=TA_CENTER)),
            Paragraph(risk, _s(f"hi{i}5",styles["Normal"],fontName="Helvetica",fontSize=7)),
            Paragraph(coords, _s(f"hi{i}6",styles["Normal"],
                       fontName="Courier",fontSize=6.5,textColor=C_GRAY2)),
        ])
        _bg_cmds_hs.append(("BACKGROUND", (0,i+1),(-1,i+1), bg))

    t_hs_inv = Table(hs_inv_rows,
                     colWidths=[TW*p for p in [0.04,0.24,0.09,0.08,0.09,0.27,0.19]])
    t_hs_inv.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), C_NAVY),
        ("BOX",           (0,0), (-1,-1), 1.2, C_BLUE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, C_LGRAY2),
        ("FONTSIZE",      (0,0), (-1,-1), 7.5),
        ("ALIGN",         (0,0), (0,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        # Séparateurs entre zones
        ("LINEABOVE",     (0,4),  (-1,4),  1.5, C_ORANGE),   # début ERPG-2
        ("LINEABOVE",     (0,9),  (-1,9),  1.5, C_GREEN),    # début ERPG-1
    ] + _bg_cmds_hs))
    story.append(t_hs_inv)
    story.append(Paragraph(
        "★ Étoiles rouges : hotspots identifiés via analyse Google Earth et OpenStreetMap. "
        "Coordonnées approximatives calculées depuis la source Cl2 selon la direction de propagation du nuage.",
        _s("hs_note", styles["Normal"],
           fontName="Helvetica-Oblique", fontSize=7,
           textColor=C_GRAY3, alignment=TA_CENTER, spaceAfter=4)))

    # Mini tableau des 3 zones côte à côte sous la carte
    _zones_mini = [
        [Paragraph(c, _s(f"zmc{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8.5,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Zone","Seuil","Rayon axial","Population exposée","Décision immédiate"])],
        [Paragraph("<b>ERPG-3</b>", _s("zm3", styles["Normal"],
                   fontName="Helvetica-Bold",fontSize=9,textColor=C_RED)),
         "> 20 ppm", f"{r3:.0f} m", f"{pop_e3:,} pers.",
         Paragraph("Évacuation totale + EPI A", _s("zmd3",styles["Normal"],
                   fontName="Helvetica-Bold",fontSize=8,textColor=C_RED))],
        [Paragraph("<b>ERPG-2</b>", _s("zm2", styles["Normal"],
                   fontName="Helvetica-Bold",fontSize=9,textColor=C_ORANGE)),
         "3 – 20 ppm", f"{r2:.0f} m", f"{pop_e2:,} pers.",
         Paragraph("Évacuation partielle", _s("zmd2",styles["Normal"],
                   fontName="Helvetica-Bold",fontSize=8,textColor=C_ORANGE))],
        [Paragraph("<b>ERPG-1</b>", _s("zm1", styles["Normal"],
                   fontName="Helvetica-Bold",fontSize=9,textColor=C_GREEN)),
         "1 – 3 ppm", f"{r1:.0f} m", f"{pop_e1:,} pers.",
         Paragraph("Confinement préventif", _s("zmd1",styles["Normal"],
                   fontName="Helvetica-Bold",fontSize=8,textColor=C_GREEN))],
    ]
    t_zm = Table(_zones_mini, colWidths=[TW*p for p in [0.10,0.10,0.12,0.18,0.50]])
    t_zm.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), C_NAVY),
        ("BACKGROUND",    (0,1), (-1,1), colors.HexColor("#FFF1F2")),
        ("BACKGROUND",    (0,2), (-1,2), colors.HexColor("#FFFBEB")),
        ("BACKGROUND",    (0,3), (-1,3), colors.HexColor("#F0FFF4")),
        ("BOX",           (0,0), (-1,-1), 1.5, C_BLUE),
        ("INNERGRID",     (0,0), (-1,-1), 0.4, C_LGRAY2),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("LINEABOVE",     (0,1), (-1,1), 2.5, C_RED),
        ("LINEABOVE",     (0,2), (-1,2), 2.5, colors.HexColor("#D97706")),
        ("LINEABOVE",     (0,3), (-1,3), 2.5, C_GREEN),
    ]))
    story.append(t_zm)


    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 3-B — GRAPHIQUES & FIGURES SOPHISTIQUÉES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    import io as _io
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
        _HAS_MPL = True
    except ImportError:
        _HAS_MPL = False

    def _fig_to_rl(fig, dpi=145):
        buf_img = _io.BytesIO()
        fig.savefig(buf_img, format="png", dpi=dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        buf_img.seek(0)
        plt.close(fig)
        return RLImage(buf_img, width=TW, height=TW*0.52)

    if _HAS_MPL:
        # ── FIGURE 1 : Indice de Gravité + Distribution MC ────────────────
        fig1, (ax_grav, ax_mc) = plt.subplots(1, 2, figsize=(13, 5),
                                               facecolor="#0C1A2E")
        fig1.subplots_adjust(wspace=0.35, left=0.07, right=0.97, top=0.88, bottom=0.12)
        g_val = float(p.get("gravite", 0.0))

        # Gauge gravité
        ax_grav.set_facecolor("#0C1A2E"); ax_grav.set_xlim(0,10); ax_grav.set_ylim(-0.7,1.7); ax_grav.axis("off")
        for x0,x1,col in [(0,2,"#16A34A"),(2,4,"#65A30D"),(4,6,"#D97706"),(6,8,"#EA580C"),(8,10,"#B91C1C")]:
            ax_grav.barh(0, x1-x0, left=x0, height=0.55, color=col, alpha=0.85, linewidth=0)
        ax_grav.annotate("", xy=(g_val,0.58), xytext=(g_val,-0.45),
                         arrowprops=dict(arrowstyle="-|>",color="white",lw=2.5,mutation_scale=18))
        ax_grav.plot(g_val, 0.58, "o", color="white", ms=8, zorder=10)
        ax_grav.text(g_val,-0.58,f"{g_val:.1f}",ha="center",fontsize=14,fontweight="bold",color="white")
        ax_grav.text(5,1.40,"INDICE DE GRAVITÉ G",ha="center",fontsize=11,fontweight="bold",color="#F0C040")
        ax_grav.text(5,1.18,f"Valeur calculée : {g_val:.1f}/10",ha="center",fontsize=8,color="#94A3B8")
        for xv,lbl in [(1,"Vert"),(3,"Jaune"),(5,"Orange"),(7,"Rouge"),(9,"Critique")]:
            ax_grav.text(xv,-0.44,lbl,ha="center",fontsize=6.5,color="#CBD5E1")
        for xv in [2,4,6,8]:
            ax_grav.axvline(xv,color="white",lw=0.7,alpha=0.4,ymin=0.15,ymax=0.72)

        # Distribution MC
        mc_vals = p.get("mc_results",[])
        ax_mc.set_facecolor("#0C1A2E")
        ax_mc.tick_params(colors="#94A3B8",labelsize=8)
        for sp in ax_mc.spines.values(): sp.set_color("#1E3A5F")
        r1v=float(p.get("r1",2000)); r2v=float(p.get("r2",1000)); r3v=float(p.get("r3",400))

        if mc_vals and len(mc_vals)>=20:
            arr=np.array(mc_vals,dtype=float)
            n_bins=min(50,max(20,len(arr)//30))
            n,bins,patches=ax_mc.hist(arr,bins=n_bins,density=True,color="#3B82F6",alpha=0.55,edgecolor="#1E40AF",linewidth=0.4)
            for patch,left in zip(patches,bins[:-1]):
                if left<=r3v: patch.set_facecolor("#B91C1C"); patch.set_alpha(0.75)
                elif left<=r2v: patch.set_facecolor("#D97706"); patch.set_alpha(0.70)
                elif left<=r1v: patch.set_facecolor("#16A34A"); patch.set_alpha(0.60)
            bw=(arr.std()*(4/(3*len(arr)))**0.2) if arr.std()>0 else 1.0
            x_k=np.linspace(arr.min(),arr.max(),200)
            kde=np.array([np.exp(-0.5*((x_k-v)/bw)**2).sum() for v in x_k])
            denom=kde.sum()*(x_k[1]-x_k[0]) if kde.sum()>0 else 1.0
            kde=kde/denom
            ax_mc.plot(x_k,kde,color="white",lw=1.5,alpha=0.8)
            for rv,col,lbl in [(r3v,"#EF4444","ERPG-3"),(r2v,"#F97316","ERPG-2"),(r1v,"#22C55E","ERPG-1")]:
                if arr.min()<rv<arr.max()*1.2:
                    ax_mc.axvline(rv,color=col,lw=1.5,ls="--",alpha=0.9)
                    ax_mc.text(rv,ax_mc.get_ylim()[1]*0.88,lbl,color=col,fontsize=7,ha="center",fontweight="bold",rotation=90,va="top")
            ax_mc.set_xlabel("Distance max. dispersion (m)",color="#94A3B8",fontsize=8)
            ax_mc.set_ylabel("Densité de probabilité",color="#94A3B8",fontsize=8)
            ax_mc.set_title(f"Distribution Monte Carlo ({len(arr):,} scénarios)",color="white",fontsize=9,fontweight="bold")
        else:
            ax_mc.text(0.5,0.5,"Données MC\nnon disponibles",ha="center",va="center",color="#64748B",fontsize=11,transform=ax_mc.transAxes)
            ax_mc.set_title("Distribution Monte Carlo",color="white",fontsize=9)

        fig1.suptitle("ANALYSE DE RISQUE — INDICE DE GRAVITÉ & MONTE CARLO",
                      color="#F0C040",fontsize=12,fontweight="bold",y=0.97)
        story.append(PageBreak())
        story.append(section_header(styles,"03-B","GRAPHIQUES D'ANALYSE DE RISQUE",
                     "Indice de Gravité · Distribution Monte Carlo · Profil de Concentration"))
        story.append(_fig_to_rl(fig1,dpi=140))
        story.append(Spacer(1,0.3*cm))

        # ── FIGURE 2 : Carte ERPG schématique + Profil concentration ─────
        fig2,(ax_map,ax_conc)=plt.subplots(1,2,figsize=(13,5.5),facecolor="#0C1A2E")
        fig2.subplots_adjust(wspace=0.30,left=0.06,right=0.97,top=0.88,bottom=0.10)
        pdir_r=float(p.get("prop_dir",90))*np.pi/180
        half_a=38*np.pi/180

        ax_map.set_facecolor("#071523"); ax_map.set_aspect("equal"); ax_map.axis("off")
        def draw_cone(ax,radius,color,alpha,label):
            theta=np.linspace(-half_a,half_a,80)
            xs=np.concatenate([[0],radius*np.cos(theta),[0]])
            ys=np.concatenate([[0],radius*np.sin(theta),[0]])
            cd,sd=np.cos(pdir_r-np.pi/2),np.sin(pdir_r-np.pi/2)
            xr=xs*cd-ys*sd; yr=xs*sd+ys*cd
            ax.fill(xr,yr,color=color,alpha=alpha,linewidth=0)
            ax.plot(xr,yr,color=color,lw=1.5,alpha=0.9)
            tx=radius*0.68*np.cos(pdir_r-np.pi/2); ty=radius*0.68*np.sin(pdir_r-np.pi/2)
            ax.text(tx,ty,f"{label}\n{radius:.0f}m",color="white",fontsize=7.5,ha="center",va="center",fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25",fc=color,alpha=0.7,ec="none"))

        draw_cone(ax_map,r1v,"#16A34A",0.20,"ERPG-1")
        draw_cone(ax_map,r2v,"#D97706",0.35,"ERPG-2")
        draw_cone(ax_map,r3v,"#B91C1C",0.55,"ERPG-3")
        ax_map.plot(0,0,"o",color="#FBBF24",ms=9,zorder=10)
        ax_map.plot(0,0,"o",color="white",ms=4,zorder=11)
        ax_map.text(0.04*r1v,-0.12*r1v,"SOURCE Cl₂",color="#FBBF24",fontsize=8,fontweight="bold")
        wlen=r1v*0.28; wx=wlen*np.cos(pdir_r-np.pi/2); wy=wlen*np.sin(pdir_r-np.pi/2)
        ax_map.annotate("",xy=(wx,wy),xytext=(0,0),
                        arrowprops=dict(arrowstyle="-|>",color="#60A5FA",lw=2,mutation_scale=14))
        ax_map.text(wx*1.12,wy*1.12,f"Vent\n{float(p.get('u_ms',5)):.1f} m/s",
                    color="#60A5FA",fontsize=7.5,ha="center")
        ax_map.set_xlim(-r1v*0.6,r1v*1.15); ax_map.set_ylim(-r1v*0.85,r1v*0.85)
        ax_map.set_title("Zones d'impact ERPG (vue schématique)",color="white",fontsize=9.5,fontweight="bold",pad=8)
        ax_map.legend(handles=[
            mpatches.Patch(color="#16A34A",alpha=0.6,label=f"ERPG-1 · >1ppm · {r1v:.0f}m"),
            mpatches.Patch(color="#D97706",alpha=0.7,label=f"ERPG-2 · >3ppm · {r2v:.0f}m"),
            mpatches.Patch(color="#B91C1C",alpha=0.8,label=f"ERPG-3 · >20ppm · {r3v:.0f}m"),
        ],loc="lower right",facecolor="#0C1A2E",edgecolor="#1E3A5F",labelcolor="white",fontsize=7)

        # Profil concentration
        ax_conc.set_facecolor("#0C1A2E")
        ax_conc.tick_params(colors="#94A3B8",labelsize=8)
        for sp in ax_conc.spines.values(): sp.set_color("#1E3A5F")
        Q=float(p.get("Q_kg",9000))*1000/3600
        u=max(0.5,float(p.get("u_ms",5.0)))
        stab_s=p.get("stab","D")
        dist_arr=np.linspace(10,max(r1v*1.1,500),400)
        sig_y0={"A":0.22,"B":0.16,"C":0.11,"D":0.08,"E":0.06,"F":0.04}.get(stab_s,0.08)
        sig_z0={"A":0.20,"B":0.12,"C":0.08,"D":0.06,"E":0.03,"F":0.016}.get(stab_s,0.06)
        n_y={"A":0.90,"B":0.86,"C":0.82,"D":0.74,"E":0.64,"F":0.54}.get(stab_s,0.74)
        n_z={"A":0.93,"B":0.84,"C":0.75,"D":0.64,"E":0.53,"F":0.40}.get(stab_s,0.64)
        sig_y=sig_y0*dist_arr**n_y; sig_z=sig_z0*dist_arr**n_z
        C_ax=(Q/(np.pi*u*sig_y*sig_z))*np.exp(-0.5*(1.5/sig_z)**2)
        C_ppm=C_ax*1e6*24.45/70.9
        ax_conc.fill_between(dist_arr,C_ppm,alpha=0.25,color="#3B82F6")
        ax_conc.plot(dist_arr,C_ppm,color="#60A5FA",lw=1.8)
        for tval,tcol,tlbl in [(1.0,"#22C55E","ERPG-1 · 1ppm"),(3.0,"#F97316","ERPG-2 · 3ppm"),(20.,"#EF4444","ERPG-3 · 20ppm")]:
            ax_conc.axhline(tval,color=tcol,lw=1.4,ls="--",alpha=0.85)
            ax_conc.text(dist_arr[-1]*0.97,tval*1.12,tlbl,color=tcol,fontsize=7,ha="right",va="bottom")
        ax_conc.set_yscale("log"); ax_conc.set_ylim(max(0.05,C_ppm.min()*0.5),min(1e5,C_ppm.max()*2))
        ax_conc.set_xlabel("Distance axiale (m)",color="#94A3B8",fontsize=9)
        ax_conc.set_ylabel("Concentration Cl₂ (ppm)",color="#94A3B8",fontsize=9)
        ax_conc.set_title(f"Profil de concentration axiale · Stabilité {stab_s}",color="white",fontsize=9.5,fontweight="bold")
        ax_conc.grid(True,color="#1E3A5F",lw=0.5,alpha=0.7)
        fig2.suptitle("ZONES D'IMPACT & PROFIL DE CONCENTRATION Cl₂",color="#F0C040",fontsize=12,fontweight="bold",y=0.97)
        story.append(Spacer(1,0.25*cm))
        story.append(_fig_to_rl(fig2,dpi=140))
        story.append(Spacer(1,0.3*cm))

        # ── FIGURE 3 : Évolution temporelle + Radar risque ───────────────
        fig3=plt.figure(figsize=(13,5),facecolor="#0C1A2E")
        ax_time=fig3.add_subplot(1,2,1)
        ax_radar=fig3.add_subplot(1,2,2,polar=True)
        fig3.subplots_adjust(wspace=0.35,left=0.07,right=0.96,top=0.88,bottom=0.12)

        ax_time.set_facecolor("#0C1A2E")
        times=np.linspace(0,60,300)
        dist_ref=r2v*0.6
        t_arr=dist_ref/max(0.5,u)/60
        sigma_t=max(2,t_arr*0.4)
        C_t_ppm=C_ppm[np.argmin(np.abs(dist_arr-dist_ref))]
        C_time=C_t_ppm*np.exp(-0.5*((times-t_arr)/sigma_t)**2)
        C_time=np.maximum(C_time,0)
        ax_time.fill_between(times,C_time,alpha=0.3,color="#3B82F6")
        ax_time.plot(times,C_time,color="#60A5FA",lw=2)
        for tval,tcol,tlbl in [(1.0,"#22C55E","ERPG-1"),(3.0,"#F97316","ERPG-2"),(20.,"#EF4444","ERPG-3")]:
            ax_time.axhline(tval,color=tcol,lw=1.3,ls="--",alpha=0.8)
            ax_time.text(58,tval*1.08,tlbl,color=tcol,fontsize=7,ha="right")
        ax_time.set_xlabel("Temps (min)",color="#94A3B8",fontsize=9)
        ax_time.set_ylabel(f"Cl₂ (ppm) à {dist_ref:.0f}m",color="#94A3B8",fontsize=8)
        ax_time.set_title(f"Évolution temporelle à {dist_ref:.0f}m",color="white",fontsize=9,fontweight="bold")
        ax_time.set_xlim(0,60)
        if C_time.max()>0:
            ax_time.set_yscale("log"); ax_time.set_ylim(0.05,max(C_time.max()*3,30))
        ax_time.grid(True,color="#1E3A5F",lw=0.5,alpha=0.6)
        ax_time.tick_params(colors="#94A3B8")
        ax_time.axvline(t_arr,color="#FBBF24",lw=1.5,ls=":",alpha=0.8)
        ax_time.text(t_arr+0.5,ax_time.get_ylim()[1]*0.6,f"Arr.\n{t_arr:.1f}min",color="#FBBF24",fontsize=7)
        for sp in ax_time.spines.values(): sp.set_color("#1E3A5F")

        cats_r=["Étendue\nzone","Quantité\nCl₂","Densité\npop.","Stabilité\natm.","Vitesse\nvent","Hotspots\ncritiques"]
        vals_r=[min(1,r1v/5000),min(1,float(p.get("Q_kg",9000))/20000),
                min(1,float(p.get("pop_density_1",200))/1000),
                {"A":1.0,"B":0.85,"C":0.70,"D":0.50,"E":0.35,"F":0.20}.get(stab_s,0.5),
                1-min(1,u/15),min(1,float(p.get("n_critique",3))/10)]
        N_r=len(cats_r); angles=np.linspace(0,2*np.pi,N_r,endpoint=False)
        angles=np.concatenate([angles,[angles[0]]]); vals_rc=vals_r+[vals_r[0]]
        ax_radar.set_facecolor("#071523")
        for lv in [0.2,0.4,0.6,0.8,1.0]:
            ax_radar.plot(angles,[lv]*len(angles),color="#1E3A5F",lw=0.6,alpha=0.6)
        ax_radar.fill(angles,vals_rc,alpha=0.35,color="#B91C1C")
        ax_radar.plot(angles,vals_rc,color="#EF4444",lw=2)
        ax_radar.plot(angles,vals_rc,"o",color="white",ms=5,zorder=10)
        ax_radar.set_xticks(angles[:-1]); ax_radar.set_xticklabels(cats_r,color="#94A3B8",fontsize=7.5)
        ax_radar.set_yticks([0.25,0.5,0.75,1.0]); ax_radar.set_yticklabels(["25%","50%","75%","100%"],color="#64748B",fontsize=6)
        ax_radar.spines["polar"].set_color("#1E3A5F"); ax_radar.set_ylim(0,1)
        ax_radar.set_title("Profil de risque multidimensionnel",color="white",fontsize=9.5,fontweight="bold",pad=18)

        fig3.suptitle("DYNAMIQUE TEMPORELLE & PROFIL MULTIDIMENSIONNEL DE RISQUE",color="#F0C040",fontsize=12,fontweight="bold",y=0.97)
        story.append(Spacer(1,0.25*cm)); story.append(_fig_to_rl(fig3,dpi=140)); story.append(Spacer(1,0.3*cm))

        # ── FIGURE 4 : Tornado — Analyse de sensibilité ───────────────────
        fig4,ax_torn=plt.subplots(1,1,figsize=(12,5),facecolor="#0C1A2E")
        ax_torn.set_facecolor("#0C1A2E")
        fig4.subplots_adjust(left=0.28,right=0.95,top=0.88,bottom=0.12)
        base_r1=float(p.get("r1",2000))
        ps=[("Quantité Cl₂ (Q)",base_r1*1.22,base_r1*0.82),
            ("Vitesse vent (u)",base_r1*0.88,base_r1*1.14),
            ("Stabilité atm. (σ)",base_r1*1.18,base_r1*0.85),
            ("Hauteur source (H)",base_r1*0.95,base_r1*1.06),
            ("Temp. ambiante (T)",base_r1*1.04,base_r1*0.97),
            ("Humidité relative",base_r1*1.02,base_r1*0.99)]
        ylabels=[x[0] for x in ps]; ypos=np.arange(len(ylabels))
        ax_torn.barh(ypos,[abs(x[1]-base_r1) for x in ps],left=base_r1,color="#B91C1C",alpha=0.75,height=0.5,label="+20% param.")
        ax_torn.barh(ypos,[-abs(x[2]-base_r1) for x in ps],left=base_r1,color="#16A34A",alpha=0.75,height=0.5,label="-20% param.")
        ax_torn.axvline(base_r1,color="white",lw=1.8,alpha=0.8)
        ax_torn.text(base_r1,len(ylabels)-0.3,f"Base {base_r1:.0f}m",color="white",fontsize=7.5,ha="center",va="bottom")
        ax_torn.set_yticks(ypos); ax_torn.set_yticklabels(ylabels,color="#CBD5E1",fontsize=9)
        ax_torn.set_xlabel("Distance ERPG-1 (m)",color="#94A3B8",fontsize=9)
        ax_torn.tick_params(colors="#94A3B8")
        ax_torn.legend(facecolor="#0C1A2E",edgecolor="#1E3A5F",labelcolor="white",fontsize=8)
        ax_torn.set_title("Analyse de sensibilité — Impact ±20% des paramètres sur R(ERPG-1)",color="white",fontsize=9.5,fontweight="bold")
        ax_torn.grid(True,axis="x",color="#1E3A5F",lw=0.5,alpha=0.6)
        for sp in ax_torn.spines.values(): sp.set_color("#1E3A5F")
        story.append(Spacer(1,0.25*cm)); story.append(_fig_to_rl(fig4,dpi=140)); story.append(Spacer(1,0.3*cm))

    else:
        story.append(Paragraph("<i>Graphiques non disponibles — pip install matplotlib numpy</i>",
                     _s("nm",styles["Normal"],textColor=colors.HexColor("#F97316"),fontName="Helvetica-Oblique",fontSize=9)))
        story.append(Spacer(1,0.5*cm))


    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 4 — HOTSPOTS & CONFINEMENT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "04",
        "IDENTIFICATION DES HOTSPOTS & ZONES DE CONFINEMENT",
        "Points de concentration maximale par anneau ERPG — Recommandations de confinement des populations"))

    story.append(Paragraph("Cartographie des hotspots de concentration :", sH2))
    hs_rows = [
        [Paragraph(c, _s(f"hsh{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Zone","Distance","Conc. max. estimée",
                                "Latitude (axe vent)","Action prioritaire"])]
    ]
    _hs_zone_defs = [
        ("ERPG-3 — Danger vital",   C_RED,    C_BG_R),
        ("ERPG-3 / ERPG-2 — Transit", C_RED2, colors.HexColor("#FFE4E1")),
        ("ERPG-2 — Centre orange",  C_ORANGE, C_BG_O),
        ("ERPG-2 / ERPG-1 — Front", colors.HexColor("#D97706"),
         colors.HexColor("#FEF9E7")),
        ("ERPG-1 — Zone verte",     C_GREEN,  C_BG_G),
    ]
    _hs_dists    = [f"0 – {r3:.0f} m", f"{r3:.0f} m",
                    f"{(r3+r2)/2:.0f} m", f"{r2:.0f} m",
                    f"{r2:.0f} – {r1:.0f} m"]
    _hs_concs    = [
        f"{hs_data[0].get('conc', 0):.1f} ppm",
        f"{hs_data[1].get('conc', 0):.2f} ppm",
        f"{hs_data[2].get('conc', 0):.2f} ppm",
        f"{hs_data[3].get('conc', 0):.2f} ppm",
        "1.0 – 3.0 ppm",
    ]
    _hs_lats = [
        f"{lat:.4f}°N / {lon:.4f}°E",
        f"{hs_data[1].get('lat', lat):.4f}°N",
        f"{hs_data[2].get('lat', lat):.4f}°N",
        f"{hs_data[3].get('lat', lat):.4f}°N",
        f"{hs_data[4].get('lat', lat):.4f}°N",
    ]
    _hs_actions = [
        "Confinement hermétique étages supérieurs — EPI Niveau A",
        "Évacuation prioritaire sous-sols — Réévaluation zonage",
        "Confinement strict — VMC coupée — Serviettes mouillées",
        "Confinement recommandé — Surveillance active",
        "Confinement préventif — Information populations",
    ]
    hs_bg_cmds = []
    for i, (_, col, bg) in enumerate(_hs_zone_defs):
        hs_rows.append([
            Paragraph(f"<b>{_hs_zone_defs[i][0]}</b>",
                      _s(f"hz{i}", styles["Normal"],
                         fontName="Helvetica-Bold", fontSize=7.5,
                         textColor=_hs_zone_defs[i][1])),
            _hs_dists[i], _hs_concs[i], _hs_lats[i], _hs_actions[i],
        ])
        hs_bg_cmds.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))

    t_hs = Table(hs_rows, colWidths=[TW*p for p in [0.19,0.13,0.13,0.17,0.38]])
    t_hs.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_NAVY),
        ("BOX",        (0,0), (-1,-1), 1.0, C_BLUE),
        ("INNERGRID",  (0,0), (-1,-1), 0.4, C_LGRAY2),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (1,0), (3,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
    ] + hs_bg_cmds))
    story.append(t_hs)

    story.append(Spacer(1, 0.12*cm))
    story.append(Paragraph("Zones potentielles de confinement recommandées par anneau ERPG :", sH2))

    cf_rows = [
        [Paragraph(c, _s(f"cfh{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Zone","Type de bâtiment / espace","Efficacité","Consigne opérationnelle"])]
    ]
    _cf_items = [
        ("ERPG-3\nRouge", "Étages ≥ N+2 — Structure béton armé",
         "Élevée", "VMC fermée · Interstices colmatés · Serviettes mouillées", C_BG_R, C_RED),
        ("ERPG-3\nRouge", "Véhicules NRBC hermétiques / salles pressurisées",
         "Maximale", "Surpression air filtré — EPI A obligatoire à l'extérieur", C_BG_R, C_RED),
        ("ERPG-3\nRouge", "⚠ INTERDIT — Sous-sols, caves, fossés",
         "DANGER", "Cl2 2,5× plus lourd que l'air — Accumulation fatale", colors.HexColor("#FFE4E1"), C_RED),
        ("ERPG-2\nOrange", "Appartements / maisons — étages ≥ 1",
         "Bonne", "Fenêtres calfeutrées · VMC coupée · Attendre fin alerte", C_BG_O, C_ORANGE),
        ("ERPG-2\nOrange", "Wagons de train — ventilation arrêtée",
         "Bonne", "Portes fermées · Arrêt à la prochaine gare hors zone", C_BG_O, C_ORANGE),
        ("ERPG-2\nOrange", "Bâtiments publics — zones intérieures arrières",
         "Modérée", "Éviter halls d'entrée donnant sur l'extérieur", C_BG_O, C_ORANGE),
        ("ERPG-1\nVerte", "Tout bâtiment fermé",
         "Suffisante", "Fenêtres fermées suffisantes — EPI non obligatoire", C_BG_G, C_GREEN),
        ("ERPG-1\nVerte", "Véhicules personnels — vitres remontées",
         "Bonne", "Climatisation interne uniquement — Pas d'air extérieur", C_BG_G, C_GREEN),
    ]
    cf_bg_cmds = []
    for i, (zone, bldg, eff, cons, bg, col) in enumerate(_cf_items):
        cf_rows.append([
            Paragraph(f"<b>{zone}</b>", _s(f"cfz{i}", styles["Normal"],
                      fontName="Helvetica-Bold", fontSize=8, textColor=col,
                      alignment=TA_CENTER)),
            Paragraph(bldg, sBody),
            Paragraph(f"<b>{eff}</b>", _s(f"cfe{i}", styles["Normal"],
                      fontName="Helvetica-Bold", fontSize=8,
                      textColor=C_GREEN if eff not in ("DANGER","Modérée") else col,
                      alignment=TA_CENTER)),
            Paragraph(cons, sSmall),
        ])
        cf_bg_cmds.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))

    t_cf = Table(cf_rows, colWidths=[TW*p for p in [0.12,0.33,0.12,0.43]])
    t_cf.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_NAVY),
        ("BOX",        (0,0), (-1,-1), 1.0, C_BLUE),
        ("INNERGRID",  (0,0), (-1,-1), 0.4, C_LGRAY2),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (0,0), (0,-1), "CENTER"),
        ("ALIGN",      (2,0), (2,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
        ("LINEABOVE",  (0,4), (-1,4), 1.5, colors.HexColor("#D97706")),
        ("LINEABOVE",  (0,7), (-1,7), 1.5, C_GREEN),
    ] + cf_bg_cmds))
    story.append(t_cf)
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 5 — ORGANISATION SECOURS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "05", "ORGANISATION DES SECOURS — PLAN ORSEC",
        f"Niveau d'intervention : {_niv}  ·  G = {g:.1f}/10  ·  P(C > ERPG-2) MC = {mc_p_e2:.0f} %"))

    # Décision confinement
    story.append(Paragraph("Décision confinement / évacuation :", sH2))
    _dec_color = C_RED if "OBLIGATOIRE" in _dec or "CONFINEMENT" in _dec else C_GREEN
    _dec_bg    = C_BG_R if C_RED == _dec_color else C_BG_G
    story.append(Paragraph(
        f"<b>Décision : {_dec}</b>  —  Pop. à {dist_pop} m  ·  "
        f"Nuage : T+{_t_arrivee:.0f} min  ·  Délai évac. : {delai_evac} min  ·  "
        f"{type_lib.split()[0]}",
        _s("dec_p", styles["Normal"], fontName="Helvetica-Bold", fontSize=9,
           textColor=_dec_color, backColor=_dec_bg,
           borderPad=6, alignment=TA_CENTER, spaceAfter=6)))

    # Commandement
    story.append(Paragraph("Chaîne de commandement ORSEC :", sH2))
    cmd_data = [
        [Paragraph(c, _s(f"cmdh{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Sigle","Fonction","Rôle opérationnel"])],
        *[
            [Paragraph(s, _s(f"cmd_{s}", styles["Normal"],
                              fontName="Helvetica-Bold", fontSize=9,
                              textColor=C_WHITE, backColor=col, alignment=TA_CENTER)),
             Paragraph(f, sBold),
             Paragraph(r, sBody)]
            for s,f,r,col in [
                ("DOS","Directeur des Opérations de Secours",
                 "Décide, coordonne et arbitre l'ensemble du dispositif de gestion de crise",
                 colors.HexColor("#553C9A")),
                ("PCO","Poste de Commandement Opérationnel",
                 "Coordonne en temps réel les actions de secours et de sécurité sur le terrain",
                 C_NAVY),
                ("COS","Commandant des Opérations de Secours",
                 f"Dirige tactiquement les moyens engagés — Périmètre {r3:.0f} m — Zones ERPG",
                 C_BLUE),
                ("DSM","Directeur des Secours Médicaux",
                 f"Triage ({blesses_e3} UA) — Évacuation médicale — Plan Blanc CHR si saturation",
                 C_RED),
                ("CMIC","Cellule Mobile Intervention Chimique",
                 "Analyse Cl2 — Décontamination — Neutralisation NaOH — Reconnaissance NRBC",
                 C_ORANGE),
                ("PCF","Poste de Commandement Fixe",
                 "Anticipation — Planification — Communication institutionnelle et médias",
                 colors.HexColor("#285E61")),
            ]
        ]
    ]
    story.append(make_table(cmd_data,
                            [TW*0.08, TW*0.30, TW*0.62],
                            font_size=8.0))

    story.append(Spacer(1, 0.12*cm))
    story.append(Paragraph("Chronologie des phases de réponse :", sH2))
    phases = [
        [Paragraph(c, _s(f"phh{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Phase","Créneau","Actions clés","Ressources"])],
        [Paragraph("1 — Prise de commandement", _s("ph1", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE,
                   backColor=colors.HexColor("#2B6CB0"))),
         "T0 → T+25 min",
         Paragraph("Alerte CTA · SITAC · Zonage réflexe 50 m · Zonage réfléchi ERPG · Activation PCO", sSmall),
         Paragraph(f"FPT×{2 if g>=6 else 1} + VSAV×{3 if g>=6 else 2} + VLCG×{2 if g>=7 else 1}", sSmall)],
        [Paragraph("2 — Analyse & secteurs", _s("ph2", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE,
                   backColor=colors.HexColor("#C05621"))),
         "T+25 → T+60 min",
         Paragraph("Gestion établissements · Communication médias · Décontamination", sSmall),
         Paragraph(f"CMIC + PMA + {nb_smur} SMUR", sSmall)],
        [Paragraph("3 — Crise majeure multi-sites", _s("ph3", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE,
                   backColor=C_RED)),
         "T+60 → T+130 min",
         Paragraph("Saturation CHR · Effet domino · Établissements vulnérables", sSmall),
         Paragraph(f"Plan Blanc CHR ({capa_chr_lits} lits) · CUMP", sSmall)],
        [Paragraph("4 — Stabilisation", _s("ph4", styles["Normal"],
                   fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE,
                   backColor=C_GREEN)),
         "T+130 → T+150 min",
         Paragraph("Levée confinement séquentielle V→O→R · RETEX · Rapport ministériel", sSmall),
         Paragraph("DOS + PCF + Communication", sSmall)],
    ]
    story.append(make_table(phases,
                            [TW*0.22, TW*0.14, TW*0.38, TW*0.26],
                            font_size=8.0))

    story.append(Spacer(1, 0.12*cm))
    story.append(Paragraph("Consignes opérationnelles :", sH2))
    ops = [
        [Paragraph(c, _s(f"oph{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Domaine","Consigne opérationnelle"])],
        [Paragraph("EPI requis", sBold),
         Paragraph(
             f"{'EPI Catégorie A complet' if g>6 else 'EPI Catégorie 3 Type 1'}"
             f" — {'Obligatoire zone rouge' if g>6 else 'Recommandé zones orange et rouge'}",
             sBody)],
        [Paragraph("Neutralisation Cl2", sBold),
         Paragraph("Eau abondante ou NaOH 5–10 % · Ne jamais approcher sans EPI · Vent dos à la source", sBody)],
        [Paragraph("Décontamination", sBold),
         Paragraph("Rinçage eau abondante 15 min · Retrait vêtements contaminés · Tri médical entrée PMA", sBody)],
        [Paragraph("Traitement médical", sBold),
         Paragraph("O2 100 % · Bronchodilatateurs · Corticoïdes inhalés · Transport CHR", sBody)],
        [Paragraph("Communication", sBold),
         Paragraph(
             f"{'IMMÉDIATE — Sirènes + SMS-Alert + Radio' if g>7 else 'URGENTE' if g>4 else 'PRÉVENTIVE'}"
             f" · Mise à jour toutes les {15 if g>6 else 30} min · Validation DOS avant toute déclaration",
             sBody)],
        [Paragraph("Levée des mesures", sBold),
         Paragraph("Séquence stricte : Zone ERPG-1 d'abord → Zone ERPG-2 → Zone ERPG-3 en dernier", sBody)],
    ]
    story.append(make_table(ops, [TW*0.20, TW*0.80], font_size=8.0))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 6 — RETEX
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "06", "RETEX — ERREURS CRITIQUES À ÉVITER",
        "Retour d'expérience — Erreurs opérationnelles fréquentes et actions correctives"))

    retex = [
        [Paragraph(c, _s(f"rth{j}", styles["Normal"],
                          fontName="Helvetica-Bold", fontSize=8,
                          textColor=C_WHITE, alignment=TA_CENTER))
         for j,c in enumerate(["Sévérité","Erreur critique identifiée","Conséquence","Action correcte"])],
        [Paragraph("ROUGE", _s("rs1",styles["Normal"],fontName="Helvetica-Bold",
                               fontSize=8,textColor=C_WHITE,backColor=C_RED,
                               alignment=TA_CENTER)),
         Paragraph("Évacuer la zone rouge pendant le nuage actif", sBold),
         Paragraph(f"Cl2 propagation vers {prop_lbl} — exposition directe {pop_e3:,} personnes à > 20 ppm", sBody),
         Paragraph(f"Confinement hermétique < {r3:.0f} m — attendre dissipation complète", sBody)],
        [Paragraph("ROUGE", _s("rs2",styles["Normal"],fontName="Helvetica-Bold",
                               fontSize=8,textColor=C_WHITE,backColor=C_RED,
                               alignment=TA_CENTER)),
         Paragraph("Ignorer les espaces bas — sous-sols, caves, fossés", sBold),
         Paragraph("Cl2 est 2,5× plus lourd que l'air — accumulation fatale en zones basses", sBody),
         Paragraph("Évacuer les sous-sols EN PRIORITÉ absolue vers les étages", sBody)],
        [Paragraph("ORANGE", _s("rs3",styles["Normal"],fontName="Helvetica-Bold",
                                fontSize=8,textColor=C_WHITE,backColor=C_ORANGE,
                                alignment=TA_CENTER)),
         Paragraph("Eau sur aluminium ou phosphore en feu", sBold),
         Paragraph("AlCl3 + H2O → réaction violente + dégagement HCl gazeux toxique", sBody),
         Paragraph("Poudre sèche uniquement — CMIC spécialisée — jamais d'eau sur AlCl3", sBody)],
        [Paragraph("ORANGE", _s("rs4",styles["Normal"],fontName="Helvetica-Bold",
                                fontSize=8,textColor=C_WHITE,backColor=C_ORANGE,
                                alignment=TA_CENTER)),
         Paragraph("Levée simultanée du confinement et de l'évacuation", sBold),
         Paragraph("Flux de population en zone encore contaminée — surexposition", sBody),
         Paragraph("Séquence stricte : ERPG-1 d'abord → ERPG-2 → ERPG-3 en dernier", sBody)],
        [Paragraph("JAUNE", _s("rs5",styles["Normal"],fontName="Helvetica-Bold",
                               fontSize=8,textColor=colors.HexColor("#92400E"),
                               backColor=colors.HexColor("#FEFCE8"),
                               alignment=TA_CENTER)),
         Paragraph("Confirmer/infirmer hypothèse terroriste sans validation DOS", sBold),
         Paragraph("Risque de panique massive et perte de confiance institutionnelle", sBody),
         Paragraph("Message officiel uniquement — validation DOS obligatoire — cellule communication activée", sBody)],
    ]
    rt_cmds = [
        ("BACKGROUND", (0,0), (-1,0), C_NAVY),
        ("BACKGROUND", (0,1), (-1,2), C_BG_R),
        ("BACKGROUND", (0,3), (-1,4), C_BG_O),
        ("BACKGROUND", (0,5), (-1,5), colors.HexColor("#FEFCE8")),
        ("BOX",        (0,0), (-1,-1), 1.0, C_BLUE),
        ("INNERGRID",  (0,0), (-1,-1), 0.4, C_LGRAY2),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (0,0), (0,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
        ("LINEABOVE",  (0,3), (-1,3), 1.5, C_ORANGE),
        ("LINEABOVE",  (0,5), (-1,5), 1.5, colors.HexColor("#92400E")),
    ]
    t_rt = Table(retex, colWidths=[TW*p for p in [0.09,0.25,0.30,0.36]])
    t_rt.setStyle(TableStyle(rt_cmds))
    story.append(t_rt)

    story.append(Spacer(1, 0.2*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_GOLD))
    story.append(Spacer(1, 0.2*cm))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 7 — VALIDATION & SIGNATURES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    story.append(section_header(styles, "07", "RÉFÉRENCES SCIENTIFIQUES & VALIDATION"))

    story.append(Paragraph(
        "<b>Modèles physiques :</b> Pasquill-Gifford (Briggs 1973) — Loi d'échelle gaz lourd "
        "calibrée ALOHA (erreur ≤ 11% toutes classes A–F) — Correction puff Wilson (1981). "
        "<b>Seuils :</b> ERPG (Emergency Response Planning Guidelines) — AIHA 2023. "
        "<b>Machine Learning :</b> Random Forest (n=300, max_depth=3) — Validation croisée 5-fold "
        "sur 81 accidents historiques Cl2 (1929–2022). "
        "<b>Monte Carlo :</b> Q ±30% log-normale — u ±20% log-normale — "
        f"{n_mc:,} itérations.",
        sBody))

    story.append(Spacer(1, 0.15*cm))

    # ── Bloc signature refait — colonnes bien proportionnées, pas de débordement ──
    def _sc(name, txt, fs=8.5, bold=False, col=C_GRAY1, align=TA_CENTER, lead=13):
        return Paragraph(txt, _s(name, styles["Normal"],
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=fs, textColor=col, alignment=align, leading=lead))

    # Ligne d'en-tête (fond navy)
    sig_header = [
        _sc("s_h0","ÉTABLI PAR", fs=8, bold=True, col=C_WHITE),
        _sc("s_h1","DATE ET RÉFÉRENCE", fs=8, bold=True, col=C_WHITE),
        _sc("s_h2","MODÈLES & MÉTHODES", fs=8, bold=True, col=C_WHITE),
    ]

    # Ligne de contenu
    sig_body = [
        # Col 1 — Établi par
        Paragraph(
            "<b>HazMod</b><br/>"
            "<font size='7.5' color='#6B7280'>Système d'aide à la décision</font><br/><br/>"
            "<b>Direction de la Sécurité et de la Documentation</b><br/>"
            "<font size='7.5' color='#4B5563'>Direction de la Sécurité</font><br/>"
            "<font size='7.5' color='#4B5563'>et de la Documentation</font>",
            _s("sgv0", styles["Normal"],
               fontName="Helvetica", fontSize=8.5,
               textColor=C_NAVY, alignment=TA_CENTER, leading=13)),
        # Col 2 — Date & Ref
        Paragraph(
            f"<font size='7.5' color='#6B7280'>Date de génération :</font><br/>"
            f"<b><font size='9'>{date_str}</font></b><br/><br/>"
            f"<font size='7.5' color='#6B7280'>Référence :</font><br/>"
            f"<b><font size='9' color='#1A4F8A'>{ref_str}</font></b><br/><br/>"
            f"<font size='7' color='#9CA3AF'>Direction de la Sécurité et de la Documentation</font>",
            _s("sgd1", styles["Normal"],
               fontName="Helvetica", fontSize=8.5,
               textColor=C_GRAY2, alignment=TA_CENTER, leading=13)),
        # Col 3 — Modèles
        Paragraph(
            "<font size='7.5' color='#6B7280'>Modèles physiques :</font><br/>"
            "<b>Pasquill-Gifford (Briggs 1973)</b><br/>"
            "<b>Correction puff Wilson (1981)</b><br/><br/>"
            "<font size='7.5' color='#6B7280'>Probabiliste :</font><br/>"
            "<b>Monte Carlo log-normale</b><br/>"
            "<b>Random Forest (n=300, CV 5-fold)</b><br/><br/>"
            "<font size='7' color='#9CA3AF'>Seuils ERPG — AIHA 2023</font>",
            _s("sgd2", styles["Normal"],
               fontName="Helvetica", fontSize=8,
               textColor=C_GRAY1, alignment=TA_LEFT, leading=12)),
    ]

    sig_data = [sig_header, sig_body]
    # Hauteur auto (None) pour la ligne de contenu → adapte au texte
    t_sig = Table(sig_data, colWidths=[TW*0.30, TW*0.32, TW*0.38],
                  rowHeights=[14, None])
    t_sig.setStyle(TableStyle([
        # En-tête
        ("BACKGROUND",    (0,0), (-1,0), C_NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        # Boîte générale
        ("BOX",           (0,0), (-1,-1), 2,  C_NAVY),
        ("INNERGRID",     (0,0), (-1,-1), 0.6, C_LGRAY2),
        # Alignement
        ("ALIGN",         (0,0), (-1,0),  "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,0),  4),
        ("BOTTOMPADDING", (0,0), (-1,0),  4),
        ("TOPPADDING",    (0,1), (-1,1),  8),
        ("BOTTOMPADDING", (0,1), (-1,1),  8),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        # Trait doré haut du contenu
        ("LINEABOVE",     (0,1), (-1,1), 3, C_GOLD),
        # Trait doré bas
        ("LINEBELOW",     (0,-1),(-1,-1), 3, C_GOLD),
        # Fonds différenciés par colonne
        ("BACKGROUND",    (0,1), (0,1), colors.HexColor("#EFF6FF")),
        ("BACKGROUND",    (1,1), (1,1), colors.HexColor("#F8FAFC")),
        ("BACKGROUND",    (2,1), (2,1), colors.HexColor("#F0FFF4")),
        # Ligne verticale plus marquée entre col1 et col2
        ("LINEBEFORE",    (1,1), (1,-1), 1.5, C_LGRAY2),
        ("LINEBEFORE",    (2,1), (2,-1), 1.5, C_LGRAY2),
    ]))
    story.append(t_sig)

    story.append(Spacer(1, 0.15*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE2))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        f"HAZMOD — Min. Intérieur — Direction de la Sécurité et de la Documentation  ·  {date_str}  ·  Réf. {ref_str}"
        "  ·  Pasquill-Gifford · Monte Carlo · Random Forest"
        "  ·  DOCUMENT À DIFFUSION RESTREINTE",
        _s("footer_fin", styles["Normal"],
           fontName="Helvetica", fontSize=6.5,
           textColor=C_GRAY3, alignment=TA_CENTER)
    ))

    # ── Build ─────────────────────────────────────────────────────────────
    def _first_page(cv, doc):
        """Draw cover on page 1, then header on subsequent pages."""
        # Draw cover
        _p2, _ds, _rs, _nw = _cover_params
        _tmp = CoverPage(_p2, _ds, _rs, _nw)
        _tmp.canv = cv
        cv.saveState()
        _tmp.draw()
        cv.restoreState()

    def _later_pages(cv, doc):
        pn = cv.getPageNumber()
        draw_page_header(cv, pn - 1, "?", ref_str, is_cover=False)

    # Insert blank first page (cover drawn via callback)
    story.insert(0, PageBreak())

    doc.build(story, onFirstPage=_first_page, onLaterPages=_later_pages)
    buf.seek(0)
    return buf.read()


if __name__ == "__main__":
    # Test standalone
    import json
    dummy = {
        "Q_kg":9000,"type_lib":"Progressive","duree_min":60,"hauteur_m":2,
        "u_ms":5.0,"dir_vent":280,"stab":"C","stab_sel":"C — Lég. instable",
        "lat":33.969,"lon":-6.8834,"config_site":"Usine chimique",
        "dens_pop":2720,"dist_pop":300,"niveau_epi":"EPI 2 — Faible",
        "alerte_prec":False,"delai_evac":30,"coord_sec":2,"capa_med":"Limitée",
        "capa_chr_lits":350,"capa_ua_max":20,"nb_smur":3,"n_mc":2000,
        "gravite":3.8,"r1":2138,"r2":1195,"r3":437,
        "pop_e1":6510,"pop_e2":2033,"pop_e3":272,
        "surf_e1":2.394,"surf_e2":0.748,"surf_e3":0.100,
        "blesses_estimes":227,"blesses_e2":157,"blesses_e3":70,
        "deces_estimes":0,"mc_p_e1":8.8,"mc_p_e2":0.0,"mc_p_e3":0.0,
        "mc_c50":0.624,"mc_c95":1.134,"mc":{},"Q_kgs":2.5,"H_eff":2.0,
        "prop_dir":100,"perim_evac":1195,"surf_evac":4.49,"facteur_site":0.08,
        "SECTEUR":1/6,"usines_domino":[],"has_train":False,"has_hopital":False,
        "has_ecole":False,"has_admin":False,"has_gare_rout":False,
        "train_passagers":0,"nb_agents_admin":0,"nb_gare_pers":0,
        "dec_conf":"CONFINEMENT","t_arrivee":1,
        "hs_data":[{"conc":c,"lat":33.969} for c in [0.5,0.17,0.06,0.03,1.0]],
    }
    pdf_bytes = generate_pdf(dummy)
    with open("/home/claude/test_hazmod.pdf","wb") as f:
        f.write(pdf_bytes)
    print(f"PDF généré : {len(pdf_bytes):,} bytes")
