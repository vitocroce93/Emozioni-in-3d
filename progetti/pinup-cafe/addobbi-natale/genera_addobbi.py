#!/usr/bin/env python3
"""
Emozioni in 3D - Addobbi di Natale PIN-UP Cafe (6-8 cm) con logo sul retro.

  hamburger  - 3D, stampato SCOMPOSTO (6 pezzi, ognuno di un colore) e montato con perno e clip
  sandwich   - 3D, tramezzino triangolare a strati con stecchino e oliva
  polpo      - piatto, con cappello di Babbo Natale, dettagli in rilievo
  pesciolino - piatto, dettagli in rilievo
  pizza_pezzi- piatto, a incastro: base, salsa, mozzarella e salame stampati a parte
  patatine   - 3D, cartoccio rosso con fascia bianca e patatine
  pizza      - piatto, spicchio a strati (impasto, salsa, mozzarella, salame)

Regola: in ogni strato di stampa c'è UN SOLO colore (i colori possono ripetersi
nelle fasce successive) e ogni fascia dura il più possibile.

Ogni pezzo è già orientato per la stampa (Z = direzione di stampa) ed è diviso
in parti per colore. Le parti di ogni addobbo occupano fasce di quota separate,
così si stampa con un solo ugello cambiando filamento alle quote indicate.

Uso: python3 genera_addobbi.py  -> parti/<addobbo>__<ordine>_<colore>.stl + quote.json
"""
import json, os, sys
import numpy as np, cv2
from manifold3d import CrossSection, Manifold, FillRule, JoinType, set_circular_segments

QUI = os.path.dirname(os.path.abspath(__file__))
LOGHI = os.path.join(QUI, "..", "loghi")
set_circular_segments(96)
R = JoinType.Round

COLORI = {
    "pane": "#C27326", "pane_chiaro": "#D4A866", "carne": "#5A3420", "formaggio": "#F6C12C",
    "insalata": "#5DA93B", "pomodoro": "#D9372B", "prosciutto": "#EFA3A1", "oliva": "#5E7A2A",
    "rosso": "#C8202F", "bianco": "#F4F4F0", "nero": "#202020", "azzurro": "#2E8FD0",
    "salsa": "#CF3A24", "patatina": "#F3B63A", "impasto": "#D9A04E", "formaggio_scuro": "#D9821A", "mozzarella": "#F6D257", "salame": "#8A1D1A",
}

# ----------------------------------------------------------------- utilità 2D/3D
def ellisse(rx, ry, c=(0, 0)):
    return CrossSection.circle(1.0).scale([rx, ry]).translate(c)

def cerchio(r, c=(0, 0)):
    return CrossSection.circle(r).translate(c)

def poligono(pts):
    return CrossSection([np.array(pts, float)], FillRule.EvenOdd)

def arrotonda(cs, r):
    return cs.offset(-r, R).offset(r, R)

def tratto(punti, raggi):
    """Linea spessa e morbida: unione degli inviluppi di cerchi consecutivi."""
    out = CrossSection()
    for (p, r), (q, s) in zip(zip(punti, raggi), zip(punti[1:], raggi[1:])):
        out = out + (cerchio(r, p) + cerchio(s, q)).hull()
    return out

def arco(c, r, a0, a1, spess, n=40):
    t = np.radians(np.linspace(a0, a1, n))
    pts = [(c[0] + r * np.cos(a), c[1] + r * np.sin(a)) for a in t]
    return tratto(pts, [spess / 2] * n)

def contorno_ondulato(r, ampiezza, onde, n=360):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rr = r + ampiezza * np.sin(onde * t)
    return poligono(np.column_stack([rr * np.cos(t), rr * np.sin(t)]))

def estrudi(cs, h, z=0.0):
    return Manifold.extrude(cs, h).translate([0, 0, z])

def rivoluzione(profilo):
    return Manifold.revolve(CrossSection([np.array(profilo, float)]), 0, 360)

def logo_2d(larghezza):
    info = json.load(open(os.path.join(LOGHI, "logo_lungo.json")))
    px, W, H = info["mm_per_px"], info["px_w"], info["px_h"]
    m = np.zeros((H, W), np.uint8)
    for col in info["layers"]:
        m |= (cv2.imread(os.path.join(LOGHI, f"logo_lungo_{col}.png"), 0) > 127).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cnts:
        c = cv2.approxPolyDP(c, 0.6, True).reshape(-1, 2).astype(float)
        if len(c) >= 3:
            polys.append(np.column_stack([(c[:, 0] + 0.5 - W / 2) * px, (H / 2 - c[:, 1] - 0.5) * px]))
    s = larghezza / info["width_mm"]
    return CrossSection(polys, FillRule.EvenOdd).scale([s, s])

