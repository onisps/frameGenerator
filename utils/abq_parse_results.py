# -*- utf-8 -*-

import os, sys
import math
import json

from odbAccess import openOdb

SYS_AGREEMENT_ERROR_BY_TIME = 0.01

if sys.version_info.major >=3:
    xrange = range

try:
    from types import SimpleNamespace  # type: ignore
except Exception:  # pragma: no cover
    class SimpleNamespace(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)



def load_json_utf8(path):
    try:
        import io
        with io.open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except TypeError:
        with open(path, 'rb') as f:
            return json.loads(f.read().decode('utf-8'))

def _nearest_frame(step, target_time):
    # Return (frame, idx, actual_time) closest to target_time
    frames = step.frames
    if not frames:
        return None, -1, None
    best = None
    best_idx = -1
    best_dt = 1e99
    for i, fr in enumerate(frames):
        t = fr.frameValue
        dt = abs(t - target_time)
        if dt < best_dt:
            best = fr; best_idx = i; best_dt = dt
    return best, best_idx, (best.frameValue if best else None)

def _write_csv(path, header, rows):
    import csv
    with open(path, 'wb') as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def _sum_reaction_forces(frame, inst_name):
    """Sum nodal RF over all nodes of instance 'inst_name' in this frame."""
    if 'RF' not in frame.fieldOutputs:
        return None  # not available
    RF = frame.fieldOutputs['RF']
    # Filter values by instance
    vals = [v for v in RF.values if v.instance and v.instance.name == inst_name]
    sx = sy = sz = 0.0
    for v in vals:
        # v.data is a 3-component vector
        d = v.data
        sx += d[0]; sy += d[1]; sz += d[2]
    mag = math.sqrt(sx*sx + sy*sy + sz*sz)
    return sx, sy, sz, mag, len(vals)

def _transform_U_to_cyl(frame, datum):
    """Return transformed U field (Ur, Utheta, Uz) using cylindrical datum."""
    if 'U' not in frame.fieldOutputs:
        return None
    U = frame.fieldOutputs['U']
    try:
        Uc = U.getTransformedField(datumCsys=datum)  # vector field transformation
        return Uc
    except Exception as e:
        return None

