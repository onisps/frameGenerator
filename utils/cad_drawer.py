import cadquery as cq
import numpy as np
from jupyter_cadquery.viewer.client import show, show_object
import matplotlib.colors as mcolors
import time


def create_cell(w, h1, h2, h3, l1, l2, arc_offset, offset_l, fillet_a, fillet_b, fillet_c):
    def create_cell_no_arc():
        a0 = (w / 2, 0)
        a1 = (-w / 2, 0)

        b0 = (w / 2, h1)
        b1 = (-w / 2, h1)

        c0 = (offset_l + w / 2, l1 + h1)
        c1 = (-1 * (offset_l + w / 2), l1 + h1)

        c_ark0 = (offset_l + w / 2 + arc_offset,
                  l1 + h1 + h2 / 2)
        c_ark1 = (-1 * (offset_l + w / 2 + arc_offset),
                  l1 + h1 + h2 / 2)

        d0 = (offset_l + w / 2, l1 + h1 + h2)
        d1 = (-1 * (offset_l + w / 2), l1 + h1 + h2)

        e0 = (w / 2, l1 + h1 + h2 + l2)
        e1 = (-w / 2, l1 + h1 + h2 + l2)

        top0 = (w / 2, l1 + h1 + h2 + l2 + h3)
        top1 = (-w / 2, l1 + h1 + h2 + l2 + h3)

        sketch = (cq.Sketch()
                  .segment(a0, b0)  # a_up
                  .segment(b0, c0)  # b_up
                  .segment(c0, d0)  # c_up
                  .segment(d0, e0)  # d_up
                  .segment(e0, top0)  # e_up
                  .segment(top0, top1)  # e_up
                  .segment(top1, e1)  # e_down
                  .segment(e1, d1)  # d_down
                  .segment(d1, c1)  # c_down
                  .segment(c1, b1)  # b_down
                  .segment(b1, a1)  # b_down
                  .close().assemble()
                  ).reset()
        # sketch.vertices().fillet(fillet).reset()
        if fillet_a > 0:
            sketch.vertices(cq.NearestToPointSelector(a0)).fillet(fillet_a).reset()
            sketch.vertices(cq.NearestToPointSelector(a1)).fillet(fillet_a).reset()
            sketch.vertices(cq.NearestToPointSelector(top0)).fillet(fillet_a).reset()
            sketch.vertices(cq.NearestToPointSelector(top1)).fillet(fillet_a).reset()
        if fillet_b > 0:
            sketch.vertices(cq.NearestToPointSelector(b0)).fillet(fillet_b).reset()
            sketch.vertices(cq.NearestToPointSelector(b1)).fillet(fillet_b).reset()
            sketch.vertices(cq.NearestToPointSelector(e0)).fillet(fillet_b).reset()
            sketch.vertices(cq.NearestToPointSelector(e1)).fillet(fillet_b).reset()
        if fillet_c > 0:
            sketch.vertices(cq.NearestToPointSelector(c0)).fillet(fillet_c).reset()
            sketch.vertices(cq.NearestToPointSelector(d0)).fillet(fillet_c).reset()
            sketch.vertices(cq.NearestToPointSelector(d1)).fillet(fillet_c).reset()
            sketch.vertices(cq.NearestToPointSelector(c1)).fillet(fillet_c).reset()

        cell_size_height = a0[1] + top0[1]
        cell_size_width = np.abs(c_ark0[0]) + np.abs(c_ark1[0])
        if l1 > l2:
            ark_len = top0[1] - c_ark0[1]
        else:
            ark_len = c_ark0[1] - a0[1]
        return sketch, cell_size_height, cell_size_width, ark_len, d0[1], b0[1]

    def create_cell_arc():
        a0 = (w / 2, 0)
        a1 = (-w / 2, 0)

        b0 = (w / 2, h1)
        b1 = (-w / 2, h1)

        c0 = (offset_l + w / 2, l1 + h1)
        c1 = (-1 * (offset_l + w / 2), l1 + h1)

        c_ark0 = (offset_l + w / 2 + arc_offset,
                  l1 + h1 + h2 / 2)
        c_ark1 = (-1 * (offset_l + w / 2 + arc_offset),
                  l1 + h1 + h2 / 2)
        d0 = (offset_l + w / 2, l1 + h1 + h2)
        d1 = (-1 * (offset_l + w / 2), l1 + h1 + h2)

        e0 = (w / 2, l1 + h1 + h2 + l2)
        e1 = (-w / 2, l1 + h1 + h2 + l2)

        top0 = (w / 2, l1 + h1 + h2 + l2 + h3)
        top1 = (-w / 2, l1 + h1 + h2 + l2 + h3)

        sketch = (cq.Sketch()
                  .segment(a0, b0)  # a_up
                  .segment(b0, c0)  # b_up
                  .arc(c0, c_ark0, d0)  # c_up
                  .segment(d0, e0)  # d_up
                  .segment(e0, top0)  # e_up
                  .segment(top0, top1)  # e_up
                  .segment(top1, e1)  # e_down
                  .segment(e1, d1)  # d_down
                  .arc(d1, c_ark1, c1)  # c_down
                  .segment(c1, b1)  # b_down
                  .segment(b1, a1)  # b_down
                  .close().assemble()
                  ).reset()
        # sketch.vertices().fillet(fillet).reset()
        if fillet_a > 0:
            sketch.vertices(cq.NearestToPointSelector(a0)).fillet(fillet_a).reset()
            sketch.vertices(cq.NearestToPointSelector(a1)).fillet(fillet_a).reset()
            sketch.vertices(cq.NearestToPointSelector(top0)).fillet(fillet_a).reset()
            sketch.vertices(cq.NearestToPointSelector(top1)).fillet(fillet_a).reset()
        if fillet_b > 0:
            sketch.vertices(cq.NearestToPointSelector(b0)).fillet(fillet_b).reset()
            sketch.vertices(cq.NearestToPointSelector(b1)).fillet(fillet_b).reset()
            sketch.vertices(cq.NearestToPointSelector(e0)).fillet(fillet_b).reset()
            sketch.vertices(cq.NearestToPointSelector(e1)).fillet(fillet_b).reset()
        if fillet_c > 0:
            sketch.vertices(cq.NearestToPointSelector(c0)).fillet(fillet_c).reset()
            sketch.vertices(cq.NearestToPointSelector(d0)).fillet(fillet_c).reset()
            sketch.vertices(cq.NearestToPointSelector(d1)).fillet(fillet_c).reset()
            sketch.vertices(cq.NearestToPointSelector(c1)).fillet(fillet_c).reset()

        cell_size_height = a0[1] + top0[1]
        cell_size_width = np.abs(c_ark0[0]) + np.abs(c_ark1[0])
        if l1 > l2:
            ark_len = top0[1] - c_ark0[1]
        else:
            ark_len = c_ark0[1] - a0[1]
        return sketch, cell_size_height, cell_size_width, ark_len, d0[1], c0[1]

    if arc_offset != 0:
        return create_cell_arc()
    else:
        return create_cell_no_arc()