PROF_LOGO = 0.6

def incidi_logo_sotto(corpo, sagoma, larghezza, centro=(0, 0), angolo=0):
    """Incide il logo (specchiato) sulla faccia appoggiata al piatto = retro."""
    lg = logo_2d(larghezza).rotate(angolo).mirror([1, 0]).translate(centro) ^ sagoma.offset(-1.5, R)
    return corpo - estrudi(lg, PROF_LOGO + 0.01, -0.01)

# ----------------------------------------------------------------- HAMBURGER (3D)
# Stampato SCOMPOSTO: ogni pezzo in un solo colore, nessun cambio filamento.
# Il pane sotto ha un perno esagonale che infila carne, formaggio, insalata e
# pomodoro (l'esagono li tiene allineati) e termina con una clip a scatto che
# si aggancia dentro il pane sopra.
PERNO_ESAGONO = 8.0        # mm tra le facce piane
GIOCO_FORO = 0.4           # foro dei pezzi intermedi = perno + gioco
CLIP_D, CLIP_H = 8.0, 7.0  # parte tonda finale del perno (clip)
CLIP_DENTE = 0.45          # sporgenza del dentino della clip
CLIP_TAGLIO = 1.6          # fessura che rende elastiche le due metà

def esagono(af):
    return CrossSection.circle(af / np.sqrt(3), 6).rotate(30)

def hamburger():
    Z_SOTTO, H_CARNE, H_FORM, H_INS, H_POM = 9.0, 10.0, 2.4, 3.0, 2.8
    z_carne = Z_SOTTO
    z_form = z_carne + H_CARNE
    z_ins = z_form + H_FORM
    z_pom = z_ins + H_INS
    z0 = z_pom + H_POM                      # base del pane sopra
    foro = esagono(PERNO_ESAGONO + GIOCO_FORO)

    # --- pane sotto (bordo inferiore a 45 gradi: si stampa senza supporti) + perno con clip
    pb = [(0, 0), (26.5, 0), (29.0, 2.5), (30.0, 4.5), (30.0, 7.5), (29.3, Z_SOTTO), (0, Z_SOTTO)]
    pane_sotto = rivoluzione(pb)
    pane_sotto = incidi_logo_sotto(pane_sotto, cerchio(28), 44)
    perno = estrudi(esagono(PERNO_ESAGONO), z0 - Z_SOTTO + 0.02, Z_SOTTO - 0.01)
    r, d = CLIP_D / 2, CLIP_DENTE
    clip = rivoluzione([(0, 0), (r, 0), (r, 4.2), (r + d, 4.4), (r + d, 5.4), (r - 0.4, CLIP_H), (0, CLIP_H)])
    clip = clip - Manifold.cube([CLIP_TAGLIO, 20, CLIP_H], center=True).translate([0, 0, CLIP_H / 2 + 1.2])
    pane_sotto = pane_sotto + perno + clip.translate([0, 0, z0])

    # --- pezzi intermedi con foro esagonale
    carne = estrudi(arrotonda(contorno_ondulato(31.5, 0.9, 23), 0.6) - foro, H_CARNE, z_carne)
    formaggio = estrudi(arrotonda(CrossSection.square([48, 48], center=True).rotate(12), 3) - foro, H_FORM, z_form)
    insalata = estrudi(contorno_ondulato(32, 2.4, 13) - foro, H_INS, z_ins)
    pomodoro = estrudi(cerchio(29.5) - foro, H_POM, z_pom)

    # --- pane sopra: cupola + sesamo + anellino; sotto, la sede della clip con la scanalatura
    a, b = 31.0, 23.8
    prof = [(0, z0), (a - 1.5, z0)] + [(a * np.cos(t), z0 + 1.5 + (b - 1.5) * np.sin(t)) for t in np.linspace(0, np.pi / 2, 40)][1:]
    cupola = rivoluzione(prof)
    semi = Manifold()
    rng = np.random.default_rng(7)
    for i in range(26):
        th = rng.uniform(0, 2 * np.pi); ph = rng.uniform(0.35, 1.25)
        x, y = a * np.cos(ph) * np.cos(th), a * np.cos(ph) * np.sin(th)
        z = z0 + 1.5 + (b - 1.5) * np.sin(ph)
        seme = Manifold.sphere(1.0, 16).scale([1.9, 1.1, 0.9]).rotate([0, 0, np.degrees(th) + rng.uniform(-40, 40)])
        semi = semi + seme.translate([x * 0.985, y * 0.985, z - 0.15])
    anello = Manifold.revolve(cerchio(1.9, (5.5, 0)), 0, 360).rotate([90, 0, 0]).translate([0, 0, z0 + b + 4.6])
    rs = r + 0.15
    sede = rivoluzione([(0, -1), (rs, -1), (rs, 3.95), (rs + d + 0.15, 4.15), (rs + d + 0.15, 5.6),
                        (rs, 6.3), (rs, CLIP_H + 0.4), (0, CLIP_H + 0.4)])
    pane_sopra = cupola + semi + anello - sede.translate([0, 0, z0])

    return [("pane", pane_sotto), ("carne", carne), ("formaggio", formaggio),
            ("insalata", insalata), ("pomodoro", pomodoro), ("pane", pane_sopra)]