def _collect_S_mises(frame, inst_name):
    """Collect (elementLabel, ipIndex, mises) for instance 'inst_name'."""
    if 'S' not in frame.fieldOutputs:
        return []
    S = frame.fieldOutputs['S']
    # prefer integration points
    try:
        from abaqusConstants import INTEGRATION_POINT
        S = S.getSubset(position=INTEGRATION_POINT)
    except Exception:
        pass
    out = []
    for v in S.values:
        if not v.instance or v.instance.name != inst_name:
            continue
        # v.integrationPoint or v.sectionPoint (depending on element type)
        ip = getattr(v, 'integrationPoint', None)
        ipID = getattr(ip, 'number', 1) if ip else 1
        try:
            vm = v.mises
        except Exception:
            # fallback compute from v.data (length 6)
            d = (v.data + (0.0,)*6)[:6]
            s11, s22, s33, s12, s13, s23 = d
            j2 = 0.5*((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2) + 3.0*(s12**2 + s13**2 + s23**2)
            vm = math.sqrt(max(j2,0.0))
        out.append((v.elementLabel, ipID, vm))
    return out


def _collect_U1_cyl(frame, datum, inst_name):
    """Collect (nodeLabel, U1) where U transformed to cylindrical CS."""
    Uc = _transform_U_to_cyl(frame, datum)
    if Uc is None:
        return []
    out = []
    for v in Uc.values:
        if not v.instance or v.instance.name != inst_name:
            continue
        d = v.data
        u1 = d[0] if len(d) > 1 else ''
        out.append((v.nodeLabel, u1))
    return out

def _series(history_region, key):
    """
    Extract a time series from an assembly-level history region.

    Parameters
    ----------
    history_region : HistoryRegion
        The 'Assembly ASSEMBLY' history region from an ODB step.
    key : str
        History output key (e.g., 'ALLIE', 'ALLKE', 'ALLAE', 'ALLWK').

    Returns
    -------
    (list[float], list[float])
        Tuple (times, values). Returns ([], []) if the key is missing or empty.
    """
    if key not in history_region.historyOutputs:
        return [], []
    data = history_region.historyOutputs[key].data or []
    if not data:
        return [], []
    t = [float(tv[0]) for tv in data]
    v = [float(tv[1]) for tv in data]
    return t, v

def _nearest_indices(query_t, src_t):
    """
    Map each query time to the nearest index in a monotone source time array.

    This is a single-pass two-pointer merge with O(N+M) complexity,
    which is efficient for up to ~10k frames.

    Parameters
    ----------
    query_t : list[float]
        Monotone non-decreasing query times (e.g., frame.frameValue).
    src_t : list[float]
        Monotone non-decreasing source times from a history output.

    Returns
    -------
    list[int]
        For each query time, the index in src_t of the nearest time (ties resolved to the right).
        Returns a zero-filled list if src_t is empty.
    """
    n, m = len(query_t), len(src_t)
    idx = [0] * n
    if m == 0 or n == 0:
        return idx
    j = 0
    for i in xrange(n):
        tq = query_t[i]
        while (j + 1) < m and abs(src_t[j + 1] - tq) <= abs(src_t[j] - tq):
            j += 1
        idx[i] = j
    return idx

def _safe_div(a, b, eps=1e-16):
    """
    Numerically safe division a/b with sign-preserving epsilon.

    Parameters
    ----------
    a : float
    b : float
    eps : float
        Epsilon used when |b| is too small.

    Returns
    -------
    float
        a / b if |b| > eps, otherwise a / sign_preserving_eps.
    """
    if abs(b) > eps:
        return a / b
    return a / (eps if b >= 0.0 else -eps)

def last_stable_frame_fast(frames, step,
                           tauK=0.05, tauA=0.05, tauDelta=0.2):
    """
    Pick the last stable frame based on energy criteria using O(N+M) time matching.

    Criteria per frame f (quasi-static intent):
      - RK = ALLKE/ALLIE <= tauK  (small kinetic energy)
      - RA = ALLAE/ALLIE <= tauA  (small artificial energy; 0 if ALLAE missing)
      - Ebal = |ALLWK - (ALLIE+ALLKE+ALLAE+ALLVD+ALLCD)| / max(|ALLWK|, eps) <= tauE
      - Smoothness: dI = |delta(ALLIE)| / max(1, |ALLIE|) <= tauDelta

    The function scans frames from the end to achieve early exit on the first stable frame.
    If no frame satisfies thresholds, it returns the frame with minimal aggregated violation.

    Parameters
    ----------
    frames : list[Frame]
        Frames of the target step (e.g., step.frames).
    step : OdbStep
        The step object owning `frames` (to access 'Assembly ASSEMBLY' histories).
    tauK : float
        Threshold for RK.
    tauA : float
        Threshold for RA.
    tauE : float
        Threshold for Ebal.
    tauDelta : float
        Threshold for the relative increment of ALLIE.

    Returns
    -------
    (Frame, int)
        The selected frame object and its index within `frames`.
        If assembly histories are missing, returns the last frame by default.
    """
    if not frames:
        return None, -1

    try:
        hr = step.historyRegions['Assembly ASSEMBLY']
    except Exception:
        return frames[-1], len(frames) - 1

    tI, I = _series(hr, 'ALLIE')
    tK, K = _series(hr, 'ALLKE')
    tA, A = _series(hr, 'ALLAE')
    tW, W = _series(hr, 'ALLWK')

    if not (tI and tK and tW):
        return frames[-1], len(frames) - 1

    Ft = [fr.frameValue for fr in frames]

    iI = _nearest_indices(Ft, tI)
    iK = _nearest_indices(Ft, tK)
    iW = _nearest_indices(Ft, tW)
    iA = _nearest_indices(Ft, tA) if tA else []

    best_idx, best_score = None, 1e30

    for idx in xrange(len(frames) - 1, -1, -1):
        Ii = I[iI[idx]]
        Ki = K[iK[idx]]
        Ai = A[iA[idx]] if tA else 0.0

        RK = abs(_safe_div(Ki, Ii))
        RA = abs(_safe_div(Ai, Ii)) if tA else 0.0

        if idx > 0:
            prevI = I[iI[idx - 1]]
            dI = abs(Ii - prevI) / max(1.0, abs(Ii))
        else:
            dI = 0.0

        ok = (RK <= tauK) and (RA <= tauA) and (dI <= tauDelta)
        if ok:
            return frames[idx], idx  # early exit: last stable

        score = (max(RK - tauK, 0.0) +
                 max(RA - tauA, 0.0) +
                 max(dI - tauDelta, 0.0))
        if score < best_score:
            best_score, best_idx = score, idx

    return frames[best_idx], best_idx

def parce_results(
    solver_cfg
):
    step_name  = solver_cfg.step_name
    job_name   = solver_cfg.job_name_prefix
    res_root   = solver_cfg.results_root

    odb_path = str(job_name+'.odb')

    out_dir = os.path.join(res_root, job_name)

    if not os.path.exists(res_root):
        os.makedirs(res_root)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # open ODB
    print(odb_path)
    odb = openOdb(odb_path, readOnly=True)
    asm = odb.rootAssembly

    step = odb.steps[str(step_name)]

    # build cylindrical datum as in the model (origin, point1=(1,0,0), point2=(0,1,0), axis Z)
    cyl_datum = asm.datumCsyses[asm.datumCsyses.keys()[-1]]

    # target times
    # targets = [0.1, 0.75, 1.0]
    targets = solver_cfg.outputs.frame_time_for_metric

    frame_last, idx_last = last_stable_frame_fast(step.frames, step, tauK=0.05, tauA=0.05, tauDelta=0.2)

    print(' *-* Found last frame: ', step.frames[idx_last].frameValue)

    for tt in targets:
        fr, idx, t_act = _nearest_frame(step, tt)

        print('expects %5f > get %5f' % (tt, step.frames[idx].frameValue))
        if tt - step.frames[idx].frameValue > SYS_AGREEMENT_ERROR_BY_TIME:
            print('\t Error: nearest time frame not found.')
            continue
        tt = step.frames[idx].frameValue
        if fr is None:
            sys.stderr.write("WARN: no frames in step; skip t=%.3f\n" % tt); continue

        # 1) S_Mises on frame
        print('_collect_S_mises')
        s_rows = _collect_S_mises(fr, 'FRAME')
        _write_csv(os.path.join(out_dir, "S_Mises_frame_t%.2f.csv" % tt),
                  ['elementLabel','ipIndex','Mises'],
                  s_rows)

        # 2) Sum RF on balloon (vector sum -> resultant)
        print('_sum_reaction_forces')
        rf = _sum_reaction_forces(fr, 'BALLOON')
        if rf is not None:
            sx, sy, sz, mag, n = rf
            print(rf)
            _write_csv(os.path.join(out_dir, "RF_balloon_SUM_t%.2f.csv" % tt),
                      ['sum_RFx','sum_RFy','sum_RFz','resultant','n_nodes'],
                      [(sx, sy, sz, mag, n)])
        else:
            sys.stderr.write("INFO: RF field not present at t=%.2f; skip RF sum.\n" % tt)

        # 3) U1 in cylindrical CS on frame
        u_rows = []
        if cyl_datum is not None:
            u_rows = _collect_U1_cyl(fr, cyl_datum, 'FRAME')
        if u_rows:
            _write_csv(os.path.join(out_dir, "U1_frame_cyl_t%.2f.csv" % tt),
                      ['nodeLabel','U1_cyl'],
                      u_rows)
        else:
            sys.stderr.write("INFO: cannot transform U to cylindrical at t=%.2f (no U or no datum).\n" % tt)

        sys.stdout.write("OK: exported t_target=%.2f (frame idx=%d, t_actual=%.6f)\n" % (tt, idx, t_act))


    s_rows = _collect_S_mises(frame_last, 'FRAME')
    _write_csv(os.path.join(out_dir, "S_Mises_frame_t_last.csv"),
               ['elementLabel', 'ipIndex', 'Mises'],
               s_rows)
    rf = _sum_reaction_forces(frame_last, 'BALLOON')

    sx, sy, sz, mag, n = rf
    print(rf)
    _write_csv(os.path.join(out_dir, "RF_balloon_SUM_t_last.csv"),
               ['sum_RFx', 'sum_RFy', 'sum_RFz', 'resultant', 'n_nodes'],
               [(sx, sy, sz, mag, n)])

    u_rows = _collect_U1_cyl(step.frames[idx_last], cyl_datum, 'FRAME')
    _write_csv(os.path.join(out_dir, "U1_frame_cyl_t_last.csv"),
               ['nodeLabel', 'U1_cyl'],
               u_rows)

    _write_csv(os.path.join(out_dir, "last_time_step.csv"),
               ['last_time',], [(frame_last.frameValue,)])
    odb.close()

if __name__ == "__main__":

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

    solver_cfg = _ns(data.get("solver_cfg", {}))
    parce_results(solver_cfg)