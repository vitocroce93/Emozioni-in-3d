"""
Rendering degli addobbi con Blender (Cycles).
Uso: blender -b -P render_blender.py -- <addobbo> <vista> <out.png> [campioni]
  vista: fronte | retro | gruppo
"""
import bpy, sys, json, os, math
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:]
NOME, VISTA, OUT = argv[0], argv[1], argv[2]
CAMPIONI = int(argv[3]) if len(argv) > 3 else 64
QUI = os.path.dirname(os.path.abspath(__file__))
PARTI = os.path.join(QUI, "parti")
quote = json.load(open(os.path.join(PARTI, "quote.json")))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = CAMPIONI
sc.cycles.use_denoising = False      # Blender di Debian/Ubuntu senza OIDN
sc.cycles.max_bounces = 6
sc.cycles.filter_width = 1.8
sc.render.resolution_x = 1400 if VISTA == "gruppo" else 1100
sc.render.resolution_y = 900 if VISTA == "gruppo" else 1100
sc.render.film_transparent = False
sc.view_settings.view_transform = "Filmic" if "Filmic" in [v.identifier for v in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Standard"
sc.view_settings.look = "Medium High Contrast" if sc.view_settings.view_transform == "Filmic" else "None"

def hex2rgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c] + [1]

def materiale(nome, hexcol, rough=0.42):
    m = bpy.data.materials.get(nome)
    if m: return m
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex2rgb(hexcol)
    b.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in b.inputs: b.inputs["Specular IOR Level"].default_value = 0.35
    return m

def importa(addobbo):
    objs = []
    for p in quote[addobbo]["parti"]:
        path = os.path.join(PARTI, p["file"])
        bpy.ops.wm.stl_import(filepath=path)
        o = bpy.context.selected_objects[0]
        o.data.materials.append(materiale(p["colore"], p["hex"]))
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth()
        o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(35)
        objs.append(o)
    # raggruppa sotto un vuoto
    vuoto = bpy.data.objects.new(addobbo, None); bpy.context.collection.objects.link(vuoto)
    for o in objs:
        o.scale = (0.01, 0.01, 0.01); o.location = (0, 0, 0); o.parent = vuoto   # mm -> unità (1 = 10 cm)
    piatto = addobbo in ("polpo", "pesciolino", "pizza", "pizza_pezzi")
    if piatto:
        vuoto.rotation_euler = Euler((math.radians(90), 0, 0))   # faccia superiore verso -Y (camera)
    return vuoto, objs, piatto

def centro_ingombro(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (mn + mx) / 2, mx - mn

def luce_area(nome, loc, energia, size, colore=(1, 1, 1)):
    l = bpy.data.lights.new(nome, "AREA"); l.energy = energia; l.size = size; l.color = colore
    o = bpy.data.objects.new(nome, l); bpy.context.collection.objects.link(o); o.location = loc
    d = Vector((0, 0, 0)) - Vector(loc); o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o

def mondo(colore, forza=0.6):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = hex2rgb(colore); bg.inputs[1].default_value = forza

def sfondo(colore, gradiente=True):
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 9, 0)); p = bpy.context.object
    p.rotation_euler = (math.radians(90), 0, 0)
    m = materiale("sfondo_" + colore, colore, 0.9); p.data.materials.append(m)

def camera(loc, target, lente=85):
    c = bpy.data.cameras.new("cam"); c.lens = lente
    o = bpy.data.objects.new("cam", c); bpy.context.collection.objects.link(o); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = o
    return o

def filo(sopra, lungh=3.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.004, depth=lungh, location=(sopra.x, sopra.y, sopra.z + lungh / 2))
    bpy.context.object.data.materials.append(materiale("filo", "#C9A13B", 0.3))

