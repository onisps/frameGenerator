import cadquery as cd
from jupyter_cadquery.viewer.client import show, show_object


def model_drawer(radius=4, height=20, repeat=5, cell_size_height=2, cell_size_rad=0.2, cut_space=1.0):
    cyl_out = cd.Workplane('XY').cylinder(height=height, radius=radius, direct=cd.Vector((0, 0, 1)))
    cyl_cut = cd.Workplane('XY').cylinder(height=height, radius=radius - 0.5, direct=cd.Vector((0, 0, 1)))
    cyl = cyl_out.cut(cyl_cut)
    # s = (
    #     cd.Sketch().arc((0, 0), cell_size_rad, 0.0, 360.0)
    #     .arc((0, cell_size_height), cell_size_rad, 0.0, 360.0)
    #     .hull()
    # )
    s = cd.Sketch().arc((0, 0), cell_size_rad, 0.0, 360.0).segment((cell_size_height / 2, cell_size_height / 2),
                                                                   (-cell_size_height / 2, cell_size_height / 2)).arc(
        (0, cell_size_height), cell_size_rad, 0.0, 360.0).hull().clean()

    # show(s)
    mesh = cd.Workplane('XY')
    mesh_sketch = cd.Workplane('XY')
    rot = 180 / repeat
    mesh = (
        mesh_sketch.union(
            mesh_sketch
            .workplane()
            .placeSketch(s)
            .extrude(2 * radius)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, radius, -height / 2))

        )
    )
    mesh_pattern = mesh
    for i in range(int(repeat)):
        mesh_pattern = mesh_pattern.union(
            mesh.rotate((0, 0, 0), (0, 0, 1), i * rot)
        )
    # show(cyl, mesh_pattern)

    for hi in range(int(height / (cut_space*cell_size_height))):
        cyl = (
            cyl.cut(
                mesh_pattern
                .rotate((0, 0, 0), (0, 0, 1), rot * i)
            )
        )
        if hi % 2 == 1:
            sight = 1
        else:
            sight = -1
        mesh_pattern = (
            mesh_pattern
            .translate((0, 0, cut_space*cell_size_height))
            .rotate((0, 0, 0), (0, 0, 1), sight*rot / 2)
        )
        # show(cyl)

    cd.exporters.export(cyl, './geoms/cyl2.stp','STEP')
    show(cyl)