# ----------------------------------------------------------------- SANDWICH (3D)
def triangolo(lato, r):
    h = lato * np.sqrt(3) / 2
    t = poligono([(-lato / 2, -h / 3), (lato / 2, -h / 3), (0, 2 * h / 3)])
    return t.offset(-r, R).offset(r, R)

def fetta_pane(pane2d, h, z):
    """Fetta di pane con spigoli smussati."""
    return (estrudi(pane2d.offset(-1.4, R), h, z) + estrudi(pane2d, h - 2.4, z + 1.2)).hull()

def sandwich():
    lato = 70
    pane2d = triangolo(lato, 7)
    h = lato * np.sqrt(3) / 2
    parti = []
    pane_sotto = fetta_pane(pane2d, 6.0, 0)
    pane_sotto = incidi_logo_sotto(pane_sotto, pane2d, 38, centro=(0, -1.5))
    parti.append(("pane_chiaro", pane_sotto)); z = 6.0
    prosc = estrudi(ondulato_triangolo(lato + 4.5, 1.3, 6), 2.6, z); z += 2.6
    parti.append(("prosciutto", prosc))
    form = estrudi(triangolo(lato + 2, 3).rotate(7), 2.0, z); z += 2.0
    parti.append(("formaggio", form))
    insal = estrudi(ondulato_triangolo(lato + 6, 2.4, 6), 2.8, z); z += 2.8
    parti.append(("insalata", insal))
    parti.append(("pane_chiaro", fetta_pane(pane2d, 6.0, z))); z += 6.0
    # stecchino al baricentro con oliva e anellino in cima: si appende da qui
    stecco = Manifold.cylinder(15, 1.2, 1.2, 24).translate([0, 0, z - 0.01])   # appoggiato: niente verde negli strati del pane
    oliva = Manifold.sphere(1.0, 40).scale([4.6, 4.6, 5.4]).translate([0, 0, z + 9.5])
    anello = Manifold.revolve(cerchio(1.6, (4.0, 0)), 0, 360).rotate([90, 0, 0]).translate([0, 0, z + 9.5 + 5.4 + 3.6])
    parti.append(("oliva", stecco + oliva + anello))
    return parti   # non unire: i due pani stanno in fasce di quota diverse

def ondulato_triangolo(lato, amp, onde_per_lato):
    return increspa(triangolo(lato, 7), amp, onde_per_lato * 3)

def increspa(base, amp, k, fase=0.0, seme=None):
    """Increspa il contorno di una forma convessa lungo la normale (k onde in tutto)."""
    pts = []
    poly = base.to_polygons()[0]
    poly = np.array(poly)
    # ricampiona il contorno e lo increspa lungo la normale
    seg = np.diff(np.vstack([poly, poly[:1]]), axis=0); L = np.linalg.norm(seg, axis=1)
    s = np.concatenate([[0], np.cumsum(L)]); tot = s[-1]
    n = 600; ss = np.linspace(0, tot, n, endpoint=False)
    P = np.array([np.interp(ss, s, np.append(poly[:, k], poly[0, k])) for k in range(2)]).T
    T = np.roll(P, -1, 0) - np.roll(P, 1, 0); N = np.column_stack([T[:, 1], -T[:, 0]])
    N /= np.linalg.norm(N, axis=1)[:, None]
    if CrossSection([P + N * 0.5]).area() < CrossSection([P]).area(): N = -N
    onda = np.sin(2 * np.pi * k * ss / tot + fase)
    if seme is not None:   # gocce irregolari (formaggio fuso)
        rng = np.random.default_rng(seme)
        onda = onda * rng.uniform(0.4, 1.3, int(k) + 1)[(k * ss / tot).astype(int)]
    return CrossSection([P + N * (amp * onda)[:, None]])

