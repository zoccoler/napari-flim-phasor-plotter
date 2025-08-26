import numpy as np
from typing import Tuple


def compute_phasor_adjustment(
    calib_img: np.ndarray,
    laser_frequency: float,
    calibration_lifetime: float,
    harmonic: int = 1,
) -> Tuple[float, float]:
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
    Tuple[float, float]
            Phase and modulation for calibrate_phasor_coordinates.
    """
    from .phasors import get_phasor_components

    g_calib, s_calib, _ = get_phasor_components(calib_img, harmonic=harmonic)
    intensity_calib = np.sum(calib_img, axis=0)
    G_com, S_com = get_phasor_center_of_mass(
        g_calib, s_calib, intensity=intensity_calib
    )
    G_ref, S_ref = theoretical_phasor_coordinate(
        laser_frequency,
        calibration_lifetime,
        harmonic=harmonic,
    )
    phase, modulation = calculate_phasor_rotation_and_scaling((G_com, S_com), (G_ref, S_ref))
    return phase, modulation


def get_phasor_center_of_mass(
    g: np.ndarray,
    s: np.ndarray,
    intensity: np.ndarray = None,
) -> Tuple[float, float]:
    """
    Calculate the center of mass of phasor coordinates (G, S) from G and S arrays.

    Parameters
    ----------
    g : np.ndarray
        G image (same shape as s)
    s : np.ndarray
        S image (same shape as g)
    intensity : np.ndarray, optional
        Intensity image (same shape as g/s) to use as weights. If None, uses uniform weights.

    Returns
    -------
    Tuple[float, float]
        (G, S) of center of mass.
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
    return G_com, S_com


def theoretical_phasor_coordinate(
    laser_frequency_mhz: float,
    lifetime_ns: float,
    harmonic: int = 1,
) -> Tuple[float, float]:
    """
    Calculate theoretical phasor coordinate (G, S) for a given lifetime and laser frequency.

    Parameters
    ----------
    laser_frequency_mhz : float
        Laser frequency in MHz.
    lifetime_ns : float
        Lifetime in nanoseconds.
    harmonic : int, optional
        Harmonic to use, by default 1.

    Returns
    -------
    Tuple[float, float]
        (G, S) for the given lifetime.
    """
    omega = 2 * np.pi * laser_frequency_mhz * 1e6 * harmonic
    tau = lifetime_ns * 1e-9
    denom = 1 + (omega * tau) ** 2
    G = 1 / denom
    S = (omega * tau) / denom
    return G, S


def calculate_phasor_rotation_and_scaling(
    measured: Tuple[float, float],
    reference: Tuple[float, float],
) -> Tuple[float, float]:
    """
    Calculate the phase (rotation) and modulation (scaling) needed to map measured phasor coordinates to reference.

    Parameters
    ----------
    measured : Tuple[float, float]
        (G, S) center of mass from calibration image.
    reference : Tuple[float, float]
        (G, S) theoretical/reference coordinate.

    Returns
    -------
    Tuple[float, float]
        phase (float, radians), modulation (float, scaling factor)
    """
    measured_phase = np.arctan2(measured[1], measured[0])
    reference_phase = np.arctan2(reference[1], reference[0])
    measured_modulation = np.hypot(measured[0], measured[1])
    reference_modulation = np.hypot(reference[0], reference[1])
    phase = reference_phase - measured_phase
    modulation = reference_modulation / measured_modulation if measured_modulation != 0 else 1.0
    return phase, modulation


def apply_phasor_adjustment(
    g: np.ndarray, s: np.ndarray, phase: float, modulation: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calibrate phasor coordinates by rotating by 'phase' and scaling by 'modulation'.

    Parameters
    ----------
    g : np.ndarray
        G image (same shape as s)
    s : np.ndarray
        S image (same shape as g)
    phase : float
        Rotation angle in radians.
    modulation : float
        Scaling factor.

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
    g_factor = modulation * xp.cos(phase)
    s_factor = modulation * xp.sin(phase)
    g_cal = g * g_factor - s * s_factor
    s_cal = g * s_factor + s * g_factor
    return g_cal, s_cal
