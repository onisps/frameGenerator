import cadquery as cd
import numpy as np
from jupyter_cadquery.viewer.client import show, show_object
import matplotlib.colors as mcolors
import time


def model_drawer(
        diameter=18,
        height=20,
        repeat=7,
        cell_size_height=8,
        cell_size_rad=0.2,

):
    padding = 0.5
    radius = diameter / 2
    cyl_out = cd.Workplane('XY').cylinder(height=height, radius=radius, direct=cd.Vector((0, 0, 1)))
    cyl_cut = cd.Workplane('XY').cylinder(height=height, radius=radius - 0.5, direct=cd.Vector((0, 0, 1)))
    cyl = cyl_out.cut(cyl_cut)

    # pilon sketch pattern
    # s = (
    #     cd.Sketch().arc((0, 0), cell_size_rad, 0.0, 360.0)
    #     .arc((0, cell_size_height), cell_size_rad, 0.0, 360.0)
    #     .hull()
    # )

    # rhombus sketch pattern
    # s = cd.Sketch().arc((0, 0), cell_size_rad, 0.0, 360.0).segment((cell_size_height / 2, cell_size_height / 2),
    #                                                                (-cell_size_height / 2, cell_size_height / 2)).arc(
    #     (0, cell_size_height), cell_size_rad, 0.0, 360.0).hull().clean()

    # hex sketch pattern
    ang1 = np.deg2rad(45) / 2
    spacing = 0.2
    e1 = 0.75
    h = cell_size_height
    e2 = 1
    ang2 = np.deg2rad(45) / 2 / (e2 / e1)
    s = (cd.Sketch()
         .segment((-spacing / 2, 0), (spacing / 2, 0))
         .segment((-np.cos(ang1) * e1, np.sin(ang1) * e1), (np.cos(ang1) * e1, np.sin(ang1) * e1))
         .segment((-np.cos(ang2) * e2, h - np.sin(ang2) * e2), (np.cos(ang2) * e2, h - np.sin(ang2) * e2))
         .segment((-spacing / 2, h), (spacing / 2, h)).hull().vertices().fillet(0.5).clean()
         )

    # s = (cd.Sketch()
    #      .segment((np.cos(ang1) * e1, -np.sin(ang1) * e1), (-spacing, 0))
    #      .segment((spacing, 0), (np.cos(ang1) * e1, np.sin(ang1) * e1))
    #      .segment((h - np.cos(ang2) * e2, -np.sin(ang2) * e2), (h, -spacing))
    #      .segment((h, spacing), (h - np.cos(ang2) * e2, np.sin(ang2) * e2)).clean()
    #      .hull().vertices().fillet(0.2)
    #      )
    # show_object(s)
    # return
    # show(s)
    mesh = cd.Workplane('XY')
    mesh_sketch = cd.Workplane('XY')
    if repeat > 0:

        rot = 180 / repeat
        mesh = (
            mesh_sketch.union(
                mesh_sketch
                .workplane()
                .placeSketch(s)
                .extrude(2 * radius)
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .translate((0, radius, -2*height / 4 + padding))

            )
        )
        mesh_pattern = mesh


        for i in range(int(repeat)):
                mesh_pattern = mesh_pattern.union(
                    mesh.rotate((0, 0, 0), (0, 0, 1), i * rot)
                )

        mesh_pattern_inv = (mesh_pattern.rotate((0,0, -height / 2), (0,1, -height / 2), 180)
                            .translate((0, 0, -cell_size_height/2))
                            .rotate((0, 0, 0), (0, 0, 1), rot / 2))
            # show(cyl, mesh_pattern)

        for flag in [0, 1]:
            if flag == 0:
                mesh_to_cut = mesh_pattern
            else:
                mesh_to_cut = mesh_pattern_inv
            for hi in range(int(np.floor(height / (cell_size_height*0.5 + padding*2)))):
                cyl = (
                    cyl.cut(
                        mesh_to_cut
                        # .rotate((0, 0, 0), (0, 0, 1), rot * i)
                    )
                )
                if hi % 2 == 1:
                    sight = 1
                else:
                    sight = -1
                mesh_to_cut = (
                    mesh_to_cut
                    .translate((0, 0, padding + cell_size_height))
                    # .rotate((0, 0, 0), (0, 0, 1), sight * rot / 2)
                )
                # show(cyl, mesh_to_cut)
                # time.sleep(1)
    else:
        # Extract points from the sketch for wrapping

        # Project the wrapped sketch onto the cylindrical surface and extrude
        mesh = (cd.Workplane('XY')
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
                .translate((0, -radius, -(0.5*height-0.5*cell_size_height)))
                # .translate((0, -radius, -(0.5*height+0.5*cell_size_height+padding)))

            )
        )
        mesh_to_cut = mesh
        for hi in range(int(np.floor(height / (cell_size_height*0.5 + padding*2)))):
            cyl = (
                cyl.cut(
                    mesh_to_cut
                    # .rotate((0, 0, 0), (0, 0, 1), rot * i)
                )
            )
            mesh_to_cut = (
                mesh
                .translate((0, 0, hi*(padding + cell_size_height)))
            )
            # show(cyl, mesh_to_cut)
            # time.sleep(1)
    cd.exporters.export(cyl, './geoms/cyl3.stp','STEP')
    show_object(cyl)  # , name=('Cyl','Sketch'))#, options=dict(alpha=1,color='#C0C0C0'))
