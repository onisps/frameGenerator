from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import *




## Model
# create model
model = mdb.Model('Model-1')
# draw arc
sketch = model.ConstrainedSketch(name='baloon', sheetSize=1.0)
sketch.ArcByCenterEnds(center=(0, 0), point1=(-3.3, 0), point2=(3.3, 0), direction=CLOCKWISE)
# set part
part = model.Part(name='ballon', dimensionality=THREE_D, type=DEFORMABLE_BODY)
# extrude scetch
part.BaseShellExtrude(sketch=sketch, depth=30)

## Create sets
# set for section assingment
part.Set(name='set-all', faces=part.faces.findAt(coordinates=((3.3, 0, 0.0),)))
# surface for  BC and contact
part.Surface(name='surface-contact',
             side1Faces=part.faces.findAt(coordinates=((3.3, 0, 0),)))

## Assembly
# create cylindrical coordinate system
csys = model.rootAssembly
datum = csys.DatumCsysByThreePoints(
    coordSysType=CYLINDRICAL,
    origin=(0, 0, 0), point1=(1, 0, 0), point2=(0, 1, 0),
    line1=(0, 0, 1), line2=(0, 1, 0), name='test').id

# create assembly
model.rootAssembly.Instance(name='instance', part=part, dependent=ON)

## Section
# ballon section
model.SurfaceSection(name='section', useDensity=OFF)
part.SectionAssignment(region=part.sets['set-all'], sectionName='section')

## Step
model.StaticStep(name='Step-1', previous='Initial', description='',
                        timePeriod=1.0, timeIncrementationMethod=AUTOMATIC,
                        maxNumInc=200, initialInc=0.0025, minInc=0.0001, maxInc=0.1)

## Output request
model.FieldOutputRequest('F-Output-1', createStepName='Step-1',
                                 variables=('S', 'E', 'U'))

## Boundary condition
# define boundary to set BC
expanding_disp = model.rootAssembly.instances['instance'].sets['set-all']
# create BC in specific coordinate system
model.DisplacementBC(name='BC-1', createStepName='Step-1', localCsys=csys.datums[datum],
                          region=expanding_disp, u1=1, u2=0, u3=0)

## Mesh
# set elem type
part.setElementType(regions=(part.faces,), elemTypes=[mesh.ElemType(elemCode=SFM3D4)])
# set number of element per edge
part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((3.3, 0, 1.0), (-3.3, 0, 1.0))), number=1)
part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((0, 3.3, 0.0), (0, 3.3, 30.0))), number=50)
# create mesh
part.generateMesh()

## Job
job = mdb.Job(name='Ballon_expand', model='Model-1', numCpus=16, numDomains=16, multiprocessingMode=THREADS)
job.writeInput()

## Submit the job

# job.submit()
# job.waitForCompletion()

# Save abaqus cae
mdb.saveAs('compression.cae')

