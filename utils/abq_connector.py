# utils/compute_utils_ext.py
import os, subprocess
import json
import tempfile
from typing import Union, Dict, Any

# Полифилл: в окружении Abaqus может не быть types.SimpleNamespace
try:
    from types import SimpleNamespace  # type: ignore
except Exception:  # pragma: no cover
    class SimpleNamespace(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

def _to_plain(obj: Any):
    """
    Рекурсивно приводит структуру к JSON-совместимой:
    - OmegaConf (DictConfig/ListConfig) → dict/list через OmegaConf.to_container(resolve=True)
    - SimpleNamespace → dict
    - numpy (ndarray, generic числа) → list / float / int
    - set/tuple → list
    - PathLike → str
    - всё остальное — как есть
    """
    # OmegaConf (Hydra)
    try:
        from omegaconf import DictConfig, ListConfig, OmegaConf  # type: ignore
        if isinstance(obj, (DictConfig, ListConfig)):
            return _to_plain(OmegaConf.to_container(obj, resolve=True))
    except Exception:
        pass

    # SimpleNamespace
    if isinstance(obj, SimpleNamespace):
        return {k: _to_plain(v) for k, v in obj.__dict__.items()}

    # dict / list / tuple / set
    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_plain(v) for v in obj]

    # numpy: скаляры и массивы
    try:
        import numpy as np  # type: ignore
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.generic,)):
            return obj.item()
    except Exception:
        pass

    # PathLike
    if hasattr(obj, "__fspath__"):
        try:
            return os.fspath(obj)
        except Exception:
            pass

    # Enum → value
    try:
        import enum
        if isinstance(obj, enum.Enum):
            return _to_plain(obj.value)
    except Exception:
        pass

    return obj  # уже JSON-совместимое


def connector_console(
    geometry_cfg: Union[Dict[str, Any], SimpleNamespace, None] = None,
    frame_lenght: float = 30.0,
    material_model: str = "linear",
    material_prop: Union[Dict[str, Any], SimpleNamespace, None] = None,
    solver_cfg: Union[Dict[str, Any], SimpleNamespace, None] = None,
    solver_path: str = None,
    abaqus_cmd: str = None,
    script_relpath: str = "utils/abq_connector.py",
    json_path: str = None,
    project_root: str = None,
):
    """
    Запускает Abaqus/CAE в noGUI-режиме, передавая параметры в abq_connector.py через JSON.
    Блокирующий вызов (ждёт окончания расчёта). Возвращает код возврата процесса (0 = успех).

    Параметры:
      - geometry_cfg, material_prop, solver_cfg — словари с параметрами геометрии, свойств материала, настройками солвера.
      - project_root: корень проекта (где лежит utils/abq_connector.py). По умолчанию — текущая папка.
      - solver_path: путь/имя команды Abaqus (например, "/opt/abaqus/Commands/abaqus"); по умолчанию "abaqus".
      - script_relpath: относительный путь к скрипту (по умолчанию "utils/abq_connector.py").
      - json_path: куда сохранить JSON; если не задано — создаётся временный файл в project_root.
    """
    solver_path = solver_path or os.getcwd()
    abaqus_cmd = abaqus_cmd or (
        (getattr(solver_cfg, "abaqus_cmd", None) if isinstance(solver_cfg, SimpleNamespace) else None)
        or (solver_cfg or {}).get("abaqus_cmd") if isinstance(solver_cfg, dict) else None
    ) or "abaqus"

    # Сериализуем параметры
    payload = {
        "geometry_cfg": _to_plain(geometry_cfg),
        "frame_lenght": float(frame_lenght),
        "material_model": str(material_model),
        "material_prop": _to_plain(material_prop or {}),
        "solver_cfg": _to_plain(solver_cfg or {}),
    }

    # Путь к JSON
    if json_path is None:
        tmpdir = tempfile.mkdtemp(prefix="abq_params_", dir=solver_path)
        json_path = os.path.join(tmpdir, "params.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Путь к вашему скрипту abq_connector.py
    script_path = os.path.join(solver_path, script_relpath)
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Не найден скрипт Abaqus: {script_path}")

    # Сформируем команду; паттерн: abaqus cae noGUI=<script> -- <params.json>
    # На *nix корректно с 'cd &&'; на Windows используйте аналогично, либо задайте абсолютные пути.
    os.chdir(solver_path)
    cmd = f'{abaqus_cmd} cae noGUI="{script_path}" -- "{json_path}"'
    #
    # print("-------------------------------------------------------")
    # print("Running the following command:")
    # print(cmd)
    # print("-------------------------------------------------------")


    subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    os.chdir(project_root)
