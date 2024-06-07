from abaqus import *
from abaqusConstants import *
from caeModules import *

## Model
# create model
model = mdb.Model('Expand_frame')
# draw arc
balloon_dia = 18.4 / 2
frame_dia = 18 / 2
sketch = model.ConstrainedSketch(name='balloon', sheetSize=1.0)
sketch.ArcByCenterEnds(center=(0, 0), point1=(balloon_dia, 0), point2=(balloon_dia, 0), direction=CLOCKWISE)
# set part
part = model.Part(name='ballon', dimensionality=THREE_D, type=DEFORMABLE_BODY)

# extrude scetch
part.BaseShellExtrude(sketch=sketch, depth=30)

# import frame from STEP
geom_file = mdb.openStep(fileName='../geoms/cyl3.stp')
part2 = model.PartFromGeometryFile(name='frame', geometryFile=geom_file, dimensionality=THREE_D, type=DEFORMABLE_BODY)

## Mesh balloon
# set elem type
part.setElementType(regions=(part.faces,), elemTypes=[mesh.ElemType(elemCode=SFM3D4)])

# set number of element per edge
part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((balloon_dia, 0, 1.0), (-balloon_dia, 0, 1.0))), number=1)
part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((0, balloon_dia, 0.0), (0, balloon_dia, 30.0))), number=100)
# create mesh
part.generateMesh()

## Create sets
# set for section assingment
part.Set(name='set-all', faces=part.faces.findAt(coordinates=((balloon_dia, 0, 0.0),)))
# surface for  BC and contact
part.Surface(name='surface-contact',
             side1Faces=part.faces.findAt(coordinates=((balloon_dia, 0, 0),)), )

## Mesh Frame
# set elem type
part2.createVirtualTopology(regions=(part2.faces, part2.edges, part2.nodes, part2.cells),
                            ignoreRedundantEntities=TRUE
                            )
part2.setElementType(regions=(part2.cells,), elemTypes=[mesh.ElemType(elemCode=C3D8)])
part2.seedPart(size=0.2)
# # set number of element per edge
# part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((3.3, 0, 1.0), (-3.3, 0, 1.0))), number=1)
# part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((0, 3.3, 0.0), (0, 3.3, 30.0))), number=50)

# create mesh
part2.generateMesh()

part2.Set(name='set-cells', cells=part2.cells)

surfaces_all = part2.Surface(name='all_faces', side2Faces=part2.faces)
part2.Set(name='sur-test',
          nodes=part2.nodes.getByBoundingCylinder(center1=(0, 0, -10), center2=(0, 0, 10), radius=frame_dia), )
t_faces = part2.faces.getClosest(
                  coordinates=
                  (
                      (frame_dia+0.1, 0, 5),
                      (frame_dia+0.1, 0, -5),
                  ),
              )
coords = list()
for i in range(20):
    coords.append((frame_dia, 0, 0.5*i))
surfaces_outer = part2.Surface(name='surface-contact', side2Faces=part2.faces.findAt(
    coordinates=coords
    # (
    #     (frame_dia, 0, -10),
    #     (frame_dia, 0, -9),
    #     (frame_dia, 0, -8),
    #     (frame_dia, 0, -7),
    #     (frame_dia, 0, -6),
    #     (frame_dia, 0, -5),
    #     (frame_dia, 0, -4),
    #     (frame_dia, 0, -3),
    #     (frame_dia, 0, -2),
    #     (frame_dia, 0, -1),
    #     (frame_dia, 0, 0),
    # )
))
surfaces_inner = part2.Surface(name='inner_faces',
                               side2Faces=part2.faces.getByBoundingCylinder(
                                   center1=(0, 0, 10),
                                   center2=(0, 0, -10),
                                   radius=frame_dia-0.5)
                               )

print('surf all:', surfaces_all)
print('surf out:', surfaces_outer)
print('surf in:', surfaces_inner)

