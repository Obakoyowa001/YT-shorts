"""3D toy-style kit for Shorts, built on Blender's Python API (bpy).

Everything a shot needs: scene setup, toy-plastic materials, mesh primitives, 3D text,
toy characters with expressive faces, sets, props, lighting presets and a camera rig.

Units are metres. +Z is up. The camera normally looks toward +Y, so "front" is -Y.
Times passed to animation helpers are in SECONDS from the start of the shot.
"""
import math
import os
import random
import warnings

import bpy  # noqa: I001  (bpy must be imported before bmesh/mathutils)
import bmesh
from mathutils import Vector

warnings.filterwarnings("ignore", category=DeprecationWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
FPS = 30
_fonts = {}
_mats = {}

# ---------------------------------------------------------------- palette (sRGB 0-255)
SKIN = (240, 196, 158)
SKIN_TAN = (205, 148, 104)
SKIN_DARK = (128, 82, 56)
INK = (32, 26, 24)
WHITE = (250, 247, 240)
CREAM = (244, 230, 200)
GOLD = (246, 190, 40)
EMERALD = (24, 130, 86)
RED = (206, 50, 46)
PLAID = (180, 40, 38)
PURPLE = (110, 64, 150)
GREY = (138, 140, 146)
STEEL = (92, 104, 120)
WOOD = (140, 92, 56)
WOOD_D = (96, 60, 36)
WOOD_L = (190, 140, 92)
MONEY = (150, 200, 130)
MONEY_D = (70, 130, 84)
SKY = (150, 200, 236)
PASTELS = [(236, 208, 168), (226, 180, 160), (204, 214, 186), (238, 222, 176),
           (214, 196, 222), (240, 196, 150), (196, 214, 222), (230, 214, 196)]
SHUTTERS = [(40, 90, 150), (36, 120, 80), (190, 50, 46), (60, 70, 120), (200, 150, 40)]


def lin(c):
    """sRGB 0-255 tuple -> linear 0-1 tuple (what Blender colour inputs expect)."""
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(v) for v in c[:3])


# ---------------------------------------------------------------- scene
def new_scene(width=720, height=1280, fps=FPS, samples=4):
    """Fresh scene set up for fast CPU path tracing (Cycles + denoiser)."""
    global FPS
    FPS = fps
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    _fonts.clear()
    sc = bpy.context.scene
    r = sc.render
    r.fps = fps
    r.resolution_x, r.resolution_y, r.resolution_percentage = width, height, 100
    r.engine = "CYCLES"
    r.use_persistent_data = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.film_transparent = False
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    for attr, val in (("denoising_input_passes", "RGB_ALBEDO_NORMAL"),
                      ("denoising_prefilter", "ACCURATE"), ("max_bounces", 3),
                      ("diffuse_bounces", 2), ("glossy_bounces", 1), ("transmission_bounces", 1),
                      ("transparent_max_bounces", 2), ("volume_bounces", 0),
                      ("caustics_reflective", False), ("caustics_refractive", False),
                      ("blur_glossy", 1.0), ("use_light_tree", False)):
        if hasattr(cy, attr):
            try:
                setattr(cy, attr, val)
            except (TypeError, ValueError):
                pass
    try:
        bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "NONE"
    except (KeyError, TypeError):
        pass
    vs = sc.view_settings
    vs.view_transform = "AgX"
    for look in ("AgX - Punchy", "Punchy"):
        try:
            vs.look = look
            break
        except TypeError:
            continue
    vs.exposure = 0.0
    sc.frame_start = 1
    world = bpy.data.worlds.new("world")
    sc.world = world
    world.use_nodes = True
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
    return sc


def f(t):
    """Seconds -> frame number (frames start at 1)."""
    return 1 + round(t * FPS)


# ---------------------------------------------------------------- materials
def mat(rgb, rough=0.42, emit=0.0, metal=0.0, name="m", coat=0.15, alpha=1.0):
    key = (tuple(rgb), rough, emit, metal, coat, alpha)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    col = (*lin(rgb), 1)
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for nm in ("Coat Weight", "Clearcoat"):
        if nm in b.inputs:
            b.inputs[nm].default_value = coat
            break
    if emit:
        b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    _mats[key] = m
    return m


def _nodes(m):
    nt = m.node_tree
    return nt, nt.nodes, nt.links


def mat_stripes(c1, c2, scale=6.0, axis="X", rough=0.6, name="stripes"):
    """Two-colour stripes (awnings, shirts)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, n, ln = _nodes(m)
    b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    mul = n.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = scale
    fr = n.new("ShaderNodeMath")
    fr.operation = "PINGPONG"
    fr.inputs[1].default_value = 0.5
    gt = n.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.25
    mix = n.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*lin(c1), 1)
    mix.inputs["B"].default_value = (*lin(c2), 1)
    ln.new(tc.outputs["Object"], sep.inputs[0])
    ln.new(sep.outputs[axis], mul.inputs[0])
    ln.new(mul.outputs[0], fr.inputs[0])
    ln.new(fr.outputs[0], gt.inputs[0])
    ln.new(gt.outputs[0], mix.inputs["Factor"])
    ln.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


def mat_plaid(c1, c2, scale=10.0, name="plaid"):
    m = mat_stripes(c1, c2, scale, "X", 0.7, name)
    nt, n, ln = _nodes(m)
    tc = [x for x in n if x.bl_idname == "ShaderNodeTexCoord"][0]
    mix = [x for x in n if x.bl_idname == "ShaderNodeMix"][0]
    sep = n.new("ShaderNodeSeparateXYZ")
    mul = n.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = scale
    fr = n.new("ShaderNodeMath")
    fr.operation = "PINGPONG"
    fr.inputs[1].default_value = 0.5
    gt = n.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.3
    dark = n.new("ShaderNodeMix")
    dark.data_type = "RGBA"
    dark.inputs["B"].default_value = (*lin(INK), 1)
    dark.inputs["Factor"].default_value = 0.0
    fac = n.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    fac.inputs[1].default_value = 0.35
    ln.new(tc.outputs["Object"], sep.inputs[0])
    ln.new(sep.outputs["Z"], mul.inputs[0])
    ln.new(mul.outputs[0], fr.inputs[0])
    ln.new(fr.outputs[0], gt.inputs[0])
    ln.new(gt.outputs[0], fac.inputs[0])
    ln.new(fac.outputs[0], dark.inputs["Factor"])
    ln.new(mix.outputs["Result"], dark.inputs["A"])
    ln.new(dark.outputs["Result"], n["Principled BSDF"].inputs["Base Color"])
    return m


def mat_cobble(base=(196, 182, 160), mortar=(120, 108, 96), scale=8.0, name="cobble"):
    """Procedural cobblestones: Voronoi cells with dark mortar gaps and bump."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, n, ln = _nodes(m)
    b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    vor = n.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale
    vor2 = n.new("ShaderNodeTexVoronoi")
    vor2.inputs["Scale"].default_value = scale
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*lin(mortar), 1)
    ramp.color_ramp.elements[1].position = 0.12
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    var = n.new("ShaderNodeMix")
    var.data_type = "RGBA"
    var.inputs["A"].default_value = (*lin(base), 1)
    var.inputs["B"].default_value = (*lin(tuple(min(255, c + 26) for c in base)), 1)
    sep = n.new("ShaderNodeSeparateColor")
    mulc = n.new("ShaderNodeMix")
    mulc.data_type = "RGBA"
    mulc.blend_type = "MULTIPLY"
    mulc.inputs["Factor"].default_value = 1.0
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bramp = n.new("ShaderNodeMapRange")
    bramp.inputs["From Min"].default_value = 0.0
    bramp.inputs["From Max"].default_value = 0.3
    ln.new(tc.outputs["Object"], vor.inputs["Vector"])
    ln.new(tc.outputs["Object"], vor2.inputs["Vector"])
    ln.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    ln.new(vor2.outputs["Color"], sep.inputs[0])
    ln.new(sep.outputs[0], var.inputs["Factor"])
    ln.new(var.outputs["Result"], mulc.inputs["A"])
    ln.new(ramp.outputs["Color"], mulc.inputs["B"])
    ln.new(mulc.outputs["Result"], b.inputs["Base Color"])
    ln.new(vor.outputs["Distance"], bramp.inputs["Value"])
    ln.new(bramp.outputs["Result"], bump.inputs["Height"])
    ln.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.8
    return m


