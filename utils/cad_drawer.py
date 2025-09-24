import os
from os.path import exists
from types import SimpleNamespace

import cadquery as cq
import numpy as np
from jupyter_cadquery.viewer.client import show, show_object
from typing import Union
import math

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

def _as_shape(obj) -> cq.Shape:
    """Безопасно извлечь cq.Shape из Workplane/Shape."""
    if isinstance(obj, cq.Workplane):
        # если внутри один солид — .solids().val()
        sols = obj.solids()
        if len(sols.objects) > 0:
            return sols.val()
        # иначе пробуем склеить и взять единственный shape
        return obj.combineSolids().val()
    return obj  # уже Shape/Compound

def _radial_compound(base: Union[cq.Workplane, cq.Shape, cq.Compound], count: int, step_deg: float) -> cq.Compound:
    """Быстрый радиальный паттерн из копий base (Shape)."""
    base = _as_shape(base)
    copies = [base.rotate((0, 0, 0), (0, 0, 1), i * step_deg) for i in range(count)]
    return cq.Compound.makeCompound(copies)


def model_drawer(local_geometry_cfg, file_name) -> float:
    # -*-*- parce cfg -*-*-
    local_geometry_cfg = SimpleNamespace(**local_geometry_cfg)
    diameter = local_geometry_cfg.diameter
    h1 = local_geometry_cfg.h1
    h2 = local_geometry_cfg.h2
    h3 = local_geometry_cfg.h3
    h2_3rd_layer = local_geometry_cfg.h2_3rd_layer
    width_low_cut = local_geometry_cfg.width_low_cut
    cell_height_1st_layer =local_geometry_cfg.cell_height_1st_layer
    repeat =local_geometry_cfg.repeat
    fillet_a =local_geometry_cfg.fillet_a
    fillet_b =local_geometry_cfg.fillet_b
    fillet_c =local_geometry_cfg.fillet_c
    assymetry_1st_layer =local_geometry_cfg.assymetry_1st_layer
    padding = local_geometry_cfg.padding
    arc_offset = local_geometry_cfg.arc_offset

    # calc size of cell
    circle_length = 2 * np.pi * diameter / 2
    cell_size_width = (circle_length) / repeat - 3 * padding

    length_1 = np.round((cell_height_1st_layer - (h1 + h2 + h3)) / 2 * assymetry_1st_layer, 4)
    length_2 = np.round((cell_height_1st_layer - (h1 + h2 + h3)) - length_1, 4)
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


    cyl_out = cq.Workplane('XY').cylinder(height=height, radius=radius, direct=cq.Vector((0, 0, 1)))
    cyl_cut = cq.Workplane('XY').cylinder(height=height, radius=radius - 0.5, direct=cq.Vector((0, 0, 1)))
    cyl = cyl_out.cut(cyl_cut).translate((0, 0, (height - height_1st_layer) / 2))
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


    mesh_pattern = _radial_compound(mesh_pattern, repeat, rot)
    mesh_pattern_inv = _radial_compound(mesh_pattern_inv, repeat, rot)
    mesh_low_cut = _radial_compound(mesh_low_cut, repeat, rot)
    mesh_2nd_layer = _radial_compound(mesh_2nd_layer, repeat, rot)
    mesh_3rd_layer = _radial_compound(mesh_3rd_layer, repeat, rot)
    mesh_top_cut = _radial_compound(mesh_top_cut, repeat, rot)

    all_cuts = cq.Compound.makeCompound(
        [mesh_pattern_inv, mesh_pattern, mesh_low_cut, mesh_2nd_layer, mesh_3rd_layer, mesh_top_cut]
    )
    result = cyl.cut(all_cuts)
    # show(all_cuts, result)
# time.sleep(15)
#     bbox = _as_shape(result).BoundingBox()
    # print(f'bbox is: [({bbox.xmin}, {bbox.ymin}, {bbox.zmin}), ({bbox.xmax}, {bbox.ymax}, {bbox.zmax})]')
    os.makedirs('geoms',exist_ok=True)
    if result.solids().size() > 1:
        raise Exception(f'Fail in model generation. With this parameters get {result.solids().size()}')
    cq.exporters.export(result, f'./geoms/{file_name}_full.stp', 'STEP')

    # ---- функция получения сектора ----
    def sector_of_cyl(solid: cq.Workplane,
                      outer_radius: float,
                      repeat: int,
                      start_angle_deg: float = 0.0) -> cq.Workplane:
        """
        Возвращает сектор исходного тела 'solid' с центральным углом 360/repeat,
        начиная от направления 'start_angle_deg' (в градусах, 0 по оси +X).
        Техника: строим 2D сектор на плоскости XY и делаем пересечение (intersect).
        """
        if repeat <= 0:
            raise ValueError("repeat должен быть положительным целым числом")
        theta = 360.0 / float(repeat)

        # Радиус эскиза сектора выбираем чуть больше внешнего радиуса,
        # чтобы маска гарантированно покрывала сечение цилиндра.
        R = outer_radius + 5.0

        # Конечная точка дуги сектора в декартовых координатах
        end_x = R * math.cos(math.radians(start_angle_deg + theta))
        end_y = R * math.sin(math.radians(start_angle_deg + theta))

        # Строим «пирог» (круговой сектор) на XY:
        # из центра -> по радиусу на угол start -> дуга на угол theta -> назад в центр.
        # Используем radiusArc, чтобы получить дугу заданного радиуса R.
        sector_wire = (
            cq.Workplane("XY")
            .moveTo(0, 0)
            .lineTo(R * math.cos(math.radians(start_angle_deg)),
                    R * math.sin(math.radians(start_angle_deg)))
            .radiusArc((end_x, end_y), R)
            .lineTo(0, 0)
            .close()
        )

        # Выдавливаем сектор симметрично по Z, чтобы наверняка перекрыть исходное тело
        # (extrude(..., both=True) — симметричная экструзия).
        sector_prism = sector_wire.extrude(2.0 * max(1.0, solid.val().BoundingBox().zlen), both=True)

        # Пересечение маски с исходным телом
        return sector_prism.intersect(solid)
    result_sector = sector_of_cyl(result, outer_radius=radius, repeat=repeat, start_angle_deg=0.0)
    # show(result_sector)
    cq.exporters.export(result_sector, f'./geoms/{file_name}.stp', 'STEP')

    return height