def model_drawer(
        h1=0.3,
        h2=1,
        h3=0.3,
        h2_3rd_layer=4,
        width_low_cut=0.5,
        cell_height_1st_layer=7,
        repeat=12,
        fillet_a=0.02,
        fillet_b=0.3,
        fillet_c=0.4,
        assymetry_1st_layer=0.5,
        padding=0.5,
        arc_offset=0.1
):
    diameter = 29
    # calc size of cell
    circle_length = 2 * np.pi * diameter / 2
    cell_size_width = (circle_length) / repeat - 3 * padding
    for assymetry_1st_layer in [0.5, 1.0, 1.5]:
        for arc_offset in [0.30, 0.15, 0, -0.15, -0.3]:
            length_1 = np.round((cell_height_1st_layer - (h1 + h2 + h3)) / 2 * assymetry_1st_layer, 4)
            length_2 = np.round((cell_height_1st_layer - (h1 + h2 + h3)) - length_1, 4)
            print(
                f'ass > {assymetry_1st_layer} | l1 > {length_1} | l2 > {length_2} | summ: {h1 + h2 + h3 + length_1 + length_2} | ',
                end='')
            tri_a = 0.5 * (cell_size_width - width_low_cut)

            # draw cell
            s_low_cut, cell_size_low_cut, _, arc_line_low_cut, d_point_low_cut, c_point_low_cut = create_cell(
                width_low_cut, h1, 5 * h2, h3,
                length_1, length_2,
                0,
                tri_a, fillet_a, fillet_b,
                fillet_c)

            s_1st_layer, _, _, arc_line_1st_layer, _, _ = create_cell(
                width_low_cut, h1, h2, h3,
                length_1, length_2,
                arc_offset,
                tri_a, fillet_a, fillet_b, fillet_c)

            s_2nd_layer, cell_size_2nd_layer, _, arc_line_2nd_layer, _, _ = create_cell(
                width_low_cut, h1, h2, h1,
                length_1, length_1,
                arc_offset,
                tri_a, fillet_a, fillet_b, fillet_c)

            s_3rd_layer, cell_size_3rd_layer, _, _, d_point_3rd_layer, _ = create_cell(
                width_low_cut, h1, h2_3rd_layer, h1,
                length_1, length_1,
                arc_offset,
                tri_a, fillet_a, fillet_b, fillet_c)
            s_top_cut, cell_size_top_cut, _, _, d_point_top_cut, _ = create_cell(
                width_low_cut, h1, 5 * h2, h3,
                length_1, length_2,
                0,
                tri_a, fillet_a, fillet_b,
                fillet_c)
            radius = diameter / 2
            if assymetry_1st_layer < 1:
                height_1st_layer = cell_height_1st_layer + arc_line_1st_layer + 2 * padding
                direct_shift = (0, radius, -height_1st_layer / 2 + 0.75 * padding)
                inversed_shift = (0, radius, -height_1st_layer / 2 + 0.75 * padding)
                direct_shift_2nd_layer = (0, radius, -height_1st_layer / 2 + cell_height_1st_layer + 1.75 * padding)
                direct_shift_3rd_layer = (
                    0,
                    radius,
                    -height_1st_layer / 2 + cell_height_1st_layer + arc_line_2nd_layer + 2.5 * padding
                )
                direct_low_cut = (0, radius, -height_1st_layer / 2 + h1 + length_1 + padding)
                direct_top_cut = (0, 0, arc_line_2nd_layer + d_point_3rd_layer + 0.5 * padding)
            elif assymetry_1st_layer == 1:
                height_1st_layer = cell_height_1st_layer + arc_line_1st_layer + 2 * padding
                direct_shift = (0, radius, -height_1st_layer / 2 + 0.75 * padding)
                inversed_shift = (0, radius, -height_1st_layer / 2 + 0.75 * padding)
                direct_shift_2nd_layer = (0, radius, -height_1st_layer / 2 + cell_height_1st_layer + 1.75 * padding)
                direct_shift_3rd_layer = (
                    0,
                    radius,
                    -height_1st_layer / 2 + cell_height_1st_layer + arc_line_2nd_layer + 3 * padding
                )
                direct_low_cut = (0, radius, -height_1st_layer / 2 + h1 + length_1 + padding)
                direct_top_cut = (0, 0, arc_line_2nd_layer + d_point_3rd_layer + padding)
            else:
                height_1st_layer = cell_height_1st_layer + (cell_height_1st_layer - arc_line_1st_layer) + 2.5 * padding
                direct_shift = (0, radius, -height_1st_layer / 2 + padding)
                inversed_shift = (0, radius, -cell_height_1st_layer + 1.75 * padding)
                direct_shift_2nd_layer = (0, radius, -height_1st_layer / 2 + cell_height_1st_layer + 2 * padding)
                direct_shift_3rd_layer = (
                    0,
                    radius,
                    -height_1st_layer / 2 + cell_height_1st_layer + arc_line_2nd_layer + 3 * padding
                )
                direct_low_cut = (0, radius, -(cell_size_low_cut - d_point_low_cut))
                direct_top_cut = (0, 0, arc_line_2nd_layer + d_point_3rd_layer + padding)
            height_2nd_layer = arc_line_2nd_layer
            height_3rd_layer = d_point_3rd_layer + 0.5 * padding
            height = height_1st_layer + height_2nd_layer + height_3rd_layer
            print(f'total height > {height} | cell height > {cell_height_1st_layer}')

            cyl_out = cq.Workplane('XY').cylinder(height=height, radius=radius, direct=cq.Vector((0, 0, 1)))
            cyl_cut = cq.Workplane('XY').cylinder(height=height, radius=radius - 0.5, direct=cq.Vector((0, 0, 1)))
            cyl = cyl_out.cut(cyl_cut).translate((0, 0, (height - height_1st_layer) / 2))
            # mesh = cq.Workplane('XY')
            mesh_sketch = cq.Workplane('XY')

            rot = 360 / repeat
            mesh_low_cut = (
                cq.Workplane('XY')
                .workplane()
                .placeSketch(s_low_cut)
                .extrude(2)
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .rotate((0, 0, 0), (0, 1, 0), 180)
                .translate(direct_low_cut)
                .rotate((0, 0, 0), (0, 0, 1), rot / 2)
            )

            mesh = (
                mesh_sketch.union(
                    mesh_sketch
                    .workplane()
                    .placeSketch(s_1st_layer)
                    .extrude(2)
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .translate(direct_shift)

                )
            )

            mesh_inversed = (
                mesh_sketch.union(
                    mesh_sketch
                    .workplane()
                    .placeSketch(s_1st_layer)
                    .extrude(2)
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .translate(inversed_shift)
                    .rotate((0, 0, 0), (0, 1, 0), 180)
                    .rotate((0, 0, 0), (0, 0, 1), rot / 2)
                )
            )

            mesh_2nd_layer = (
                mesh_sketch.union(
                    mesh_sketch
                    .workplane()
                    .placeSketch(s_2nd_layer)
                    .extrude(2)
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .translate(direct_shift_2nd_layer)
                )
            )

            mesh_3rd_layer = (
                mesh_sketch.union(
                    mesh_sketch
                    .workplane()
                    .placeSketch(s_3rd_layer)
                    .extrude(2)
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .translate(direct_shift_3rd_layer)
                    .rotate((0, 0, 0), (0, 0, 1), rot / 2)
                )
            )
            mesh_top_cut = (
                mesh_sketch.union(
                    mesh_sketch
                    .workplane()
                    .placeSketch(s_top_cut)
                    .extrude(2)
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .translate(direct_shift_2nd_layer)
                    .translate(direct_top_cut)
                )
            )
            # show(cyl, mesh, mesh_inversed, mesh_low_cut, mesh_2nd_layer, mesh_3rd_layer, mesh_top_cut)
            # continue

            mesh_pattern = mesh
            mesh_pattern_inv = mesh_inversed
            for i in range(int(repeat)):
                mesh_pattern = mesh_pattern.union(
                    mesh_pattern.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )
                mesh_pattern_inv = mesh_pattern_inv.union(
                    mesh_pattern_inv.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )
                mesh_low_cut = mesh_low_cut.union(
                    mesh_low_cut.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )
                mesh_2nd_layer = mesh_2nd_layer.union(
                    mesh_2nd_layer.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )
                mesh_3rd_layer = mesh_3rd_layer.union(
                    mesh_3rd_layer.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )
                mesh_top_cut = mesh_top_cut.union(
                    mesh_top_cut.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )
            cyl = (
                cyl.cut(mesh_pattern_inv)
                .cut(mesh_pattern)
                .cut(mesh_low_cut)
                .cut(mesh_2nd_layer)
                .cut(mesh_3rd_layer)
                .cut(mesh_top_cut)
            )
            show(cyl)
        # time.sleep(15)
            cq.exporters.export(cyl, f'./geoms/full_frame_arc_{arc_offset}_ass_{assymetry_1st_layer}.stp', 'STEP')
