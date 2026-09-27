"""Seeded low-cost landscape meshes in metres and Z-up coordinates.

Leaves are folded mesh silhouettes, not spheres or image cards. A small number
of material batches keep the editable scene inexpensive. No external assets.
"""
import math
import numpy as np
import trimesh


def _taper(a, b, ra, rb, sections=9):
    a, b = np.asarray(a, float), np.asarray(b, float)
    delta = b - a
    length = np.linalg.norm(delta)
    angle = np.arange(sections) * math.tau / sections
    vertices = np.array([[r * math.cos(t), r * math.sin(t), z]
                         for z, r in [(0, ra), (length, rb)] for t in angle])
    faces = []
    for i in range(sections):
        j = (i + 1) % sections
        faces.extend([(i, j, sections + j), (i, sections + j, sections + i)])
    faces.extend((0, j + 1, j) for j in range(1, sections - 1))
    faces.extend((sections, sections + j, sections + j + 1)
                 for j in range(1, sections - 1))
    m = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], delta / length))
    m.apply_translation(a)
    return m


def _leaf(vertices, faces, base, heading, length, width, pitch):
    base = np.asarray(base, float)
    forward = np.array([math.cos(heading) * math.cos(pitch),
                        math.sin(heading) * math.cos(pitch), math.sin(pitch)])
    across = np.array([-math.sin(heading), math.cos(heading), 0.])
    middle = base + forward * length * .48
    start = len(vertices)
    vertices.extend([base, middle + across * width, base + forward * length,
                     middle - across * width, middle + [0, 0, width * .27]])
    faces.extend((start + a, start + b, start + c)
                 for a, b, c in [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)])


def build_pruned_tree(add, x, y, z, scale=1, seed=2709):
    rng = np.random.default_rng(seed)
    origin = np.array([x, y, z])
    woody = []
    leaves = {key: ([], []) for key in ['leaf', 'leaf2']}
    def pt(v):
        return origin + np.asarray(v) * scale
    trunk = [(0, 0, -.012), (.06, -.02, .75), (-.04, .015, 1.46), (.02, 0, 2.16)]
    for a, b, ra, rb in zip(trunk, trunk[1:], [.14, .104, .072], [.104, .072, .027]):
        woody.append(_taper(pt(a), pt(b), ra * scale, rb * scale))
    for i in range(7):
        angle = i * 2.39996 + .25
        reach = .66 + rng.uniform(0, .21) if i < 6 else .16
        high = 2.08 + .13 * (i % 3) if i < 6 else 2.54
        root = np.array([-.025, .0, 1.22 + .08 * (i % 3)])
        elbow = np.array([math.cos(angle) * reach * .46, math.sin(angle) * reach * .46, 1.72 + .055 * i])
        end = np.array([math.cos(angle) * reach, math.sin(angle) * reach, high])
        woody.extend([_taper(pt(root), pt(elbow), .045 * scale, .028 * scale),
                      _taper(pt(elbow), pt(end), .028 * scale, .009 * scale)])
        for j in range(5):
            heading = angle + (j - 2) * .49
            tip = end + [.25 * math.cos(heading), .25 * math.sin(heading), .07 + .04 * (j % 2)]
            woody.append(_taper(pt(end), pt(tip), .009 * scale, .0025 * scale, 6))
            for k in range(16):
                t = (k + .4) / 16
                # Leaf petioles meet the twig; alternating sides create airy pads.
                attach = end * (1 - t) + tip * t
                side = 1 if k % 2 else -1
                h = heading + side * rng.uniform(.5, 1.30)
                length = rng.uniform(.075, .14) * scale
                key = 'leaf2' if rng.random() < .28 else 'leaf'
                _leaf(*leaves[key], pt(attach), h, length, length * .30,
                      rng.uniform(-.35, .45))
    add('tree_tapered_branchwork', trimesh.util.concatenate(woody), 'woodlight')
    for key, (v, f) in leaves.items():
        add('tree_individual_leaves_' + key,
            trimesh.Trimesh(vertices=v, faces=f, process=False), key)


def build_water_surface(add):
    # The bank boundary and mean waterline remain unchanged at z=-0.78m.
    xs, ys = np.linspace(-8, 24, 161), np.linspace(-8, -2, 41)
    v, f = [], []
    for yy in ys:
        for xx in xs:
            zz = -.78 + .006 * math.sin(xx * 4.1 + yy * 2.3) + .004 * math.sin(yy * 7 - xx * 1.2)
            v.append((xx, yy, zz))
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            a = j * len(xs) + i
            f.extend([(a, a + 1, a + len(xs) + 1), (a, a + len(xs) + 1, a + len(xs))])
    add('canal_ripple_surface', trimesh.Trimesh(vertices=v, faces=f, process=False), 'water')


def build_bank_ferns(add):
    rng = np.random.default_rng(2819)
    # Attached to the bank ledge, outside bridge, dock and arrival passages.
    for idx, (x, y) in enumerate([(-5.8, -1.91), (-3.9, -1.91), (13.6, -1.91), (16.4, -1.91),
                                 (-4.5, -8.07), (.7, -8.07), (15.8, -8.07)]):
        v, f, ribs = [], [], []
        for j in range(8):
            heading = j * math.tau / 8 + rng.uniform(-.15, .15)
            length = rng.uniform(.25, .44)
            start = np.array([x, y, -.012])
            end = start + [length * math.cos(heading), length * math.sin(heading), -.24]
            ribs.append(_taper(start, end, .004, .001, 5))
            for k in range(1, 9):
                t = k / 10
                center = start * (1 - t) + end * t + [0, 0, .09 * math.sin(math.pi * t)]
                for side in [-1, 1]:
                    ll = .095 * (1 - t * .75)
                    _leaf(v, f, center, heading + side * 1.02, ll, ll * .17, -.10)
        add('bank_fern_fronds_' + str(idx), trimesh.Trimesh(vertices=v, faces=f, process=False), 'leaf')
        add('bank_fern_ribs_' + str(idx), trimesh.util.concatenate(ribs), 'leaf2')
