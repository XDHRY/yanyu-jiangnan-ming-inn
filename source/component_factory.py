"""Authoritative Ming component manufacturing factory.
Generates isolated, reproducible Ming-style 3D components and integrates them
into the master Jiangnan waterfront inn scene.
"""
from pathlib import Path
import json, math, random
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

COL = {
    'plaster': 'ded9c8', 'wood': '493324', 'woodlight': '796047', 'tile': '303d42',
    'stone': '777e79', 'paving': '999e91', 'water': '34616b', 'leaf': '47664d',
    'leaf2': '64734b', 'red': 'a95531', 'glow': 'f6bf69', 'fabric': 'b5b1a0',
    'soil': '4c4938', 'metal': '454943', 'lacquer': '171411', 'paper': 'd7cfb8',
    'brass': 'b39a59', 'celadon': '92bab0', 'lotus': '875324'
}

class ComponentBuilder:
    """Wrapper that provides unified box, beam, lathe, sphere, mesh primitives."""
    def __init__(self, scene=None, records=None, layer='component'):
        self.scene = scene if scene is not None else trimesh.Scene()
        self.records = records if records is not None else []
        self.layer = layer
        self.materials = {
            k: PBRMaterial(
                name=k,
                baseColorFactor=[*bytes.fromhex(v), 255],
                roughnessFactor=0.23 if k in ['water', 'tile', 'paving'] else 0.76,
                metallicFactor=0.72 if k in ['metal', 'brass'] else 0,
                doubleSided=True
            ) for k, v in COL.items()
        }

    def add(self, name, m, mat='wood'):
        m.update_faces(m.nondegenerate_faces())
        m.remove_unreferenced_vertices()
        m.visual = trimesh.visual.TextureVisuals(material=self.materials[mat])
        n = f"{self.layer}/{name}_{len(self.records):05d}"
        self.scene.add_geometry(m, node_name=n, geom_name=n)
        self.records.append({
            'name': n,
            'layer': self.layer,
            'material': mat,
            'bounds': m.bounds.round(4).tolist(),
            'vertices': len(m.vertices),
            'triangles': len(m.faces)
        })
        return m

    def box(self, name, c, d, mat='wood'):
        if min(d) < 0.0001:
            return None
        m = trimesh.creation.box(extents=d)
        m.apply_translation(c)
        return self.add(name, m, mat)

    def beam(self, name, a, b, r=0.012, mat='wood', sections=12):
        a = np.array(a, float)
        b = np.array(b, float)
        d = b - a
        length = np.linalg.norm(d)
        if length < 0.001:
            return None
        m = trimesh.creation.cylinder(radius=r, height=length, sections=sections)
        m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d / length))
        m.apply_translation((a + b) / 2)
        return self.add(name, m, mat)

    def sphere(self, name, c, scale, mat='leaf', sub=1):
        m = trimesh.creation.icosphere(subdivisions=sub)
        m.apply_scale(scale)
        m.apply_translation(c)
        return self.add(name, m, mat)

    def lathe(self, name, c, profile, mat='stone', N=24):
        v = []
        f = []
        for z, r in profile:
            for i in range(N):
                t = i * math.tau / N
                v.append([c[0] + r * math.cos(t), c[1] + r * math.sin(t), c[2] + z])
        for j in range(len(profile) - 1):
            for i in range(N):
                a = j * N + i
                b = j * N + (i + 1) % N
                d = (j + 1) * N + i
                e = (j + 1) * N + (i + 1) % N
                f.extend([[a, b, e], [a, e, d]])
        mesh_obj = trimesh.Trimesh(vertices=v, faces=f, process=False)
        return self.add(name, mesh_obj, mat)

    def ring(self, name, c, r, t=0.008, mat='brass'):
        m = trimesh.creation.torus(major_radius=r, minor_radius=t, major_sections=24, minor_sections=8)
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        m.apply_translation(c)
        return self.add(name, m, mat)

    def frame(self, name, x, y, z, w, h, t=0.035, depth=0.065, mat='wood'):
        for xx in [x - w / 2 + t / 2, x + w / 2 - t / 2]:
            self.box(name + '_stile', (xx, y, z + h / 2), (t, depth, h), mat)
        for zz in [z + t / 2, z + h - t / 2]:
            self.box(name + '_rail', (x, y, zz), (w - 2 * t, depth, t), mat)


class ComponentBuilderBridge:
    """Bridges procedural scene builders (like base_geometry in refine_ming.py)
    to ComponentBuilder primitives without duplicating state.
    """
    def __init__(self, base_mod, layer='ming_components'):
        self.b = base_mod
        self.scene = getattr(base_mod, 'S', None)
        self.records = getattr(base_mod, 'records', None)
        self.default_layer = layer

    @property
    def layer(self):
        return getattr(self.b, 'layer', self.default_layer)

    @layer.setter
    def layer(self, v):
        self.b.layer = v

    def add(self, name, m, mat='wood'):
        return self.b.add(name, m, mat)

    def box(self, name, c, d, mat='wood'):
        return self.b.box(name, c, d, mat)

    def beam(self, name, a, b, r=0.012, mat='wood', sections=12):
        return self.b.beam(name, a, b, r, mat, sections)

    def sphere(self, name, c, scale, mat='leaf', sub=1):
        return self.b.sphere(name, c, scale, mat, sub)

    def lathe(self, name, c, profile, mat='stone', N=24):
        return self.b.lathe(name, c, profile, mat, N)

    def ring(self, name, c, r, t=0.008, mat='brass'):
        m = trimesh.creation.torus(major_radius=r, minor_radius=t, major_sections=24, minor_sections=8)
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        m.apply_translation(c)
        return self.add(name, m, mat)

    def frame(self, name, x, y, z, w, h, t=0.035, depth=0.065, mat='wood'):
        for xx in [x - w / 2 + t / 2, x + w / 2 - t / 2]:
            self.box(name + '_stile', (xx, y, z + h / 2), (t, depth, h), mat)
        for zz in [z + t / 2, z + h - t / 2]:
            self.box(name + '_rail', (x, y, zz), (w - 2 * t, depth, t), mat)


