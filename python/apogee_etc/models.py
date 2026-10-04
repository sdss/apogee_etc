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
    npix_per_resolution_element: float  # Legacy name: effective spatial extraction pixels.
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
    stellar_magnitude_slope: float = -0.4
    normalize_fiber_at_reference: bool = False
    single_read_noise_e: float | None = None
    read_interval_s: float = 10.6


@dataclass(frozen=True)
class ETCInput:
    observatory: str = "APO"
    hmag: float = 15.0
    exptime_s: float = 500.0
    nexp: int = 1
    seeing_fwhm_arcsec: float | None = None
    airmass: float | None = None
    sky_e_per_s_arcsec2: float | None = None
    fiber_coupling_model: str = "empirical_only"
    include_empirical_terms: bool = True
    target_snr: float | None = None
    moon_illumination: float = 0.0  # Fraction, 0 (new) to 1 (full).
    moon_above_horizon: bool = True
    galactic_latitude: str = "high"
    full_moon_e_per_s_arcsec2: float | None = None
    galactic_e_per_s_arcsec2: float | None = None
    snr_unit: str = "native"


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
    exptime_per_exposure_s: float = 0.0
    nreads: int = 0
    ngdreads: int = 0
    ramp_photon_variance_factor: float = 1.0
    native_snr: float = 0.0
    snr_unit: str = "native"
    snr_bin_width_angstrom: float = 0.2844
    flux_electrons: float = 0.0
    noise_electrons: float = 0.0
    seeing_flux_factor: float = 1.0
