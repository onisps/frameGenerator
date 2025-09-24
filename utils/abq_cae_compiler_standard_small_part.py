# -*- coding: utf-8 -*-

import numpy as np
import regionToolset as r
from abaqus import mdb
from abaqusConstants import *
from caeModules import *
import math
import json

##
_ADPTIVE_MESH = False

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

def _linspace_lo_hi(lo, hi, n):
    """Inclusive linspace without numpy; returns n>=2 points from lo to hi."""
    if n <= 1:
        return [lo]
    step = (hi - lo) / float(n - 1)
    return [lo + i * step for i in range(n)]

def _rotate_z(pt, angle):
    """Rotate point (x,y,z) CCW around Z by 'angle' [rad]."""
    x, y, z = pt
    ca, sa = math.cos(angle), math.sin(angle)
    return (ca * x - sa * y, sa * x + ca * y, z)

def make_plane_pointclouds(frame_rad, frame_length, repeats,
                           nz=11, nr=3, tol_r_band=0.5):
    """
    Generate two point clouds on planes:
      - XZ (y=0), positive X side;
      - rotated by +360/repeats CCW about Z.

    Parameters
    ----------
    frame_rad : float
        Nominal radius R [mm]. Points are sampled at radii in [R-0.5, R+0.1].
    frame_length : float
        Axial length along Z [mm], z ∈ [0, frame_length].
    repeats: int
        Number of sector repeats; rotation angle = 2π/repeats (CCW).
    nz : int
        Number of points along Z (≥2). Default 11.
    nr : int
        Number of radii across the radial band [R-0.5, R] (≥1). Default 3.
    tol_r_band : float
        Width of radial band (default 0.5 mm).

    Returns
    -------
    coords_arr : list of two lists
        coords_arr[0] -> list of (x,y,z) on XZ plane (y=0, x>=0).
        coords_arr[1] -> same points rotated by +2π/repeats.

    Notes
    -----
    - Designed for Abaqus 2021 (Python 2.7) findAt usage on planar faces
      formed by datum planes through the Z-axis (meridional cuts).
    - No NumPy; deterministic ordering: loop over z fastest, then radii.
    - If repeats < 1 or geometry invalid, returns [[], []].
    """
    # Basic validation
    if frame_rad <= 0.0 or frame_length < 0.0 or repeats < 1:
        return [[], []]
    if nz < 2:
        nz = 2
    if nr < 1:
        nr = 1

    R_hi = frame_rad + 0.1
    R_lo = max(0.0, frame_rad - float(tol_r_band))  # enforce non-negative

    # Build Z and radial samples
    zs = _linspace_lo_hi(-float(frame_length), float(frame_length), nz)
    if nr == 1:
        rs = [(R_lo + R_hi) * 0.5]
    else:
        rs = _linspace_lo_hi(R_lo, R_hi, nr)

    # XZ plane (y=0), pick +X half-plane for unambiguous findAt
    base_pts = []
    for z in zs:
        for r in rs:
            base_pts.append((r, 0.0, z))  # (x=+r, y=0, z)

    # Rotate by +2π/repeats CCW
    phi = 2.0 * math.pi / float(repeats)
    rot_pts = [_rotate_z(p, phi) for p in base_pts]
    print(base_pts)
    return (base_pts, rot_pts)