# ==============================================================================
# Component 1: Four-Panel Folding Screen (四扇折叠屏风)
# ==============================================================================
def build_four_panel_screen(builder, x=0, y=0, z=0, rotDeg=0, angle_deg=10, width=2.4, height=1.9):
    """
    Ming-style four-panel folding screen (插屏/围屏).
    Features alternating folded leaves, delicate timber stiles, translucent paper fields,
    carved lotus lower aprons, and miniature aged-brass hinges.
    """
    start_idx = len(builder.records)
    num_leaves = 4
    leaf_w = width / num_leaves
    leaf_h = height
    t_frame = 0.036
    d_frame = 0.042

    cur_x = -width / 2 + leaf_w / 2
    for i in range(num_leaves):
        fold_sign = -1 if i % 2 == 0 else 1
        leaf_ang = math.radians(angle_deg * fold_sign)
        lx = cur_x
        ly = math.sin(leaf_ang) * (leaf_w * 0.25)
        lz = 0.0

        # Vertical stiles
        for side in [-1, 1]:
            builder.box('screen_stile',
                        (lx + side * (leaf_w / 2 - t_frame / 2), ly, lz + leaf_h / 2),
                        (t_frame, d_frame, leaf_h), 'wood')

        # Horizontal rails (top, bottom, and dividing rail at apron level)
        h_apron = 0.42
        for rz in [lz + t_frame / 2, lz + h_apron, lz + leaf_h - t_frame / 2]:
            builder.box('screen_rail',
                        (lx, ly, rz),
                        (leaf_w - 2 * t_frame, d_frame, t_frame), 'wood')

        # Upper paper screen panel
        paper_h = leaf_h - h_apron - t_frame * 2
        paper_z = lz + h_apron + t_frame + paper_h / 2
        builder.box('screen_paper_panel',
                    (lx, ly, paper_z),
                    (leaf_w - t_frame * 2 - 0.01, 0.012, paper_h - 0.01), 'paper')

        # Paper panel inner muntins (restrained 2 x 4 lattice)
        inner_w = leaf_w - t_frame * 2
        builder.box('screen_muntin_v',
                    (lx, ly, paper_z),
                    (0.018, 0.02, paper_h - 0.02), 'woodlight')
        for mz in [paper_z - paper_h * 0.25, paper_z, paper_z + paper_h * 0.25]:
            builder.box('screen_muntin_h',
                        (lx, ly, mz),
                        (inner_w - 0.02, 0.02, 0.018), 'woodlight')

        # Lower solid carved panel
        apron_inner_h = h_apron - t_frame * 2
        builder.box('screen_lotus_apron',
                    (lx, ly, lz + t_frame + apron_inner_h / 2),
                    (leaf_w - t_frame * 2, 0.022, apron_inner_h), 'lotus')
        # Brass inlay border on apron
        builder.box('screen_apron_trim',
                    (lx, ly - 0.012, lz + t_frame + apron_inner_h / 2),
                    (leaf_w - t_frame * 2 - 0.04, 0.005, apron_inner_h - 0.04), 'brass')

        # Brass connecting hinges between panels
        if i < num_leaves - 1:
            hx = lx + leaf_w / 2
            for hz in [lz + 0.35, lz + 0.95, lz + 1.55]:
                builder.box('screen_brass_hinge',
                            (hx, ly, hz),
                            (0.022, 0.035, 0.045), 'brass')

        cur_x += leaf_w

    # Apply global transform to all geometry added in this block
    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 2: Ming Altar Table with Upturned Flanges (明式夹头榫翘头案)
# ==============================================================================
def build_altar_table(builder, x=0, y=0, z=0, rotDeg=0, length=2.1, width=0.48, height=0.86):
    """
    Ming huanghuali altar table with graceful upturned flanges (翘头案).
    Features recessed legs, cloud-scroll aprons (夹头榫牙条), and double side stretchers.
    """
    start_idx = len(builder.records)
    t_top = 0.055
    top_z = height - t_top / 2

    # Main table board
    builder.box('altar_table_top', (0, 0, top_z), (length, width, t_top), 'wood')

    # Upturned flanges at both ends
    for side in [-1, 1]:
        fx = side * (length / 2 - 0.025)
        # S-curve flange profile
        builder.box('altar_flange_body',
                    (fx, 0, top_z + t_top / 2 + 0.025),
                    (0.045, width, 0.05), 'wood')
        builder.beam('altar_flange_scroll',
                     (fx + side * 0.015, -width / 2, top_z + t_top / 2 + 0.05),
                     (fx + side * 0.015, width / 2, top_z + t_top / 2 + 0.05),
                     0.022, 'wood', 12)

    # Recessed legs (侧角收分)
    leg_x_inset = 0.22 * length
    leg_y_inset = width / 2 - 0.055
    leg_h = height - t_top
    leg_r = 0.038
    for sx in [-1, 1]:
        lx = sx * (length / 2 - leg_x_inset)
        for sy in [-1, 1]:
            ly = sy * leg_y_inset
            # Subtle outward slant for stability
            builder.beam('altar_leg',
                         (lx + sx * 0.025, ly + sy * 0.01, 0),
                         (lx, ly, leg_h),
                         leg_r, 'wood', 12)

    # Apron with cloud-cut ends (夹头榫卷云纹牙头)
    apron_h = 0.085
    apron_y = width / 2 - 0.02
    for sy in [-1, 1]:
        builder.box('altar_apron_front',
                    (0, sy * apron_y, height - t_top - apron_h / 2),
                    (length - leg_x_inset * 0.9, 0.028, apron_h), 'wood')
        for sx in [-1, 1]:
            # Cloud spandrel near leg junction
            cx = sx * (length / 2 - leg_x_inset + 0.08)
            builder.box('altar_spandrel',
                        (cx, sy * apron_y, height - t_top - apron_h - 0.04),
                        (0.12, 0.025, 0.08), 'woodlight')

    # Side double stretchers connecting legs
    for sx in [-1, 1]:
        lx = sx * (length / 2 - leg_x_inset)
        for sz_level in [0.22, 0.48]:
            builder.beam('altar_side_stretcher',
                         (lx, -leg_y_inset, sz_level),
                         (lx, leg_y_inset, sz_level),
                         0.022, 'wood', 8)

    # Apply global transform
    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 3: Scholar Rock & Porcelain Vase Set (文房太湖石供与梅瓶)
# ==============================================================================
def build_scholar_rock(builder, x=0, y=0, z=0, scale=1.0):
    """
    Ming scholar desk stone (文房供石/太湖石供) on a sculpted rootwood/brass stand.
    """
    start_idx = len(builder.records)
    # Tiered carved pedestal
    builder.lathe('rock_pedestal', (0, 0, 0),
                  [(0, 0), (0.015, 0.16 * scale), (0.04, 0.14 * scale),
                   (0.065, 0.155 * scale), (0.08, 0.11 * scale), (0.085, 0)],
                  'brass', 24)

    # Asymmetrical organic limestone core with natural hollows
    builder.sphere('rock_mass_main', (0, 0, 0.22 * scale),
                   (0.12 * scale, 0.09 * scale, 0.16 * scale), 'stone', 1)
    builder.sphere('rock_mass_upper', (0.03 * scale, -0.02 * scale, 0.35 * scale),
                   (0.09 * scale, 0.07 * scale, 0.12 * scale), 'stone', 1)
    builder.sphere('rock_outcrop_left', (-0.08 * scale, 0.02 * scale, 0.26 * scale),
                   (0.06 * scale, 0.05 * scale, 0.08 * scale), 'stone', 1)
    builder.sphere('rock_outcrop_peak', (0.01 * scale, 0.01 * scale, 0.44 * scale),
                   (0.05 * scale, 0.04 * scale, 0.07 * scale), 'stone', 1)

    # Moss accent on crevice
    builder.sphere('rock_moss_accent', (-0.03 * scale, 0.04 * scale, 0.29 * scale),
                   (0.035 * scale, 0.03 * scale, 0.025 * scale), 'leaf2', 1)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