if VISTA in ("esploso", "stampa"):
    v, objs, piatto = importa(NOME)
    v.rotation_euler = Euler((0, 0, 0))          # pezzi sdraiati come si stampano
    bpy.context.view_layer.update()
    if VISTA == "esploso":
        for i, o in enumerate(objs):
            o.location.z += i * (0.10 if piatto else 0.13) + (0.12 if i == len(objs) - 1 and not piatto else 0)
    else:   # pezzi appoggiati sul piatto come si stampano, in griglia 3 x 2
        for i, o in enumerate(objs):
            bpy.context.view_layer.update()
            zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
            o.location = (((i % 3) - 1) * 0.78, (i // 3) * 0.78 - 0.39, -zmin)
    c, dim = centro_ingombro(objs)
    v.location -= c
    mondo("#FBF6EE", 0.55)
    if VISTA == "stampa":
        bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, -dim.z / 2 - 0.001))
        bpy.context.object.data.materials.append(materiale("piatto_stampa", "#2B2B2E", 0.6))
        sfondo("#F3E9DA")
        D = max(dim.x, dim.y)
        camera((0.0, -1.25 * D, 1.25 * D), (0, 0.0, -dim.z / 2), 50)
    else:
        sfondo("#F3E9DA")
        r = max(dim) * 2.6
        if piatto: camera((r * 0.12, -r * 0.62, r * 0.78), (0, 0, 0), 85)
        else: camera((r * 0.25, -r * 0.95, r * 0.22), (0, 0, 0), 85)
    luce_area("key", (-1.2, -1.6, 2.2), 260, 1.6, (1, 0.96, 0.9))
    luce_area("fill", (1.6, -1.2, 0.6), 90, 2.0, (0.9, 0.95, 1))
    luce_area("rim", (0.3, 1.6, 1.8), 120, 1.2)
elif VISTA in ("fronte", "retro"):
    v, objs, piatto = importa(NOME)
    if VISTA == "retro":
        if piatto or NOME == "patatine": v.rotation_euler.z = math.radians(180)
        else: v.rotation_euler = Euler((0, math.radians(180), 0))   # capovolto: si vede il fondo
    c, dim = centro_ingombro(objs)
    for o in [v]: v.location -= c
    c, dim = centro_ingombro(objs)
    mondo("#FBF6EE", 0.55)
    sfondo("#F3E9DA")
    r = max(dim) * 2.9
    if NOME == "patatine":
        camera((r * 0.18, -r * 0.95, r * 0.22), (0, 0, 0), 85)
    elif NOME in ("hamburger", "sandwich") and VISTA == "fronte":
        camera((r * 0.15, -r * 0.95, r * (0.30 if NOME == "hamburger" else 0.42)), (0, 0, -0.02), 85)
    elif NOME in ("hamburger", "sandwich"):
        camera((0.0, -r * 0.55, r * 0.85), (0, 0, 0), 85)
    else:
        camera((r * 0.22, -r * 0.97, r * 0.12), (0, 0, 0), 85)
    luce_area("key", (-0.6, -0.9, 0.9), 70, 0.8, (1, 0.96, 0.9))
    luce_area("fill", (0.9, -0.6, 0.2), 25, 1.2, (0.9, 0.95, 1))
    luce_area("rim", (0.2, 1.0, 0.9), 35, 0.6)
else:  # gruppo: tutti appesi su sfondo verde scuro
    disp = [("hamburger", -2.10, 0.10), ("polpo", -1.27, -0.14), ("patatine", -0.42, 0.10), ("pizza", 0.42, -0.06), ("sandwich", 1.27, 0.12), ("pesciolino", 2.10, -0.12)]
    for nome, x, z in disp:
        v, objs, piatto = importa(nome)
        c, dim = centro_ingombro(objs)
        v.location -= c
        v.location += Vector((x, 0, z))
        v.rotation_euler.z += math.radians({"hamburger": 20, "polpo": -8, "pizza": 6, "patatine": 25, "sandwich": 10, "pesciolino": -12}[nome])
        c, dim = centro_ingombro(objs)
        filo(Vector((c.x, c.y, c.z + dim.z / 2 - 0.01)))
    mondo("#0E2A1C", 0.4)
    sfondo("#123524")
    # lucine sfocate sullo sfondo
    import random; random.seed(3)
    for i in range(46):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(random.uniform(-4.0, 4.0), 7.0, random.uniform(-2.2, 2.4)))
        m = bpy.data.materials.new(f"lux{i}"); m.use_nodes = True
        n = m.node_tree.nodes; em = n.new("ShaderNodeEmission")
        em.inputs[0].default_value = hex2rgb(random.choice(["#FFD27A", "#FFB347", "#FFF1C1"])); em.inputs[1].default_value = 18
        m.node_tree.links.new(em.outputs[0], n["Material Output"].inputs[0])
        bpy.context.object.data.materials.append(m)
    cam = camera((0.0, -7.8, 0.25), (0.0, 0, 0.0), 50)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 7.8; cam.data.dof.aperture_fstop = 0.9
    luce_area("key", (-2.0, -3.0, 2.4), 900, 2.5, (1, 0.93, 0.82))
    luce_area("fill", (2.6, -2.4, 0.4), 320, 3.0, (0.85, 0.92, 1))
    luce_area("rim", (0.0, 2.0, 2.5), 400, 2.5)

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
