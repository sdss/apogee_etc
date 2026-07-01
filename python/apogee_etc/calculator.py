from __future__ import annotations

from dataclasses import replace

import numpy as np

from .models import ETCInput, ETCOutput
from .observatories import get_observatory
from .physics import fiber_area_arcsec2, gaussian_fiber_fraction


def _stellar_rate_e_per_s(inp: ETCInput) -> tuple[float, float]:
    obs = get_observatory(inp.observatory)

    log_rate = obs.empirical_zp_log10_e_per_s_h0 - 0.4 * inp.hmag

    if inp.include_empirical_terms:
        log_rate += obs.seeing_slope_dex_per_arcsec * (
            inp.seeing_fwhm_arcsec - obs.seeing_ref_arcsec
        )
        log_rate += obs.airmass_slope_dex_per_airmass * (
            inp.airmass - obs.airmass_ref
        )

    if inp.fiber_coupling_model == "gaussian":
        fiber_fraction = gaussian_fiber_fraction(
            inp.seeing_fwhm_arcsec, obs.fiber_diameter_arcsec
        )
    elif inp.fiber_coupling_model in {"none", "empirical_only"}:
        fiber_fraction = 1.0
    else:
        raise ValueError(
            "fiber_coupling_model must be 'gaussian', 'empirical_only', or 'none'"
        )

    return float(10**log_rate * fiber_fraction), fiber_fraction


def calculate_snr(inp: ETCInput) -> ETCOutput:
    obs = get_observatory(inp.observatory)
    warnings: list[str] = []

    if inp.nexp < 1:
        raise ValueError("nexp must be >= 1")
    if inp.exptime_s <= 0:
        raise ValueError("exptime_s must be positive")
    if inp.hmag < -5 or inp.hmag > 25:
        warnings.append("H magnitude is outside the usual calibrated range.")
    if inp.seeing_fwhm_arcsec < 0.5 or inp.seeing_fwhm_arcsec > 4.0:
        warnings.append("Seeing is outside the nominal calibration range.")
    if inp.airmass < 1.0 or inp.airmass > 2.5:
        warnings.append("Airmass is outside the nominal calibration range.")

    total_exptime_s = inp.exptime_s * inp.nexp
    star_rate, fiber_fraction = _stellar_rate_e_per_s(inp)
    stellar_e = star_rate * total_exptime_s

    sky_rate_area = (
        obs.default_sky_e_per_s_arcsec2
        if inp.sky_e_per_s_arcsec2 is None
        else inp.sky_e_per_s_arcsec2
    )
    sky_e = sky_rate_area * fiber_area_arcsec2(obs.fiber_diameter_arcsec) * total_exptime_s

    dark_e = obs.dark_current_e_per_s_pix * obs.npix_per_resolution_element * total_exptime_s
    rn_var = inp.nexp * obs.npix_per_resolution_element * obs.read_noise_e**2
    empirical_var = (obs.empirical_noise_floor_frac * stellar_e) ** 2

    variance = stellar_e + sky_e + dark_e + rn_var + empirical_var
    noise_e = float(np.sqrt(variance))
    snr = float(stellar_e / noise_e) if noise_e > 0 else 0.0

    return ETCOutput(
        snr=snr,
        total_exptime_s=total_exptime_s,
        stellar_electrons=float(stellar_e),
        sky_electrons=float(sky_e),
        dark_electrons=float(dark_e),
        read_noise_variance_e2=float(rn_var),
        empirical_noise_variance_e2=float(empirical_var),
        total_noise_electrons=noise_e,
        fiber_fraction=float(fiber_fraction),
        observatory=obs.name,
        warnings=warnings,
    )


def exposure_time_for_snr(
    inp: ETCInput,
    target_snr: float,
    min_exptime_s: float = 1.0,
    max_exptime_s: float = 100_000.0,
    rtol: float = 1e-3,
) -> ETCOutput:
    """Find per-exposure time required to reach a target S/N for fixed nexp."""
    if target_snr <= 0:
        raise ValueError("target_snr must be positive")

    lo = min_exptime_s
    hi = max_exptime_s

    out_hi = calculate_snr(replace(inp, exptime_s=hi))
    if out_hi.snr < target_snr:
        msg = f"Target S/N not reached by max_exptime_s={max_exptime_s}."
        return replace(out_hi, warnings=[*out_hi.warnings, msg])

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        out_mid = calculate_snr(replace(inp, exptime_s=mid))
        if out_mid.snr < target_snr:
            lo = mid
        else:
            hi = mid
        if (hi - lo) / hi < rtol:
            break

    return calculate_snr(replace(inp, exptime_s=hi))