def build_porcelain_vase(builder, x=0, y=0, z=0, scale=1.0):
    """
    Ming celadon/white porcelain plum vase (梅瓶).
    Small round lip rim, narrow neck, swollen shoulder, tapered body.
    """
    start_idx = len(builder.records)
    profile = [
        (0.00, 0.0),
        (0.01 * scale, 0.052 * scale),
        (0.12 * scale, 0.065 * scale),
        (0.24 * scale, 0.092 * scale),
        (0.32 * scale, 0.118 * scale),
        (0.36 * scale, 0.112 * scale),
        (0.38 * scale, 0.055 * scale),
        (0.41 * scale, 0.042 * scale),
        (0.43 * scale, 0.049 * scale),
        (0.44 * scale, 0.028 * scale),
        (0.44 * scale, 0.0)
    ]
    builder.lathe('porcelain_plum_vase', (0, 0, 0), profile, 'celadon', 32)

    # Slender plum blossom twig emerging from the vase
    stem_top = (0.02 * scale, 0.01 * scale, 0.65 * scale)
    builder.beam('vase_plum_twig',
                 (0, 0, 0.38 * scale), stem_top,
                 0.006 * scale, 'wood', 8)
    builder.beam('vase_plum_branch',
                 stem_top, (0.12 * scale, -0.04 * scale, 0.74 * scale),
                 0.004 * scale, 'wood', 6)
    # Delicate blossom petals
    for bx, by, bz in [(0.12 * scale, -0.04 * scale, 0.74 * scale),
                       (0.04 * scale, 0.02 * scale, 0.68 * scale),
                       (0.08 * scale, -0.01 * scale, 0.71 * scale)]:
        builder.sphere('plum_blossom_bud', (bx, by, bz),
                       (0.018 * scale, 0.018 * scale, 0.018 * scale), 'red', 1)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 4: Jiangnan Courtyard Bamboo Cluster (江南庭院幽竹丛)
# ==============================================================================
def build_bamboo_cluster(builder, x=0, y=0, z=0, count=6, height=3.0, seed=42):
    """
    Delicate Jiangnan bamboo grove (修竹丛).
    Slender jointed stems, realistic ring nodes, graceful branching, and spray leaves.
    """
    start_idx = len(builder.records)
    rng = random.Random(seed)
    culm_radius = 0.018
    node_spacing = 0.32

    for c in range(count):
        # Organic offset from cluster center
        bx = rng.uniform(-0.35, 0.35)
        by = rng.uniform(-0.30, 0.30)
        h = height * rng.uniform(0.85, 1.15)
        # Slight natural lean
        lean_x = rng.uniform(-0.12, 0.12)
        lean_y = rng.uniform(-0.10, 0.10)

        # Build jointed culm segments
        num_nodes = int(h / node_spacing)
        prev_pt = np.array([bx, by, 0.0])
        for k in range(1, num_nodes + 1):
            t = k / num_nodes
            cur_pt = np.array([
                bx + lean_x * (t ** 1.3),
                by + lean_y * (t ** 1.3),
                k * node_spacing
            ])
            # Culm segment
            builder.beam('bamboo_culm', prev_pt, cur_pt, culm_radius * (1.0 - 0.25 * t), 'leaf', 8)
            # Bamboo joint ring (节环)
            builder.ring('bamboo_node_ring', cur_pt, culm_radius * 1.25, 0.005, 'leaf2')

            # Upper nodes produce leafy twigs
            if k >= int(num_nodes * 0.45):
                branch_ang = rng.uniform(0, math.tau)
                branch_len = rng.uniform(0.25, 0.45)
                branch_end = cur_pt + np.array([
                    math.cos(branch_ang) * branch_len,
                    math.sin(branch_ang) * branch_len,
                    rng.uniform(0.08, 0.18)
                ])
                builder.beam('bamboo_twig', cur_pt, branch_end, 0.005, 'leaf', 6)
                # Leaf spray at twig tip
                for _ in range(4):
                    leaf_off = np.array([
                        rng.uniform(-0.06, 0.06),
                        rng.uniform(-0.06, 0.06),
                        rng.uniform(-0.02, 0.04)
                    ])
                    builder.sphere('bamboo_leaf_spray',
                                   branch_end + leaf_off,
                                   (0.09, 0.04, 0.015), 'leaf2', 1)

            prev_pt = cur_pt

    # Apply global translation/rotation
    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 5: Veranda Meirengkao Balustrade (回廊吴王靠 / 美人靠)
# ==============================================================================
def build_veranda_balustrade(builder, x0, x1, y, z, bench_w=0.30, height=0.92):
    """
    Ming curved veranda bench balustrade (吴王靠 / 美人靠).
    Features relaxed low bench seat, S-shaped backrest balusters, and continuous crest rail.
    """
    start_idx = len(builder.records)
    L = abs(x1 - x0)
    cx = (x0 + x1) / 2
    bench_z = z + 0.44

    # Low timber seating bench plank
    builder.box('meirengkao_seat',
                (cx, y, bench_z),
                (L, bench_w, 0.045), 'woodlight')

    # Continuous curved backrest rail (搭脑扶手梁)
    rail_z = z + height
    back_y = y - 0.14  # curves outward
    builder.beam('meirengkao_crest_rail',
                 (x0, back_y, rail_z), (x1, back_y, rail_z),
                 0.038, 'wood', 12)

    # Base apron beam beneath seat
    builder.box('meirengkao_base_apron',
                (cx, y, bench_z - 0.065),
                (L, 0.035, 0.08), 'wood')

    # S-shaped curved balusters (鹅颈木靠背立柱)
    spacing = 0.22
    num_spindles = max(3, int(L / spacing) + 1)
    spindle_xs = np.linspace(x0 + 0.10, x1 - 0.10, num_spindles)

    for sx in spindle_xs:
        # Support bracket under seat
        builder.beam('meirengkao_under_bracket',
                     (sx, y, z + 0.08), (sx, y, bench_z),
                     0.024, 'wood', 8)
        # S-curve upright: seat -> back arch -> crest rail
        p0 = (sx, y - 0.04, bench_z + 0.02)
        p1 = (sx, y - 0.16, bench_z + (rail_z - bench_z) * 0.45)
        p2 = (sx, back_y, rail_z - 0.02)
        builder.beam('meirengkao_gooseneck_lo', p0, p1, 0.018, 'wood', 8)
        builder.beam('meirengkao_gooseneck_hi', p1, p2, 0.018, 'wood', 8)