surfaces_self_contact = part2.SurfaceByBoolean(
    name='self-contact',
    surfaces=[surfaces_all, surfaces_inner, surfaces_outer],
    operation=DIFFERENCE
)
part2.SurfaceByBoolean(
    name='surface-contact',
    surfaces=[surfaces_all, surfaces_inner, surfaces_self_contact],
    operation=DIFFERENCE
)

## Assembly
# create cylindrical coordinate system
csys = model.rootAssembly
datum = csys.DatumCsysByThreePoints(
    coordSysType=CYLINDRICAL,
    origin=(0, 0, 0), point1=(1, 0, 0), point2=(0, 1, 0),
    line1=(0, 0, 1), line2=(0, 1, 0), name='test').id

# create assembly
model.rootAssembly.Instance(name='balloon', part=part, dependent=ON).translate(vector=(0, 0, -15))
model.rootAssembly.Instance(name='frame', part=part2, dependent=ON)

# Material
material = model.Material(name='material_NiTi')
material.Elastic(table=((233000., 0.35),))
material.Plastic(table=((414., 0.),
                        (933., 0.445),))

## Section
# ballon section
model.SurfaceSection(name='section_balloon', useDensity=OFF)
model.HomogeneousSolidSection(name='section_frame', material='material_NiTi', thickness=None)
part.SectionAssignment(region=part.sets['set-all'], sectionName='section_balloon')
part2.SectionAssignment(region=part2.sets['set-cells'], sectionName='section_frame')

## Step
model.StaticStep(name='Step-Load', previous='Initial', description='',
                 timePeriod=1.0, timeIncrementationMethod=AUTOMATIC,
                 maxNumInc=1000, initialInc=0.01, minInc=1E-06, maxInc=0.1, nlgeom=ON)

## Output request
model.FieldOutputRequest('F-Output-1', createStepName='Step-Load', timeInterval=0.025,
                         variables=('S', 'E', 'U'))

## Boundary condition
# create Amplitude
amp_name = 'Ampl-expand'
model.TabularAmplitude(name=amp_name, data=((0, 0), (0.75, 1), (1, 0.75),), )
# define boundary to set BC
expanding_disp = model.rootAssembly.instances['balloon'].sets['set-all']
# create BC in specific coordinate system
model.DisplacementBC(name='BC-1', createStepName='Step-Load', localCsys=csys.datums[datum], amplitude=amp_name,
                     region=expanding_disp, u1=-5.2, u2=0, u3=0)

## interaction
# set_frame = model.rootAssembly.instances['frame'].surfaces['surface-contact']
set_frame = model.rootAssembly.instances['frame'].surfaces['surface-contact']
set_balloon = model.rootAssembly.instances['balloon'].surfaces['surface-contact']
set_frame_self_contact = model.rootAssembly.instances['frame'].surfaces['self-contact']
prop = model.ContactProperty(name='InterProp')
prop.TangentialBehavior(formulation=PENALTY, table=((0.2,),), fraction=0.005, )
prop.NormalBehavior(pressureOverclosure=HARD, )

model.SurfaceToSurfaceContactStd(name='contact_test', createStepName='Step-Load',
                                 slave=set_frame,
                                 master=set_balloon,
                                 sliding=FINITE, interferenceType=NONE,
                                 interactionProperty='InterProp', enforcement=NODE_TO_SURFACE)

model.SelfContactStd(name='self-contact-frame', createStepName='Step-Load',
                     surface=set_frame_self_contact,
                     interactionProperty='InterProp', enforcement=SURFACE_TO_SURFACE)

## Job
job = mdb.Job(name='a_Ballon_expand', model='Expand_frame', numCpus=16, numDomains=16, multiprocessingMode=THREADS)
job.writeInput()

## Submit the job

# job.submit()
# job.waitForCompletion()

# Save abaqus cae
mdb.saveAs('a_compression.cae')

import os, glob

# for f in glob.glob("abaqus*"):
#     os.remove(f)
# for f in glob.glob("*.sat"):
#     os.remove(f)