# ----------------------------------------------------------------- PIATTI: quote
BASE_H, RILIEVO1, RILIEVO2 = 4.0, 1.0, 0.8   # base, dettagli bianchi, dettagli neri

def piatto(sagoma, foro, bianchi, neri, logo_larg, logo_c=(0, 0), colore_base="rosso"):
    base = estrudi(sagoma - foro, BASE_H)
    base = incidi_logo_sotto(base, sagoma - foro.offset(2, R), logo_larg, logo_c)
    b = estrudi((bianchi ^ sagoma) - foro, RILIEVO1, BASE_H - 0.01)
    n = estrudi((neri ^ sagoma) - foro, RILIEVO2, BASE_H + RILIEVO1 - 0.02)
    return [(colore_base, base), ("bianco", b), ("nero", n)]

# ----------------------------------------------------------------- POLPO (piatto)
def polpo():
    s = 0.86
    testa = ellisse(21, 19, (0, 12))
    tent = CrossSection(); ventose = CrossSection()
    partenze = [-15, -9, -3, 3, 9, 15]
    arrivi = [(-31, -12), (-21, -26), (-7, -31), (7, -31), (21, -26), (31, -12)]
    for x0, (xe, ye) in zip(partenze, arrivi):
        sg = np.sign(x0)
        p0 = np.array([x0, 6.0]); p2 = np.array([xe, ye]); p1 = (p0 + p2) / 2 + np.array([-sg * 3, 2])
        t = np.linspace(0, 1, 18)
        pts = [tuple((1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2) for u in t]
        # punta che piega dolcemente verso l'esterno, arrotondata
        d = p2 - p1; d /= np.linalg.norm(d)
        fuori = np.array([sg, 0.35]); fuori /= np.linalg.norm(fuori)
        ext = [tuple(p2 + d * 2.0 * k + fuori * 3.0 * k * k) for k in np.linspace(0.25, 1, 4)]
        pts += ext
        rag = list(np.linspace(4.3, 2.5, 18)) + [2.5, 2.6, 2.7, 2.8]
        tent = tent + tratto(pts, rag)
        for u in (0.35, 0.55, 0.75):
            q = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2
            ventose = ventose + cerchio(1.05, tuple(q))
    # cappello di Babbo Natale
    cappello = arrotonda(poligono([(-15, 25), (15, 25), (6, 38), (19, 47), (21, 44)]).hull()
                         + poligono([(-15, 25), (15, 25), (8, 40), (20, 46)]), 1.5)
    pompon_c = (21, 46)
    pompon = cerchio(4.6, pompon_c)
    sagoma = testa + tent + cappello + pompon
    sagoma = arrotonda(sagoma, 0.8)
    foro = cerchio(1.7, pompon_c)
    bordo = (arrotonda(CrossSection.square([36, 6], center=True), 2.6)).translate([0, 26.5])
    occhi_b = cerchio(5.0, (-8, 12)) + cerchio(5.0, (8, 12))
    bianchi = bordo + pompon + occhi_b + ventose
    pupille = cerchio(2.5, (-7.2, 11.2)) + cerchio(2.5, (8.8, 11.2))
    luci = cerchio(0.9, (-6.4, 12.4)) + cerchio(0.9, (9.6, 12.4))
    sorriso = arco((0.8, 4.5), 4.6, 200, 340, 1.4)
    neri = (pupille - luci) + sorriso
    parti = piatto(sagoma, foro, bianchi, neri, 36, (0, 10))
    return [(c, m.scale([s, s, 1])) for c, m in unisci_per_colore(parti)]

# ----------------------------------------------------------------- PESCIOLINO (piatto)
def pesciolino():
    corpo = ellisse(27, 17.5, (-4, 0))
    coda = arrotonda(poligono([(16, 0), (38, 16), (32, 0), (38, -16)]).offset(1.5, R), 1.0)
    dors = arrotonda(poligono([(-16, 14), (-3, 24), (12, 12)]).offset(1.0, R), 1.0)
    tab_c = (-4, 23.5)
    tab = cerchio(4.4, tab_c)
    ventr = arrotonda(poligono([(-6, -15), (2, -22), (7, -13)]).offset(1.0, R), 1.0)
    sagoma = arrotonda(corpo + coda + dors + tab + ventr, 0.8)
    foro = cerchio(1.7, tab_c)
    # dettagli bianchi: occhio, branchia, squame, righe pinne, cuffia di Natale
    occhio = cerchio(5.2, (-19, 4))
    branchia = arco((-24, 0), 13, -42, 42, 1.4)
    squame = CrossSection()
    for i, x in enumerate(np.arange(-12, 17, 5.5)):
        for y in (np.arange(-9, 10, 6.0) + (3 if i % 2 else 0)):
            squame = squame + arco((x, y), 3.2, 100, 260, 1.1, 16)
    corpo_int = corpo.offset(-2.2, R)
    squame = squame ^ corpo_int
    righe = CrossSection()
    for a in (-24, -8, 8, 24):
        t = np.radians(a)
        righe = righe + tratto([(21, 0), (21 + 13 * np.cos(t), 13 * np.sin(t))], [0.6, 0.6])
    righe = righe ^ coda.offset(-1.5, R)
    bianchi = occhio + branchia + squame + righe
    pupilla = cerchio(2.6, (-20, 4.5)) - cerchio(0.9, (-21, 5.6))
    bocca = arco((-28.5, -4), 3.0, 200, 320, 1.2)
    neri = pupilla + bocca
    parti = piatto(sagoma, foro, bianchi, neri, 40, (-2, -1), colore_base="azzurro")
    return unisci_per_colore(parti)


# ----------------------------------------------------------------- PIZZA (piatto, a strati)
def settore(r, gradi, n=60):
    a = np.radians(np.linspace(90 - gradi / 2, 90 + gradi / 2, n))
    return poligono([(0, 0)] + [(r * np.cos(t), r * np.sin(t)) for t in a])

def pizza():
    R_, ANG = 70.0, 44.0
    # spicchio con cornicione bitorzoluto in alto
    a = np.radians(np.linspace(90 - ANG / 2, 90 + ANG / 2, 90))
    rr = R_ + 1.1 * np.sin(np.linspace(0, 7 * np.pi, len(a)))
    spicchio = poligono([(0, 0)] + [(r * np.cos(t), r * np.sin(t)) for r, t in zip(rr, a)])
    spicchio = arrotonda(spicchio.offset(1.0, R), 2.2)
    foro_c = (0, 66.0)
    foro = cerchio(1.7, foro_c)
    # un solo colore per strato; i colori possono ripetersi:
    #   impasto 0-4  ->  salsa (rosso) 4-4.6  ->  mozzarella (giallo) 4.6-5.4  ->  salame (stesso rosso) 5.4-6.2
    salsa2d = settore(62.5, ANG).offset(-1.4, R) ^ spicchio
    mozz2d = increspa(settore(60.0, ANG).offset(-3.2, R), 1.6, 15, seme=4)
    fette = [((-8, 50), 6.2), ((11, 47.5), 5.8), ((-2.5, 34), 5.6), ((3.5, 19.5), 4.2)]
    salame2d = CrossSection()
    for c, r in fette:
        salame2d = salame2d + cerchio(r, c)
    mozz2d = (mozz2d + salame2d.offset(1.2, R)) ^ salsa2d.offset(-0.8, R)   # il salame poggia sempre sulla mozzarella
    salame2d = salame2d ^ mozz2d.offset(-0.6, R)
    base = estrudi(spicchio - foro, BASE_H)
    base = incidi_logo_sotto(base, spicchio - settore(64, ANG + 10).offset(-30, R) - foro.offset(2, R), 30, (0, 49))
    parti = [("impasto", base),
             ("salsa", estrudi(salsa2d, 0.6, BASE_H - 0.01)),
             ("mozzarella", estrudi(mozz2d, 0.8, BASE_H + 0.59)),
             ("salsa", estrudi(salame2d, 0.8, BASE_H + 1.38))]
    return [(c, m.translate([0, -35, 0])) for c, m in parti]

# ----------------------------------------------------------------- PATATINE (3D, a strati)
def stella(r_est, r_int, c=(0, 0), rot=90):
    a = np.radians(rot + np.arange(10) * 36)
    r = np.where(np.arange(10) % 2 == 0, r_est, r_int)
    return poligono(np.column_stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)]))