# ==============================================================================
# Component 7: Ming Daybed with Three-Sided Railing (明式三围独板罗汉榻)
# ==============================================================================
def build_ming_daybed(builder, x=0, y=0, z=0, rotDeg=0, length=2.05, depth=1.05, height=0.76):
    """
    Classic Ming huanghuali daybed (罗汉床/榻).
    Features three-sided low waist railing, cabriole legs with inward-turned horse-hoof feet,
    and a comfortable woven mat seat with brocade cushion.
    """
    start_idx = len(builder.records)
    seat_z = 0.46
    t_frame = 0.065

    # Main bed platform frame
    builder.box('daybed_frame', (0, 0, seat_z - t_frame / 2),
                (length, depth, t_frame), 'wood')
    # Soft woven teal brocade mattress cushion
    builder.box('daybed_cushion', (0, 0, seat_z + 0.035),
                (length - 0.10, depth - 0.10, 0.07), 'fabric')

    # Three-sided railing: back and two sides
    rail_h = height - seat_z
    back_y = depth / 2 - 0.035
    builder.box('daybed_back_rail', (0, back_y, seat_z + rail_h / 2),
                (length, 0.05, rail_h), 'wood')
    builder.box('daybed_back_panel', (0, back_y, seat_z + rail_h / 2),
                (length - 0.16, 0.025, rail_h - 0.08), 'lotus')

    for sx in [-1, 1]:
        side_x = sx * (length / 2 - 0.035)
        builder.box('daybed_side_rail', (side_x, -0.04, seat_z + rail_h / 2),
                    (0.05, depth - 0.08, rail_h), 'wood')
        builder.box('daybed_side_panel', (side_x, -0.04, seat_z + rail_h / 2),
                    (0.025, depth - 0.20, rail_h - 0.08), 'lotus')

    # Robust cabriole legs with inward-turned feet (马蹄足)
    leg_r = 0.045
    for sx in [-1, 1]:
        lx = sx * (length / 2 - 0.10)
        for sy in [-1, 1]:
            ly = sy * (depth / 2 - 0.10)
            builder.beam('daybed_leg', (lx + sx * 0.02, ly + sy * 0.02, 0.04),
                         (lx, ly, seat_z - t_frame), leg_r, 'wood', 12)
            builder.box('daybed_horsehoof_foot', (lx + sx * 0.02, ly + sy * 0.02, 0.02),
                        (0.09, 0.09, 0.04), 'wood')

    # Waist and apron with beaded edge (束腰与牙板)
    apron_h = 0.08
    for sy in [-1, 1]:
        builder.box('daybed_apron_long', (0, sy * (depth / 2 - 0.03), seat_z - t_frame - apron_h / 2),
                    (length - 0.22, 0.035, apron_h), 'wood')
    for sx in [-1, 1]:
        builder.box('daybed_apron_short', (sx * (length / 2 - 0.03), 0, seat_z - t_frame - apron_h / 2),
                    (0.035, depth - 0.22, apron_h), 'wood')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 8: Scholar Brush Pot with Brushes (文房黄花梨笔筒)
# ==============================================================================
def build_brush_pot(builder, x=0, y=0, z=0, scale=1.0):
    """
    Ming scholar brush pot (笔筒) carved from huanghuali wood, with fine brushes.
    """
    start_idx = len(builder.records)
    r = 0.085 * scale
    h = 0.18 * scale
    profile = [
        (0.0, 0.0),
        (0.015 * scale, r),
        (0.09 * scale, r * 0.94),
        (h - 0.015 * scale, r * 0.98),
        (h, r),
        (h, r * 0.82),
        (0.02 * scale, r * 0.80),
        (0.02 * scale, 0.0)
    ]
    builder.lathe('brush_pot_body', (0, 0, 0), profile, 'wood', 32)

    # 3 Calligraphy writing brushes standing inside
    brush_angles = [0.15, 2.2, 4.3]
    brush_leans = [0.08, 0.07, 0.09]
    for ang, lean in zip(brush_angles, brush_leans):
        bx = math.cos(ang) * (r * 0.4)
        by = math.sin(ang) * (r * 0.4)
        b_len = 0.26 * scale
        tip_pt = (bx + math.cos(ang) * lean * b_len,
                  by + math.sin(ang) * lean * b_len,
                  0.02 * scale + b_len)
        builder.beam('calligraphy_brush_handle',
                     (bx, by, 0.02 * scale), tip_pt,
                     0.006 * scale, 'woodlight', 8)
        # Brush hair tip
        builder.sphere('brush_hair_tip',
                       tip_pt, (0.012 * scale, 0.012 * scale, 0.025 * scale), 'metal', 1)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 9: Woven Bamboo Scroll Basket (竹编卷轴画筒)
# ==============================================================================
def build_bamboo_scroll_basket(builder, x=0, y=0, z=0, scale=1.0):
    """
    Ming woven bamboo scroll container (竹编画筒), holding paper art scrolls.
    """
    start_idx = len(builder.records)
    r = 0.16 * scale
    h = 0.45 * scale

    # Bamboo basket rings and vertical staves
    for level_z in [0.02, 0.15, 0.30, h]:
        builder.ring('scroll_basket_hoop', (0, 0, level_z * scale), r, 0.008 * scale, 'woodlight')
    num_staves = 16
    for i in range(num_staves):
        t = i * math.tau / num_staves
        px = r * math.cos(t)
        py = r * math.sin(t)
        builder.beam('scroll_basket_stave', (px, py, 0), (px, py, h), 0.007 * scale, 'woodlight', 6)
    builder.box('scroll_basket_base', (0, 0, 0.015 * scale),
                (r * 1.9, r * 1.9, 0.02 * scale), 'woodlight')

    # Rolled-up paper scrolls inside
    scroll_offsets = [(-0.06, 0.02, 0.12), (0.05, 0.04, 0.18), (0.0, -0.06, 0.15), (0.06, -0.03, 0.08)]
    for ox, oy, extra_h in scroll_offsets:
        sx = ox * scale
        sy = oy * scale
        tot_h = (h + extra_h) * scale
        builder.beam('paper_scroll_roll', (sx, sy, 0.02 * scale), (sx, sy, tot_h),
                     0.026 * scale, 'paper', 12)
        # Wooden scroll spindle ends
        builder.sphere('scroll_wooden_knob', (sx, sy, tot_h + 0.015 * scale),
                       (0.016 * scale, 0.016 * scale, 0.016 * scale), 'wood', 1)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 10: Ming Lacquer Chest with Brass Mounts (黑漆描金官皮箱)
# ==============================================================================
def build_lacquer_chest(builder, x=0, y=0, z=0, rotDeg=0, scale=1.0):
    """
    Ming black lacquer jewelry/document chest (官皮箱/印匣).
    Deep black lacquer body with gold trims, circular brass lock plate, and corner brackets.
    """
    start_idx = len(builder.records)
    w = 0.42 * scale
    d = 0.32 * scale
    h = 0.36 * scale

    # Lacquer chest body
    builder.box('lacquer_chest_body', (0, 0, h / 2), (w, d, h), 'lacquer')
    # Lid separation groove
    builder.box('lacquer_lid_trim', (0, 0, h * 0.72), (w + 0.01 * scale, d + 0.01 * scale, 0.018 * scale), 'metal')

    # Front circular brass faceplate & hasp (面叶与拍子)
    builder.lathe('chest_brass_faceplate', (0, -d / 2 - 0.005 * scale, h * 0.65),
                  [(0, 0), (0.004 * scale, 0.048 * scale), (0.004 * scale, 0)], 'brass', 24)
    builder.box('chest_padlock_hasp', (0, -d / 2 - 0.012 * scale, h * 0.62),
                (0.018 * scale, 0.012 * scale, 0.055 * scale), 'brass')

    # Brass corner brackets (铜包角)
    for sx in [-1, 1]:
        for sz_level in [0.03 * scale, h - 0.03 * scale]:
            builder.box('chest_corner_brace',
                        (sx * (w / 2 - 0.015 * scale), -d / 2 - 0.002 * scale, sz_level),
                        (0.035 * scale, 0.006 * scale, 0.035 * scale), 'brass')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 11: Roof Ridge Chiwen Ornament (正脊鸱吻卷草脊首)
