#!/usr/bin/env python3
"""
Emozioni in 3D - Portachiavi PIN-UP Cafe con gettone per carrello.

Genera i file da stampare:
  stl/portachiavi_<colore>.stl  e  stl/gettone_<colore>.stl  (un file per colore)
  portachiavi_pinup_multicolore.3mf  (tutti i pezzi, già divisi per colore)

Pezzi:
  1) PORTACHIAVI: placchetta 58 x 28 mm, logo lungo sul davanti, anello a scatto
     sul retro che trattiene il gettone.
  2) GETTONE: disco come una moneta da 1 euro (23,25 x 2,33 mm), logo tondo su
     entrambe le facce.

I loghi sono intarsiati a filo (colore nei primi/ultimi 3 strati): superfici
lisce, quindi il gettone ha lo spessore esatto di una moneta.

Requisiti: pip install manifold3d trimesh opencv-python-headless numpy
Uso:       python3 genera_portachiavi.py
"""
import json, os, zipfile
import numpy as np, cv2
from manifold3d import CrossSection, Manifold, FillRule, JoinType, set_circular_segments

QUI = os.path.dirname(os.path.abspath(__file__))
set_circular_segments(160)

# ----------------------------------------------------------------- parametri
# Gettone (moneta da 1 euro: 23,25 x 2,33 mm)
DIAMETRO_GETTONE = 23.25
SPESSORE_GETTONE = 2.33
SMUSSO_GETTONE = 0.3
LOGO_SU_DUE_FACCE = True

# Portachiavi
LUNGHEZZA = 58.0
LARGHEZZA = 28.0
SPESSORE_PLACCA = 2.6
RAGGIO_ANGOLI = 6.0
DIAMETRO_FORO = 5.0
DISTANZA_FORO = 5.5          # dal bordo al centro del foro

# Aggancio a scatto
GIOCO_DIAMETRO = 0.35        # tasca un po' più larga del gettone
GIOCO_SPESSORE = 0.25
SPORGENZA_LABBRO = 0.45      # quanto il labbro copre il bordo del gettone
ALTEZZA_LABBRO = 0.9
SPESSORE_ANELLO = 1.6
APERTURA_GRADI = 44          # apertura per estrarre il gettone con l'unghia
FESSURE = True               # tagli laterali che rendono l'anello elastico
LARGHEZZA_FESSURA = 0.8

PROFONDITA_LOGO = 0.6        # 3 strati da 0,2 mm
MARGINE_LOGO_PLACCA = 0.6

COLORI = {  # nome -> colore indicativo (per anteprima e 3MF)
    "bianco": "#F2F2F2", "blu": "#28506E", "grigio": "#62665F", "rosso": "#962837",
}

