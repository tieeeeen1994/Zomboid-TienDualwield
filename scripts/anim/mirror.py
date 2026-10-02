"""
Mirror a vanilla Bob clip left <-> right (prototype).

    python mirror.py <ClipName> <out.x> [--prop2 mirror|vanilla]

World pose W'_b = S W_m(b) S K_b, S = reflection across file X (the character's left/right),
K_b = (S B_m(b) S)^-1 B_b from the bind pose B, so the bind pose maps to itself. Props have
no handedness convention: Prop1 <-> Prop2 use K = I, which keeps the long axis and the edge.
--prop2 vanilla keeps Prop2 at the idle's left grip instead of the mirrored right grip.
"""

import sys

import numpy as np

import xmath  # noqa: F401  (puts the TienInspectWeapon pipeline on sys.path)
import xanim
from xmath import S, bones, clip_path, mirror_name, ortho, rest, times, world


def mirror_clip(name, out, prop2="mirror"):
    src = clip_path(name)
    xa = xanim.read(src, with_mesh=True)
    B = rest(xa)
    frames = bones(xa)
    parent = {f.name: f.parent for f in frames}
    K = {}
    for f in frames:
        m = mirror_name(f.name)
        if "Prop" in f.name or f.name not in B or m not in B:
            K[f.name] = np.eye(4)
        else:
            K[f.name] = np.linalg.inv(S @ B[m] @ S) @ B[f.name]
    idle = xanim.read(clip_path("Bob_Idle"))
    wi = world(idle, 0)
    grip_l = np.linalg.inv(wi["Bip01_L_Hand"]) @ wi["Bip01_Prop2"]

    tracked = {tr.bone for tr in xa.tracks}
    out_tracks = {b: xanim.Track(b) for b in tracked}
    for t in times(xa):
        w = world(xa, t)
        mw = {}
        for f in frames:
            m = mirror_name(f.name)
            src_w = w[m] if m in w else w[f.name]
            mw[f.name] = S @ src_w @ S @ K[f.name]
        if prop2 == "vanilla":
            mw["Bip01_Prop2"] = mw["Bip01_L_Hand"] @ grip_l
        for f in frames:
            if f.name not in tracked:
                continue
            p = parent[f.name]
            loc = np.linalg.inv(mw[p]) @ mw[f.name] if p in mw else mw[f.name]
            loc = ortho(loc)
            s, q, tr = xanim.mat4_to_srt(loc.tolist())
            ot = out_tracks[f.name]
            ot.S[t] = [1.0, 1.0, 1.0]
            ot.R[t] = q
            ot.T[t] = tr
    # keep quaternion hemisphere continuity
    for ot in out_tracks.values():
        prev = None
        for t in sorted(ot.R):
            q = ot.R[t]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                q = tuple(-c for c in q)
                ot.R[t] = q
            prev = q
    order = [tr.bone for tr in xa.tracks]
    clip = out.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
    xanim.write_clip(src, out, clip, [out_tracks[b] for b in order], xa.ticks_per_second)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "mirror"
    if "--prop2" in args:
        i = args.index("--prop2")
        mode = args[i + 1]
        del args[i:i + 2]
    print(mirror_clip(args[0], args[1], mode))