# ==============================================================================
def build_roof_ridge_cap(builder, x=0, y=0, z=0, rotDeg=0, scale=1.0):
    """
    Gabled roof ridge terminal Chiwen / cloud crest (正脊鸱吻/兽头).
    Sculpted upward-curving crest protecting the ridge end from weather.
    """
    start_idx = len(builder.records)
    # Ridge mount base
    builder.box('ridge_cap_pedestal', (0, 0, 0.06 * scale),
                (0.24 * scale, 0.32 * scale, 0.12 * scale), 'tile')

    # Main curving Chiwen tail profile (curving upward and backward)
    pts = [
        (0, -0.10 * scale, 0.10 * scale),
        (0, 0.02 * scale, 0.22 * scale),
        (0, 0.12 * scale, 0.38 * scale),
        (0, 0.08 * scale, 0.52 * scale),
        (0, -0.04 * scale, 0.58 * scale),
        (0, -0.12 * scale, 0.52 * scale)
    ]
    for p_a, p_b in zip(pts[:-1], pts[1:]):
        builder.beam('chiwen_tail_body', p_a, p_b, 0.048 * scale, 'tile', 8)

    # Cloud scroll curled crest at top
    builder.ring('chiwen_cloud_scroll',
                 (0, -0.06 * scale, 0.54 * scale),
                 0.055 * scale, 0.02 * scale, 'tile')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 12: Waterfront Stone Lotus Basin (水榭青石荷花缸)
# ==============================================================================
def build_lotus_pot(builder, x=0, y=0, z=0, scale=1.0):
    """
    Deep carved limestone lotus bowl (水榭青石荷花缸).
    Circular basin filled with water, floating green lotus leaves, and a rising pink bud.
    """
    start_idx = len(builder.records)
    r = 0.42 * scale
    h = 0.48 * scale
    profile = [
        (0.0, 0.0),
        (0.03 * scale, r * 0.72),
        (0.18 * scale, r * 0.94),
        (0.38 * scale, r * 1.02),
        (h - 0.02 * scale, r),
        (h, r * 1.05),
        (h, r * 0.88),
        (0.06 * scale, r * 0.82),
        (0.06 * scale, 0.0)
    ]
    builder.lathe('stone_lotus_basin', (0, 0, 0), profile, 'stone', 32)
    # Water surface inside basin
    builder.lathe('basin_water_surface', (0, 0, h - 0.05 * scale),
                  [(0, 0), (0.01 * scale, r * 0.88), (0.01 * scale, 0)], 'water', 24)

    # Floating round lotus pads (荷叶)
    leaf_locs = [
        (r * 0.35, r * 0.25, 0.09 * scale),
        (-r * 0.32, r * 0.30, 0.12 * scale),
        (-r * 0.28, -r * 0.28, 0.11 * scale),
        (r * 0.25, -r * 0.32, 0.10 * scale)
    ]
    for lx, ly, lr in leaf_locs:
        builder.sphere('floating_lotus_pad',
                       (lx, ly, h - 0.045 * scale),
                       (lr, lr, 0.008 * scale), 'leaf', 1)

    # One rising pink lotus flower bud
    bud_pt = (0.04 * scale, 0.02 * scale, h + 0.14 * scale)
    builder.beam('lotus_flower_stem', (0, 0, h - 0.04 * scale), bud_pt,
                 0.007 * scale, 'leaf2', 6)
    builder.sphere('lotus_flower_bud', bud_pt,
                   (0.035 * scale, 0.035 * scale, 0.055 * scale), 'red', 1)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 13: Scholar Large Painting Desk (明式文房大画案)
# ==============================================================================
def build_scholar_desk(builder, x=0, y=0, z=0, rotDeg=0, length=1.85, width=0.82, height=0.82):
    """
    Ming huanghuali large painting desk (画案/书案).
    Wide flat top with ice-plate edge, straight legs with inward horsehoof feet,
    recessed apron, and giant-arm s-curved stretchers (霸王枨).
    """
    start_idx = len(builder.records)
    t_top = 0.055
    top_z = height - t_top / 2

    # Thick huanghuali desk top
    builder.box('desk_top', (0, 0, top_z), (length, width, t_top), 'wood')

    # Straight sturdy legs with inward horsehoof feet (直腿马蹄足)
    leg_x_inset = 0.14 * length
    leg_y_inset = width / 2 - 0.075
    leg_h = height - t_top
    for sx in [-1, 1]:
        lx = sx * (length / 2 - leg_x_inset)
        for sy in [-1, 1]:
            ly = sy * leg_y_inset
            builder.beam('desk_leg', (lx, ly, 0.04), (lx, ly, leg_h), 0.042, 'wood', 12)
            builder.box('desk_horsehoof_foot', (lx, ly, 0.02), (0.095, 0.095, 0.04), 'wood')
            # Giant-arm S-curved stretcher (霸王枨) connecting leg to desk bottom
            b_mid = (lx - sx * 0.12, ly - sy * 0.10, leg_h * 0.55)
            b_top = (lx - sx * 0.28, ly - sy * 0.22, leg_h)
            builder.beam('desk_spandrel_arm', (lx, ly, leg_h * 0.65), b_mid, 0.016, 'woodlight', 8)
            builder.beam('desk_spandrel_arm_top', b_mid, b_top, 0.016, 'woodlight', 8)

    # Recessed waist and apron (束腰与牙板)
    apron_h = 0.075
    for sy in [-1, 1]:
        builder.box('desk_apron_front', (0, sy * (width / 2 - 0.035), height - t_top - apron_h / 2),
                    (length - leg_x_inset * 1.5, 0.03, apron_h), 'wood')
    for sx in [-1, 1]:
        builder.box('desk_apron_side', (sx * (length / 2 - leg_x_inset * 0.75), 0, height - t_top - apron_h / 2),
                    (0.03, width - 0.18, apron_h), 'wood')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 14: Huanghuali Compound Wardrobe with Top Chest (明式黄花梨顶箱大立柜)
