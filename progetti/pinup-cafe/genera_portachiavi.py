#!/usr/bin/env python3
"""
Emozioni in 3D - Portachiavi PIN-UP Cafe con gettone per carrello.

Versione per ugello 0,4 mm, un solo filamento per pezzo:
  stl/portachiavi.stl  -> logo lungo IN RILIEVO sul davanti
                          (cambio colore a metà stampa per avere la scritta colorata)
  stl/gettone.stl      -> logo tondo INCISO su entrambe le facce

Il gettone si infila DENTRO il portachiavi da una fessura sul lato corto (in
fondo, dal lato opposto al foro per le chiavi) e viene bloccato da una
linguetta elastica con un dentino. Per toglierlo: si preme la linguetta dal
retro e si spinge il gettone fuori con il pollice dalla finestra rotonda.

Requisiti: pip install manifold3d trimesh opencv-python-headless numpy
Uso:       python3 genera_portachiavi.py
"""
import json, os
import numpy as np, cv2
from manifold3d import CrossSection, Manifold, FillRule, JoinType, set_circular_segments

QUI = os.path.dirname(os.path.abspath(__file__))
set_circular_segments(160)

# ----------------------------------------------------------------- parametri
# Gettone (moneta da 1 euro: 23,25 x 2,33 mm)
DIAMETRO_GETTONE = 23.25
SPESSORE_GETTONE = 2.33
SMUSSO_GETTONE = 0.2
PROFONDITA_INCISIONE = 0.4      # 2 strati da 0,2 mm
INCISO_SU_DUE_FACCE = True

# Portachiavi (misure scelte multiple di 0,2 mm = altezza strato)
LUNGHEZZA = 58.0
LARGHEZZA = 28.0
RAGGIO_ANGOLI = 6.0
FONDO = 1.2                     # spessore sotto il gettone
ALTEZZA_SEDE = 2.6              # gettone 2,33 + 0,27 di gioco
TETTO = 1.2                     # spessore sopra il gettone
RILIEVO_LOGO = 0.6              # 3 strati: cambio colore a quota FONDO+SEDE+TETTO
MARGINE_LOGO = 0.8
DIAMETRO_FORO = 5.0
DISTANZA_FORO = 5.5             # dal bordo al centro del foro chiavi

# Sede del gettone e blocco
GIOCO_DIAMETRO = 0.4            # sede più larga del gettone
CENTRO_SEDE_X = 13.0            # centro del gettone inserito (0 = centro portachiavi)
DIAMETRO_FINESTRA = 15.0        # finestra sul retro per spingere fuori il gettone
DENTINO_ALTEZZA = 0.8           # quanto sporge il dentino nella sede
DENTINO_LUNGHEZZA = 1.6         # rampa di invito
LINGUETTA_LARGHEZZA = 3.6       # lungo X
LINGUETTA_LUNGHEZZA = 11.0      # lungo Y (più lunga = più morbida)
TAGLIO_LINGUETTA = 0.6

# ----------------------------------------------------------------- utilità
ROUND = JoinType.Round

def carica_logo(prefisso):
    """Unisce i livelli colore del logo in un'unica forma 2D centrata (mm)."""
    info = json.load(open(os.path.join(QUI, "loghi", prefisso + ".json")))
    px, W, H = info["mm_per_px"], info["px_w"], info["px_h"]
    m = np.zeros((H, W), np.uint8)
    for col in info["layers"]:
        m |= (cv2.imread(os.path.join(QUI, "loghi", f"{prefisso}_{col}.png"), 0) > 127).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cnts:
        c = cv2.approxPolyDP(c, 0.6, True).reshape(-1, 2).astype(float)
        if len(c) >= 3:
            polys.append(np.column_stack([(c[:, 0] + 0.5 - W / 2) * px, (H / 2 - c[:, 1] - 0.5) * px]))
    return CrossSection(polys, FillRule.EvenOdd)

def cerchio(d, centro=(0, 0)):
    return CrossSection.circle(d / 2).translate(centro)

def rettangolo(x0, y0, x1, y1):
    return CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])

def estrudi(cs, h, z=0.0):
    return Manifold.extrude(cs, h).translate([0, 0, z])

def rivoluzione(profilo_rz):
    return Manifold.revolve(CrossSection([np.array(profilo_rz, float)]), 0, 360)

