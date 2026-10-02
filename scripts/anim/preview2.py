"""
Blender: import a clip, put a weapon on Prop1 (dark) and one on Prop2 (red), render views.

    blender -b --factory-startup -P preview2.py -- <clip.x> <out_dir> <frames> [weapon1.x|none] [weapon2.x|none]
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
                                                 "TienInspectWeapon", "scripts", "anim")))
import x_import  # noqa: E402
import x_preview  # noqa: E402

VIEWS = {
    "front": ((0.0, -1.9, 0.75), (0.0, 0.0, 0.55)),
    "q34": ((-0.95, -1.55, 0.85), (0.0, 0.0, 0.55)),
    "top": ((0.0, -0.6, 2.2), (0.0, -0.2, 0.5)),
}
MACHETE = os.path.join(x_preview.MEDIA, "models_X/weapons/1handed/Machete.x")

argv = sys.argv[sys.argv.index("--") + 1:]
clip, out_dir, spec = argv[0], os.path.abspath(argv[1]), argv[2]
w1 = argv[3] if len(argv) > 3 else MACHETE
w2 = argv[4] if len(argv) > 4 else MACHETE
arm = x_import.load(clip)
scene = bpy.context.scene
os.makedirs(out_dir, exist_ok=True)
if w1 != "none":
    x_preview.attach_to_bone(x_preview.static_mesh(w1, "WeaponR"), arm, "Bip01_Prop1")
if w2 != "none":
    ob = x_preview.static_mesh(w2, "WeaponL")
    ob.data.materials[0].diffuse_color = (0.8, 0.15, 0.1, 1.0)
    x_preview.attach_to_bone(ob, arm, "Bip01_Prop2")
x_preview.setup_render(scene)
cams = {n: x_preview.camera("Cam_" + n, loc, tgt) for n, (loc, tgt) in VIEWS.items()}
if os.environ.get("PREVIEW_ORTHO"):
    for cam in cams.values():
        cam.data.ortho_scale = float(os.environ["PREVIEW_ORTHO"])
for frame in x_preview.parse_frames(spec, scene):
    scene.frame_set(frame)
    for n, cam in cams.items():
        scene.camera = cam
        scene.render.filepath = os.path.join(out_dir, "%s_%03d.png" % (n, frame))
        bpy.ops.render.render(write_still=True)
print("[render2] done", out_dir)