# ==============================================================================
def build_huanghuali_cabinet(builder, x=0, y=0, z=0, rotDeg=0, width=1.1, depth=0.55, height=2.05):
    """
    Ming compound wardrobe with upper top chest (顶箱大立柜/四件柜).
    Split into lower large wardrobe and upper top chest, with large circular brass mounts.
    """
    start_idx = len(builder.records)
    h_top_chest = 0.65
    h_base_cab = height - h_top_chest

    # Lower main wardrobe body
    builder.box('cabinet_main_body', (0, 0, h_base_cab / 2), (width, depth, h_base_cab), 'wood')
    # Upper top chest body
    builder.box('cabinet_top_chest', (0, 0, h_base_cab + h_top_chest / 2), (width, depth, h_top_chest), 'wood')

    # Front door floating relief panels (浮雕心板)
    for level_z, sec_h in [(h_base_cab * 0.52, h_base_cab * 0.78), (h_base_cab + h_top_chest * 0.5, h_top_chest * 0.72)]:
        for sx in [-width * 0.25, width * 0.25]:
            builder.box('cabinet_door_panel', (sx, -depth / 2 - 0.012, level_z),
                        (width * 0.44, 0.018, sec_h), 'lotus')
            builder.frame('cabinet_panel_molding', sx, -depth / 2 - 0.015, level_z - sec_h / 2,
                          width * 0.44, sec_h, 0.024, 0.02, 'woodlight')

    # Central circular brass faceplates with padlock pins (大圆形面叶与钮头)
    for cz in [h_base_cab * 0.55, h_base_cab + h_top_chest * 0.5]:
        builder.lathe('cabinet_brass_faceplate', (0, -depth / 2 - 0.018, cz),
                      [(0, 0), (0.005, 0.085), (0.005, 0)], 'brass', 32)
        builder.box('cabinet_padlock_hasp', (0, -depth / 2 - 0.025, cz - 0.02),
                    (0.022, 0.012, 0.075), 'brass')

    # Heavy corner brass hinges on door stiles
    for cz in [0.25, h_base_cab - 0.25, h_base_cab + 0.15, height - 0.15]:
        for sx in [-width / 2 + 0.02, width / 2 - 0.02]:
            builder.box('cabinet_brass_hinge', (sx, -depth / 2 - 0.012, cz),
                        (0.045, 0.016, 0.065), 'brass')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 15: Ming Footstool Roller Bench (明式方几滚凳脚踏)
# ==============================================================================
def build_footstool(builder, x=0, y=0, z=0, rotDeg=0, length=0.62, width=0.32, height=0.22):
    """
    Ming wooden footstool with rolling massage cylinders (滚凳/脚踏).
    Low bench frame with arched apron, cabriole legs, and 3 rolling timber rollers.
    """
    start_idx = len(builder.records)
    t = 0.035

    # Outer wooden border frame
    builder.frame('footstool_frame', 0, 0, height - t, length, width, t, t, 'wood')

    # 3 Revolving wooden roller cylinders inside frame (滚棍)
    r_roller = 0.022
    for rx in [-length * 0.26, 0, length * 0.26]:
        builder.beam('footstool_roller',
                     (rx, -width / 2 + t + 0.01, height - t / 2),
                     (rx, width / 2 - t - 0.01, height - t / 2),
                     r_roller, 'woodlight', 12)

    # 4 Curved cabriole legs with inward-turned feet
    for sx in [-1, 1]:
        lx = sx * (length / 2 - 0.045)
        for sy in [-1, 1]:
            ly = sy * (width / 2 - 0.045)
            builder.beam('footstool_leg', (lx + sx * 0.015, ly + sy * 0.015, 0),
                         (lx, ly, height - t), 0.024, 'wood', 8)

    # Arched cloud aprons beneath frame
    apron_h = 0.04
    for sy in [-1, 1]:
        builder.box('footstool_apron_long', (0, sy * (width / 2 - 0.015), height - t - apron_h / 2),
                    (length - 0.12, 0.018, apron_h), 'wood')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 16: Moon Shadow Garden Stone Lantern (月影庭院石灯笼)
# ==============================================================================
def build_moon_lamp(builder, x=0, y=0, z=0, scale=1.0):
    """
    Ming hexagonal stone courtyard lantern (月影石灯笼).
    Lotus pedestal, square pillar stem, hexagonal lamp house with lattice, umbrella roof.
    """
    start_idx = len(builder.records)
    # Hexagonal tiered pedestal base (莲花须弥座)
    builder.lathe('moon_lamp_base', (0, 0, 0),
                  [(0, 0), (0.04 * scale, 0.28 * scale), (0.10 * scale, 0.22 * scale),
                   (0.18 * scale, 0.24 * scale), (0.24 * scale, 0.15 * scale), (0.24 * scale, 0)],
                  'stone', 6)

    # Pillar stem
    builder.beam('moon_lamp_pillar', (0, 0, 0.24 * scale), (0, 0, 0.65 * scale),
                 0.08 * scale, 'stone', 6)

    # Middle plate (中台)
    builder.lathe('moon_lamp_mid_plinth', (0, 0, 0.65 * scale),
                  [(0, 0), (0.05 * scale, 0.25 * scale), (0.08 * scale, 0.22 * scale), (0.08 * scale, 0)],
                  'stone', 6)

    # Lamp chamber with hollow windows (六角火袋)
    h_house = 0.32 * scale
    for i in range(6):
        ang = i * math.tau / 6
        px = math.cos(ang) * (0.18 * scale)
        py = math.sin(ang) * (0.18 * scale)
        builder.beam('lamp_post', (px, py, 0.73 * scale), (px, py, 0.73 * scale + h_house),
                     0.02 * scale, 'stone', 6)

    # Luminous warm core inside lamp chamber
    builder.sphere('lamp_warm_core', (0, 0, 0.73 * scale + h_house / 2),
                   (0.09 * scale, 0.09 * scale, 0.11 * scale), 'glow', 1)

    # Hexagonal umbrella roof and jewel finial (伞盖与宝珠)
    builder.lathe('moon_lamp_umbrella_roof', (0, 0, 0.73 * scale + h_house),
                  [(0, 0), (0.06 * scale, 0.32 * scale), (0.14 * scale, 0.12 * scale),
                   (0.20 * scale, 0.04 * scale), (0.20 * scale, 0)],
                  'stone', 6)
    builder.sphere('moon_lamp_finial_jewel', (0, 0, 0.73 * scale + h_house + 0.24 * scale),
                   (0.045 * scale, 0.045 * scale, 0.065 * scale), 'stone', 1)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 17: Literati Silk Hand Fan (泥金沉香骨团扇)