def mat_dots(c1, c2, scale=14.0, name="dots"):
    """Polka dots (dresses, wallpaper)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, n, ln = _nodes(m)
    b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    vor = n.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = scale
    vor.inputs["Randomness"].default_value = 0.0
    lt = n.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = 0.22
    mix = n.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*lin(c1), 1)
    mix.inputs["B"].default_value = (*lin(c2), 1)
    ln.new(tc.outputs["Object"], vor.inputs["Vector"])
    ln.new(vor.outputs["Distance"], lt.inputs[0])
    ln.new(lt.outputs[0], mix.inputs["Factor"])
    ln.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    return m


# ---------------------------------------------------------------- mesh primitives
def _link(o, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    o.location = loc
    o.rotation_euler = tuple(math.radians(a) for a in rot)
    o.scale = scale
    return o


def _mesh(name, bm, material, parent, loc, rot, scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if material is not None:
        me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    return _link(o, parent, loc, rot, scale)


def empty(name="empty", loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.1
    return _link(o, parent, loc, rot)


def sphere(r, loc=(0, 0, 0), material=None, parent=None, scale=(1, 1, 1), rot=(0, 0, 0),
           seg=32, rings=16, name="sphere", hemi=False):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    if hemi:  # keep the upper half only (eyelids, domes, hats)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
    for fc in bm.faces:
        fc.smooth = True
    return _mesh(name, bm, material, parent, loc, rot, scale)


def capsule(r, length, loc=(0, 0, 0), material=None, parent=None, scale=(1, 1, 1),
            rot=(0, 0, 0), name="capsule", seg=32):
    """Pill shape along Z: total height = length + 2r."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=16, radius=r)
    for v in bm.verts:
        v.co.z += length / 2 if v.co.z > 1e-5 else (-length / 2 if v.co.z < -1e-5 else 0)
    for fc in bm.faces:
        fc.smooth = True
    return _mesh(name, bm, material, parent, loc, rot, scale)


def box(size, loc=(0, 0, 0), material=None, bevel=0.03, parent=None, rot=(0, 0, 0),
        name="box"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    if bevel > 0:
        bev = min(bevel, min(size) * 0.45)
        res = bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=bev, segments=3,
                              profile=0.5, affect="EDGES", clamp_overlap=True)
        for fc in res["faces"]:
            fc.smooth = True
    return _mesh(name, bm, material, parent, loc, rot)


def cyl(r, depth, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), r2=None, seg=32,
        name="cyl", caps=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    for fc in bm.faces:
        fc.smooth = abs(fc.normal.z) < 0.9
    return _mesh(name, bm, material, parent, loc, rot)


def torus(R, r, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), arc=360,
          name="torus", seg=40, rseg=12, scale=(1, 1, 1)):
    """Torus in the XY plane; arc < 360 keeps a centred arc (opening toward -Y... toward +Y)."""
    bm = bmesh.new()
    n = max(3, int(seg * arc / 360))
    rings = []
    for i in range(n + 1 if arc < 360 else n):
        a = math.radians(-90 - arc / 2 + arc * i / (n if arc < 360 else n))
        c = Vector((math.cos(a) * R, math.sin(a) * R, 0))
        ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            d = Vector((math.cos(a), math.sin(a), 0)) * math.cos(b) + Vector((0, 0, math.sin(b)))
            ring.append(bm.verts.new(c + d * r))
        rings.append(ring)
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if arc >= 360 else [])
    for ra, rb in pairs:
        for j in range(rseg):
            fc = bm.faces.new((ra[j], ra[(j + 1) % rseg], rb[(j + 1) % rseg], rb[j]))
            fc.smooth = True
    if arc < 360:  # round end caps
        for ring in (rings[0], rings[-1]):
            bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh(name, bm, material, parent, loc, rot, scale)


def cone(r, depth, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), name="cone"):
    return cyl(r, depth, loc, material, parent, rot, r2=0.0, name=name)


def prism(width, height, depth, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0),
          name="prism"):
    """Triangular prism (roof gable / pediment): base along X, apex up, extruded along Y."""
    bm = bmesh.new()
    pts = [(-width / 2, 0), (width / 2, 0), (0, height)]
    front = [bm.verts.new((x, -depth / 2, z)) for x, z in pts]
    back = [bm.verts.new((x, depth / 2, z)) for x, z in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh(name, bm, material, parent, loc, rot)


def plane(size, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), name="plane"):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
    return _mesh(name, bm, material, parent, loc, rot)


# ---------------------------------------------------------------- 3D text
def font(name="LuckiestGuy"):
    if name not in _fonts:
        _fonts[name] = bpy.data.fonts.load(os.path.join(FONT_DIR, name + ".ttf"))
    return _fonts[name]