# ----------------------------------------------------------------- loghi
def carica_logo(prefisso):
    """Legge le maschere dei colori e restituisce {colore: CrossSection} centrato (mm)."""
    info = json.load(open(os.path.join(QUI, "loghi", prefisso + ".json")))
    px, W, H = info["mm_per_px"], info["px_w"], info["px_h"]
    livelli = {}
    for col in info["layers"]:
        m = cv2.imread(os.path.join(QUI, "loghi", f"{prefisso}_{col}.png"), 0)
        cnts, _ = cv2.findContours((m > 127).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        polys = []
        for c in cnts:
            c = cv2.approxPolyDP(c, 0.6, True).reshape(-1, 2).astype(float)
            if len(c) < 3: continue
            xy = np.column_stack([(c[:, 0] + 0.5 - W / 2) * px, (H / 2 - c[:, 1] - 0.5) * px])
            polys.append(xy)
        livelli[col] = CrossSection(polys, FillRule.EvenOdd)
    return livelli

def specchia_x(cs):
    return cs.mirror([1, 0])

# ----------------------------------------------------------------- forme base
def _join_round():
    return JoinType.Round

def rettangolo_arrotondato(l, w, r):
    return CrossSection.square([l - 2 * r, w - 2 * r], center=True).offset(r, _join_round())

def cerchio(d, centro=(0, 0)):
    return CrossSection.circle(d / 2).translate(centro)

def estrudi(cs, h, z=0.0):
    return Manifold.extrude(cs, h).translate([0, 0, z])

def rivoluzione(profilo_rz, gradi=360):
    return Manifold.revolve(CrossSection([np.array(profilo_rz, float)]), 0, gradi)

def settore(r, gradi, centro_gradi=0):
    a = np.radians(np.linspace(centro_gradi - gradi / 2, centro_gradi + gradi / 2, 40))
    pts = [(0, 0)] + [(r * np.cos(t), r * np.sin(t)) for t in a]
    return CrossSection([np.array(pts)])

# ----------------------------------------------------------------- portachiavi
def costruisci_portachiavi(logo):
    centro_anello = (LUNGHEZZA / 2 - LARGHEZZA / 2, 0)
    centro_foro = (-LUNGHEZZA / 2 + DISTANZA_FORO, 0)
    x_logo = (centro_foro[0] + DIAMETRO_FORO / 2 + 1.5 + LUNGHEZZA / 2) / 2

    placca = rettangolo_arrotondato(LUNGHEZZA, LARGHEZZA, RAGGIO_ANGOLI) - cerchio(DIAMETRO_FORO, centro_foro)
    area_logo = placca.offset(-MARGINE_LOGO_PLACCA, _join_round())

    # il davanti è appoggiato al piatto: logo specchiato
    loghi2d = {c: specchia_x(cs).translate([x_logo, 0]) ^ area_logo for c, cs in logo.items()}
    tutti = CrossSection()
    for cs in loghi2d.values(): tutti = tutti + cs

    base = estrudi(placca - tutti, PROFONDITA_LOGO) + estrudi(placca, SPESSORE_PLACCA - PROFONDITA_LOGO, PROFONDITA_LOGO)

    # anello a scatto
    r_tasca = (DIAMETRO_GETTONE + GIOCO_DIAMETRO) / 2
    r_labbro = DIAMETRO_GETTONE / 2 - SPORGENZA_LABBRO
    r_est = r_tasca + SPESSORE_ANELLO
    h_tasca = SPESSORE_GETTONE + GIOCO_SPESSORE
    htot = h_tasca + ALTEZZA_LABBRO
    profilo = [(r_tasca, 0), (r_est, 0), (r_est, htot), (r_labbro + 0.3, htot),
               (r_labbro, htot - 0.3), (r_labbro, h_tasca), (r_tasca, h_tasca)]
    anello = rivoluzione(profilo)
    taglio = settore(r_est + 2, APERTURA_GRADI, 0) - cerchio(2 * (r_labbro - 0.5))
    anello = anello - estrudi(taglio, htot + 2, -1)
    if FESSURE:
        for a in (-100, 100):
            f = CrossSection.square([3.5, LARGHEZZA_FESSURA]).translate([r_tasca - 0.6, -LARGHEZZA_FESSURA / 2]).rotate(a)
            anello = anello - estrudi(f, htot + 2, -1)
    anello = anello.translate([centro_anello[0], centro_anello[1], SPESSORE_PLACCA - 0.01])
    base = base + anello

    parti = {"bianco": base}
    for c, cs in loghi2d.items():
        parti[c] = estrudi(cs, PROFONDITA_LOGO)
    return parti, centro_anello

# ----------------------------------------------------------------- gettone
def costruisci_gettone(logo):
    r, t, s = DIAMETRO_GETTONE / 2, SPESSORE_GETTONE, SMUSSO_GETTONE
    disco = rivoluzione([(0, 0), (r - s, 0), (r, s), (r, t - s), (r - s, t), (0, t)])
    area = cerchio(2 * (r - s - 0.2))
    parti_col = {}
    for c, cs in logo.items():
        sotto = estrudi(specchia_x(cs) ^ area, PROFONDITA_LOGO)
        m = sotto
        if LOGO_SU_DUE_FACCE:
            m = m + estrudi(cs ^ area, PROFONDITA_LOGO, t - PROFONDITA_LOGO)
        parti_col[c] = m
    base = disco
    for m in parti_col.values(): base = base - m
    return {"bianco": base, **parti_col}

# ----------------------------------------------------------------- esportazione
def a_trimesh(m):
    import trimesh
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)

def scrivi_3mf(percorso, oggetti):
    """oggetti: lista di (nome_oggetto, [(nome_parte, colore_hex, trimesh)]).
    Ogni oggetto ha le sue parti come componenti: nei slicer (Bambu Studio,
    OrcaSlicer, PrusaSlicer) appare come un oggetto con più parti, a cui si
    assegna il filamento di ciascun colore."""
    res, build, mats, idx = [], [], [], {}
    for col in COLORI:
        idx[col] = len(mats); mats.append(f'<base name="{col}" displaycolor="{COLORI[col]}FF"/>')
    oid = 2
    for nome, parti in oggetti:
        comp_ids = []
        for nparte, col, tm in parti:
            v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm.vertices)
            f = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm.faces)
            res.append(f'<object id="{oid}" name="{nome}_{nparte}" type="model" pid="1" pindex="{idx[col]}">'
                       f'<mesh><vertices>{v}</vertices><triangles>{f}</triangles></mesh></object>')
            comp_ids.append(oid); oid += 1
        comps = "".join(f'<component objectid="{i}"/>' for i in comp_ids)
        res.append(f'<object id="{oid}" name="{nome}" type="model"><components>{comps}</components></object>')
        build.append(f'<item objectid="{oid}"/>'); oid += 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="it-IT" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><basematerials id="1">{"".join(mats)}</basematerials>{"".join(res)}</resources>'
             f'<build>{"".join(build)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(percorso, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)

def main():
    os.makedirs(os.path.join(QUI, "stl"), exist_ok=True)
    pk, centro_anello = costruisci_portachiavi(carica_logo("logo_lungo"))
    gt = costruisci_gettone(carica_logo("logo_tondo"))

    oggetti = []
    for nome, parti, spost in [("portachiavi", pk, (0, 0, 0)),
                               ("gettone", gt, (0, LARGHEZZA / 2 + DIAMETRO_GETTONE / 2 + 6, 0))]:
        lista = []
        for col, m in parti.items():
            assert m.status().name == "NoError", (nome, col, m.status())
            tm = a_trimesh(m)
            tm.export(os.path.join(QUI, "stl", f"{nome}_{col}.stl"))
            tm2 = tm.copy(); tm2.apply_translation(spost)
            lista.append((col, col, tm2))
            print(f"{nome:12s} {col:7s} volume {m.volume():8.1f} mm3  ingombro {np.round(tm.extents, 2)}")
        oggetti.append((nome, lista))
    scrivi_3mf(os.path.join(QUI, "portachiavi_pinup_multicolore.3mf"), oggetti)
    print("Fatto.")

if __name__ == "__main__":
    main()