def patatine():
    H, Z_BIANCO = 38.0, 31.0             # cartoccio rosso fino a 31, fascia bianca fino a 38
    def rett(w, d, z, r=3.0):
        return estrudi(arrotonda(CrossSection.square([w, d], center=True), r), 0.01, z)
    cart = (rett(30, 16, 0) + rett(41, 22.5, H - 0.01)).hull()
    dentro = (rett(30 - 1.2, 16 - 1.2, 0) + rett(41 - 1.2, 22.5 - 1.2, H - 0.01)).hull()
    guscio = cart - dentro                                  # pelle di 0,6 mm per le incisioni
    def prisma_xz(cs2d, lato):                              # forma 2D nel piano XZ, attraverso metà Y
        m = Manifold.extrude(cs2d, 30).rotate([90, 0, 0])    # estrusione verso -Y
        return m if lato < 0 else m.mirror([0, 1, 0])
    # davanti: tre stelle come nel logo; retro: logo PIN-UP (specchiato per leggerlo da dietro)
    stelle = stella(4.2, 1.8, (-9, 19), 90) + stella(5.6, 2.4, (0, 22), 90) + stella(4.2, 1.8, (9, 19), 90)
    cart = cart - (guscio ^ prisma_xz(stelle, -1))
    logo = logo_2d(33).mirror([1, 0]).translate([0, 17.5])
    cart = cart - (guscio ^ prisma_xz(logo, +1))
    # vano in alto (bordo di 1,6 mm) da cui escono le patatine
    vano = (rett(41 - 3.2, 22.5 - 3.2, H - 6) + rett(41 - 3.2, 22.5 - 3.2, H + 1)).hull()
    cart = cart - vano
    # patatine: bastoncini 4x4 di altezze e inclinazioni diverse
    rng = np.random.default_rng(11)
    pos = [(-14, -5), (-14, 3), (-9, -1), (-9, 6), (-4, -6), (-2.6, 0.5), (2.6, 0.5), (4, -6), (4, 6.5),
           (9, -2), (9, 5.5), (14, -5), (14, 2.5), (-4, 6.5), (0, -7.5)]
    alti = {(-2.6, 0.5): 27, (2.6, 0.5): 27}
    fritte = Manifold()
    for (x, y) in pos:
        L = alti.get((x, y), rng.uniform(12, 23) - abs(x) * 0.25)
        lung = L + 9
        st = Manifold.cube([4, 4, lung], center=True).translate([0, 0, lung / 2])
        tilt = (0, 0) if (x, y) in alti else (rng.uniform(-9, 9) + x * 0.5, rng.uniform(-7, 7))
        st = st.rotate([tilt[1], tilt[0], rng.uniform(-25, 25)]).translate([x, y, H - 7])
        fritte = fritte + st
    cima = H - 7 + 27 + 9
    anello = Manifold.revolve(cerchio(1.6, (4.2, 0)), 0, 360).rotate([90, 0, 0]).translate([0, 0.5, cima + 3.0])
    tutto = cart + fritte + anello
    big = 200
    fascia = lambda z0, z1: Manifold.cube([big, big, z1 - z0]).translate([-big / 2, -big / 2, z0])
    return [("rosso", tutto ^ fascia(-1, Z_BIANCO)),
            ("bianco", tutto ^ fascia(Z_BIANCO, H)),
            ("patatina", tutto ^ fascia(H, 120))]