# ==============================================================================
def build_hand_fan(builder, x=0, y=0, z=0, rotDeg=0, scale=1.0):
    """
    Ming literati round silk/paper hand fan (团扇/合欢扇).
    Circular parchment surface with bamboo/wood hoop, dark wood handle, and silk tassel.
    """
    start_idx = len(builder.records)
    r_fan = 0.15 * scale

    # Circular paper/silk screen face
    builder.lathe('fan_face', (0, 0, r_fan + 0.12 * scale),
                  [(0, 0), (0.005 * scale, r_fan - 0.008 * scale), (0.005 * scale, 0)], 'paper', 32)
    # Outer bamboo hoop binding
    builder.ring('fan_outer_hoop', (0, 0, r_fan + 0.12 * scale),
                 r_fan, 0.006 * scale, 'wood')

    # Central spine and handle (扇柄)
    builder.beam('fan_spine', (0, 0, 0.05 * scale), (0, 0, r_fan * 2 + 0.10 * scale),
                 0.005 * scale, 'wood', 8)
    builder.beam('fan_handle', (0, 0, -0.08 * scale), (0, 0, 0.05 * scale),
                 0.008 * scale, 'wood', 8)
    # Tassel loop and silk fringe (流苏)
    builder.ring('fan_tassel_ring', (0, 0, -0.09 * scale), 0.012 * scale, 0.003 * scale, 'brass')
    builder.beam('fan_silk_tassel', (0, 0, -0.19 * scale), (0, 0, -0.09 * scale),
                 0.008 * scale, 'fabric', 6)

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 18: Four-Leaf Lattice Partition Door (明式步步锦格扇门)
# ==============================================================================
def build_lattice_door(builder, x=0, y=0, z=0, rotDeg=0, width=1.8, height=2.4):
    """
    Ming traditional four-leaf partition door (格扇门/隔扇门组).
    Upper two-thirds step-lattice windows, middle waist board, lower carved solid apron.
    """
    start_idx = len(builder.records)
    num_leaves = 4
    leaf_w = width / num_leaves
    leaf_h = height
    t_frame = 0.04
    d_frame = 0.05

    cur_x = -width / 2 + leaf_w / 2
    for i in range(num_leaves):
        lx = cur_x
        # Outer leaf stiles
        for side in [-1, 1]:
            builder.box('door_stile', (lx + side * (leaf_w / 2 - t_frame / 2), 0, leaf_h / 2),
                        (t_frame, d_frame, leaf_h), 'wood')

        # Dividing rails: top, upper lattice bottom, waist rail, bottom apron rail
        h_apron = 0.65
        h_waist = 0.22
        z_waist = h_apron
        z_lattice = h_apron + h_waist

        for rz in [t_frame / 2, h_apron, z_lattice, leaf_h - t_frame / 2]:
            builder.box('door_rail', (lx, 0, rz), (leaf_w - 2 * t_frame, d_frame, t_frame), 'wood')

        # Upper lattice window field
        lattice_h = leaf_h - z_lattice - t_frame
        # Fine muntin lattice
        cols = 3
        for c in range(1, cols):
            mx = lx - (leaf_w - 2 * t_frame) / 2 + c * ((leaf_w - 2 * t_frame) / cols)
            builder.beam('door_muntin_v', (mx, 0, z_lattice), (mx, 0, leaf_h - t_frame),
                         0.010, 'woodlight', 6)
        rows = 6
        for r in range(1, rows):
            mz = z_lattice + r * (lattice_h / rows)
            builder.beam('door_muntin_h', (lx - leaf_w / 2 + t_frame, 0, mz), (lx + leaf_w / 2 - t_frame, 0, mz),
                         0.010, 'woodlight', 6)

        # Middle waist board (绦环板)
        builder.box('door_waist_panel', (lx, 0, z_waist + h_waist / 2),
                    (leaf_w - 2 * t_frame - 0.02, 0.02, h_waist - 0.03), 'woodlight')

        # Lower solid carved skirt apron (裙板)
        builder.box('door_apron_panel', (lx, 0, t_frame + (h_apron - t_frame) / 2),
                    (leaf_w - 2 * t_frame - 0.02, 0.024, h_apron - t_frame - 0.02), 'lotus')

        # Brass hinges on stiles
        if i < num_leaves - 1:
            hx = lx + leaf_w / 2
            for hz in [0.45, 1.25, 2.05]:
                builder.box('door_brass_hinge', (hx, 0, hz), (0.024, 0.035, 0.05), 'brass')

        cur_x += leaf_w

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 19: Carved Cloud Timber Bracket Corbel (梁头卷草雕花雀替)
# ==============================================================================
def build_carved_beam_end(builder, x=0, y=0, z=0, rotDeg=0, scale=1.0):
    """
    Ming carved cloud timber bracket / corbel (雀替/梁头角花).
    Supports beam-column junction with curved cloud openwork.
    """
    start_idx = len(builder.records)
    L = 0.42 * scale
    H = 0.32 * scale
    th = 0.065 * scale

    # S-curved cloud brackets connecting horizontal beam to vertical post
    pts = [
        (0, 0, 0),
        (0.08 * scale, 0, -0.06 * scale),
        (0.22 * scale, 0, -0.16 * scale),
        (0.35 * scale, 0, -0.28 * scale),
        (L, 0, -H)
    ]
    for p_a, p_b in zip(pts[:-1], pts[1:]):
        builder.beam('corbel_cloud_body', p_a, p_b, 0.032 * scale, 'wood', 8)

    # Cloud scroll curled center
    builder.ring('corbel_cloud_curl', (0.16 * scale, 0, -0.12 * scale),
                 0.045 * scale, 0.015 * scale, 'woodlight')
    # Timber back mounting plate
    builder.box('corbel_back_plate', (L / 2, 0, -H / 2), (L, th, H), 'wood')

    if rotDeg != 0 or x != 0 or y != 0 or z != 0:
        T = trimesh.transformations.rotation_matrix(math.radians(rotDeg), [0, 0, 1])
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 20: Waterfront Mooring Bollard Stone Cap (码头系缆桩青石莲花座帽)
# ==============================================================================
def build_dock_pile_cap(builder, x=0, y=0, z=0, scale=1.0):
    """
    Heavy timber mooring pile topped with carved blue limestone lotus cap (系缆桩帽).
    """
    start_idx = len(builder.records)
    r_pile = 0.12 * scale
    h_pile = 0.85 * scale

    # Wooden piling stem
    builder.beam('dock_bollard_stem', (0, 0, 0), (0, 0, h_pile), r_pile, 'wood', 12)

    # Carved octagonal limestone lotus petal cap (莲花石帽)
    profile = [
        (0, 0),
        (0.02 * scale, r_pile * 1.05),
        (0.08 * scale, r_pile * 1.35),
        (0.16 * scale, r_pile * 1.45),
        (0.24 * scale, r_pile * 1.15),
        (0.30 * scale, r_pile * 0.4),
        (0.30 * scale, 0)
    ]
    builder.lathe('dock_bollard_stone_cap', (0, 0, h_pile), profile, 'stone', 8)

    # Thick hemp rope wrapped around pile (系缆粗绳)
    for z_rope in [h_pile * 0.35, h_pile * 0.45, h_pile * 0.55]:
        builder.ring('mooring_rope_loop', (0, 0, z_rope), r_pile * 1.08, 0.016 * scale, 'fabric')

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 21: Waterfront Reeds Bundle (水岸滩渚芦苇丛)
# ==============================================================================
def build_reed_bundle(builder, x=0, y=0, z=0, count=14, height=1.9, seed=33):
    """
    Clustered Jiangnan water reeds (滩渚芦苇丛).
    Slender jointed reed stalks, swaying feather plume plumes, and long blade leaves.
    """
    start_idx = len(builder.records)
    rng = random.Random(seed)

    for i in range(count):
        rx = rng.uniform(-0.35, 0.35)
        ry = rng.uniform(-0.35, 0.35)
        h = height * rng.uniform(0.75, 1.25)
        sway_x = rng.uniform(-0.18, 0.18)
        sway_y = rng.uniform(-0.18, 0.18)

        # Reed stalk
        p0 = (rx, ry, 0)
        p1 = (rx + sway_x * 0.5, ry + sway_y * 0.5, h * 0.6)
        p2 = (rx + sway_x, ry + sway_y, h)
        builder.beam('reed_stalk_lo', p0, p1, 0.007, 'leaf', 6)
        builder.beam('reed_stalk_hi', p1, p2, 0.005, 'leaf', 6)

        # Swaying fluffy plume flower head at tip (芦花穗)
        builder.sphere('reed_feather_plume', (rx + sway_x, ry + sway_y, h + 0.12),
                       (0.045, 0.045, 0.16), 'woodlight', 1)

        # Slender blade leaf branching off
        p_leaf = (rx + sway_x * 0.4 + rng.uniform(-0.15, 0.15),
                  ry + sway_y * 0.4 + rng.uniform(-0.15, 0.15),
                  h * 0.45)
        builder.beam('reed_leaf_blade', p1, p_leaf, 0.004, 'leaf2', 6)

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()


