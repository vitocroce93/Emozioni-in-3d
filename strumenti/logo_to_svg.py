#!/usr/bin/env python3
"""
Converte un logo (immagine) in livelli vettoriali SVG, uno per colore,
pronti per essere importati in OpenSCAD e stampati in multicolore.

- separa i colori (rosso, blu, grigio) dallo sfondo bianco
- scala il logo alla larghezza/diametro desiderati in mm
- ingrossa i tratti troppo sottili per un ugello da 0.4 mm
- elimina i dettagli troppo piccoli per essere stampati
- vettorializza ogni livello con potrace (stessa origine -> livelli allineati)

Uso:
  python3 logo_to_svg.py IMG OUT_PREFIX --fit-width 45 --fit-height 21
  python3 logo_to_svg.py IMG OUT_PREFIX --fit-circle 21.4 --min-area-mm2 0.6
"""
import argparse, subprocess, os, json
import cv2, numpy as np
from skimage.morphology import medial_axis

ap = argparse.ArgumentParser()
ap.add_argument("img"); ap.add_argument("out")
ap.add_argument("--crop-bottom", type=int, default=0, help="pixel da tagliare in basso (es. watermark)")
ap.add_argument("--fit-width", type=float); ap.add_argument("--fit-height", type=float)
ap.add_argument("--fit-circle", type=float, help="diametro mm del cerchio in cui far stare il logo")
ap.add_argument("--min-width", type=float, default=0.45, help="spessore minimo dei tratti (mm)")
ap.add_argument("--min-area-mm2", type=float, default=0.15, help="elimina elementi più piccoli (mm2)")
ap.add_argument("--upscale", type=int, default=3)
a = ap.parse_args()

im = cv2.imread(a.img)
if a.crop_bottom: im = im[:-a.crop_bottom]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
H, S, V = [hsv[..., i].astype(int) for i in range(3)]
dark = V < 200
masks = {}
masks["rosso"] = dark & (S > 80) & ((H < 12) | (H > 165))
masks["blu"]   = dark & (S > 50) & (H > 90) & (H < 130)
masks["grigio"] = dark & ~masks["rosso"] & ~masks["blu"]
# l'alone JPEG attorno ai colori viene letto come grigio: lo togliamo
_near = cv2.dilate((masks["rosso"] | masks["blu"]).astype(np.uint8),
                   np.ones((7, 7), np.uint8)).astype(bool)
masks["grigio"] &= ~_near
allm = np.zeros(dark.shape, np.uint8)
for m in masks.values(): allm |= m.astype(np.uint8)
# rimuovi rumore isolato prima di calcolare l'ingombro
n, lab, st, _ = cv2.connectedComponentsWithStats(allm, 8)
keep = np.zeros_like(allm)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 40: keep[lab == i] = 1

ys, xs = np.nonzero(keep)
if a.fit_circle:
    (cx, cy), r = cv2.minEnclosingCircle(np.column_stack([xs, ys]).astype(np.float32))
    mm_per_px = a.fit_circle / (2 * r)
    x0, y0, w, h = int(cx - r) - 2, int(cy - r) - 2, int(2 * r) + 4, int(2 * r) + 4
else:
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    mm_per_px = min(a.fit_width / w, a.fit_height / h)
    x0 -= 2; y0 -= 2; w += 4; h += 4

def prep(m):
    m = m.astype(np.uint8) * 255
    pad = np.zeros((h, w), np.uint8)
    sub = m[max(y0, 0):y0 + h, max(x0, 0):x0 + w]
    pad[max(0, -y0):max(0, -y0) + sub.shape[0], max(0, -x0):max(0, -x0) + sub.shape[1]] = sub
    up = cv2.resize(pad, (w * a.upscale, h * a.upscale), interpolation=cv2.INTER_LINEAR)
    return (up > 127).astype(np.uint8)

px = mm_per_px / a.upscale                       # mm per pixel dopo upscale
minw = max(1, int(round(a.min_width / px)))      # tratto minimo in px
min_area = a.min_area_mm2 / (px * px)
disk = lambda d: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d, d))

out = {}
for name in ["grigio", "rosso", "blu"]:
    m = prep(masks[name])
    # elimina dettagli troppo piccoli (es. scritte microscopiche)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    clean = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= min_area: clean[lab == i] = 1
    # ingrossa solo i tratti più sottili del minimo: sull'asse mediano del
    # tratto, dove lo spessore locale è < minimo, si disegna un cerchio
    # di diametro pari allo spessore minimo
    skel, dist = medial_axis(clean.astype(bool), return_distance=True)
    grow = np.zeros_like(clean)
    r = minw / 2.0
    for y, x in zip(*np.nonzero(skel & (dist < r))):
        cv2.circle(grow, (int(x), int(y)), int(round(r)), 1, -1)
    m2 = (clean | grow).astype(np.float32)
    # leviga i bordi ondulati lasciati dall'ingrossamento
    sig = max(1.0, minw / 5.0)
    out[name] = (cv2.GaussianBlur(m2, (0, 0), sig) > 0.5).astype(np.uint8)
# priorità: blu sopra rosso sopra grigio (niente sovrapposizioni tra livelli)
out["rosso"] &= 1 - out["blu"]
out["grigio"] &= 1 - out["blu"]; out["grigio"] &= 1 - out["rosso"]

dpi = 25.4 / px
info = {"mm_per_px": float(px), "px_w": int(w * a.upscale), "px_h": int(h * a.upscale), "width_mm": float(w * mm_per_px), "height_mm": float(h * mm_per_px), "layers": []}
for name, m in out.items():
    if m.sum() == 0: continue
    cv2.imwrite(f"{a.out}_{name}.png", m * 255)   # maschera usata dal generatore 3D
    pbm = f"{a.out}_{name}.pbm"
    cv2.imwrite(pbm, (1 - m) * 255)
    subprocess.run(["potrace", "-s", "-r", f"{dpi:.4f}", "-t", "4", "-a", "1.0", "-O", "0.3",
                    "-o", f"{a.out}_{name}.svg", pbm], check=True)
    os.remove(pbm)
    info["layers"].append(name)
json.dump(info, open(f"{a.out}.json", "w"), indent=1)
# anteprima a colori
col = {"grigio": (95, 100, 95), "rosso": (55, 40, 150), "blu": (110, 80, 40)}
prev = np.full((h * a.upscale, w * a.upscale, 3), 255, np.uint8)
for name, m in out.items(): prev[m.astype(bool)] = col[name]
cv2.imwrite(f"{a.out}_anteprima.png", prev)
print(json.dumps(info))