# ----------------------------------------------------------------- PIZZA A PEZZI (incastri)
GIOCO = 0.25        # gioco per lato tra pezzo e sede (P2S: 0,2-0,3 mm)

def pizza_pezzi():
    """Base con sede per la salsa, salsa con sede per la mozzarella, mozzarella con sedi
    per il salame. Ogni pezzo si stampa piatto e di un solo colore."""
    R_, ANG = 70.0, 44.0
    a = np.radians(np.linspace(90 - ANG / 2, 90 + ANG / 2, 90))
    rr = R_ + 1.1 * np.sin(np.linspace(0, 7 * np.pi, len(a)))
    spicchio = arrotonda(poligono([(0, 0)] + [(r * np.cos(t), r * np.sin(t)) for r, t in zip(rr, a)]).offset(1.0, R), 2.2)
    foro = cerchio(1.7, (0, 66.0))
    salsa2d = settore(62.5, ANG).offset(-1.4, R) ^ spicchio.offset(-1.2, R)
    salsa2d = arrotonda(salsa2d, 1.0)
    # fette di salame sempre intere: il raggio si riduce finché la fetta sta tutta nella mozzarella
    consentito = salsa2d.offset(-1.6 - 1.4, R)
    fette = [((-7, 50), 6.0), ((8.5, 47), 5.6), ((-1.5, 34), 5.4), ((0.5, 22), 4.2)]
    salame2d = CrossSection()
    for c, r in fette:
        while r > 2.5 and (cerchio(r, c) - consentito).area() > 0.01:
            r -= 0.1
        salame2d = salame2d + cerchio(r, c)
    mozz2d = increspa(settore(60.0, ANG).offset(-3.2, R), 1.6, 15, seme=4)
    mozz2d = arrotonda((mozz2d + salame2d.offset(1.6, R)) ^ salsa2d.offset(-1.6, R), 0.6)

    H_BASE, SEDE = 5.0, 0.8        # spessore base, profondità di ogni sede
    T = 1.6                        # spessore di salsa, mozzarella e salame
    sede = lambda cs: cs.offset(GIOCO, R)
    # base: impasto con sede per la salsa, logo inciso sotto
    base = estrudi(spicchio - foro, H_BASE) - estrudi(sede(salsa2d), SEDE + 1, H_BASE - SEDE)
    base = incidi_logo_sotto(base, spicchio - settore(64, ANG + 10).offset(-30, R) - foro.offset(2, R), 30, (0, 49))
    z_s = H_BASE - SEDE
    salsa = estrudi(salsa2d, T, z_s) - estrudi(sede(mozz2d), SEDE + 1, z_s + T - SEDE)
    z_m = z_s + T - SEDE
    mozz = estrudi(mozz2d, T, z_m) - estrudi(sede(salame2d), SEDE + 1, z_m + T - SEDE)
    z_f = z_m + T - SEDE
    salame = estrudi(salame2d, T, z_f)
    parti = [("impasto", base), ("salsa", salsa), ("mozzarella", mozz), ("salame", salame)]
    return [(c, m.translate([0, -35, 0])) for c, m in parti]

