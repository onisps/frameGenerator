import cadquery as cq
import numpy as np
from jupyter_cadquery.viewer.client import show, show_object
import matplotlib.colors as mcolors
import time


def model_drawer(
        diameter=18,
        repeat=7,
):
    def create_cell(h1, h2, h3, l1, l2, arc_percent, ang1, ang2, fillet):
        def create_cell_zero_arc(h1, h2, h3, l1, l2, ang1, ang2, fillet):
            cell_size_height = h1 + h2 + h3 + np.cos(ang1) * l1 + np.cos(ang1) * l2
            s = (cq.Sketch()
                 .segment(
                (0, 0),
                (0, h1)
            )  # a_up
                 .segment(
                (0, h1),
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1)
            )  # b_up
                 .segment(
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1),
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1 + h2)
            )  # c_up
                 .segment(
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1 + h2),
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1))
            )  # d_up
                 .segment(
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1)),
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3)
            )  # e_up
                 .segment(
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3),
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3)
            )  # up
                 .segment(
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3),
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1))
            )  # e_down
                 .segment(
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1)),
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1 + h2)
            )  # d_down
                 .segment(
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1 + h2),
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1)
            )  # c_down
                 .segment(
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1),
                (w, h1)
            )  # b_down
                 .segment(
                (w, h1),
                (w, 0)
            )  # a_down
                 .close().assemble().vertices().fillet(fillet)
                 )
            return s, cell_size_height

        def create_cell_arc(h1, h2, h3, l1, l2, arc_percent, ang1, ang2, fillet):
            cell_size_height = h1 + h2 + h3 + np.cos(ang1) * l1 + np.cos(ang1) * l2
            s = (cq.Sketch()
                 .segment(
                (0, 0),
                (0, h1)
            )  # a_up
                 .segment(
                (0, h1),
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1)
            )  # b_up
                 .arc(
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1),
                (l1 * np.sin(-ang1) - arc_percent,
                 ((l1 * np.cos(ang1) + h1) + (l1 * np.cos(ang1) + h1 + h2)) / 2),
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1 + h2)
            )  # c_up
                 .segment(
                (l1 * np.sin(-ang1), l1 * np.cos(ang1) + h1 + h2),
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1))
            )  # d_up
                 .segment(
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1)),
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3)
            )  # e_up
                 .segment(
                (0, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3),
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3)
            )  # up
                 .segment(
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3),
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1))
            )  # e_down
                 .segment(
                (w, l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1)),
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1 + h2)
            )  # d_down
                 .arc(
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1 + h2),
                (w + l1 * np.sin(ang1) + arc_percent,
                 ((l1 * np.cos(ang1) + h1 + h2) + (l1 * np.cos(ang1) + h1)) / 2),
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1)
            )  # c_down
                 .segment(
                (w + l1 * np.sin(ang1), l1 * np.cos(ang1) + h1),
                (w, h1)
            )  # b_down
                 .segment(
                (w, h1),
                (w, 0)
            )  # a_down
                 .close().assemble()
                 ).reset()
            s.vertices().fillet(fillet).reset()
            return s, cell_size_height

        if arc_percent != 0:
            return create_cell_arc(h1, h2, h3, l1, l2, arc_percent, ang1, ang2, fillet)
        else:
            return create_cell_zero_arc(h1, h2, h3, l1, l2, ang1, ang2, fillet)

    # hex sketch pattern

    ang1 = np.deg2rad(30)
    e1 = 0.1
    h1 = 0.25
    l1 = 2
    h2 = 0.5
    l2 = 2
    h3 = 0.25
    e2 = 1
    w = 0.5
    arc_offset = 0.05
    ang2 = np.deg2rad(45) / 2 / (e2 / e1)

    cell_size_height = h1 + h2 + h3 + np.cos(ang1) * l1 + np.cos(ang1) * l2
    print(cell_size_height)
    s, cell_size_height = create_cell(h1, h2, h3, l1, l2, arc_offset, ang1, ang2, 0.1)

    padding = 0.5
    height = 4 * (l1 * np.cos(ang1) + h1 + h2 + l2 * np.cos(ang1) + h3) - padding - 3 * padding / 4
    show(s)
    return
    radius = diameter / 2
    cyl_out = cq.Workplane('XY').cylinder(height=height, radius=radius, direct=cq.Vector((0, 0, 1)))
    cyl_cut = cq.Workplane('XY').cylinder(height=height, radius=radius - 0.5, direct=cq.Vector((0, 0, 1)))
    cyl = cyl_out.cut(cyl_cut)
    mesh = cq.Workplane('XY')
    mesh_sketch = cq.Workplane('XY')
    if repeat > 0:

        rot = 360 / repeat
        mesh = (
            mesh_sketch.union(
                mesh_sketch
                .workplane()
                .placeSketch(s)
                .extrude(1 * radius)
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .translate((0, radius, -2 * height / 4 + padding))

            )
        )
        mesh_pattern = mesh

        for i in range(int(repeat)):
            mesh_pattern = mesh_pattern.union(
                mesh.rotate((0, 0, 0), (0, 0, 1), i * rot)
            )

        mesh_pattern_inv = (mesh_pattern
                            .translate((0, 0, -cell_size_height / 2))
                            .rotate((0, 0, 0), (0, 0, 1), rot / 2))

        for flag in [0, 1]:
            if flag == 0:
                mesh_to_cut = mesh_pattern
            else:
                mesh_to_cut = mesh_pattern_inv
            for hi in range(int(np.floor(height / (cell_size_height * 0.5 + padding * 2)))):
                cyl = (
                    cyl.cut(
                        mesh_to_cut
                    )
                )
                mesh_to_cut = (
                    mesh_to_cut
                    .translate((0, 0, padding + cell_size_height))
                )
                # show(cyl, mesh_to_cut)
                # time.sleep(1)
    else:
        mesh = (cq.Workplane('XY')
                .circle(radius)
                .extrude(height)
                .faces(">Z")
                .workplane()
                .add(s)
                .extrude(1)  # Example extrusion depth
                )
        show(cyl, mesh)
        mesh = (
            mesh_sketch.union(
                mesh_sketch
                .workplane()
                .placeSketch(s)
                .extrude(2 * radius)
                .rotate((0, 0, 0), (-1, 0, 0), 90)
                .translate((0, -radius, -(0.5 * height - 0.5 * cell_size_height)))

            )
        )
        mesh_to_cut = mesh
        for hi in range(int(np.floor(height / (cell_size_height * 0.5 + padding * 2)))):
            mesh_to_cut = (
                mesh
                .translate((0, 0, hi * (padding + cell_size_height)))
            )
            cyl = (
                cyl.cut(
                    mesh_to_cut
                    # .rotate((0, 0, 0), (0, 0, 1), rot * i)
                )
            )
            show(cyl, mesh_to_cut)
            time.sleep(1)
    show(cyl)
    cq.exporters.export(cyl, './geoms/cyl3.stp', 'STEP')