def text(s, loc=(0, 0, 0), size=0.3, material=None, rot=(90, 0, 0), fnt="LuckiestGuy",
         extrude=0.01, parent=None, align="CENTER", name="text", spacing=1.0):
    """Upright text facing -Y (toward the default camera)."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    cu.font = font(fnt)
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.space_character = spacing
    if extrude:
        cu.bevel_depth = extrude * 0.3
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(material or mat(INK))
    return _link(o, parent, loc, rot)


# ---------------------------------------------------------------- keyframes
def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "layers", [])) == 0:
        return act.fcurves
    from bpy_extras import anim_utils
    cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
    return cb.fcurves if cb else []


def key(obj, path, t, value, interp=None, index=-1):
    """Keyframe obj.<path> = value at time t (seconds). interp: None=smooth, 'CONSTANT', 'LINEAR'."""
    target = obj
    parts = path.split(".")
    for p in parts[:-1]:
        target = getattr(target, p)
    attr = parts[-1]
    if attr == "rotation_euler" and value is not None:
        value = tuple(math.radians(a) for a in value)
    if value is not None:
        if index >= 0:
            cur = list(getattr(target, attr))
            cur[index] = value
            value = cur
        setattr(target, attr, value)
    fr = f(t)
    target.keyframe_insert(attr, frame=fr, index=index)
    if interp and isinstance(target, bpy.types.ID):
        for fc in _fcurves(target):
            if fc.data_path == attr:
                for kp in fc.keyframe_points:
                    if abs(kp.co.x - fr) < 0.5:
                        kp.interpolation = interp


def ease_keys(obj, path, keys, interp=None):
    """keys: [(t, value), ...]"""
    for t, v in keys:
        key(obj, path, t, v, interp)


# ---------------------------------------------------------------- toy characters
EYES = {  # upper-lid angle (deg): - opens, + closes
    "wide": -110, "open": -75, "half": -10, "smug": 8, "squint": 25, "closed": 92,
}
BROWS = {  # (roll deg for the left brow, height offset)
    "flat": (0, 0.0), "up": (-6, 0.035), "angry": (22, -0.02), "sad": (-20, 0.015),
    "sly": (12, 0.0),
}


class Toy:
    """A toy-figure character: big round head, capsule body, peg limbs, expressive face.

    Built at `loc`, facing -Y (toward the camera) rotated by `yaw` degrees.
    Proportions are given by `height` (feet to top of head).
    """

    def __init__(self, name, loc=(0, 0, 0), yaw=0.0, height=1.3, head=0.36, skin=SKIN,
                 body=(60, 110, 170), body_w=1.0, legs=INK, feet=INK, arms=None,
                 hands=None, eye_size=1.0, pupil=INK, brow=INK, nose=None, body_mat=None,
                 seed=0):
        self.name = name
        self.rng = random.Random(seed or hash(name) % 1000)
        self.root = empty(name, loc, (0, 0, yaw))
        self.height = height
        self.R = head
        leg_len = max(0.18, height * 0.24)
        body_h = max(0.25, height - leg_len - head * 1.75)
        self.body_r = head * 0.62 * body_w
        skin_m = mat(skin, 0.5, coat=0.05)
        self.skin = skin_m
        body_m = body_mat or mat(body, 0.5)
        limb_m = mat(legs, 0.45)

        # hips -> body -> neck -> head
        self.hips = empty(name + ".hips", (0, 0, leg_len), parent=self.root)
        self.body = capsule(self.body_r, max(0.01, body_h - 2 * self.body_r * 0.8),
                            (0, 0, body_h / 2), body_m, parent=self.hips,
                            scale=(1, 0.86, 1), name=name + ".body")
        self.neck = empty(name + ".neck", (0, 0, body_h * 0.92), parent=self.hips)
        self.head_pivot = empty(name + ".headpivot", (0, 0, 0), parent=self.neck)
        self.head = sphere(head, (0, 0, head * 0.86), skin_m, parent=self.head_pivot,
                           name=name + ".head", scale=(1, 0.95, 0.97), seg=40, rings=20)
        self.face = empty(name + ".face", (0, 0, head * 0.86), parent=self.head_pivot)
        self.top = empty(name + ".top", (0, 0, head * 1.9), parent=self.head_pivot)

        # legs + feet
        self.legs = []
        lw = self.body_r * 0.42
        for sx in (-1, 1):
            hip = empty(f"{name}.leg{sx}", (sx * lw, 0, 0.02), parent=self.hips)
            cyl(0.028 * max(1, height / 1.4), leg_len, (0, 0, -leg_len / 2), limb_m, parent=hip,
                seg=16)
            sphere(0.055 * max(1, height / 1.4), (0, -0.035, -leg_len + 0.02), mat(feet, 0.35),
                   parent=hip, scale=(0.9, 1.35, 0.6))
            self.legs.append(hip)

        # arms
        self.arms = []
        arm_len = body_h * 0.62
        am = mat(arms or legs, 0.45)
        hm = mat(hands or skin, 0.5)
        for sx in (-1, 1):
            sh = empty(f"{name}.arm{sx}", (sx * self.body_r * 0.98, 0, body_h * 0.74),
                       (0, sx * 12, 0), parent=self.hips)
            cyl(0.024 * max(1, height / 1.4), arm_len, (0, 0, -arm_len / 2), am, parent=sh,
                seg=12)
            sphere(0.045 * max(1, height / 1.4), (0, 0, -arm_len), hm, parent=sh)
            self.arms.append(sh)
        self.hand_tips = [empty(f"{name}.hand{i}", (0, 0, -arm_len), parent=a)
                          for i, a in enumerate(self.arms)]

        # face: eyes (white, pupil, highlight), upper lids, brows, mouth shapes
        R = head
        es = 0.24 * R * eye_size
        self.eyes, self.lids, self.pupils, self.brows = [], [], [], []
        white = mat(WHITE, 0.25, coat=0.4)
        pm = mat(pupil, 0.2, coat=0.6)
        lid_m = mat(tuple(max(0, c - 14) for c in skin), 0.5)
        brow_m = mat(brow, 0.5)
        for sx in (-1, 1):
            d = Vector((sx * 0.36, -0.88, 0.16)).normalized() * (R * 0.93)
            eye = empty(f"{name}.eye{sx}", tuple(d), parent=self.face)
            sphere(es, (0, 0, 0), white, parent=eye, scale=(1, 0.75, 1.12))
            look = empty(f"{name}.look{sx}", parent=eye)
            sphere(es * 0.52, (0, -es * 0.62, 0), pm, parent=look, scale=(1, 0.6, 1.1))
            sphere(es * 0.15, (es * 0.18, -es * 0.98, es * 0.26), mat(WHITE, 0.1, emit=0.6),
                   parent=look)
            lid = empty(f"{name}.lid{sx}", parent=eye, rot=(EYES["open"], 0, 0))
            sphere(es * 1.1, (0, 0, 0), lid_m, parent=lid, hemi=True, scale=(1, 0.8, 1.14))
            bpos = Vector((sx * 0.38, -0.82, 0.5)).normalized() * (R * 0.98)
            bw = empty(f"{name}.brow{sx}", tuple(bpos), parent=self.face)
            capsule(0.022 * R / 0.36, es * 1.25, (0, 0, 0), brow_m, parent=bw,
                    rot=(0, 90, 0), scale=(1, 0.7, 1))
            self.eyes.append(eye)
            self.lids.append(lid)
            self.pupils.append(look)
            self.brows.append((bw, sx, tuple(bpos)))
        if nose:
            sphere(R * 0.13, tuple(Vector((0, -1, -0.1)).normalized() * R * 1.0),
                   mat(nose, 0.4), parent=self.face, scale=(1.1, 0.9, 0.9))
        mouth_at = Vector((0, -0.9, -0.42)).normalized() * (R * 0.95)
        self.mouth_root = empty(name + ".mouth", tuple(mouth_at), parent=self.face,
                                rot=(-24, 0, 0))
        dark = mat((70, 30, 30), 0.5)
        self.mouths = {
            "smile": torus(R * 0.2, R * 0.035, (0, 0, 0.02 * R), mat(INK, 0.5),
                           parent=self.mouth_root, arc=150, rot=(90, 0, 0)),
            "grin": sphere(R * 0.24, (0, 0.01, 0), dark, parent=self.mouth_root, hemi=True,
                           rot=(180, 0, 0), scale=(1, 0.4, 0.75)),
            "open": sphere(R * 0.13, (0, 0, -0.03 * R), dark, parent=self.mouth_root,
                           scale=(1, 0.5, 1.2)),
            "flat": capsule(R * 0.03, R * 0.22, (0, 0, 0), mat(INK, 0.5), parent=self.mouth_root,
                            rot=(0, 90, 0)),
            "frown": torus(R * 0.16, R * 0.032, (0, 0, -0.1 * R), mat(INK, 0.5),
                           parent=self.mouth_root, arc=140, rot=(-90, 0, 0)),
        }
        self.state = dict(eyes="open", brows="flat", mouth="smile")
        self._set_mouth(0, "smile")

    # ---- face
    def _set_mouth(self, t, m):
        for k, o in self.mouths.items():
            key(o, "scale", t, (1, 1, 1) if k == m else (0, 0, 0), "CONSTANT")

    def expr(self, t, eyes=None, brows=None, mouth=None, blend=0.12):
        """Change expression at time t. eyes: wide/open/half/smug/squint/closed;
        brows: flat/up/angry/sad/sly; mouth: smile/grin/open/flat/frown."""
        if eyes:
            prev = EYES[self.state["eyes"]]
            for lid in self.lids:
                key(lid, "rotation_euler", max(0, t - blend), (prev, 0, 0))
                key(lid, "rotation_euler", t, (EYES[eyes], 0, 0))
            self.state["eyes"] = eyes
        if brows:
            pr, ph = BROWS[self.state["brows"]]
            r, h = BROWS[brows]
            for bw, sx, base in self.brows:
                key(bw, "rotation_euler", max(0, t - blend), (0, sx * pr, 0))
                key(bw, "location", max(0, t - blend), (base[0], base[1], base[2] + ph))
                key(bw, "rotation_euler", t, (0, sx * r, 0))
                key(bw, "location", t, (base[0], base[1], base[2] + h))
            self.state["brows"] = brows
        if mouth:
            self._set_mouth(t, mouth)
            self.state["mouth"] = mouth

    def blink(self, t):
        cur = EYES[self.state["eyes"]]
        for lid in self.lids:
            key(lid, "rotation_euler", t, (cur, 0, 0))
            key(lid, "rotation_euler", t + 0.07, (EYES["closed"], 0, 0))
            key(lid, "rotation_euler", t + 0.16, (cur, 0, 0))

    def look(self, t, yaw=0.0, pitch=0.0, hold=None):
        """Point the pupils: yaw + = viewer's right, pitch + = up (degrees)."""
        for p in self.pupils:
            if hold is not None:
                key(p, "rotation_euler", t - hold, None)
            key(p, "rotation_euler", t, (pitch, 0, -yaw))

    def talk(self, t0, t1, rate=7.0):
        """Flap the mouth between open and the current shape."""
        base = self.state["mouth"]
        t, i = t0, 0
        while t < t1:
            self._set_mouth(t, "open" if i % 2 == 0 else base)
            t += (1 / rate) * self.rng.uniform(0.7, 1.3)
            i += 1
        self._set_mouth(t1, base)

    # ---- body
    def head_turn(self, t, yaw=0.0, tilt=0.0, nod=0.0, dur=0.25):
        key(self.head_pivot, "rotation_euler", max(0, t - dur), None)
        key(self.head_pivot, "rotation_euler", t, (nod, tilt, yaw))

    def arm(self, t, side, raise_deg=0.0, forward=0.0, dur=0.25):
        """side: 0=character's right (viewer's left), 1=left. raise_deg lifts sideways."""
        a = self.arms[side]
        sx = -1 if side == 0 else 1
        key(a, "rotation_euler", max(0, t - dur), None)
        key(a, "rotation_euler", t, (forward, sx * (12 + raise_deg), 0))

    def wave(self, t0, t1, side=1):
        sx = -1 if side == 0 else 1
        a = self.arms[side]
        key(a, "rotation_euler", t0, (0, sx * 12, 0))
        t, i = t0 + 0.2, 0
        while t < t1 - 0.15:
            key(a, "rotation_euler", t, (0, sx * (150 + (15 if i % 2 else -15)), 0))
            t += 0.18
            i += 1
        key(a, "rotation_euler", t1, (0, sx * 12, 0))

    def at(self, t, loc=None, yaw=None):
        if loc is not None:
            key(self.root, "location", t, loc)
        if yaw is not None:
            key(self.root, "rotation_euler", t, (0, 0, yaw))

    def walk(self, t0, t1, to, yaw=None, step=0.16, bounce=0.035):
        """Walk from the current position to `to` between t0 and t1 with leg swing + bob."""
        key(self.root, "location", t0, None)
        if yaw is not None:
            key(self.root, "rotation_euler", t0, (0, 0, yaw))
        key(self.root, "location", t1, to, "LINEAR")
        n = max(2, int((t1 - t0) / step))
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            s = 1 if i % 2 else -1
            if i == n:
                s = 0
            key(self.legs[0], "rotation_euler", t, (28 * s, 0, 0))
            key(self.legs[1], "rotation_euler", t, (-28 * s, 0, 0))
            key(self.arms[0], "rotation_euler", t, (-22 * s, -12, 0))
            key(self.arms[1], "rotation_euler", t, (22 * s, 12, 0))
            key(self.hips, "location", t, (0, 0, self.hips.location.z + (bounce if i % 2 else 0)))

    def hop(self, t, h=0.25, dur=0.4):
        z = self.root.location.z
        key(self.root, "location", t, None)
        key(self.root, "location", t + dur / 2, (*self.root.location[:2], z + h))
        key(self.root, "location", t + dur, (*self.root.location[:2], z))
        key(self.body, "scale", t, (1.1, 0.86 * 1.1, 0.88))
        key(self.body, "scale", t + 0.1, (0.92, 0.86 * 0.92, 1.12))
        key(self.body, "scale", t + dur, (1, 0.86, 1))

    def shake(self, t0, t1, amount=6.0):
        """Head shaking 'no' / nervous jitter."""
        t, i = t0, 0
        while t < t1:
            key(self.head_pivot, "rotation_euler", t, (0, 0, amount * (1 if i % 2 else -1)))
            t += 0.1
            i += 1
        key(self.head_pivot, "rotation_euler", t1, (0, 0, 0))

    def idle(self, t0, t1, blinks=True):
        """Breathing bob + occasional blinks so nobody looks frozen."""
        z = self.hips.location.z
        t = t0
        while t < t1:
            key(self.hips, "location", t, (0, 0, z))
            key(self.hips, "location", min(t1, t + 0.9), (0, 0, z + 0.012))
            t += 1.8
        if blinks:
            t = t0 + self.rng.uniform(0.4, 1.4)
            while t < t1 - 0.2:
                self.blink(t)
                t += self.rng.uniform(1.8, 3.2)


