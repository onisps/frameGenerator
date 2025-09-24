import os
import pathlib
import sys
from typing import Tuple, Any, List
from types import SimpleNamespace

from omegaconf import DictConfig


def read_conf(cfg:DictConfig, globalPath: str = None) -> tuple[list[str], list[str], SimpleNamespace, str, SimpleNamespace, SimpleNamespace]:
    geometry_cfg = SimpleNamespace()
    material_cfg =  SimpleNamespace()
    solver_cfg =  SimpleNamespace()
    material_model = str()
    parameters = list()
    objectives = list()

    error_count = 0

    print(f'Cfg parsing:')
    # check parameters, objectives and constraints
    if hasattr(cfg, 'problem'):
        if hasattr(cfg.problem, 'parameters'):
            parameters = list(cfg.problem.parameters)
        else:
            print('No attr \'problem.parameters\'. Exit')
            error_count += 1
        if hasattr(cfg.problem, 'objectives'):
            objectives = list(cfg.problem.objectives)
        else:
            print('No attr \'problem.objectives\'. Exit')
            error_count += 1
    else:
        print('No attr \'problem\'. Exit')
        error_count += 1

    if hasattr(cfg, 'paths'):
        os.makedirs(os.path.join(globalPath,cfg.paths.work_root), exist_ok=True)
        solver_cfg.work_root = cfg.paths.work_root
    else:
        print('No attr \'paths.work_root\'. Abaqus works in "./work"')
        os.makedirs("./work", exist_ok=True)
        solver_cfg.work_root = 'work'

    if hasattr(cfg, 'paths'):
        os.makedirs(os.path.join(globalPath,cfg.paths.results_root), exist_ok=True)
        solver_cfg.results_root = cfg.paths.results_root
    else:
        print('No attr \'paths.results_root\'. Results at "./results"')
        os.makedirs("./results", exist_ok=True)
        solver_cfg.results_root = 'results'

    if hasattr(cfg, 'geometry'):
    # if 'diameter' not in parameters:
        if hasattr(cfg.geometry, 'diameter'):
            geometry_cfg.diameter = cfg.geometry.diameter
        else:
            print('No attr \'geometry.diameter\'. Set default = 29 mm')
            geometry_cfg.diameter = 29

    # if 'h1' not in parameters:
        if hasattr(cfg.geometry, 'h1'):
            geometry_cfg.h1 = cfg.geometry.h1
        else:
            print('No attr \'geometry.h1\'. Set default = 0.3 mm')
            geometry_cfg.h1 = 0.3

    # if 'h2' not in parameters:
        if hasattr(cfg.geometry, 'h2'):
            geometry_cfg.h2 = cfg.geometry.h2
        else:
            print('No attr \'geometry.h2\'. Set default = 1 mm')
            geometry_cfg.h2 = 1

    # if 'h3' not in parameters:
        if hasattr(cfg.geometry, 'h3'):
            geometry_cfg.h3 = cfg.geometry.h3
        else:
            print('No attr \'geometry.h3\'. Set default = 0.3 mm')
            geometry_cfg.h3 = 0.3

    # if 'h2_3rd_layer' not in parameters:
        if hasattr(cfg.geometry, 'h2_3rd_layer'):
            geometry_cfg.h2_3rd_layer = cfg.geometry.h2_3rd_layer
        else:
            print('No attr \'geometry.h2_3rd_layer\'. Set default = 4 mm')
            geometry_cfg.h2_3rd_layer = 4

    # if 'width_low_cut' not in parameters:
        if hasattr(cfg.geometry, 'width_low_cut'):
            geometry_cfg.width_low_cut = cfg.geometry.width_low_cut
        else:
            print('No attr \'geometry.width_low_cut\'. Set default = 0.5 mm')
            geometry_cfg.width_low_cut = 0.5

    # if 'cell_height_1st_layer' not in parameters:
        if hasattr(cfg.geometry, 'cell_height_1st_layer'):
            geometry_cfg.cell_height_1st_layer = cfg.geometry.cell_height_1st_layer
        else:
            print('No attr \'geometry.cell_height_1st_layer\'. Set default = 7 mm')
            geometry_cfg.cell_height_1st_layer = 0.5

    # if 'repeat' not in parameters:
        if hasattr(cfg.geometry, 'repeat'):
            geometry_cfg.repeat = cfg.geometry.repeat
        else:
            print('No attr \'geometry.repeat\'. Set default = 12 times')
            geometry_cfg.repeat = 12

    # if 'fillet_a' not in parameters:
        if hasattr(cfg.geometry, 'fillet_a'):
            geometry_cfg.fillet_a = cfg.geometry.fillet_a
        else:
            print('No attr \'geometry.fillet_a\'. Set default = 0.02 mm')
            geometry_cfg.fillet_a = 0.02

    # if 'fillet_b' not in parameters:
        if hasattr(cfg.geometry, 'fillet_b'):
            geometry_cfg.fillet_b = cfg.geometry.fillet_b
        else:
            print('No attr \'geometry.fillet_b\'. Set default = 0.3 mm')
            geometry_cfg.fillet_b = 0.3

    # if 'fillet_c' not in parameters:
        if hasattr(cfg.geometry, 'fillet_c'):
            geometry_cfg.fillet_c = cfg.geometry.fillet_c
        else:
            print('No attr \'geometry.fillet_c\'. Set default = 0.4 mm')
            geometry_cfg.fillet_c = 0.4

    # if 'assymetry_1st_layer' not in parameters:
        if hasattr(cfg.geometry, 'assymetry_1st_layer'):
            geometry_cfg.assymetry_1st_layer = cfg.geometry.assymetry_1st_layer
        else:
            print('No attr \'geometry.assymetry_1st_layer\'. Set default = 0.5 times')
            geometry_cfg.assymetry_1st_layer = 0.5

    # if 'padding' not in parameters:
        if hasattr(cfg.geometry, 'padding'):
            geometry_cfg.padding = cfg.geometry.padding
        else:
            print('No attr \'geometry.padding\', its sturt width. Set default = 0.5 mm')
            geometry_cfg.padding = 0.5

    # if 'arc_offset' not in parameters:
        if hasattr(cfg.geometry, 'arc_offset'):
            geometry_cfg.arc_offset = cfg.geometry.arc_offset
        else:
            print('No attr \'geometry.arc_offset\'. Set default = 0.1 mm')
            geometry_cfg.arc_offset = 0.5

        if hasattr(cfg.geometry, 'thk'):
            geometry_cfg.thk = cfg.geometry.thk
        else:
            print('No attr \'geometry.thk\'. Set default = 0.5 mm')
            geometry_cfg.thk = 0.5
    else:
        print('No attr \'geometry\'. Exit')
        error_count += 1

    if hasattr(cfg, 'material'):
        if hasattr(cfg.material, 'name'):
            material_cfg.name = cfg.material.name
        else:
            print('No attr \'material.name\'. Set default = noname')
            material_cfg.name = 1

        if hasattr(cfg.material, 'EM'):
            material_cfg.EM = cfg.material.EM
        else:
            print('No attr \'material.EM\'. Set default = 1 MPa')
            material_cfg.EM = 1

        if hasattr(cfg.material, 'density'):
            material_cfg.density = float(str(cfg.material.density).replace(',','.'))
        else:
            print('No attr \'material.density\'. Set default = 1e-9 MPa')
            material_cfg.density = 1e-9

        if hasattr(cfg.material, 'Poisson'):
            material_cfg.Poisson = cfg.material.Poisson
        else:
            print('No attr \'material.Poisson\'. Set default = 0.45')
            material_cfg.Poisson = 0.45

        if hasattr(cfg.material, 'material_model'):
            material_cfg.material_model = cfg.material.material_model
            material_model = cfg.material.material_model
            if cfg.material.material_model.lower() == 'superelastic':
                material_cfg.EA = cfg.material.superelastic.EA
                material_cfg.nuA = cfg.material.superelastic.nuA
                material_cfg.nuM = cfg.material.superelastic.nuM
                material_cfg.sig_s_AS = cfg.material.superelastic.sig_s_AS
                material_cfg.sig_f_AS = cfg.material.superelastic.sig_f_AS
                material_cfg.sig_s_SA = cfg.material.superelastic.sig_s_SA
                material_cfg.sig_f_SA = cfg.material.superelastic.sig_f_SA
                material_cfg.sig_s_AC = cfg.material.superelastic.sig_s_AC
                material_cfg.eps_L = cfg.material.superelastic.eps_L
                material_cfg.eps_V = cfg.material.superelastic.eps_V
                material_cfg.T0 = cfg.material.superelastic.T0
                material_cfg.dSig_dT_L_per_C = cfg.material.superelastic.dSig_dT_L_per_C
                material_cfg.dSig_dT_U_per_C = cfg.material.superelastic.dSig_dT_U_per_C
            elif cfg.material.material_model.lower() == 'polynomial':
                material_cfg.mat_table = cfg.material.mat_table
    else:
        print('No attr \'material\'. Exit')
        error_count += 1

    if hasattr(cfg, 'solver'):
        if hasattr(cfg.solver, 'job_name_prefix'):
            solver_cfg.job_name_prefix = cfg.solver.job_name_prefix
        else:
            print('No attr \'solver.job_name_prefix\'. Set default = \"noname\"')
            solver_cfg.job_name_prefix = 'noname'

        if hasattr(cfg.solver, 'step_name'):
            solver_cfg.step_name = cfg.solver.step_name
        else:
            print('No attr \'solver.step_name\'. Set default = \"Step-Load\"')
            solver_cfg.step_name = 'Step-Load'

        if hasattr(cfg.solver, 'step_time'):
            solver_cfg.step_time = cfg.solver.step_time
        else:
            print('No attr \'solver.step_time\'. Set default = 1 sec')
            solver_cfg.step_time = 1

        if hasattr(cfg.solver, 'cpus'):
            solver_cfg.cpus = cfg.solver.cpus
        else:
            print('No attr \'solver.cpus\'. Set default = 4')
            solver_cfg.cpus = 4

        solver_cfg.outputs = SimpleNamespace()

        if hasattr(cfg.solver, 'outputs'):
            if hasattr(cfg.solver.outputs, 'field_outputs'):
                solver_cfg.outputs.field_outputs = cfg.solver.outputs.field_outputs
            else:
                print('No attr \'solver.outputs.field_outputs\'. Set default = [S, LE, U]')
                solver_cfg.outputs.field_outputs = ["S", "U", "LE"]

            if hasattr(cfg.solver.outputs, 'history_outputs'):
                solver_cfg.outputs.history_outputs = cfg.solver.outputs.history_outputs
            else:
                print('No attr \'solver.outputs.history_outputs\'. Set default = [ALLAE, ALLIE, ALLKE]')
                solver_cfg.outputs.history_outputs = ["ALLAE","ALLIE","ALLKE"]

            if hasattr(cfg.solver.outputs, 'time_interval'):
                solver_cfg.outputs.time_interval = cfg.solver.outputs.time_interval
            else:
                print('No attr \'solver.outputs.time_interval\'. Set default - 10 per Step Time')
                solver_cfg.outputs.field_outputs = solver_cfg.step_time / 10

            if hasattr(cfg.solver.outputs, 'frame_time_for_metric'):
                solver_cfg.outputs.frame_time_for_metric = cfg.solver.outputs.frame_time_for_metric
            else:
                print('No attr \'solver.outputs.frame_time_for_metric\'. Set default - [0., 1.] second')
                solver_cfg.outputs.field_outputs = [0., 1.]

        else:
            print('No attr \'solver.outputs\'. Exit')
            error_count += 1
    else:
        print('No attr \'solver\'. Exit')
        error_count += 1

    if error_count > 0:
        sys.exit("Error count > 1")
    else:
        print("Done!")

    return parameters, objectives, geometry_cfg, material_model, material_cfg, solver_cfg