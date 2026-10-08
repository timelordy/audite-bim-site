"""Render an authored architectural model, with no private BIM data.

Run with Blender's bundled Python. Transparent 2400px model layers are used
at no more than 2040px in the UHD composition, so details remain native.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    'bone': '#F3F5FF', 'edge': '#ADB8D9', 'glass': '#1A31B9',
    'ink': '#11154F', 'lime': '#DFFF00', 'steel': '#7184CB',
}
PARTS = []
GLASS = []
HIGHLIGHTS = []
BASE = []


def set_color(mat, hex_color):
    value = hex_color.lstrip('#')
    color = tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mat.diffuse_color = (*color, 1)
    linear = tuple(c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4 for c in color)
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*linear, 1)


def material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    set_color(mat, PALETTE[name])
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .22 if name == 'glass' else .4
    shader.inputs['Metallic'].default_value = .55 if name in ('glass', 'steel') else .03
    return mat


def boxes(name, specs, mat, parent=None, bevel=0):
    vertices, faces = [], []
    for location, dimensions in specs:
        x, y, z = location
        a, b, c = (v / 2 for v in dimensions)
        first = len(vertices)
        vertices.extend([(x + sx * a, y + sy * b, z + sz * c)
                         for sz in (-1, 1) for sy in (-1, 1)
                         for sx in (-1, 1)])
        faces.extend([tuple(first + i for i in face) for face in
                      [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
                       (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    if bevel:
        mod = obj.modifiers.new('Soft architectural edges', 'BEVEL')
        mod.width, mod.segments = bevel, 2
    return obj


def empty(name, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def make_floor(root, level, mats):
    floor = empty(f'Floor {level + 1}', root)
    floor.location.z = level * 1.13
    PARTS.append((floor, level))
    slabs = [((0, 0, 0), (7.6, 4.6, .14)),
             ((-2.1, 3.1, 0), (3.4, 2.0, .14))]
    slab = boxes(f'Slab {level}', slabs, mats['bone'], floor, .025)
    if level == 2:
        HIGHLIGHTS.append(slab)
    columns = [((x, y, .55), (.15, .15, 1.0))
               for x in (-3.45, -1.15, 1.15, 3.45) for y in (-2.0, 2.0)]
    columns += [((-3.4, 3.7, .55), (.15, .15, 1.0)),
                ((-.75, 3.7, .55), (.15, .15, 1.0))]
    boxes(f'Frame {level}', columns, mats['bone'], floor, .016)
    walls = [((-.65, 1.15, .48), (.09, 2.05, .82)),
             ((-2.05, .8, .48), (2.7, .09, .82)),
             ((2.0, .9, .48), (2.6, .08, .82)),
             ((-2.4, 2.65, .48), (1.8, .09, .82))]
    boxes(f'Partitions {level}', walls, mats['edge'], floor)
    glazing = [((x, -2.05, .53), (2.08, .035, .86))
               for x in (-2.3, 0, 2.3)]
    glazing += [((3.5, .0, .53), (.035, 3.92, .86))]
    GLASS.append(boxes(f'Glazing {level}', glazing, mats['glass'], floor))
    mullions = [((x, -2.08, .55), (.035, .07, .99))
                for x in (-3.45, -2.87, -2.3, -1.72, -1.15, -.57,
                          0, .57, 1.15, 1.72, 2.3, 2.87, 3.45)]
    GLASS.append(boxes(f'Mullions {level}', mullions, mats['steel'], floor))
    services = [((.65, .1, .88), (5.25, .14, .14)),
                ((1.6, -.72, .88), (.14, 1.64, .14)),
                ((-1.8, 1.32, .88), (.14, 2.44, .14))]
    boxes(f'Service network {level}', services, mats['lime'], floor, .018)
    steps = [((-2.25 + i * .095, 2.95, .1 + i * .069),
              (.19, .72, .105)) for i in range(13)]
    boxes(f'Stairs {level}', steps, mats['bone'], floor)
    return floor


def build_model(mats):
    root = empty('Audite architectural demonstration')
    for i in range(6):
        make_floor(root, i, mats)
    roof = empty('Roof assembly', root)
    roof.location.z = 6 * 1.13
    PARTS.append((roof, 6))
    boxes('Roof slabs', [((0, 0, 0), (7.6, 4.6, .14)),
                         ((-2.1, 3.1, 0), (3.4, 2.0, .14))],
          mats['bone'], roof, .025)
    boxes('Roof equipment', [((-1.8, .6, .28), (1.05, 1.3, .48)),
                              ((.05, .65, .25), (1.25, 1.1, .42)),
                              ((1.7, 1.05, .15), (.9, 1.6, .2))],
          mats['steel'], roof, .035)
    boxes('Roof ducts', [((-.8, -.55, .21), (3.8, .18, .18)),
                         ((-2.5, .05, .21), (.18, 1.2, .18))],
          mats['lime'], roof, .018)
    BASE.append(boxes('Foundation', [((0, .8, -.3), (9.15, 7.3, .35))],
                      mats['edge'], root, .06))
    return root


def area_light(name, position, energy, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = energy, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, 3)) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def configure_scene(size, engine):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE' if engine == 'eevee' else 'BLENDER_WORKBENCH'
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 20
    scene.render.film_transparent = True
    scene.eevee.taa_render_samples = 16
    scene.display.render_aa = '16'
    shade = scene.display.shading
    shade.light, shade.color_type = 'STUDIO', 'MATERIAL'
    shade.show_shadows = True
    shade.show_cavity = True
    shade.cavity_type = 'BOTH'
    shade.curvature_ridge_factor = 1.1
    shade.curvature_valley_factor = 1.0
    shade.show_specular_highlight = True
    shade.show_object_outline = False
    scene.view_settings.view_transform = 'AgX'
    scene.world.color = (.15, .15, .15)
    area_light('Large soft key', (-7, -10, 15), 1700, 8)
    area_light('Architectural fill', (8, -4, 10), 1200, 7)
    area_light('Rim light', (2, 8, 13), 2100, 8)
    camera_data = bpy.data.cameras.new('Architectural camera')
    camera = bpy.data.objects.new('Architectural camera', camera_data)
    bpy.context.collection.objects.link(camera)
    camera_data.type = 'ORTHO'
    scene.camera = camera
    return scene, camera


def pose(root, camera, shot, progress, mats):
    set_color(mats['bone'], '#2543C5' if shot == 2 else PALETTE['bone'])
    set_color(mats['edge'], '#102373' if shot == 2 else PALETTE['edge'])
    set_color(mats['lime'], '#FFFFFF' if shot == 2 else PALETTE['lime'])
    explosion = (.22 + .43 * math.sin(progress * math.pi / 2)) if shot == 2 else 0
    for obj, level in PARTS:
        obj.location.z = level * (1.13 + explosion)
        obj.location.x = math.sin(progress * math.pi) * .16 * level if shot == 2 else 0
        obj.hide_render = (shot == 1 and level not in (1, 2, 3)) or (shot == 3 and level != 2)
        for child in obj.children:
            child.hide_render = obj.hide_render
    for obj in BASE:
        obj.hide_render = shot in (1, 3)
    for obj in GLASS:
        obj.hide_render = shot != 0
    for obj in HIGHLIGHTS:
        obj.data.materials[0] = mats['lime'] if shot in (2, 3) else mats['bone']
    root.rotation_euler.z = math.radians(-14 + progress * 28 + (12 if shot == 1 else 0))
    target_z = 3.55 + (1.45 if shot == 2 else 0)
    if shot == 1:
        target_z = 2.9
    if shot == 3:
        target_z = 2.5
    camera.location = (12, -17, 12.6 if shot != 3 else 24)
    target = Vector((0, .75, target_z))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = 14.9 if shot != 2 else 18
    if shot == 1:
        camera.data.ortho_scale = 12.5
    if shot == 3:
        camera.data.ortho_scale = 11.6


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--size', type=int, default=2400)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--engine', default='eevee', choices=('eevee', 'workbench'))
    options = parser.parse_args(args)
    directory = Path(options.out)
    directory.mkdir(parents=True, exist_ok=True)
    scene, camera = configure_scene(options.size, options.engine)
    mats = {name: material(name) for name in PALETTE}
    root = build_model(mats)
    count = 1 if options.test else 75
    for shot in range(4):
        for frame in range(count):
            path = directory / f'shot-{shot}-{frame:03d}.png'
            if path.exists():
                continue
            pose(root, camera, shot, .5 if options.test else frame / 74, mats)
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
        print(f'COMPLETED SHOT {shot}', flush=True)


if __name__ == '__main__':
    main()