# ----------------------------------------------------------------- 3MF di stampa
import zipfile

def _mesh_xml(m):
    me = m.to_mesh()
    V = np.asarray(me.vert_properties)[:, :3]; F = np.asarray(me.tri_verts)
    v = "".join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in V)
    f = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in F)
    return f"<mesh><vertices>{v}</vertices><triangles>{f}</triangles></mesh>"

def scrivi_3mf(percorso, oggetti):
    """oggetti: lista di (nome, [(nome_parte, colore, Manifold)], (x, y)).
    Ogni oggetto ha le parti come componenti (nello slicer: un oggetto con più parti)."""
    cols = list(COLORI); mats = "".join(f'<base name="{c}" displaycolor="{COLORI[c]}FF"/>' for c in cols)
    res, build, oid = [], [], 2
    for nome, parti, (tx, ty) in oggetti:
        ids = []
        for np_, col, m in parti:
            res.append(f'<object id="{oid}" name="{nome}_{np_}" type="model" pid="1" pindex="{cols.index(col)}">{_mesh_xml(m)}</object>')
            ids.append(oid); oid += 1
        comps = "".join(f'<component objectid="{i}"/>' for i in ids)
        res.append(f'<object id="{oid}" name="{nome}" type="model"><components>{comps}</components></object>')
        build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {tx:.2f} {ty:.2f} 0"/>'); oid += 1
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="it-IT" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><basematerials id="1">{mats}</basematerials>{"".join(res)}</resources>'
             f'<build>{"".join(build)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(percorso, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)

NOMI_KIT = {"hamburger": ["pane_sotto", "carne", "formaggio", "insalata", "pomodoro", "pane_sopra"],
            "pizza_pezzi": ["base", "salsa", "mozzarella", "salame"]}

