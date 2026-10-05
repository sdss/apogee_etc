from __future__ import annotations

from dataclasses import replace

import numpy as np

from .models import ETCInput, ETCOutput
from .observatories import get_observatory
from .physics import fiber_area_arcsec2, gaussian_fiber_fraction


def _stellar_rate_e_per_s(inp: ETCInput) -> tuple[float, float]:
    obs = get_observatory(inp.observatory)

    log_rate = obs.empirical_zp_log10_e_per_s_h0 + obs.stellar_magnitude_slope * inp.hmag

    if inp.include_empirical_terms:
        log_rate += obs.seeing_slope_dex_per_arcsec * (
            inp.seeing_fwhm_arcsec - obs.seeing_ref_arcsec
        )
        log_rate += obs.airmass_slope_dex_per_airmass * (
            inp.airmass - obs.airmass_ref
        )

    coupling_correction = 1.0
    if inp.fiber_coupling_model == "gaussian":
        fiber_fraction = gaussian_fiber_fraction(
            inp.seeing_fwhm_arcsec, obs.fiber_diameter_arcsec
        )
        coupling_correction = fiber_fraction
        if obs.normalize_fiber_at_reference:
            coupling_correction /= gaussian_fiber_fraction(
                obs.seeing_ref_arcsec, obs.fiber_diameter_arcsec
            )
    elif inp.fiber_coupling_model in {"none", "empirical_only"}:
        fiber_fraction = 1.0
    else:
        raise ValueError(
            "fiber_coupling_model must be 'gaussian', 'empirical_only', or 'none'"
        )

    return float(10**log_rate * coupling_correction), fiber_fraction