# ==============================================================================
# Component 22: Garden Rain Puddle Ripple (庭院青石积水涟漪)
# ==============================================================================
def build_rain_puddle(builder, x=0, y=0, z=0, rx=0.75, ry=0.48):
    """
    Thin reflective rainwater puddle on wet limestone paving with subtle ripple ring.
    """
    start_idx = len(builder.records)
    # Thin reflective water sheet
    m = trimesh.creation.cylinder(radius=1.0, height=0.008, sections=36)
    m.apply_scale([rx, ry, 1.0])
    m.apply_translation((0, 0, 0.004))
    builder.add('rain_water_puddle', m, 'water')

    # Water ripple ring
    builder.ring('puddle_ripple_ring', (0, 0, 0.006), rx * 0.65, 0.008, 'water')

    if x != 0 or y != 0 or z != 0:
        T = np.eye(4)
        T[:3, 3] = [x, y, z]
        for rec in builder.records[start_idx:]:
            m = builder.scene.geometry[rec['name']]
            m.apply_transform(T)
            rec['bounds'] = m.bounds.round(4).tolist()



# ==============================================================================
# Standalone Export and Catalog Production
# ==============================================================================
def manufacture_standalone_assets(output_dir=None):
    """
    Manufactures each component as an isolated GLB model with catalog metadata.
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / "generated_assets" / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog = {
        'schema': 'jiangnan.component-catalog.v1',
        'generated_by': 'source/component_factory.py',
        'components': []
    }

    definitions = [
        ('prop_four_panel_screen', 'Four-Panel Ming Folding Screen',
         lambda b: build_four_panel_screen(b, 0, 0, 0, width=2.2, height=1.85)),
        ('prop_altar_table', 'Ming Upturned Altar Table',
         lambda b: build_altar_table(b, 0, 0, 0, length=2.0, width=0.48, height=0.86)),
        ('prop_scholar_rock', 'Sculpted Scholar Rock with Stand',
         lambda b: build_scholar_rock(b, 0, 0, 0, scale=1.0)),
        ('prop_porcelain_vase', 'Celadon Plum Blossom Vase',
         lambda b: build_porcelain_vase(b, 0, 0, 0, scale=1.0)),
        ('env_bamboo_cluster', 'Jiangnan Garden Bamboo Cluster',
         lambda b: build_bamboo_cluster(b, 0, 0, 0, count=5, height=2.8)),
        ('arch_veranda_balustrade', 'Ming Meirengkao Veranda Balustrade',
         lambda b: build_veranda_balustrade(b, -1.2, 1.2, 0, 0)),
        ('prop_ming_daybed', 'Ming Daybed with Three-Sided Railing',
         lambda b: build_ming_daybed(b, 0, 0, 0, length=2.05, depth=1.05, height=0.76)),
        ('prop_brush_pot', 'Scholar Huanghuali Brush Pot with Brushes',
         lambda b: build_brush_pot(b, 0, 0, 0, scale=1.0)),
        ('prop_bamboo_scroll_basket', 'Woven Bamboo Scroll Basket',
         lambda b: build_bamboo_scroll_basket(b, 0, 0, 0, scale=1.0)),
        ('prop_lacquer_chest', 'Black Lacquer Chest with Brass Mounts',
         lambda b: build_lacquer_chest(b, 0, 0, 0, scale=1.0)),
        ('arch_roof_ridge_cap', 'Roof Ridge Chiwen Ornament',
         lambda b: build_roof_ridge_cap(b, 0, 0, 0, scale=1.0)),
        ('env_lotus_pot', 'Waterfront Stone Lotus Basin',
         lambda b: build_lotus_pot(b, 0, 0, 0, scale=1.0)),
        ('prop_scholar_desk', 'Scholar Large Painting Desk',
         lambda b: build_scholar_desk(b, 0, 0, 0, length=1.85, width=0.82, height=0.82)),
        ('prop_huanghuali_cabinet', 'Huanghuali Compound Wardrobe with Top Chest',
         lambda b: build_huanghuali_cabinet(b, 0, 0, 0, width=1.1, depth=0.55, height=2.05)),
        ('prop_footstool', 'Ming Footstool Roller Bench',
         lambda b: build_footstool(b, 0, 0, 0, length=0.62, width=0.32, height=0.22)),
        ('prop_moon_lamp', 'Moon Shadow Garden Stone Lantern',
         lambda b: build_moon_lamp(b, 0, 0, 0, scale=1.0)),
        ('prop_hand_fan', 'Literati Silk Hand Fan',
         lambda b: build_hand_fan(b, 0, 0, 0, scale=1.0)),
        ('arch_lattice_door', 'Four-Leaf Lattice Partition Door',
         lambda b: build_lattice_door(b, 0, 0, 0, width=1.8, height=2.4)),
        ('arch_carved_beam_end', 'Carved Cloud Timber Bracket Corbel',
         lambda b: build_carved_beam_end(b, 0, 0, 0, scale=1.0)),
        ('arch_dock_pile_cap', 'Waterfront Mooring Bollard Stone Cap',
         lambda b: build_dock_pile_cap(b, 0, 0, 0, scale=1.0)),
        ('env_reed_bundle', 'Waterfront Reeds Bundle',
         lambda b: build_reed_bundle(b, 0, 0, 0, count=14, height=1.9)),
        ('env_rain_puddle', 'Garden Rain Puddle Ripple',
         lambda b: build_rain_puddle(b, 0, 0, 0, rx=0.75, ry=0.48))
    ]

    for comp_id, label, func in definitions:
        b = ComponentBuilder(layer=comp_id)
        func(b)
        out_glb = output_dir / f"{comp_id}.glb"
        # Export GLB
        G = b.scene.copy()
        G.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
        out_glb.write_bytes(G.export(file_type='glb'))

        total_faces = sum(len(m.faces) for m in b.scene.geometry.values())
        total_verts = sum(len(m.vertices) for m in b.scene.geometry.values())
        bounds = b.scene.bounds.round(4).tolist()

        catalog['components'].append({
            'id': comp_id,
            'name': label,
            'file': str(out_glb.relative_to(output_dir.parent.parent)),
            'objects': len(b.records),
            'triangles': total_faces,
            'vertices': total_verts,
            'bounds': bounds,
            'dimensions': (np.ptp(b.scene.bounds, axis=0)).round(4).tolist()
        })
        print(f"Manufactured {comp_id}: {total_faces} tris, {len(b.records)} objects -> {out_glb.name}")

    catalog_path = output_dir.parent / "component_catalog.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Catalog written to {catalog_path}")
    return catalog

if __name__ == '__main__':
    manufacture_standalone_assets()
