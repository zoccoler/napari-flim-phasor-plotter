import numpy as np
from typing import Tuple, Union


def get_phasor_calibration_transform(
    calib_img: np.ndarray,
    laser_frequency: float,
    calibration_lifetime: float,
    harmonic: int = 1,
) -> dict:
    """
    Calculate the calibration transform from a calibration image and reference lifetime.

    Parameters
    ----------
    calib_img : np.ndarray
            Calibration FLIM image (microtime first axis).
    laser_frequency : float
            Laser frequency in MHz.
    calibration_lifetime : float
            Reference lifetime in ns.
    harmonic : int, optional
            Harmonic to use, by default 1.

    Returns
    -------
    dict
            Transform dictionary for calibrate_phasor_coordinates.
    """
    from .phasors import get_phasor_components

    g_calib, s_calib, _ = get_phasor_components(calib_img, harmonic=harmonic)
    intensity_calib = np.sum(calib_img, axis=0)
    G_com, S_com = get_phasor_center_of_mass(
        g_calib, s_calib, intensity=intensity_calib, as_polar=False
    )
    G_ref, S_ref = theoretical_phasor_coordinate(
        laser_frequency,
        calibration_lifetime,
        harmonic=harmonic,
        as_polar=False,
    )
    transform = calculate_phasor_transform(
        (G_com, S_com), (G_ref, S_ref), mode="euclidean"
    )
    return transform


def get_phasor_center_of_mass(
    g: np.ndarray,
    s: np.ndarray,
    intensity: np.ndarray = None,
    as_polar: bool = False,
) -> Union[Tuple[float, float], Tuple[float, float]]:
    """
    Calculate the center of mass of phasor coordinates (G, S) from G and S arrays.
    Optionally return as polar coordinates (modulus, phase).

    Parameters
    ----------
    g : np.ndarray
            G image (same shape as s)
    s : np.ndarray
            S image (same shape as g)
    intensity : np.ndarray, optional
            Intensity image (same shape as g/s) to use as weights. If None, uses uniform weights.
    as_polar : bool, optional
            If True, return (modulus, phase), else (G, S).

    Returns
    -------
    Tuple[float, float]
            (G, S) or (modulus, phase) of center of mass.
    """
    import dask.array as da

    is_dask = (hasattr(g, "compute") and isinstance(g, da.Array)) or (
        hasattr(s, "compute") and isinstance(s, da.Array)
    )
    xp = da if is_dask else np
    mask = xp.isfinite(g) & xp.isfinite(s)
    g_flat = g[mask]
    s_flat = s[mask]
    if intensity is not None:
        weights = intensity[mask]
    else:
        weights = None
    if is_dask:
        G_com = da.average(g_flat, weights=weights)
        S_com = da.average(s_flat, weights=weights)
    else:
        G_com = np.average(g_flat, weights=weights)
        S_com = np.average(s_flat, weights=weights)
    if as_polar:
        modulus = xp.sqrt(G_com**2 + S_com**2)
        phase = xp.arctan2(S_com, G_com)
        return modulus, phase
    return G_com, S_com


def theoretical_phasor_coordinate(
    laser_frequency_mhz: float,
    lifetime_ns: float,
    harmonic: int = 1,
    as_polar: bool = False,
) -> Tuple[float, float]:
    """
    Calculate theoretical phasor coordinate for a given lifetime and laser frequency.

    Parameters
    ----------
    laser_frequency_mhz : float
            Laser frequency in MHz.
    lifetime_ns : float
            Lifetime in nanoseconds.
    harmonic : int, optional
            Harmonic to use, by default 1.
    as_polar : bool, optional
            If True, return (modulus, phase), else (G, S).

    Returns
    -------
    Tuple[float, float]
            (G, S) or (modulus, phase) for the given lifetime.
    """
    omega = 2 * np.pi * laser_frequency_mhz * 1e6 * harmonic
    tau = lifetime_ns * 1e-9
    denom = 1 + (omega * tau) ** 2
    G = 1 / denom
    S = (omega * tau) / denom
    if as_polar:
        modulus = np.sqrt(G**2 + S**2)
        phase = np.arctan2(S, G)
        return modulus, phase
    return G, S


def calculate_phasor_transform(
    measured: Tuple[float, float],
    reference: Tuple[float, float],
    mode: str = "euclidean",
) -> dict:
    """
    Calculate the transform needed to map measured phasor coordinates to reference.

    Parameters
    ----------
    measured : Tuple[float, float]
            (G, S) center of mass from calibration image.
    reference : Tuple[float, float]
            (G, S) theoretical/reference coordinate.
    mode : str, optional
            'euclidean' (translation+rotation) or 'polar' (modulus/phase shift), by default 'euclidean'.

    Returns
    -------
    dict
            Transform parameters.
    """
    if mode == "polar":
        m_mod = np.sqrt(measured[0] ** 2 + measured[1] ** 2)
        m_phase = np.arctan2(measured[1], measured[0])
        r_mod = np.sqrt(reference[0] ** 2 + reference[1] ** 2)
        r_phase = np.arctan2(reference[1], reference[0])
        scale = r_mod / m_mod if m_mod != 0 else 1.0
        shift = r_phase - m_phase
        return {"mode": "polar", "scale": scale, "phase_shift": shift}
    else:
        # rotation + translation (no scaling, as phasor plot is unit circle)
        angle = np.arctan2(reference[1], reference[0]) - np.arctan2(
            measured[1], measured[0]
        )
        rot_matrix = np.array(
            [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
        )
        translation = np.array(reference) - rot_matrix @ np.array(measured)
        return {
            "mode": "euclidean",
            "rotation": angle,
            "translation": translation,
        }


def calibrate_phasor_coordinates(
    g: np.ndarray, s: np.ndarray, transform: dict
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply calibration transform to G and S images directly.

    Parameters
    ----------
    g : np.ndarray
            G image (same shape as s)
    s : np.ndarray
            S image (same shape as g)
    transform : dict
            Transform as returned by calculate_phasor_transform.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
            Calibrated (G, S) images, same shape as input.
    """
    import dask.array as da

    is_dask = hasattr(g, "compute") and isinstance(g, da.Array)
    xp = da if is_dask else np
    g = xp.asarray(g)
    s = xp.asarray(s)
    if transform["mode"] == "polar":
        mod = xp.sqrt(g**2 + s**2)
        phase = xp.arctan2(s, g)
        mod_cal = mod * transform["scale"]
        phase_cal = phase + transform["phase_shift"]
        g_cal = mod_cal * xp.cos(phase_cal)
        s_cal = mod_cal * xp.sin(phase_cal)
        return g_cal, s_cal
    else:
        # rotate and translate
        angle = transform["rotation"]
        rot_matrix = xp.array(
            [[xp.cos(angle), -xp.sin(angle)], [xp.sin(angle), xp.cos(angle)]]
        )
        shape = g.shape
        coords = xp.stack([g.ravel(), s.ravel()], axis=-1)
        coords_rot = coords @ rot_matrix.T
        coords_cal = coords_rot + transform["translation"]
        g_cal = coords_cal[:, 0].reshape(shape)
        s_cal = coords_cal[:, 1].reshape(shape)
        return g_cal, s_cal
