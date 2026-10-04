from __future__ import annotations

from .models import ObservatoryConfig

# Sky rates from measured sky-fiber levels per arcsec² in 500 s.
# Stellar fits are measured ADU per green-detector spectral pixel,
# converted to electrons/s. Seeing/airmass references are provisional.
OBSERVATORIES: dict[str, ObservatoryConfig] = {
    "APO": ObservatoryConfig(
        name="APO",
        telescope_diameter_m=2.5,
        fiber_diameter_arcsec=2.0,
        gain_e_per_adu=1.9,
        read_noise_e=12.0,
        dark_current_e_per_s_pix=0.012803235142,
        single_read_noise_e=20.9,
        npix_per_resolution_element=3.0,
        default_sky_e_per_s_arcsec2=0.080,
        empirical_zp_log10_e_per_s_h0=5.39930362,
        stellar_magnitude_slope=-0.4,
        normalize_fiber_at_reference=True,
        seeing_ref_arcsec=1.3,
        airmass_ref=1.2,
        seeing_slope_dex_per_arcsec=0.0,
        airmass_slope_dex_per_airmass=-0.016,
        empirical_noise_floor_frac=0.0,
        full_moon_e_per_s_arcsec2=0.080,
        galactic_high_e_per_s_arcsec2=0.0,
        galactic_low_e_per_s_arcsec2=0.104,
        notes="Measured sky background: high latitude 40–80, low latitude median 92 e-/arcsec²/500s. Stellar normalization measured for X<1.5 and seeing<1.5 arcsec; reference conditions and detector noise remain provisional.",
    ),
    "LCO": ObservatoryConfig(
        name="LCO",
        telescope_diameter_m=2.5,
        fiber_diameter_arcsec=1.3,
        gain_e_per_adu=3.0,
        read_noise_e=12.0,
        dark_current_e_per_s_pix=0.014439738679,
        single_read_noise_e=24.0,
        npix_per_resolution_element=3.0,
        default_sky_e_per_s_arcsec2=0.054,
        empirical_zp_log10_e_per_s_h0=5.13881373,
        stellar_magnitude_slope=-0.4,
        normalize_fiber_at_reference=True,
        seeing_ref_arcsec=1.1,
        airmass_ref=1.2,
        seeing_slope_dex_per_arcsec=0.0,
        airmass_slope_dex_per_airmass=-0.016,
        empirical_noise_floor_frac=0.0,
        full_moon_e_per_s_arcsec2=0.0294,
        galactic_high_e_per_s_arcsec2=0.0,
        galactic_low_e_per_s_arcsec2=0.086,
        notes="Measured sky background: high latitude 27–41.7, low latitude median 70 e-/arcsec²/500s. Stellar normalization measured for X<1.5 and seeing<1.5 arcsec; reference conditions and detector noise remain provisional.",
    ),
}


def list_observatories() -> list[str]:
    return sorted(OBSERVATORIES)


def get_observatory(name: str) -> ObservatoryConfig:
    key = name.upper()
    if key not in OBSERVATORIES:
        allowed = ", ".join(list_observatories())
        raise ValueError(f"Unknown observatory {name!r}. Allowed values: {allowed}")
    return OBSERVATORIES[key]