def calculate_snr(inp: ETCInput) -> ETCOutput:
    obs = get_observatory(inp.observatory)
    inp = replace(inp,
                  seeing_fwhm_arcsec=obs.seeing_ref_arcsec if inp.seeing_fwhm_arcsec is None else inp.seeing_fwhm_arcsec,
                  airmass=obs.airmass_ref if inp.airmass is None else inp.airmass)
    warnings: list[str] = []

    if inp.nexp < 1:
        raise ValueError("nexp must be >= 1")
    if not np.isfinite(inp.exptime_s) or inp.exptime_s <= 0:
        raise ValueError("exptime_s must be positive")
    if inp.hmag < -5 or inp.hmag > 25:
        warnings.append("H magnitude is outside the usual calibrated range.")
    if inp.seeing_fwhm_arcsec < 0.5 or inp.seeing_fwhm_arcsec > 4.0:
        warnings.append("Seeing is outside the nominal calibration range.")
    if inp.airmass < 1.0 or inp.airmass > 2.5:
        warnings.append("Airmass is outside the nominal calibration range.")

    # ETC convention: t = nreads * read interval, first read rejected.
    nreads = max(3, int(np.ceil(inp.exptime_s / obs.read_interval_s - 1e-12)))
    ngdreads = nreads - 1
    actual_exptime_s = nreads * obs.read_interval_s
    if not np.isclose(actual_exptime_s, inp.exptime_s, rtol=0, atol=1e-8):
        warnings.append(f"Per-exposure time rounded up to {actual_exptime_s:.3f} s ({nreads} reads).")
    total_exptime_s = actual_exptime_s * inp.nexp
    star_rate, fiber_fraction = _stellar_rate_e_per_s(inp)
    stellar_e = star_rate * total_exptime_s

    sky_rate_area = (
        obs.default_sky_e_per_s_arcsec2
        if inp.sky_e_per_s_arcsec2 is None
        else inp.sky_e_per_s_arcsec2
    )
    if not np.isfinite(inp.moon_illumination) or not 0 <= inp.moon_illumination <= 1:
        raise ValueError("moon_illumination must be between 0 and 1")
    if inp.galactic_latitude not in {"high", "low"}:
        raise ValueError("galactic_latitude must be 'high' or 'low'")
    full_moon_rate = (obs.full_moon_e_per_s_arcsec2
                      if inp.full_moon_e_per_s_arcsec2 is None
                      else inp.full_moon_e_per_s_arcsec2)
    galactic_rate = (getattr(obs, f"galactic_{inp.galactic_latitude}_e_per_s_arcsec2")
                     if inp.galactic_e_per_s_arcsec2 is None
                     else inp.galactic_e_per_s_arcsec2)
    for rate in (sky_rate_area, full_moon_rate, galactic_rate):
        if not np.isfinite(rate) or rate < 0:
            raise ValueError("Background rates must be finite and nonnegative")
    # A configurable approximation at fixed Moon/target geometry, not a
    # calibrated scattered-moonlight model. Rates use the same spectral unit
    # as the stellar rate and the original atmospheric sky rate.
    moon_rate = (full_moon_rate * inp.moon_illumination
                 if inp.moon_above_horizon and inp.galactic_latitude == "high" else 0.0)
    area_time = fiber_area_arcsec2(obs.fiber_diameter_arcsec) * total_exptime_s
    atmospheric_e = sky_rate_area * area_time
    moon_e = moon_rate * area_time
    galactic_e = galactic_rate * area_time
    sky_e = atmospheric_e + moon_e + galactic_e
    if inp.galactic_latitude == "high" and inp.moon_above_horizon and inp.moon_illumination > 0 and full_moon_rate == 0:
        warnings.append("Moon background coefficient is unset (zero); illumination has no effect.")
    if inp.galactic_latitude == "low":
        warnings.append("Low-latitude background uses a representative median; measured field-to-field variation is large. Moon dependence is disabled for this regime.")

    dark_e = obs.dark_current_e_per_s_pix * obs.npix_per_resolution_element * total_exptime_s
    read_factor = 12.0 * (ngdreads - 1) / (nreads * (ngdreads + 1))
    photon_factor = 6.0 * (ngdreads**2 + 1) / (5.0 * ngdreads * (ngdreads + 1))
    single_read_noise = obs.single_read_noise_e
    if single_read_noise is None:
        raise ValueError("single_read_noise_e must be configured for the ramp model")
    rn_var = (inp.nexp * obs.npix_per_resolution_element
              * read_factor * single_read_noise**2)
    empirical_var = (obs.empirical_noise_floor_frac * stellar_e) ** 2

    variance = photon_factor * (stellar_e + sky_e + dark_e) + rn_var + empirical_var
    noise_e = float(np.sqrt(variance))
    snr = float(stellar_e / noise_e) if noise_e > 0 else 0.0

    widths = {"native": 0.2844, "apvisit": 0.2844 / 2,
              "apstar": 0.2229, "resolution": 2 * 0.2229}
    if inp.snr_unit not in widths:
        raise ValueError("snr_unit must be 'native', 'apvisit', 'apstar', or 'resolution'")
    # Equivalent-bin S/N; detector budget stays in native apCframe pixels.
    bin_ratio = widths[inp.snr_unit] / widths["native"]
    scaled_snr = snr * np.sqrt(bin_ratio)
    return ETCOutput(
        snr=float(scaled_snr),
        flux_electrons=float(stellar_e * bin_ratio),
        seeing_flux_factor=float(10**(obs.seeing_slope_dex_per_arcsec *
            (inp.seeing_fwhm_arcsec - obs.seeing_ref_arcsec))) if inp.include_empirical_terms else 1.0,
        noise_electrons=float(noise_e * np.sqrt(bin_ratio)),
        native_snr=snr,
        snr_unit=inp.snr_unit,
        snr_bin_width_angstrom=widths[inp.snr_unit],
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
        atmospheric_sky_electrons=float(atmospheric_e),
        moon_electrons=float(moon_e),
        galactic_electrons=float(galactic_e),
        exptime_per_exposure_s=float(actual_exptime_s),
        nreads=nreads,
        ngdreads=ngdreads,
        ramp_photon_variance_factor=float(photon_factor),
    )


def exposure_time_for_snr(
    inp: ETCInput,
    target_snr: float,
    min_exptime_s: float = 1.0,
    max_exptime_s: float = 100_000.0,
    rtol: float = 1e-3,
) -> ETCOutput:
    """Find the shortest whole-read exposure for fixed nexp.

    rtol is retained for API compatibility; integer search is exact.
    """
    if not np.isfinite(target_snr) or target_snr <= 0:
        raise ValueError("target_snr must be finite and positive")
    if not 0 < min_exptime_s <= max_exptime_s or not np.isfinite(max_exptime_s):
        raise ValueError("Exposure bounds must be finite, positive and ordered")
    interval = get_observatory(inp.observatory).read_interval_s
    lo = max(3, int(np.ceil(min_exptime_s / interval - 1e-12)))
    hi = int(np.floor(max_exptime_s / interval + 1e-12))
    if hi < lo:
        raise ValueError("Exposure bounds contain no valid whole-read duration")
    def evaluate(reads):
        return calculate_snr(replace(inp, exptime_s=reads * interval))
    out_hi = evaluate(hi)
    if out_hi.snr < target_snr:
        msg = f"Target S/N not reached by max_exptime_s={max_exptime_s}."
        return replace(out_hi, warnings=[*out_hi.warnings, msg])
    while lo < hi:
        mid = (lo + hi) // 2
        if evaluate(mid).snr < target_snr:
            lo = mid + 1
        else:
            hi = mid
    return evaluate(lo)
