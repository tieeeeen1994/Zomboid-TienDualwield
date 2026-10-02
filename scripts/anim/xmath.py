"""
Math shared by the dual wield clip tools: world poses of a Bob clip (numpy), the bind pose,
L/R bone name mirroring. Uses TienInspectWeapon's xanim.py (sibling repo) for .x reading/writing.
"""

import os
import sys

import numpy as np

PIPELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "TienInspectWeapon", "scripts", "anim")
sys.path.insert(0, os.path.normpath(PIPELINE))
import xanim  # noqa: E402

MEDIA = os.environ.get("PZ_MEDIA") or (
    "C:/Program Files (x86)/Steam/steamapps/common/ProjectZomboid/media" if os.name == "nt" else
    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/ProjectZomboid/"
                       "Project Zomboid.app/Contents/Java/media"))
BOB = os.path.join(MEDIA, "anims_X", "Bob")
S = np.diag([-1.0, 1.0, 1.0, 1.0])


def clip_path(name):
    for ext in (".X", ".x"):
        p = os.path.join(BOB, name + ext)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def ortho(m):
    m = np.array(m, dtype=float)
    u, _, vt = np.linalg.svd(m[:3, :3])
    r = u @ vt
    out = np.eye(4)
    out[:3, :3] = r
    out[:3, 3] = m[:3, 3]
    return out


def bones(xa):
    return [f for f in xa.frames if f.name != "Body"]


def rest(xa):
    skin = xa.mesh[2] if xa.mesh else {}
    out = {}
    for f in xa.frames:
        if f.name in skin:
            out[f.name] = ortho(np.linalg.inv(np.array(skin[f.name][2])))
        elif f.parent in out:
            out[f.name] = ortho(out[f.parent] @ np.array(f.matrix))
        else:
            out[f.name] = ortho(np.array(f.matrix))
    return out


def times(xa):
    ts = set()
    for tr in xa.tracks:
        ts.update(tr.S)
        ts.update(tr.R)
        ts.update(tr.T)
    return sorted(ts)


def local(xa, t):
    tracks = {tr.bone: tr for tr in xa.tracks}
    out = {}
    for f in bones(xa):
        tr = tracks.get(f.name)
        if tr:
            s = xanim.sample(tr, "S", t) or [1, 1, 1]
            q = xanim.sample(tr, "R", t) or (1, 0, 0, 0)
            p = xanim.sample(tr, "T", t) or [0, 0, 0]
            out[f.name] = np.array(xanim.srt_to_mat4(s, q, p))
        else:
            out[f.name] = np.array(f.matrix)
    return out


def world_of(xa, loc):
    out = {}
    for f in bones(xa):
        out[f.name] = out[f.parent] @ loc[f.name] if f.parent in out else loc[f.name]
    return out


def world(xa, t):
    return world_of(xa, local(xa, t))


def mirror_name(n):
    if "_L_" in n or n.endswith("_L"):
        return n.replace("_L_", "_R_") if "_L_" in n else n[:-2] + "_R"
    if "_R_" in n or n.endswith("_R"):
        return n.replace("_R_", "_L_") if "_R_" in n else n[:-2] + "_L"
    if n == "Bip01_Prop1":
        return "Bip01_Prop2"
    if n == "Bip01_Prop2":
        return "Bip01_Prop1"
    return n


def angle(r):
    c = (np.trace(r[:3, :3]) - 1) / 2
    return np.degrees(np.arccos(np.clip(c, -1, 1)))
