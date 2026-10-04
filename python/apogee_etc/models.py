from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ObservatoryConfig:
    """Instrument/observatory-specific constants.

    Notes
    -----
    Many values in the starter config are placeholders. The intent is to
    replace them with values from APOGEE documentation and/or empirical fits.
    """

    name: str
    telescope_diameter_m: float
    fiber_diameter_arcsec: float
    gain_e_per_adu: float
    read_noise_e: float
    dark_current_e_per_s_pix: float
    npix_per_resolution_element: float
    default_sky_e_per_s_arcsec2: float
    empirical_zp_log10_e_per_s_h0: float
    seeing_ref_arcsec: float = 1.3
    airmass_ref: float = 1.2
    seeing_slope_dex_per_arcsec: float = 0.0
    airmass_slope_dex_per_airmass: float = 0.0
    empirical_noise_floor_frac: float = 0.0
    notes: str = ""
    full_moon_e_per_s_arcsec2: float = 0.0
    galactic_high_e_per_s_arcsec2: float = 0.0
    galactic_low_e_per_s_arcsec2: float = 0.0


@dataclass(frozen=True)
class ETCInput:
    observatory: str = "APO"
    hmag: float = 15.0
    exptime_s: float = 500.0
    nexp: int = 1
    seeing_fwhm_arcsec: float = 1.3
    airmass: float = 1.2
    sky_e_per_s_arcsec2: float | None = None
    fiber_coupling_model: str = "gaussian"
    include_empirical_terms: bool = True
    target_snr: float | None = None
    moon_illumination: float = 0.0  # Fraction, 0 (new) to 1 (full).
    moon_above_horizon: bool = True
    galactic_latitude: str = "high"
    full_moon_e_per_s_arcsec2: float | None = None
    galactic_e_per_s_arcsec2: float | None = None


@dataclass(frozen=True)
class ETCOutput:
    snr: float
    total_exptime_s: float
    stellar_electrons: float
    sky_electrons: float
    dark_electrons: float
    read_noise_variance_e2: float
    empirical_noise_variance_e2: float
    total_noise_electrons: float
    fiber_fraction: float
    observatory: str
    warnings: list[str] = field(default_factory=list)
    atmospheric_sky_electrons: float = 0.0
    moon_electrons: float = 0.0
    galactic_electrons: float = 0.0