# ---------------------------------------------------------------- cast accessories
def hat_beanie(toy, color=RED):
    R = toy.R
    m = mat(color, 0.8)
    sphere(R * 1.04, (0, 0, R * 1.2), m, parent=toy.head_pivot, hemi=True,
           scale=(1, 0.98, 0.9))
    torus(R * 0.97, R * 0.11, (0, 0, R * 1.26), m, parent=toy.head_pivot, scale=(1, 0.97, 1))
    sphere(R * 0.17, (0, 0, R * 2.15), mat(WHITE, 0.9), parent=toy.head_pivot)


def hat_bowler(toy, color=INK):
    R = toy.R
    m = mat(color, 0.35)
    sphere(R * 0.8, (0, 0, R * 1.5), m, parent=toy.head_pivot, hemi=True,
           scale=(1, 1, 0.95))
    cyl(R * 1.25, R * 0.06, (0, 0, R * 1.5), m, parent=toy.head_pivot)


def hat_top(toy, color=INK, band=RED):
    R = toy.R
    m = mat(color, 0.35)
    cyl(R * 1.15, R * 0.05, (0, 0, R * 1.6), m, parent=toy.head_pivot)
    cyl(R * 0.62, R * 0.9, (0, 0, R * 2.05), m, parent=toy.head_pivot)
    cyl(R * 0.63, R * 0.14, (0, 0, R * 1.72), mat(band, 0.5), parent=toy.head_pivot)