def cambi_colore(parti, strato=0.2):
    """Controlla che ogni strato abbia un solo colore e restituisce le fasce [(colore, z_da, z_a)]."""
    fasce = []
    for col, m in parti:
        b = m.bounding_box(); z0, z1 = round(b[2] / strato) * strato, round(b[5] / strato) * strato
        fasce.append((col, round(z0, 2), round(z1, 2)))
    fasce.sort(key=lambda f: f[1])
    for (c1, a1, b1), (c2, a2, b2) in zip(fasce, fasce[1:]):
        assert b1 <= a2 + 1e-6, f"due colori nello stesso strato: {c1} {a1}-{b1} e {c2} {a2}-{b2}"
    unite = []
    for f in fasce:
        if unite and unite[-1][0] == f[0] and abs(unite[-1][2] - f[1]) < 1e-6:
            unite[-1] = (f[0], unite[-1][1], f[2])
        else:
            unite.append(f)
    return unite

def esporta_stampa(nome, parti, cartella):
    os.makedirs(cartella, exist_ok=True)
    if nome in NOMI_KIT:   # ogni pezzo è un oggetto a sé: si stampa solo quello che serve
        ogg = []
        for i, ((col, m), np_) in enumerate(zip(parti, NOMI_KIT[nome])):
            b = m.bounding_box()
            m0 = m.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])
            ogg.append((f"{nome}_{np_}", [(np_, col, m0)], (((i % 3) - 1) * 75.0, (i // 3) * 75.0 - 37.5)))
            scrivi_3mf(os.path.join(cartella, f"{nome}_{i + 1}_{np_}.3mf"), [ogg[-1][:2] + ((0, 0),)])
        scrivi_3mf(os.path.join(cartella, f"{nome}_tutti_i_pezzi.3mf"), ogg)
        return {"tipo": "a pezzi", "pezzi": [{"pezzo": n, "colore": c} for (c, _), n in zip(parti, NOMI_KIT[nome])]}
    fasce = cambi_colore(parti)
    unite = {}
    for col, m in parti: unite[col] = unite[col] + m if col in unite else m
    scrivi_3mf(os.path.join(cartella, f"{nome}.3mf"), [(nome, [(c, c, m) for c, m in unite.items()], (0, 0))])
    return {"tipo": "a strati", "fasce": fasce,
            "cambi_a_mm": [f[1] for f in fasce[1:]]}

# ----------------------------------------------------------------- export
def unisci_per_colore(parti):
    out = {}
    ordine = []
    for c, m in parti:
        if c in out: out[c] = out[c] + m
        else: out[c] = m; ordine.append(c)
    return [(c, out[c]) for c in ordine]

def salva(nome, parti, cartella):
    import trimesh
    quote = []
    for i, (col, m) in enumerate(parti):
        assert m.status().name == "NoError", (nome, col)
        me = m.to_mesh()
        tm = trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)
        fn = f"{nome}__{i}_{col}.stl"
        tm.export(os.path.join(cartella, fn))
        b = m.bounding_box()
        quote.append({"file": fn, "colore": col, "hex": COLORI[col], "z_min": round(b[2], 2), "z_max": round(b[5], 2)})
    tutto = Manifold()
    for _, m in parti: tutto = tutto + m
    b = tutto.bounding_box()
    print(f"{nome:11s} ingombro {b[3]-b[0]:.1f} x {b[4]-b[1]:.1f} x {b[5]-b[2]:.1f} mm  volume {tutto.volume()/1000:.1f} cm3")
    return {"parti": quote, "ingombro_mm": [round(b[3]-b[0], 1), round(b[4]-b[1], 1), round(b[5]-b[2], 1)]}

KIT = {"hamburger", "pizza_pezzi"}   # addobbi stampati a pezzi separati

def main():
    cartella = os.path.join(QUI, "parti"); os.makedirs(cartella, exist_ok=True)
    fq = os.path.join(cartella, "quote.json")
    tutti = json.load(open(fq)) if os.path.exists(fq) else {}
    for nome, f in [("hamburger", hamburger), ("sandwich", sandwich), ("polpo", polpo), ("pesciolino", pesciolino), ("pizza", pizza), ("pizza_pezzi", pizza_pezzi), ("patatine", patatine)]:
        if len(sys.argv) > 1 and nome not in sys.argv[1:]: continue
        parti = f()
        tutti[nome] = salva(nome, parti, cartella)
        tutti[nome]["kit"] = nome in KIT
        tutti[nome]["stampa"] = esporta_stampa(nome, parti, os.path.join(QUI, "stampa"))
    json.dump(tutti, open(fq, "w"), indent=1)

if __name__ == "__main__":
    main()
