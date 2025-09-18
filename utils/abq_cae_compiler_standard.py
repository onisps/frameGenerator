import numpy as np
import regionToolset
from abaqus import mdb
from abaqusConstants import *
from caeModules import *
import json


def load_json_utf8(path):
    try:
        import io
        with io.open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except TypeError:
        with open(path, 'rb') as f:
            return json.loads(f.read().decode('utf-8'))


def as_tuple(x):
    if isinstance(x, (list, tuple, np.ndarray)):
        return tuple(as_tuple(v) for v in x)
    return x

## Model
# create model
def connector(
        frame_dia = 29,
        frame_length = 30,
        material_model = 'linear',
        material_prop = None,
        solver_cfg = None
    ):
    model = mdb.Model('Compress_frame')
    if 'Model-1' in mdb.models.keys():
        del mdb.Model['Model-1']
    balloon_rad = (frame_dia+0.4) / 2
    frame_rad = frame_dia / 2
    sketch_balloon = model.ConstrainedSketch(name='balloon', sheetSize=1.0)
    sketch_balloon.ArcByCenterEnds(center=(0, 0), point1=(balloon_rad, 0), point2=(balloon_rad, 0), direction=CLOCKWISE)

    # set part
    part = model.Part(name='ballon', dimensionality=THREE_D, type=DEFORMABLE_BODY)

    # extrude sketch
    part.BaseShellExtrude(sketch=sketch_balloon, depth=frame_length*2)

    # create partition
    datumPlane = part.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    part.PartitionFaceByDatumPlane(datumPlane=part.datums[datumPlane.id], faces=part.faces)

    # import frame from STEP
    geom_file = mdb.openStep(fileName=str('../geoms/'+solver_cfg.job_name_prefix+'.stp'))
    part2 = model.PartFromGeometryFile(name='frame', geometryFile=geom_file, dimensionality=THREE_D, type=DEFORMABLE_BODY)

    ## Mesh balloon
    # set elem type
    part.setElementType(regions=(part.faces,), elemTypes=[mesh.ElemType(elemCode=SFM3D4)])

    # set number of element per edge
    part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=(
        (balloon_rad, 0, 1.0),
        (-balloon_rad, 0, 1.0)
    )), number=1)
    part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=(
        (0, balloon_rad, 0.0),
        (0, balloon_rad, frame_length*2)
    )
    ), number=150)
    # create mesh
    part.generateMesh()

    ## Create sets
    # set for section assingment
    part.Set(name='set-all', faces=part.faces.findAt(coordinates=((0, balloon_rad, 0.0),(0,-balloon_rad, 0.0)),))
    # surface for  BC and contact
    part.Surface(name='surface-contact',
                 side1Faces=part.faces.findAt(coordinates=((0,balloon_rad,  0),(0, -balloon_rad, 0))), )

    ## Mesh Frame
    # set elem type
    part2.createVirtualTopology(regions=(part2.faces, part2.edges, part2.nodes, part2.cells),
                                ignoreRedundantEntities=TRUE
                                )
    part2.setMeshControls(regions=part2.cells, elemShape=TET, technique=FREE)
    el_tet_c3d4 = mesh.ElemType(elemCode=C3D4, elemLibrary=STANDARD)
    el_tet_c3d4h = mesh.ElemType(elemCode=C3D4H, elemLibrary=STANDARD)
    part2.setElementType(regions=(part2.cells,), elemTypes=(el_tet_c3d4, el_tet_c3d4h))

    # # set number of element per edge
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((3.3, 0, 1.0), (-3.3, 0, 1.0))), number=1)
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((0, 3.3, 0.0), (0, 3.3, 30.0))), number=50)

    numErrorMesh = 1
    raw_mesh_seed_size = 0.2
    # create mesh
    part2.seedPart(size=raw_mesh_seed_size, deviationFactor=0.1)
    part2.generateMesh()
    print('Element type: ', part2.elements[0].type)
    # bad_elems = part2.verifyMeshQuality(
    #     criterion=ANALYSIS_CHECKS
    # )
    # print("\nBasic (ANALYSIS_CHECKS):")
    # for key in bad_elems.keys():
    #     print(key, bad_elems.get(key))
    # numErrorMesh = len(bad_elems.get('failedElements'))
    # print(" ***Elements with errors: " + str(numErrorMesh) + ". Seed size " + str(raw_mesh_seed_size))

    while numErrorMesh > 0:
        part2.seedPart(size=raw_mesh_seed_size, deviationFactor=0.1)
        part2.generateMesh()
        bad_elems = part2.verifyMeshQuality(
            criterion=ANALYSIS_CHECKS
        )
        # for key in bad_elems.keys():
        #     print(key, bad_elems.get(key))
        numErrorMesh = len(bad_elems.get('failedElements'))
        print(" ***Elements with errors: " + str(numErrorMesh) + ". Seed size "+ str(raw_mesh_seed_size))
        raw_mesh_seed_size -= 0.025
        # if raw_mesh_seed_size < 0.1:
        #     numErrorMesh = 0

    part2.Set(name='set-cells', cells=part2.cells)

    surfaces_all = part2.Surface(name='all_faces', side2Faces=part2.faces)

    coords = list()
    print('before part2.findAt\n')
    for i in range(40):
        coords.append((frame_rad, 0, 0.25*i))
    surfaces_outer = part2.Surface(name='surface-contact', side2Faces=part2.faces.findAt(
        coordinates=coords
    ))

    print('surf all:', surfaces_all)
    print('surf out:', surfaces_outer)
    # print('surf in:', surfaces_inner)

    surfaces_self_contact = part2.SurfaceByBoolean(
        name='self-contact',
        surfaces=[surfaces_all, surfaces_outer],
        operation=DIFFERENCE
    )
    part2.SurfaceByBoolean(
        name='surface-contact',
        surfaces=[surfaces_all, surfaces_self_contact],
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
    model.rootAssembly.Instance(name='balloon', part=part, dependent=ON).translate(vector=(0, 0, -frame_length))
    model.rootAssembly.Instance(name='frame', part=part2, dependent=ON)

    # Material
    if str(material_model).lower() == 'linear':
        material = model.Material(name=str(material_prop.name))
        material.Elastic(table=((material_prop.EM, material_prop.Poisson),))
    elif str(material_model).lower() == 'polynomial':
        material = model.Material(name=str(material_prop.name))
        material.Elastic(table=((material_prop.EM, material_prop.Poisson),))
        mat_prop_table = as_tuple(material_prop.mat_table)
        material.Plastic(table=mat_prop_table)
    elif str(material_model).lower() == str('superelastic'):
        material = model.Material(name=str(material_prop.name))
        material.Elastic(table=((material_prop.EA, material_prop.Poisson),))
        material.SuperElasticity(
            table=((material_prop.EM, material_prop.nuM, material_prop.eps_L,
                    material_prop.sig_s_AS, material_prop.sig_f_AS, material_prop.sig_s_SA,
                    material_prop.sig_f_SA, material_prop.sig_s_AC,
                    material_prop.T0, material_prop.dSig_dT_L_per_C, material_prop.dSig_dT_U_per_C),),
            nonassociated=material_prop.eps_V   # None or number; if None then eps_V = eps_L
        )
    ## Section
    # ballon section
    model.SurfaceSection(name='section_balloon', useDensity=OFF)
    model.HomogeneousSolidSection(name='section_frame', material=str(material_prop.name), thickness=None)
    part.SectionAssignment(region=part.sets['set-all'], sectionName='section_balloon')
    part2.SectionAssignment(region=part2.sets['set-cells'], sectionName='section_frame')

    ## Step
    model.StaticStep(name=str(solver_cfg.step_name), previous='Initial', description='',
                     timePeriod=solver_cfg.step_time, timeIncrementationMethod=AUTOMATIC,
                     maxNumInc=1000, initialInc=0.01, minInc=1E-06, maxInc=0.1, nlgeom=ON,
                     stabilizationMethod=DISSIPATED_ENERGY_FRACTION)

    ## Output request

    _time_num_points = int(round(solver_cfg.step_time/ solver_cfg.outputs.time_interval))
    time_points = model.TimePoint(name='tp25ms',
                         points=tuple(i * solver_cfg.outputs.time_interval for i in range(_time_num_points + 1)))

    model.FieldOutputRequest(
                             name='Field-Output-1',
                             createStepName=str(solver_cfg.step_name),
                             timePoint='tp25ms',
                             timeMarks=ON,
                             position=INTEGRATION_POINTS,
                             variables=list([str(v) for v in solver_cfg.outputs.field_outputs])
                             )

    ## Boundary condition
    # create Amplitude
    amp_name = 'Ampl-compress'
    model.TabularAmplitude(name=amp_name, data=((0, 0), (0.75, 1), (1, 0.75),), )
    # define boundary to set BC
    expanding_disp = model.rootAssembly.instances['balloon'].sets['set-all']
    # create BC in specific coordinate system
    model.DisplacementBC(name='BC-1', createStepName=str(solver_cfg.step_name), localCsys=csys.datums[datum], amplitude=amp_name,
                         region=expanding_disp, u1=-(balloon_rad - 3), u2=0, u3=0)

    ## interaction
    set_frame = model.rootAssembly.instances['frame'].surfaces['surface-contact']
    set_balloon = model.rootAssembly.instances['balloon'].surfaces['surface-contact']
    set_frame_self_contact = model.rootAssembly.instances['frame'].surfaces['self-contact']
    prop = model.ContactProperty(name='InterProp')
    prop.TangentialBehavior(formulation=PENALTY, table=((0.2,),), fraction=0.005, )
    prop.NormalBehavior(pressureOverclosure=HARD, )

    model.SurfaceToSurfaceContactStd(name='contact_test', createStepName=str(solver_cfg.step_name),
                                     slave=set_frame,
                                     master=set_balloon,
                                     sliding=FINITE, interferenceType=NONE,
                                     interactionProperty='InterProp', enforcement=NODE_TO_SURFACE)

    model.SelfContactStd(name='self-contact-frame', createStepName=str(solver_cfg.step_name),
                         surface=set_frame_self_contact,
                         interactionProperty='InterProp', enforcement=SURFACE_TO_SURFACE)

    ## Job
    job = mdb.Job(name='a_Ballon_compress', model='Compress_frame', numCpus=int(solver_cfg.cpus), numDomains=int(solver_cfg.cpus), multiprocessingMode=THREADS)
    job.writeInput()
    # Save abaqus cae
    mdb.saveAs('a_compression.cae')
    ## Submit the job
    #
    # job.submit()
    # job.waitForCompletion()
    #
    # return job


if __name__ == "__main__":
    import sys, json, os

    try:
        from types import SimpleNamespace  # type: ignore
    except Exception:
        class SimpleNamespace(object):
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

    def _ns(obj):
        if isinstance(obj, dict):
            return SimpleNamespace(**{k: _ns(v) for k, v in obj.items()})
        return obj

    json_arg = None
    for a in sys.argv[1:]:
        if a.lower().endswith(".json"):
            json_arg = a
            break

    if not json_arg or not os.path.isfile(json_arg):
        raise RuntimeError("No json-startup command (expects *.json).")

    data = load_json_utf8(json_arg)

    frame_dia = float(data.get("frame_dia", 29.0))
    frame_length = float(data.get("frame_length", 30.0))
    material_model = str(data.get("material_model", "linear"))
    material_prop = _ns(data.get("material_prop", {}))
    solver_cfg = _ns(data.get("solver_cfg", {}))

    connector(frame_dia, frame_length, material_model, material_prop, solver_cfg)