from __future__ import annotations

import os, glob
import sys
import random
from pathlib import Path

import hydra
from omegaconf import DictConfig
import numpy as np

from utils.config_utils import read_conf
from utils.cad_drawer import model_drawer
from utils.abq_connector import connector_console

config_name = 'config_ss'
globalPath = str(Path.cwd())
round_decimals = 4
random.seed(1)

def _get_random_value(low: float, top: float) -> float:
    return np.round(random.uniform(low, top), round_decimals)

def _print_parameters(params):
    for key in params.keys():
        val = params.get(key)
        print(f'{key:10s} > {val:7f}')

@hydra.main(config_path="config", config_name=config_name, version_base=None)
def main(cfg: DictConfig):

    # reading configuration file
    parameters, objectives, geometry_cfg, material_model, material_cfg, solver_cfg = read_conf(cfg, globalPath)

    first_done = False
    attempts_done = 0
    while not first_done:
        # prepare set of geometric values
        curr_geometry_cfg = geometry_cfg.__dict__.copy()
        for key in curr_geometry_cfg.keys():
            if key in parameters:
                val_range = curr_geometry_cfg.get(key)
                if len(val_range) != 2:
                    print(f'Exception: error in .yaml configuration. '
                          f'Length of geometry.{key} = {len(val_range)} > {val_range}! '
                          f'Change it to [a, b]')
                    sys.exit(1)
                elif len(val_range) == 2:
                    curr_geometry_cfg.__setitem__(key, _get_random_value(low=val_range[0], top=val_range[1]))
                else:
                    curr_geometry_cfg.__setitem__(key, val_range)
        #

        try:
            # compile step file of stent
            length = model_drawer(curr_geometry_cfg, solver_cfg.job_name_prefix)
        except Exception as e:
            print(f'\rException in model_drawer..... It`s already {attempts_done} attempt in row', end='', flush=True)
            attempts_done += 1
            continue
        for file in glob.glob(f'./{solver_cfg.work_root}/abaqus*'):
            os.remove(path=file)
        #configure .cae and inp
        connector_console(geometry_cfg.diameter, length,
                          material_model, material_cfg, solver_cfg, solver_cfg.work_root,
                          'abaqus', os.path.join(globalPath,'utils','abq_cae_compiler_explicit.py'),
                          os.path.join(globalPath, solver_cfg.work_root,'config.json'))

        _print_parameters(curr_geometry_cfg)
        first_done = True


if __name__ == "__main__":
    main()