def spiral_on_cylinder(frame_rad, frame_length, pitch_mm=0.5, step=0.2,
                       start_theta=0.0, clockwise=False, eps=1e-12):
    """
    Generate 3D points (x, y, z) along a helix on the surface of a cylinder
    aligned with the Z-axis. The cylinder has radius `frame_rad` (mm) and length
    `frame_length` (mm). The helix pitch (axial distance between neighboring turns)
    is `pitch_mm` (default 0.5 mm). The sampling density along the curve is
    controlled by `step` (approximate chord length between consecutive points, mm).

    Parametric form:
        x(θ) = r * cos(θ0 + s*θ)
        y(θ) = r * sin(θ0 + s*θ)
        z(θ) = (pitch / (2π)) * θ
    where r = frame_rad, θ ∈ [0, θ_max], θ_max = 2π * (frame_length / pitch),
    s = +1 (counter-clockwise) or −1 (clockwise).
    The angular increment dθ is chosen so that the chord length along the helix
    is approximately `step`:
        dθ ≈ step / sqrt(r^2 + (pitch/(2π))^2)
    """
    # Validate basic inputs
    if frame_rad <= 0 or frame_length <= 0 or pitch_mm <= 0 or step <= 0:
        return []

    # Total angular span to reach z = frame_length
    theta_max = 2.0 * math.pi * (frame_length / float(pitch_mm))

    # dz/dθ and arc-length denominator
    dz_dtheta = pitch_mm / (2.0 * math.pi)
    denom = math.sqrt(frame_rad * frame_rad + dz_dtheta * dz_dtheta)

    # Angular increment to achieve ~constant chord length
    dtheta = step / denom
    if dtheta <= 0:
        dtheta = theta_max

    # Number of steps including the endpoint θ_max
    n_steps = int(math.ceil(theta_max / dtheta))

    # Winding orientation
    sign = -1.0 if clockwise else 1.0

    pts = []
    for i in range(n_steps + 1):
        theta = theta_max if i == n_steps else (i * dtheta)
        z = dz_dtheta * theta
        if z > frame_length and i < n_steps:
            z = frame_length
            theta = theta_max

        angle = start_theta + sign * theta
        x = frame_rad * math.cos(angle)
        y = frame_rad * math.sin(angle)

        # keep only first-quadrant points (strictly > 0 with tolerance)
        if (x > eps) and (y > eps):
            pts.append((x, y, z))

    return pts