def hair_sidepart(toy, color=(60, 40, 30)):
    R = toy.R
    m = mat(color, 0.4, coat=0.5)
    sphere(R * 1.04, (0, 0.04, R * 1.0), m, parent=toy.head_pivot, hemi=True,
           scale=(1.01, 1.0, 0.86), rot=(-28, 0, 0))
    sphere(R * 0.32, (R * 0.4, -R * 0.55, R * 1.6), m, parent=toy.head_pivot,
           scale=(1.7, 0.9, 0.55), rot=(0, -18, 0))


def hair_bun(toy, color=(170, 80, 40)):
    R = toy.R
    m = mat(color, 0.45)
    sphere(R * 1.04, (0, 0.04, R * 1.0), m, parent=toy.head_pivot, hemi=True,
           scale=(1.01, 1, 0.86), rot=(-28, 0, 0))
    for sx in (-1, 1):
        sphere(R * 0.33, (sx * R * 0.72, 0.05, R * 1.55), m, parent=toy.head_pivot)


def mustache(toy, color=INK, size=1.0):
    R = toy.R * size
    m = mat(color, 0.5)
    base = Vector((0, -0.95, -0.22)).normalized() * toy.R * 0.98
    for sx in (-1, 1):
        sphere(R * 0.16, (base.x + sx * R * 0.2, base.y - 0.01, base.z), m, parent=toy.face,
               scale=(1.8, 0.7, 0.7), rot=(0, sx * 18, 0))
        sphere(R * 0.09, (base.x + sx * R * 0.5, base.y + 0.03, base.z + R * 0.12), m,
               parent=toy.face, scale=(1.2, 0.8, 0.8))


def glasses(toy, color=INK):
    m = mat(color, 0.3, metal=0.5)
    for eye in toy.eyes:
        torus(toy.R * 0.2, toy.R * 0.025, (0, -toy.R * 0.12, 0), m, parent=eye, rot=(90, 0, 0))


def waistcoat_chain(toy):
    b = toy.body_r
    torus(b * 0.5, 0.012, (0, -b * 0.8, toy.body.location.z - 0.02), mat(GOLD, 0.2, metal=1.0),
          parent=toy.hips, arc=170, rot=(90, 0, 0))
    sphere(0.035, (b * 0.45, -b * 0.84, toy.body.location.z - 0.02), mat(GOLD, 0.2, metal=1.0),
           parent=toy.hips)


def bare_feet(toy):
    """Gus's running gag: big bare toes."""
    for leg in toy.legs:
        for ch in leg.children:
            if ch.name.startswith("sphere"):
                ch.data.materials[0] = toy.skin
        for i in range(3):
            sphere(0.018, (-0.03 + i * 0.03, -0.1, -toy.hips.location.z + 0.03), toy.skin,
                   parent=leg)


# ---------------------------------------------------------------- the cast
def boss(loc=(0, 0, 0), yaw=0.0):
    """The Boss ("you"): short round banker, emerald waistcoat, gold chain, side-part, sly."""
    t = Toy("boss", loc, yaw, height=1.15, head=0.36, body=EMERALD, body_w=1.35,
            legs=(50, 46, 60), feet=INK, arms=(236, 232, 222), nose=(232, 170, 140))
    hair_sidepart(t, (54, 36, 26))
    waistcoat_chain(t)
    t.expr(0, eyes="smug", brows="sly", mouth="smile")
    return t


def gus(loc=(0, 0, 0), yaw=0.0):
    """Gus, the Fall Guy: huge gentle lumberjack, red beanie, plaid shirt, always barefoot."""
    t = Toy("gus", loc, yaw, height=1.75, head=0.4, skin=SKIN_TAN,
            body_mat=mat_plaid(PLAID, (230, 120, 90), 9), body_w=1.55, legs=(54, 70, 110),
            arms=PLAID, nose=(190, 120, 90))
    hat_beanie(t, RED)
    bare_feet(t)
    t.expr(0, eyes="open", brows="up", mouth="grin")
    return t


def mo(loc=(0, 0, 0), yaw=0.0):
    """Mo, the Middleman: skinny neighbour banker, giant handlebar mustache, purple coat."""
    t = Toy("mo", loc, yaw, height=1.45, head=0.32, skin=SKIN, body=PURPLE, body_w=0.9,
            legs=INK, arms=PURPLE, nose=(226, 160, 130))
    mustache(t, INK, 1.25)
    hat_top(t, INK, PURPLE)
    t.expr(0, eyes="half", brows="sly", mouth="flat")
    return t


def pike(loc=(0, 0, 0), yaw=0.0):
    """Inspector Pike, the Authority: very tall and thin, long grey coat, huge magnifier."""
    t = Toy("pike", loc, yaw, height=2.0, head=0.3, skin=SKIN, body=GREY, body_w=0.85,
            legs=(70, 72, 80), arms=GREY)
    hat_bowler(t, (60, 62, 70))
    glasses(t)
    t.expr(0, eyes="squint", brows="angry", mouth="flat")
    return t


def townsfolk(name, loc=(0, 0, 0), yaw=0.0, seed=1):
    rng = random.Random(seed)
    skin = rng.choice([SKIN, SKIN_TAN, SKIN_DARK, (226, 176, 130)])
    body = rng.choice([(70, 140, 120), (210, 120, 60), (90, 110, 190), (200, 170, 60),
                       (170, 80, 110)])
    t = Toy(name, loc, yaw, height=rng.uniform(1.0, 1.35), head=rng.uniform(0.3, 0.36),
            skin=skin, body=body, body_w=rng.uniform(0.9, 1.2), legs=INK, seed=seed)
    rng.choice([hair_bun, hair_sidepart, lambda x, c: None])(t, rng.choice(
        [(40, 30, 26), (150, 80, 40), (200, 160, 80), (20, 20, 20)]))
    return t


# ---------------------------------------------------------------- sets
def sky(color=SKY, strength=1.0, horizon=None):
    w = bpy.context.scene.world
    nt = w.node_tree
    bg = nt.nodes["Background"]
    if horizon is None:
        bg.inputs["Color"].default_value = (*lin(color), 1)
    else:  # vertical gradient sky
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*lin(horizon), 1)
        ramp.color_ramp.elements[1].position = 0.5
        ramp.color_ramp.elements[1].color = (*lin(color), 1)
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def sun(rot=(50, 10, -35), energy=3.2, color=(255, 246, 228), angle=4.0):
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = energy
    ld.color = lin(color)
    ld.angle = math.radians(angle)
    o = bpy.data.objects.new("sun", ld)
    return _link(o, rot=rot)


def point_light(loc, energy=60, color=(255, 200, 140), radius=0.2):
    ld = bpy.data.lights.new("pt", "POINT")
    ld.energy = energy
    ld.color = lin(color)
    ld.shadow_soft_size = radius
    return _link(bpy.data.objects.new("pt", ld), loc=loc)