# ----------------------------------------------------------------- portachiavi
def costruisci_portachiavi(logo):
    l, w, r = LUNGHEZZA, LARGHEZZA, RAGGIO_ANGOLI
    corpo2d = CrossSection.square([l - 2 * r, w - 2 * r], center=True).offset(r, ROUND)
    foro = cerchio(DIAMETRO_FORO, (-l / 2 + DISTANZA_FORO, 0))
    corpo2d = corpo2d - foro
    h_corpo = FONDO + ALTEZZA_SEDE + TETTO
    corpo = estrudi(corpo2d, h_corpo)

    # sede: cerchio del gettone + canale fino al bordo corto (entrata)
    cx = CENTRO_SEDE_X
    rs = (DIAMETRO_GETTONE + GIOCO_DIAMETRO) / 2
    sede2d = cerchio(2 * rs, (cx, 0)) + rettangolo(cx, -rs, l / 2 + 1, rs)
    corpo = corpo - estrudi(sede2d, ALTEZZA_SEDE, FONDO)

    # finestra sul retro (per vedere il gettone e spingerlo fuori)
    corpo = corpo - estrudi(cerchio(DIAMETRO_FINESTRA, (cx, 0)), FONDO + 0.02, -0.01)

    # linguetta elastica ricavata nel fondo, con radice verso +Y
    x0 = cx + DIAMETRO_GETTONE / 2 - 0.9
    x1 = x0 + LINGUETTA_LARGHEZZA
    y_punta = -LINGUETTA_LUNGHEZZA / 2
    y_radice = LINGUETTA_LUNGHEZZA / 2
    t = TAGLIO_LINGUETTA
    taglio = rettangolo(x0 - t, y_punta - t, x1 + t, y_radice) - rettangolo(x0, y_punta, x1, y_radice + 1)
    corpo = corpo - estrudi(taglio, FONDO + 0.02, -0.01)

    # dentino: parete verticale verso il gettone, rampa verso l'entrata
    rd = rs + 0.05
    dente = rivoluzione([(rd, 0), (rd + DENTINO_LUNGHEZZA, 0), (rd, DENTINO_ALTEZZA)]).translate([cx, 0, 0])
    impronta = rettangolo(x0, y_punta + 0.4, x1, y_punta + LINGUETTA_LUNGHEZZA * 0.55)
    dente = dente ^ estrudi(impronta, DENTINO_ALTEZZA + 1)
    corpo = corpo + dente.translate([0, 0, FONDO - 0.01])

    # logo in rilievo sul tetto
    x_logo = (-l / 2 + DISTANZA_FORO + DIAMETRO_FORO / 2 + 1.5 + l / 2) / 2
    logo2d = logo.translate([x_logo, 0]) ^ corpo2d.offset(-MARGINE_LOGO, ROUND)
    rilievo = estrudi(logo2d, RILIEVO_LOGO, h_corpo - 0.01)
    return corpo + rilievo, h_corpo

# ----------------------------------------------------------------- gettone
def costruisci_gettone(logo):
    r, t, s = DIAMETRO_GETTONE / 2, SPESSORE_GETTONE, SMUSSO_GETTONE
    disco = rivoluzione([(0, 0), (r - s, 0), (r, s), (r, t - s), (r - s, t), (0, t)])
    area = cerchio(2 * (r - s - 0.3))
    d = PROFONDITA_INCISIONE
    disco = disco - estrudi(logo ^ area, d + 0.01, t - d)                 # faccia superiore
    if INCISO_SU_DUE_FACCE:
        disco = disco - estrudi(logo.mirror([1, 0]) ^ area, d + 0.01, -0.01)  # faccia sul piatto
    return disco

# ----------------------------------------------------------------- esportazione
def salva_stl(m, nome):
    import trimesh
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    tm.export(os.path.join(QUI, "stl", nome))
    return tm

def main():
    os.makedirs(os.path.join(QUI, "stl"), exist_ok=True)
    pk, h_corpo = costruisci_portachiavi(carica_logo("logo_lungo"))
    gt = costruisci_gettone(carica_logo("logo_tondo"))
    for m, nome in [(pk, "portachiavi.stl"), (gt, "gettone.stl")]:
        assert m.status().name == "NoError", nome
        tm = salva_stl(m, nome)
        print(f"{nome:16s} ingombro {np.round(tm.extents, 2)} mm  "
              f"volume {m.volume():.0f} mm3 (~{m.volume() * 1.24 / 1000:.1f} g PLA)  watertight={tm.is_watertight}")
    print(f"Cambio colore del portachiavi a quota {h_corpo:.1f} mm "
          f"(primo strato del logo: {h_corpo:.1f}-{h_corpo + 0.2:.1f} mm)")

if __name__ == "__main__":
    main()
