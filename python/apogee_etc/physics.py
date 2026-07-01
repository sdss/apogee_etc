from __future__ import annotations

import numpy as np


def fiber_area_arcsec2(fiber_diameter_arcsec: float) -> float:
    return float(np.pi * (fiber_diameter_arcsec / 2.0) ** 2)


def gaussian_fiber_fraction(seeing_fwhm_arcsec: float, fiber_diameter_arcsec: float) -> float:
    """Fraction of a centered circular 2-D Gaussian PSF entering a fiber.

    This is useful as a smooth first-order aperture-loss model. Real APOGEE
    data should be used to calibrate residual seeing/fiber effects.
    """
    if seeing_fwhm_arcsec <= 0:
        raise ValueError("seeing_fwhm_arcsec must be positive")
    if fiber_diameter_arcsec <= 0:
        raise ValueError("fiber_diameter_arcsec must be positive")

    sigma = seeing_fwhm_arcsec / 2.354820045
    radius = fiber_diameter_arcsec / 2.0
    return float(1.0 - np.exp(-0.5 * (radius / sigma) ** 2))
