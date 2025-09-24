import os, subprocess
import time
import json
import psutil as psu
import datetime
import glob
import getpass, math
import numpy as np
from typing import Union, Dict, Any

import numpy as np

try:
    from types import SimpleNamespace  # type: ignore
except Exception:  # pragma: no cover
    class SimpleNamespace(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

def run_solver(
    solver_cfg: Union[Dict[str, Any], SimpleNamespace, None] = None,
    project_root: str = None,
    abaqus_cmd: str = None,
    globalPath: str = None
) -> (str, float):
    def _get_info_about_solving_process() -> (str, float):
        with open(project_root + '/' + solver_cfg.job_name_prefix + '.sta', 'r') as f:
            lines = f.readlines()
            line_status = lines[-1].strip('\n').strip('  ')
            _temp_array = np.array(lines[-3].strip('\n').strip('  ').split(' '))
            line_time = float([x for x in _temp_array if x != ''][-3])
        return line_status, line_time


    TIMEOUT_MIN = 60
    SLEEP_RETRIES = 4

    t0 = datetime.datetime.now()
    project_root = project_root or os.getcwd()
    abaqus_cmd = abaqus_cmd or (
        (getattr(solver_cfg, "abaqus_cmd", None) if isinstance(solver_cfg, SimpleNamespace) else None)
        or (solver_cfg or {}).get("abaqus_cmd") if isinstance(solver_cfg, dict) else None
    ) or "abaqus"
    prev_path = os.getcwd()
    os.chdir(project_root)
    cmd = (f'{abaqus_cmd} '
           f'job={solver_cfg.job_name_prefix} '
           f'inp={solver_cfg.job_name_prefix} '
           f'cpus={solver_cfg.cpus} mp_mode=threads ask_delete=OFF')

    print("-------------------------------------------------------")
    print("Running the following command:")
    print(cmd)
    print("-------------------------------------------------------")

    subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    checked = False
    current_user = getpass.getuser()
    times_check_sleep = 0
    time.sleep(5)
    if (os.path.exists(globalPath+'/' + project_root + '/' + solver_cfg.job_name_prefix + '.lck')):
        while (os.path.exists(globalPath+'/' + project_root + '/' + solver_cfg.job_name_prefix + '.lck')):
            t = datetime.datetime.now() - t0
            sec = t.seconds
            m = int(t.total_seconds() // 60)
            h = int(sec / 3600)
            if m > 1 and not checked:
                for proc in psu.process_iter(['pid','name', 'username']):
                    if proc.info['name'] == 'pre' and proc.info['username'] == current_user:
                        os.system(f'pkill -n -9 pre')
                        message = 'ABAQUS terminated with error in pre'
                        return message, 0
                    if proc.info['name'] == 'package' and proc.info['username'] == current_user:
                        os.system(f'pkill -n -9 package')
                        message = 'ABAQUS terminated with error in package'
                        return message, 0
                checked = True
            if m < TIMEOUT_MIN:
                for proc in psu.process_iter(['name', 'username']):
                    if proc.info['name'] == 'standard' and proc.info['username'] == current_user:
                        if psu.Process(proc.pid).status() == psu.STATUS_SLEEPING:
                            times_check_sleep += 1
                            if times_check_sleep > SLEEP_RETRIES:
                                os.system(f'pkill -n -9 standard')
                                message = 'ABAQUS standard killed with sleep status'
                                if os.path.exists(project_root + '/' + solver_cfg.job_name_prefix + '.lck'):
                                    os.remove(project_root + '/' + solver_cfg.job_name_prefix + '.lck')
                                os.chdir(prev_path)
                                return _get_info_about_solving_process()
                        else:
                            times_check_sleep = 0

                time.sleep(5)
            else:
                os.system('pkill -n -9 standard')
                message = 'ABAQUS terminated due time'
                _, _time = _get_info_about_solving_process()
                return message, _time
    return 'ok', 1.0


def parce_results(
    solver_cfg: Union[SimpleNamespace, dict] = None,
    abaqus_cmd: str = 'abaqus',
    json_path: str = None,
):
    project_root = solver_cfg.work_root or os.getcwd()
    prev_path = os.getcwd()
    os.chdir(project_root)

    cmd = (f'{abaqus_cmd} cae '
           f'noGUI={os.path.join(prev_path, "utils", "abq_parse_results.py")} -- {json_path}'
           )

    print("-------------------------------------------------------")
    print("Running the following command:")
    print(cmd)
    print("-------------------------------------------------------")

    subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def process_results(
        cfg: Union[SimpleNamespace, dict] = None,
        work_path: str = None
):
    def _find_element_in_array_by_float(str_array: [str] = None, mask: Union[float, int, str] = None):
        out = []
        if type(mask) == float or type(mask) == int:
            mask = str(float(mask))

        for elem in str_array:
            if mask in elem:
                out.append(elem)
        if len(out) == 1:
            return out[0]
        else:
            return out

    res_path = os.path.join(work_path, cfg.results_root, cfg.job_name_prefix)
    list_of_stress = glob.glob(os.path.join(res_path,'S_Mises*.csv'))
    list_of_reaction_force = glob.glob(os.path.join(res_path,'RF*.csv'))
    list_of_radial_displacement = glob.glob(os.path.join(res_path,'U1_frame*.csv'))

    analizing_frames = cfg.outputs.frame_time_for_metric

    for time_frame in analizing_frames:

        actual_file_s = _find_element_in_array_by_float(list_of_stress,time_frame)
        actual_file_rf = _find_element_in_array_by_float(list_of_reaction_force,time_frame)
        actual_file_u = _find_element_in_array_by_float(list_of_radial_displacement,time_frame)

        max_s_mises = np.max(np.genfromtxt(actual_file_s, delimiter=',')[1:,2])
        data_rf = np.genfromtxt(actual_file_rf, delimiter=',')[1,:-1]
        max_deformation = np.max(np.genfromtxt(actual_file_u, delimiter=',')[1:,-1])

        print(max_s_mises)
        print(data_rf)
        print(max_deformation)

