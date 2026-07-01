from __future__ import annotations

import numpy as np


def fit_empirical_zeropoint(
    hmag: np.ndarray,
    electrons: np.ndarray,
    exptime_s: np.ndarray,
    seeing: np.ndarray | None = None,
    airmass: np.ndarray | None = None,
    seeing_ref: float = 1.3,
    airmass_ref: float = 1.2,
) -> dict[str, float]:
    """Fit a simple empirical count-rate model.

    Model:
        log10(electrons / second) = zp - 0.4 H
                                     + b_seeing * (seeing - seeing_ref)
                                     + b_airmass * (airmass - airmass_ref)

    If seeing/airmass are omitted, those terms are not fit.
    """
    hmag = np.asarray(hmag, dtype=float)
    y = np.log10(np.asarray(electrons, dtype=float) / np.asarray(exptime_s, dtype=float))

    cols = [np.ones_like(hmag)]
    names = ["zp_log10_e_per_s_h0"]

    # Fix the H-mag coefficient to -0.4 by moving it to the left side.
    y = y + 0.4 * hmag

    if seeing is not None:
        cols.append(np.asarray(seeing, dtype=float) - seeing_ref)
        names.append("seeing_slope_dex_per_arcsec")
    if airmass is not None:
        cols.append(np.asarray(airmass, dtype=float) - airmass_ref)
        names.append("airmass_slope_dex_per_airmass")

    X = np.vstack(cols).T
    coeff, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {name: float(value) for name, value in zip(names, coeff)}
