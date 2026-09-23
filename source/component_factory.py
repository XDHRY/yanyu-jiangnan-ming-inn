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
         lambda b: build_veranda_balustrade(b, -1.2, 1.2, 0, 0))
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
