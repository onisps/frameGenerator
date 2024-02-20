from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import *


def connector_test(path: str = './geoms/cyl2.stp'):
    # executeOnCaeStartup()

    model = mdb.Model('Model-1')
    sketch = model.ConstrainedSketch(name='baloon', sheetSize=1.0)
    sketch.ArcByCenterEnds(center=(0, 0), point1=(-3.3, 0), point2=(3.3, 0), direction=CLOCKWISE)
    # sketch.ArcByCenterEnds(center=(0, 0), point1=(3.3, -0.3), point2=(-3.0, -0.3), direction=CLOCKWISE)
    part = model.Part(name='ballon', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    part.BaseShellExtrude(sketch=sketch, depth=30)

    # Create sets
    part.Set(name='set-all', faces=part.faces.findAt(coordinates=((3.3, 0, 0.0),)))
    part.Surface(name='surface-contact',
                 side1Faces=part.faces.findAt(coordinates=((3.3, 0, 0),)))

    # Assembly
    csys = model.rootAssembly
    datum = csys.DatumCsysByThreePoints(
        coordSysType=CYLINDRICAL,
        origin=(0, 0, 0), point1=(1, 0, 0), point2=(0, 1, 0),
        line1=(0, 0, 1), line2=(0, 1, 0), name='test').id

    model.rootAssembly.Instance(name='instance', part=part, dependent=ON)

    # Section
    model.SurfaceSection(name='section', useDensity=OFF)
    part.SectionAssignment(region=part.sets['set-all'], sectionName='section')

    # Step
    step = model.StaticStep(name='Step-1', previous='Initial', description='',
                            timePeriod=1.0, timeIncrementationMethod=AUTOMATIC,
                            maxNumInc=200, initialInc=0.0025, minInc=0.0001, maxInc=0.1)

    # Output request
    field = model.FieldOutputRequest('F-Output-1', createStepName='Step-1',
                                     variables=('S', 'E', 'U'))

    # Boundary condition
    expanding_disp = model.rootAssembly.instances['instance'].sets['set-all']
    bc = model.DisplacementBC(name='BC-1', createStepName='Step-1', localCsys=csys.datums[datum],
                              region=expanding_disp, u1=1, u2=0, u3=0)

    # Mesh-
    part.setElementType(regions=(part.faces,), elemTypes=[mesh.ElemType(elemCode=SFM3D4)])
    part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((3.3, 0, 1.0), (-3.3, 0, 1.0))), number=1)
    part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((0, 3.3, 0.0), (0, 3.3, 30.0))), number=50)
    part.generateMesh()

    # Job
    job = mdb.Job(name='Ballon_expand', model='Model-1', numCpus=16, numDomains=16)
    job.writeInput()

    # Submit the job
    # job.submit()
    # job.waitForCompletion()

    # Save abaqus model
    mdb.saveAs('compression.cae')

