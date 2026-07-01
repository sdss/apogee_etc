from __future__ import annotations

from .models import ObservatoryConfig

# Placeholder values. Replace with APOGEE/APOGEE-S calibrated values.
OBSERVATORIES: dict[str, ObservatoryConfig] = {
    "APO": ObservatoryConfig(
        name="APO",
        telescope_diameter_m=2.5,
        fiber_diameter_arcsec=2.0,
        gain_e_per_adu=1.9,
        read_noise_e=12.0,
        dark_current_e_per_s_pix=0.01,
        npix_per_resolution_element=4.0,
        default_sky_e_per_s_arcsec2=5.0,
        empirical_zp_log10_e_per_s_h0=7.67,
        seeing_ref_arcsec=1.3,
        airmass_ref=1.2,
        seeing_slope_dex_per_arcsec=-0.17,
        airmass_slope_dex_per_airmass=-0.08,
        empirical_noise_floor_frac=0.02,
        notes="Starter values; calibrate from APO exposures.",
    ),
    "LCO": ObservatoryConfig(
        name="LCO",
        telescope_diameter_m=2.5,
        fiber_diameter_arcsec=1.3,
        gain_e_per_adu=1.9,
        read_noise_e=12.0,
        dark_current_e_per_s_pix=0.01,
        npix_per_resolution_element=4.0,
        default_sky_e_per_s_arcsec2=3.5,
        empirical_zp_log10_e_per_s_h0=7.50,
        seeing_ref_arcsec=1.1,
        airmass_ref=1.2,
        seeing_slope_dex_per_arcsec=-0.12,
        airmass_slope_dex_per_airmass=-0.08,
        empirical_noise_floor_frac=0.02,
        notes="Starter values; calibrate from LCO exposures. Confirm fiber diameter and detector values.",
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
