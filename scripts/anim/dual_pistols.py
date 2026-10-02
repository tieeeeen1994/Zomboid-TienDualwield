"""
Rough dual pistol preview clip (not for shipping): vanilla's one-handed pistol aim
(Bob_IdleAimHgun_Torch, the pose with a torch in the left hand) for the right arm, the same clip
mirrored for the left arm, then a right shot and a left shot with procedural recoil.

    python dual_pistols.py <out.x> [gap_frames]

The left arm keeps its mirrored world pose and is only moved so its clavicle sits where the
vanilla torso puts it. 30 fps; gap_frames is the time between the two shots (5 = ~167 ms,
just over the anticheat's 150 ms).
"""

import os
import sys

import numpy as np

import xmath  # noqa: F401
import xanim
from mirror import mirror_clip
from xmath import bones, clip_path, ortho, world

BASE = "Bob_IdleAimHgun_Torch"
FPS = 30
LENGTH = 40
SHOT_R = 8
SPREAD = 14


def chain(frames, root):
    kids = {}
    for f in frames:
        kids.setdefault(f.parent, []).append(f.name)
    out, todo = [], [root]
    while todo:
        n = todo.pop()
        out.append(n)
        todo.extend(kids.get(n, []))
    return out


def rot_x(deg):
    a = np.radians(deg)
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = np.cos(a), -np.sin(a), np.sin(a), np.cos(a)
    return m


def rot_y(deg):
    a = np.radians(deg)
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = np.cos(a), np.sin(a), -np.sin(a), np.cos(a)
    return m


def spread(w, side, names, deg):
    """Swing the arm outward about the shoulder, then turn the hand back so the gun points ahead."""
    sign = 1 if side == "R" else -1
    up = "Bip01_%s_UpperArm" % side
    hand = "Bip01_%s_Hand" % side
    prop = "Bip01_Prop1" if side == "R" else "Bip01_Prop2"
    m = about(w[up][:3, 3].copy(), rot_y(sign * deg))
    for n in names[up] + [prop]:
        w[n] = m @ w[n]
    m = about(w[hand][:3, 3].copy(), rot_y(-sign * deg))
    for n in names[hand] + [prop]:
        w[n] = m @ w[n]


def about(pivot, r):
    t, ti = np.eye(4), np.eye(4)
    t[:3, 3], ti[:3, 3] = pivot, -pivot
    return t @ r @ ti


def kick(f, shot, peak):
    d = f - shot
    if d < 0:
        return 0.0
    if d < 2:
        return peak * d / 2
    return peak * np.exp(-(d - 2) / 4.0)


def recoil(w, side, names, f, shot):
    hand = "Bip01_%s_Hand" % side
    fore = "Bip01_%s_Forearm" % side
    prop = "Bip01_Prop1" if side == "R" else "Bip01_Prop2"
    for bone, deg in ((fore, kick(f, shot, 7)), (hand, kick(f, shot, 16))):
        if deg == 0:
            continue
        m = about(w[bone][:3, 3].copy(), rot_x(deg))
        for n in names[bone] + [prop]:
            w[n] = m @ w[n]


def main(out, gap=5):
    src = clip_path(BASE)
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "_mirror_tmp.x")
    mirror_clip(BASE, tmp)
    va = xanim.read(src, with_mesh=True)
    ma = xanim.read(tmp)
    frames = bones(va)
    parent = {f.name: f.parent for f in frames}
    left = chain(frames, "Bip01_L_Clavicle") + ["Bip01_Prop2"]
    names = {b: chain(frames, b) for b in ("Bip01_R_UpperArm", "Bip01_L_UpperArm", "Bip01_R_Forearm", "Bip01_R_Hand", "Bip01_L_Forearm", "Bip01_L_Hand")}
    dur = max(max(list(tr.R) + [0]) for tr in va.tracks) or 1
    tps = va.ticks_per_second
    tracked = [tr.bone for tr in va.tracks]
    for b in left:
        if b not in tracked:
            tracked.append(b)
    tracks = {b: xanim.Track(b) for b in tracked}
    for f in range(LENGTH + 1):
        t = (f * tps / FPS) % dur
        w = world(va, t)
        wm = world(ma, t)
        delta = w["Bip01_L_Clavicle"][:3, 3] - wm["Bip01_L_Clavicle"][:3, 3]
        for n in left:
            m = wm[n].copy()
            m[:3, 3] += delta
            w[n] = m
        spread(w, "R", names, SPREAD)
        spread(w, "L", names, SPREAD)
        recoil(w, "R", names, f, SHOT_R)
        recoil(w, "L", names, f, SHOT_R + gap)
        for b in tracked:
            p = parent[b]
            loc = ortho(np.linalg.inv(w[p]) @ w[b] if p in w else w[b])
            _, q, tr = xanim.mat4_to_srt(loc.tolist())
            key = int(round(f * tps / FPS))
            tracks[b].S[key] = [1.0, 1.0, 1.0]
            tracks[b].R[key] = q
            tracks[b].T[key] = tr
    for tr in tracks.values():
        prev = None
        for k in sorted(tr.R):
            q = tr.R[k]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                tr.R[k] = q = tuple(-c for c in q)
            prev = q
    os.remove(tmp)
    clip = os.path.basename(out).rsplit(".", 1)[0]
    xanim.write_clip(src, out, clip, [tracks[b] for b in tracked], tps)
    print("[dual]", out, "shots at frames", SHOT_R, SHOT_R + gap)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5)