## Model
# create model
def connector(
        geometry_cfg = None,
        frame_length = 30,
        material_model = 'linear',
        material_prop = None,
        solver_cfg = None
    ):
    job_name = str(solver_cfg.job_name_prefix)
    model = mdb.Model('Compress_frame')
    # if 'Model-1' in mdb.models.keys():
    #     del mdb.Model['Model-1']
    balloon_rad = (geometry_cfg.diameter+0.4) / 2
    frame_rad = geometry_cfg.diameter / 2
    sketch_balloon = model.ConstrainedSketch(name='balloon', sheetSize=1.0)

    phi_deg = 360.0 / float(geometry_cfg.repeat)
    phi_rad = math.radians(phi_deg)
    half = 0.5 * phi_rad

    p1 = (balloon_rad * math.cos(0), balloon_rad * math.sin(0))
    p2 = (balloon_rad * math.cos(phi_rad), balloon_rad * math.sin(phi_rad))
    p_half = (balloon_rad * math.cos(half), balloon_rad * math.sin(half))

    sketch_balloon.ArcByCenterEnds(center=(0, 0), point1=p1, point2=p2, direction=COUNTERCLOCKWISE)


    # set part
    part = model.Part(name='ballon', dimensionality=THREE_D, type=DEFORMABLE_BODY)

    # extrude sketch
    part.BaseShellExtrude(sketch=sketch_balloon, depth=frame_length*2)
    # mdb.saveAs('a_compression.cae')
    # create partition
    # datumPlane = part.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    # part.PartitionFaceByDatumPlane(datumPlane=part.datums[datumPlane.id], faces=part.faces)
    part.setMeshControls(regions=part.cells, elemShape=HEX, technique=STRUCTURED)
    # import frame from STEP
    geom_file = mdb.openStep(fileName=str('../geoms/'+solver_cfg.job_name_prefix+'.stp'))
    part2 = model.PartFromGeometryFile(name='FRAME', geometryFile=geom_file, dimensionality=THREE_D, type=DEFORMABLE_BODY)

    ## Mesh balloon
    # set elem type
    part.setElementType(regions=(part.faces,), elemTypes=[mesh.ElemType(elemCode=SFM3D4)])

    # set number of element per edge
    part.seedPart(size=0.2, deviationFactor=0.1)
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((balloon_rad, 0, frame_length),)), number=1)
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((-balloon_rad, 0, frame_length),)), number=1)
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=(
    #     (0, balloon_rad, 0.0),
    #     (0, balloon_rad, 2*frame_length)
    # )
    # ), number=150)
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=(
    #     (0, p_half[0], 2 * frame_length),
    #     (0, -p_half[0], 2*frame_length)
    # )
    # ), number=150)
    # create mesh
    part.generateMesh()
    ## Create sets
    # set for section assingment
    part.Set(name='set-all', faces=part.faces)
    # surface for  BC and contact
    part.Surface(name='surface-contact',
                 side2Faces=part.faces.findAt(coordinates=((p_half[0], p_half[1],  frame_length),)), )

    ## Mesh Frame
    # set elem type
    try:
        part2.createVirtualTopology(regions=(part2.faces, part2.edges, part2.nodes, part2.cells),
                                ignoreRedundantEntities=TRUE
                                )
    except Exception as e:
        pass

    part2.setMeshControls(regions=part2.cells, elemShape=HEX_DOMINATED, technique=SWEEP, allowMapped=ON)
    el_c3d8 = mesh.ElemType(elemCode=C3D8, elemLibrary=STANDARD,hourglassControl=ENHANCED)
    el_c3d8r = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD, hourglassControl=ENHANCED)
    part2.setElementType(regions=(part2.cells,), elemTypes=(el_c3d8,))

    # # set number of element per edge
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((3.3, 0, 1.0), (-3.3, 0, 1.0))), number=1)
    # part.seedEdgeByNumber(edges=part.edges.findAt(coordinates=((0, 3.3, 0.0), (0, 3.3, 30.0))), number=50)

    numErrorMesh = 1
    raw_mesh_seed_size = 0.2
    # create mesh
    # part2.seedPart(size=raw_mesh_seed_size, deviationFactor=0.1)
    # part2.generateMesh()
    # print('Element type: ', part2.elements[0].type)
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

    coords_xy, coords_rotated = make_plane_pointclouds(
                    frame_rad=frame_rad,
                    frame_length=frame_length,
                    repeats=geometry_cfg.repeat,
                    nz=201,
                    nr=41,
                    tol_r_band=geometry_cfg.thk+0.1
                )


    surfaces_outer = part2.Surface(
        name='surface-contact',
        side2Faces=part2.faces.findAt(
        coordinates=spiral_on_cylinder(frame_rad=frame_rad, frame_length=frame_length)
    ))

    surfaces_inner = part2.Surface(
        name='surface-inner',
        side2Faces=part2.faces.findAt(
        coordinates=spiral_on_cylinder(frame_rad=(frame_rad-geometry_cfg.thk), frame_length=frame_length)
    ))

    surface_fixed_u2 = part2.Surface(
        name='surface_no_rotate',
        side2Faces=part2.faces.findAt(coordinates=(coords_xy + coords_rotated))
    )

    part2.Set(name='set-no-rotation', faces=part2.faces.findAt(coordinates=(coords_xy + coords_rotated)))

    # mdb.saveAs('a_compression.cae')

    print('surf all:', surfaces_all)
    print('surf out:', surfaces_outer)
    print('surf in:', surfaces_inner)
    print('surf sides:', surface_fixed_u2)

    surfaces_self_contact = part2.SurfaceByBoolean(
        name='self-contact',
        surfaces=[surfaces_all, surfaces_outer, surfaces_inner, surface_fixed_u2],
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
    model.rootAssembly.Instance(name='FRAME', part=part2, dependent=ON)

    # faces_inst = model.rootAssembly.instances['FRAME'].faces.findAt(coordinates=(coords_xy + coords_rotated))
    # region_fix = r.Region(side2Faces=faces_inst)

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
                     maxNumInc=10000,
                     initialInc=(0.01 if 0.01<solver_cfg.outputs.time_interval else solver_cfg.outputs.time_interval),
                     minInc=1E-10,
                     maxInc=0.1,
                     nlgeom=ON,
                     stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                     stabilizationMagnitude=2e-4,
                     adaptiveDampingRatio=0.05)

    ## Output request

    _time_num_points = int(round(solver_cfg.step_time / solver_cfg.outputs.time_interval))
    _time_points_array = np.linspace(
        0.0,
        _time_num_points * float(solver_cfg.outputs.time_interval),
        _time_num_points + 1
    )
    _time_points_array = np.round(_time_points_array, 6)
    points_seq = tuple((float(t),) for t in _time_points_array.tolist())
    model.TimePoint(name='tp', points=points_seq)

    model.FieldOutputRequest(
                             name='Field-Output-1',
                             createStepName=str(solver_cfg.step_name),
                             timePoint='tp',
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
    model.DisplacementBC(
        name='BC-compress_balloon',
        createStepName=str(solver_cfg.step_name),
        localCsys=csys.datums[datum],
        amplitude=amp_name,
        region=expanding_disp,
        u1=-(balloon_rad - 3),
        u2=0,
        u3=0
    )

    model.DisplacementBC(
        name='BC-no_rotation',
        createStepName=str(solver_cfg.step_name),
        region=model.rootAssembly.instances['FRAME'].sets['set-no-rotation'],
        localCsys=csys.datums[datum],
        u2=0
    )
    # mdb.saveAs('a_compression.cae')
    ## interaction
    set_frame = model.rootAssembly.instances['FRAME'].surfaces['surface-contact']
    set_balloon = model.rootAssembly.instances['balloon'].surfaces['surface-contact']
    set_frame_self_contact = model.rootAssembly.instances['FRAME'].surfaces['self-contact']
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

    if _ADPTIVE_MESH:

        #remeshing
        ale_ctrl = model.AdaptiveMeshControl(
            name='ALE_STD_CTRL',
            remapping=SECOND_ORDER_ADVECTION,
            smoothingAlgorithm=GEOMETRY_ENHANCED,
            smoothingPriority=GRADED,
            initialFeatureAngle=30.0,
            transitionFeatureAngle=45.0,
            meshConstraintAngle=75.0,
            # key parameter for Standard
            standardVolumetricSmoothingWeight=1.0  # enable "volumetric" smoothing for Standard
        )
        assebly_data = model.rootAssembly
        inst = assebly_data.instances['FRAME'].elements[:]
        # els = part2.elements[:]
        assebly_data.Set(name='ALE_DOMAIN', elements=inst)

        ale_elems = assebly_data.sets['ALE_DOMAIN'].elements
        ale_region = r.Region(elements=ale_elems)

        model.steps[str(solver_cfg.step_name)].AdaptiveMeshDomain(region=ale_region, controls='ALE_STD_CTRL')

        # follow_reg = r.Region(nodes=part2.sufaces['surface-contact'].nodes)
        #
        # model.DisplacementAdaptiveMeshConstraint(
        #     name='ALE_FOLLOW',
        #     createStepName=str(solver_cfg.step_name),
        #     region=follow_reg,
        #     u1=SET, u2=SET, u3=SET,
        #     motionType=FOLLOW
        # )


        # model.DisplacementAdaptiveMeshConstraint(
        #     name='ALE_INDEPENDENT_LOCK',
        #     createStepName=str(solver_cfg.step_name),
        #     region=indep_reg,
        #     u1=SET, u2=SET, u3=SET,
        #     motionType=INDEPENDENT
        # )

    ## Job
    job = mdb.Job(
        name=job_name,
        model='Compress_frame',
        numCpus=int(solver_cfg.cpus),
        numDomains=int(solver_cfg.cpus),
        multiprocessingMode=THREADS,
        type=ANALYSIS
    )
    job.writeInput()
    # Save abaqus cae
    mdb.saveAs(job_name+'.cae')
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

    geometry_cfg = _ns(data.get("geometry_cfg", {}))
    frame_lenght = float(data.get("frame_lenght", 30))
    material_model = str(data.get("material_model", "linear"))
    material_prop = _ns(data.get("material_prop", {}))
    solver_cfg = _ns(data.get("solver_cfg", {}))

    connector(geometry_cfg, frame_lenght, material_model, material_prop, solver_cfg)