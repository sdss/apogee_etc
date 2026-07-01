from apogee_etc import ETCInput, calculate_snr, exposure_time_for_snr

inp = ETCInput(
    observatory="APO",
    hmag=15.0,
    exptime_s=500.0,
    nexp=8,
    seeing_fwhm_arcsec=1.3,
    airmass=1.2,
)

out = calculate_snr(inp)
print(f"Predicted S/N: {out.snr:.1f}")
print(f"Stellar electrons: {out.stellar_electrons:.0f}")
print(f"Sky electrons: {out.sky_electrons:.0f}")

needed = exposure_time_for_snr(inp, target_snr=50)
print(f"Exposure time per exposure for S/N=50: {needed.total_exptime_s / inp.nexp:.0f} s")
