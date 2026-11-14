#!/usr/bin/env python3
"""
Emozioni in 3D - Addobbi di Natale PIN-UP Cafe (6-8 cm) con logo sul retro.

  hamburger  - 3D, stampato SCOMPOSTO (6 pezzi, ognuno di un colore) e montato con perno e clip
  sandwich   - 3D, tramezzino triangolare a strati con stecchino e oliva
  polpo      - piatto, con cappello di Babbo Natale, dettagli in rilievo
  pesciolino - piatto, dettagli in rilievo
  patatine   - 3D, cartoccio rosso con fascia bianca e patatine
  pizza      - piatto, spicchio a strati (impasto, formaggio, salame)

Regola per gli addobbi piatti: i colori si susseguono dal basso verso l'alto
senza mai tornare a un colore già usato -> al massimo 2 cambi filamento.

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
    "salsa": "#CF3A24", "patatina": "#F3B63A", "impasto": "#E2AE52", "formaggio_scuro": "#D9821A", "mozzarella": "#F0C24A", "salame": "#8A1D1A",
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
    stecco = Manifold.cylinder(16, 1.2, 1.2, 24).translate([0, 0, z - 1])
    oliva = Manifold.sphere(1.0, 40).scale([4.6, 4.6, 5.4]).translate([0, 0, z + 9.5])
    anello = Manifold.revolve(cerchio(1.6, (4.0, 0)), 0, 360).rotate([90, 0, 0]).translate([0, 0, z + 9.5 + 5.4 + 3.6])
    parti.append(("oliva", stecco + oliva + anello))
    return unisci_per_colore(parti)

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
    # strati in sequenza, senza tornare a un colore già usato (2 soli cambi):
    #   giallo chiaro (impasto) 0-4  ->  giallo scuro (formaggio) 4-4.8  ->  rosso (salame) 4.8-5.6
    mozz2d = increspa(settore(61.0, ANG).offset(-2.4, R), 1.6, 15, seme=4)
    fette = [((-8, 50), 6.2), ((11, 47.5), 5.8), ((-2.5, 34), 5.6), ((3.5, 19.5), 4.2)]
    salame2d = CrossSection()
    for c, r in fette:
        salame2d = salame2d + cerchio(r, c)
    mozz2d = (mozz2d + salame2d.offset(1.2, R)) ^ spicchio.offset(-1.8, R)   # il salame poggia sempre sul formaggio
    salame2d = salame2d ^ mozz2d.offset(-0.6, R)
    base = estrudi(spicchio - foro, BASE_H)
    base = incidi_logo_sotto(base, spicchio - settore(64, ANG + 10).offset(-30, R) - foro.offset(2, R), 30, (0, 49))
    parti = [("impasto", base),
             ("formaggio_scuro", estrudi(mozz2d, RILIEVO1 - 0.2, BASE_H - 0.01)),
             ("salame", estrudi(salame2d, RILIEVO2, BASE_H + RILIEVO1 - 0.22))]
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

KIT = {"hamburger"}   # addobbi stampati a pezzi separati

def main():
    cartella = os.path.join(QUI, "parti"); os.makedirs(cartella, exist_ok=True)
    fq = os.path.join(cartella, "quote.json")
    tutti = json.load(open(fq)) if os.path.exists(fq) else {}
    for nome, f in [("hamburger", hamburger), ("sandwich", sandwich), ("polpo", polpo), ("pesciolino", pesciolino), ("pizza", pizza), ("patatine", patatine)]:
        if len(sys.argv) > 1 and nome not in sys.argv[1:]: continue
        tutti[nome] = salva(nome, f(), cartella)
        tutti[nome]["kit"] = nome in KIT
    json.dump(tutti, open(fq, "w"), indent=1)

if __name__ == "__main__":
    main()