def area_light(loc, rot, energy=200, size=3.0, color=(255, 255, 255)):
    ld = bpy.data.lights.new("area", "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = lin(color)
    return _link(bpy.data.objects.new("area", ld), loc=loc, rot=rot)


def light_day():
    sky((150, 200, 238), 0.55, horizon=(232, 236, 236))
    sun((42, 6, -38), 4.6, (255, 236, 205), 3)
    area_light((0, -9, 6), (60, 0, 0), 500, 8, (210, 225, 255))


def light_night():
    sky((40, 30, 80), 0.6, horizon=(80, 60, 120))
    sun((60, 0, 40), 0.9, (150, 150, 255), 6)
    area_light((0, -9, 6), (60, 0, 0), 300, 8, (150, 120, 230))


def light_amber():
    sky((60, 40, 30), 0.35)
    point_light((-1.5, -1.5, 2.6), 260, (255, 180, 100), 0.4)
    area_light((2, -4, 3), (60, 0, 30), 160, 3, (255, 210, 160))


def ground(size=60, material=None, z=0.0):
    return plane((size, size), (0, 0, z), material or mat_cobble())


def window(parent, x, z, shutter, w=0.62, h=0.9, flowers=True, lit=False):
    frame = mat(WHITE, 0.5)
    glass = mat((40, 60, 90), 0.15, emit=1.2 if lit else 0.0) if not lit else \
        mat((255, 200, 120), 0.3, emit=2.5)
    box((w + 0.12, 0.08, h + 0.12), (x, -0.22, z), frame, 0.02, parent)
    box((w, 0.08, h), (x, -0.25, z), glass, 0.0, parent)
    box((0.03, 0.09, h), (x, -0.27, z), frame, 0.0, parent)
    box((w, 0.09, 0.03), (x, -0.27, z + h * 0.15), frame, 0.0, parent)
    sm = mat(shutter, 0.55)
    for sx in (-1, 1):
        box((w * 0.48, 0.05, h + 0.06), (x + sx * (w * 0.76 + 0.04), -0.23, z), sm, 0.015, parent)
    if flowers:
        box((w + 0.2, 0.2, 0.16), (x, -0.33, z - h / 2 - 0.1), mat(WOOD_D, 0.6), 0.02, parent)
        greens = mat((60, 130, 60), 0.7)
        for i in range(5):
            fx = x - w / 2 + 0.04 + i * (w - 0.08) / 4
            sphere(0.07, (fx, -0.33, z - h / 2 + 0.0), greens, parent)
            sphere(0.04, (fx + 0.02, -0.4, z - h / 2 + 0.04),
                   mat(random.choice([(230, 70, 80), (250, 200, 60), (240, 140, 180)]), 0.6),
                   parent)


def facade(loc=(0, 8, 0), yaw=0.0, width=4.0, floors=3, color=None, shutter=None, sign=None,
           shop=None, awning=None, door=True, seed=0, lit=False, number=None):
    """A pastel town-house front. sign: text on a board over the ground floor.
    shop: label painted on a big shop window. awning: (c1, c2) stripe colours."""
    rng = random.Random(seed)
    color = color or rng.choice(PASTELS)
    shutter = shutter or rng.choice(SHUTTERS)
    G, fh = 2.95, 1.35  # ground-floor height, upper-floor height
    H = G + (floors - 1) * fh + 0.25
    root = empty("facade", loc, (0, 0, yaw))
    box((width, 0.4, H), (0, 0, H / 2), mat(color, 0.85), 0.02, root)
    box((width + 0.16, 0.6, 0.18), (0, -0.05, H + 0.05), mat(tuple(c - 30 for c in color), 0.8),
        0.03, root)
    box((width + 0.04, 0.46, 0.45), (0, 0, 0.22), mat(tuple(c - 40 for c in color), 0.85), 0.02,
        root)
    box((width + 0.06, 0.48, 0.1), (0, 0, G - 0.05), mat(tuple(c - 25 for c in color), 0.8),
        0.02, root)
    nwin = max(1, int(width / 1.3))
    for fl in range(1, floors):
        z = G + (fl - 1) * fh + 0.72
        for i in range(nwin):
            x = -width / 2 + width * (i + 0.5) / nwin
            window(root, x, z, shutter, lit=lit and rng.random() < 0.6)
    if door:
        dx = width / 2 - 0.75 if shop else 0
        box((0.85, 0.12, 1.6), (dx, -0.21, 0.45 + 0.8), mat(WOOD_D, 0.5), 0.03, root)
        sphere(0.04, (dx + 0.28, -0.3, 1.25), mat(GOLD, 0.2, metal=1), root)
        box((1.05, 0.14, 0.12), (dx, -0.22, 0.45 + 1.66), mat(WHITE, 0.5), 0.02, root)
    if shop:
        sw = width - 1.9 if door else width - 0.6
        sx = -width / 2 + 0.3 + sw / 2
        box((sw + 0.12, 0.1, 1.3), (sx, -0.22, 1.25), mat(WHITE, 0.5), 0.02, root)
        box((sw, 0.1, 1.15), (sx, -0.25, 1.25), mat((70, 90, 110), 0.1,
                                                    emit=1.5 if lit else 0.0), 0.0, root)
        text(shop, (sx, -0.32, 1.5), 0.2, mat(WHITE, 0.5), parent=root, extrude=0.002,
             fnt="Montserrat-Black")
    if awning:
        am = mat_stripes(awning[0], awning[1], 5.0, "X", 0.7, "awning")
        box((width - 0.3, 0.9, 0.06), (0, -0.62, 2.28), am, 0.02, root, rot=(-20, 0, 0))
    if sign:
        sw = min(width - 0.3, 0.5 + 0.26 * len(sign))
        box((sw + 0.1, 0.08, 0.6), (0, -0.3, 2.62), mat(RED, 0.6), 0.03, root)
        box((sw, 0.08, 0.5), (0, -0.36, 2.62), mat(CREAM, 0.6), 0.03, root)
        text(sign, (0, -0.42, 2.62), 0.32, mat(INK, 0.5), parent=root, extrude=0.004)
    if number:
        text(str(number), (width / 2 - 0.3, -0.22, H - 0.4), 0.18,
             mat(tuple(c - 50 for c in color)), parent=root, extrude=0.002, fnt="Montserrat-Black")
    return root


def street(signs=None, lit=False, seed=3, depth=7.5, side=True):
    """A town square: a row of facades behind (y=depth) and two side rows."""
    signs = signs or {}
    rng = random.Random(seed)
    xs = [-6.2, -2.1, 2.0, 6.1]
    for i, x in enumerate(xs):
        facade((x, depth, 0), 0, 4.0, rng.choice([3, 3, 4]), seed=seed * 10 + i,
               sign=signs.get(i), lit=lit,
               awning=[(RED, WHITE), None, ((36, 120, 80), WHITE), None][i % 4], number=10 + i)
    if side:
        for i, y in enumerate([4.5, 0.5, -3.5]):
            facade((-8.0, y, 0), -90, 4.0, 3, seed=seed * 20 + i, lit=lit, door=i != 1)
            facade((8.0, y, 0), 90, 4.0, 3, seed=seed * 30 + i, lit=lit, door=i != 2)
    bunting((-6, depth - 1.5, 4.6), (6, depth - 1.5, 4.6), sag=0.7)
    bunting((-7, depth - 4, 4.9), (7, depth - 3.2, 4.8), sag=0.9, seed=2)


def bunting(a, b, sag=0.6, n=18, seed=1):
    rng = random.Random(seed)
    a, b = Vector(a), Vector(b)
    cols = [RED, (250, 200, 50), (40, 120, 200), (40, 150, 90), WHITE]
    line = mat((60, 50, 40), 0.6)
    for i in range(n):
        u = (i + 0.5) / n
        p = a.lerp(b, u)
        p.z -= sag * 4 * u * (1 - u)
        cone(0.14, 0.32, (p.x, p.y, p.z - 0.16), mat(cols[i % len(cols)], 0.7), rot=(180, 0, 0))
    for i in range(n * 2):
        u0, u1 = i / (n * 2), (i + 1) / (n * 2)
        p0, p1 = a.lerp(b, u0), a.lerp(b, u1)
        p0.z -= sag * 4 * u0 * (1 - u0)
        p1.z -= sag * 4 * u1 * (1 - u1)
        d = p1 - p0
        c = (p0 + p1) / 2
        o = cyl(0.008, d.length, tuple(c), line, seg=6)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = d.to_track_quat("Z", "Y")


def plant_pot(loc, s=1.0):
    root = empty("pot", loc)
    cyl(0.22 * s, 0.38 * s, (0, 0, 0.19 * s), mat((200, 110, 70), 0.7), root, r2=0.17 * s)
    sphere(0.32 * s, (0, 0, 0.6 * s), mat((60, 140, 70), 0.75), root)
    return root


def lamp_post(loc, lit=False):
    root = empty("lamp", loc)
    m = mat((40, 44, 50), 0.4, metal=0.6)
    cyl(0.06, 3.0, (0, 0, 1.5), m, root)
    box((0.3, 0.3, 0.4), (0, 0, 3.2), mat((255, 220, 150), 0.3, emit=4 if lit else 0.3), 0.03,
        root)
    cone(0.26, 0.2, (0, 0, 3.5), m, root)
    if lit:
        point_light((loc[0], loc[1], loc[2] + 3.1), 120, (255, 190, 110), 0.15)
    return root


def hay_bale(loc, rot=0):
    return box((0.9, 0.55, 0.5), (loc[0], loc[1], loc[2] + 0.25), mat((222, 186, 96), 0.9), 0.08,
               rot=(0, 0, rot))


def barrel(loc, s=1.0):
    root = empty("barrel", loc)
    sphere(0.36 * s, (0, 0, 0.45 * s), mat(WOOD, 0.6), root, scale=(1, 1, 1.35))
    for z in (0.18, 0.72):
        torus(0.34 * s, 0.025 * s, (0, 0, z * s), mat((70, 70, 76), 0.4, metal=0.7), root)
    return root


def crate(loc, s=1.0, rot=0):
    return box((0.6 * s, 0.6 * s, 0.6 * s), (loc[0], loc[1], loc[2] + 0.3 * s),
               mat(WOOD_L, 0.7), 0.04, rot=(0, 0, rot))


def board(text_str, loc, w=1.6, h=1.0, yaw=0.0, size=0.26, legs=True, color=(36, 60, 48),
          ink=WHITE, fnt="Montserrat-ExtraBold"):
    """Chalkboard / sign board on an easel with readable text."""
    root = empty("board", loc, (0, 0, yaw))
    zc = 1.35 if legs else 0
    box((w + 0.12, 0.08, h + 0.12), (0, 0.02, zc), mat(WOOD, 0.6), 0.02, root)
    box((w, 0.08, h), (0, -0.01, zc), mat(color, 0.9), 0.0, root)
    txt = text(text_str, (0, -0.06, zc), size, mat(ink, 0.8, emit=0.15), parent=root,
               extrude=0.0, fnt=fnt)
    if legs:
        for sx in (-1, 1):
            o = cyl(0.03, 2.0, (sx * w * 0.38, 0.1, 0.95), mat(WOOD_D, 0.6), root)
            o.rotation_euler = (math.radians(-6), math.radians(sx * -8), 0)
    root["text"] = txt.name
    return root


def banknote(loc, rot=(0, 0, 0), s=1.0, parent=None):
    root = empty("note", loc, rot, parent)
    box((0.62 * s, 0.3 * s, 0.012 * s), (0, 0, 0), mat(MONEY, 0.7), 0.004, root)
    box((0.5 * s, 0.2 * s, 0.004 * s), (0, 0, 0.007 * s), mat(MONEY_D, 0.7), 0.0, root)
    text("$", (0, 0, 0.011 * s), 0.14 * s, mat(MONEY, 0.6), parent=root, rot=(0, 0, 0), extrude=0.0,
         fnt="Montserrat-Black")
    return root


def cash_stack(loc, n=10, s=1.0, parent=None, yaw=0.0, grow=None):
    """A stack of n cash bundles. grow=(t0, t1): bundles pop on one by one over that time."""
    root = empty("cash", loc, (0, 0, yaw), parent)
    rng = random.Random(n * 7 + int(loc[0] * 10))
    for i in range(n):
        b = empty("bundle", (rng.uniform(-0.02, 0.02) * s, rng.uniform(-0.02, 0.02) * s,
                             0.035 * s + i * 0.072 * s), (0, 0, rng.uniform(-5, 5)), root)
        box((0.62 * s, 0.3 * s, 0.07 * s), (0, 0, 0), mat(MONEY, 0.7), 0.01, b)
        box((0.1 * s, 0.31 * s, 0.072 * s), (0, 0, 0), mat((236, 228, 200), 0.6), 0.0, b)
        if grow:
            ta = grow[0] + (grow[1] - grow[0]) * i / max(1, n)
            key(b, "scale", 0, (0, 0, 0), "CONSTANT")
            key(b, "scale", ta, (1.25, 1.25, 1.25))
            key(b, "scale", ta + 0.08, (1, 1, 1))
    return root


def coin(loc, s=1.0, rot=(90, 0, 0), parent=None):
    return cyl(0.12 * s, 0.025 * s, loc, mat(GOLD, 0.25, metal=1.0), parent, rot)


def bread(loc, s=1.0, parent=None):
    return capsule(0.12 * s, 0.25 * s, loc, mat((200, 140, 70), 0.6), parent=parent,
                   rot=(0, 90, 0), scale=(1, 1.1, 0.85))


def price_tag(text_str, loc, s=1.0, yaw=0.0, parent=None):
    root = empty("tag", loc, (0, 0, yaw), parent)
    box((0.5 * s + 0.12 * len(text_str) * s, 0.03, 0.32 * s), (0, 0, 0), mat(WHITE, 0.6), 0.03,
        root)
    t = text(text_str, (0, -0.03, 0), 0.2 * s, mat(RED, 0.5), parent=root, extrude=0.0,
             fnt="Montserrat-Black")
    root["text"] = t.name
    return root


def printing_press(loc, yaw=0.0, s=1.0):
    root = empty("press", loc, (0, 0, yaw))
    iron = mat((60, 66, 74), 0.35, metal=0.7)
    box((1.0 * s, 0.7 * s, 0.6 * s), (0, 0, 0.3 * s), iron, 0.05, root)
    for sx in (-1, 1):
        box((0.12 * s, 0.12 * s, 1.0 * s), (sx * 0.4 * s, 0, 1.0 * s), iron, 0.03, root)
    box((1.0 * s, 0.3 * s, 0.14 * s), (0, 0, 1.5 * s), iron, 0.03, root)
    plate = box((0.7 * s, 0.5 * s, 0.1 * s), (0, 0, 0.9 * s), mat(GOLD, 0.3, metal=0.9), 0.02,
                root)
    cyl(0.04 * s, 0.7 * s, (0, 0, 1.2 * s), iron, root)
    wheel = torus(0.3 * s, 0.03 * s, (0.6 * s, 0, 1.0 * s), mat(RED, 0.5), root, rot=(0, 90, 0))
    root["plate"] = plate.name
    root["wheel"] = wheel.name
    return root


def wheelbarrow(loc, yaw=0.0, full=True):
    root = empty("barrow", loc, (0, 0, yaw))
    box((1.0, 0.7, 0.4), (0, 0, 0.55), mat((80, 120, 160), 0.5), 0.06, root)
    torus(0.2, 0.05, (0.55, 0, 0.22), mat(INK, 0.7), root, rot=(90, 0, 0))
    for sy in (-1, 1):
        cyl(0.025, 1.0, (-0.6, sy * 0.25, 0.5), mat(WOOD, 0.6), root, rot=(0, 75, 0))
    if full:
        for i in range(14):
            banknote((random.uniform(-0.35, 0.35), random.uniform(-0.25, 0.25),
                      0.75 + random.uniform(0, 0.25)),
                     (random.uniform(-25, 25), random.uniform(-25, 25), random.uniform(0, 180)),
                     0.8, root)
    return root


def chicken(loc, yaw=0.0, s=1.0):
    root = empty("chicken", loc, (0, 0, yaw))
    w = mat(WHITE, 0.6)
    sphere(0.22 * s, (0, 0, 0.3 * s), w, root, scale=(0.9, 1.1, 0.95))
    sphere(0.13 * s, (0, -0.16 * s, 0.52 * s), w, root)
    cone(0.04 * s, 0.1 * s, (0, -0.3 * s, 0.52 * s), mat(GOLD, 0.5), root, rot=(90, 0, 0))
    for sx in (-1, 1):
        sphere(0.025 * s, (sx * 0.07 * s, -0.25 * s, 0.56 * s), mat(INK, 0.2), root)
    sphere(0.06 * s, (0, -0.14 * s, 0.67 * s), mat(RED, 0.5), root, scale=(0.5, 1.2, 1))
    for sx in (-1, 1):
        cyl(0.012 * s, 0.14 * s, (sx * 0.07 * s, 0, 0.07 * s), mat(GOLD, 0.5), root)
    return root


def briefcase(loc, yaw=0.0, parent=None):
    root = empty("case", loc, (0, 0, yaw), parent)
    box((0.5, 0.14, 0.36), (0, 0, 0), mat((110, 60, 30), 0.4), 0.03, root)
    torus(0.07, 0.015, (0, 0, 0.2), mat(INK, 0.4), root, rot=(90, 0, 0), arc=180)
    return root


def counter(loc, w=2.4, yaw=0.0):
    root = empty("counter", loc, (0, 0, yaw))
    box((w, 0.7, 0.8), (0, 0, 0.4), mat(WOOD, 0.55), 0.04, root)
    box((w + 0.1, 0.8, 0.08), (0, 0, 0.82), mat(WOOD_L, 0.45), 0.02, root)
    return root


def room(wall=(46, 96, 70), floor=WOOD_L, w=8.0, d=6.0, h=4.0, pattern=True, wainscot=True):
    """Simple interior: back wall + floor + side walls, optional dotted wallpaper."""
    wm = mat_dots(wall, tuple(min(255, c + 22) for c in wall), 6.0) if pattern else mat(wall, 0.85)
    plane((w, d * 2), (0, 0, 0), mat_stripes(floor, tuple(c - 18 for c in floor), 2.5, "X", 0.6,
                                             "floor"))
    box((w, 0.2, h), (0, d / 2, h / 2), wm, 0.0)
    for sx in (-1, 1):
        box((0.2, d * 2, h), (sx * w / 2, 0, h / 2), wm, 0.0)
    if wainscot:
        box((w, 0.24, 1.0), (0, d / 2 - 0.04, 0.5), mat(WOOD_D, 0.6), 0.02)


def bookshelf(loc, yaw=0.0):
    root = empty("shelf", loc, (0, 0, yaw))
    box((1.6, 0.4, 2.2), (0, 0, 1.1), mat(WOOD_D, 0.6), 0.02, root)
    rng = random.Random(4)
    for row in range(4):
        x = -0.7
        while x < 0.65:
            bw = rng.uniform(0.06, 0.12)
            bh = rng.uniform(0.32, 0.42)
            box((bw, 0.3, bh), (x + bw / 2, -0.06, 0.15 + row * 0.52 + bh / 2),
                mat(rng.choice([RED, (40, 90, 150), (40, 120, 80), GOLD, CREAM]), 0.6), 0.01,
                root)
            x += bw + 0.01
    return root


# ---------------------------------------------------------------- camera
class Cam:
    """Camera on a rig with a look-at target, depth of field on the target, and handheld drift.

    at(t, pos, look_at) keys the camera position and target at time t (smooth easing between
    keys). Lens in mm (vertical frame), fstop controls background blur (lower = blurrier).
    """

    def __init__(self, lens=32, fstop=2.2, drift=0.02):
        cd = bpy.data.cameras.new("cam")
        cd.lens = lens
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 24
        cd.clip_start = 0.05
        cd.clip_end = 200
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        self.rig = empty("camrig")
        self.cam = _link(bpy.data.objects.new("cam", cd), parent=self.rig)
        self.target = empty("camtarget")
        cd.dof.focus_object = self.target
        c = self.cam.constraints.new("TRACK_TO")
        c.target = self.target
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        bpy.context.scene.camera = self.cam
        self.drift_amp = drift

    def at(self, t, pos, look_at, lens=None, fstop=None, interp=None):
        key(self.rig, "location", t, pos, interp)
        key(self.target, "location", t, look_at, interp)
        if lens is not None:
            key(self.cam.data, "lens", t, lens, interp)
        if fstop is not None:
            key(self.cam.data.dof, "aperture_fstop", t, fstop, interp)

    def roll(self, t, deg):
        key(self.cam, "rotation_euler", t, (0, 0, deg))

    def drift(self, t0, t1, amp=None, period=1.1, seed=7):
        """Gentle handheld float: small random offsets on the camera inside the rig."""
        amp = self.drift_amp if amp is None else amp
        rng = random.Random(seed)
        t = t0
        while t <= t1 + period:
            key(self.cam, "location", t, (rng.uniform(-amp, amp), rng.uniform(-amp, amp) * 0.4,
                                          rng.uniform(-amp, amp)))
            t += period * rng.uniform(0.8, 1.2)

    def shake(self, t, amp=0.06, dur=0.3):
        """A short impact shake."""
        n = 6
        for i in range(n + 1):
            a = amp * (1 - i / n)
            key(self.cam, "location", t + dur * i / n,
                (random.uniform(-a, a), 0, random.uniform(-a, a)))


def follow(obj, local=(0, 0, 0)):
    """World position of a point attached to obj (for anchors / camera targets)."""
    bpy.context.view_layer.update()
    return tuple(obj.matrix_world @ Vector(local))
