from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

from apogee_etc import ETCInput, calculate_snr, exposure_time_for_snr, list_observatories
from apogee_etc.observatories import get_observatory

st.set_page_config(page_title="APOGEE ETC", layout="centered")
st.title("APOGEE Exposure Time Calculator")

st.caption("Starter hybrid empirical/theoretical ETC. Placeholder constants should be calibrated from real data.")
st.info("Stellar rates and sky backgrounds use measured green-detector levels. Seeing/airmass references and detector noise remain provisional. "
        "The fractional noise floor is disabled; high-S/N predictions exclude systematic errors.")

with st.sidebar:
    observatory = st.selectbox("Observatory", list_observatories())
    obs = get_observatory(observatory)
    mode = st.radio("Mode", ["Predict S/N", "Exposure time for target S/N"])

    snr_labels = {"native": "Native pixel (apCframe)",
                  "apvisit": "apVisit pixel (dithered)",
                  "apstar": "apStar pixel", "resolution": "Resolution element"}
    snr_unit = st.selectbox("S/N unit", list(snr_labels), format_func=snr_labels.get)
    hmag = st.number_input("H magnitude", value=15.0, step=0.1)
    exptime_s = st.number_input("Exposure time per exposure [s]", value=500.0, step=50.0, min_value=1.0)
    nexp = st.number_input("Number of exposures", value=8, step=1, min_value=1)
    seeing = st.number_input("Seeing FWHM [arcsec]", value=obs.seeing_ref_arcsec, step=0.1, min_value=0.1, key=f"seeing_{observatory}")
    airmass = st.number_input("Airmass", value=obs.airmass_ref, step=0.05, min_value=1.0, key=f"airmass_{observatory}")
    target_snr = st.number_input("Target S/N", value=50.0, step=5.0, min_value=1.0)

    st.subheader("Background conditions")
    moon_percent = st.slider("Moon illumination [%]", 0, 100, 0,
                             help="0 = new Moon; 100 = full Moon.")
    moon_up = st.checkbox("Moon above horizon", value=True)
    latitude = st.radio("Galactic latitude", ["high", "low"],
                        format_func=lambda value: value.capitalize())
    with st.expander("Background rates"):
        st.caption("Rates in e⁻/s/arcsec² for the spectral interval used by the ETC. "
                   "Defaults use measured 500-second sky-fiber levels; "
                   "enter rates here to explore their effects.")
        sky_rate = st.number_input("Moon-down high-latitude baseline", min_value=0.0,
                                   value=obs.default_sky_e_per_s_arcsec2, key=f"sky_{observatory}")
        moon_rate = st.number_input("Added background at full Moon", min_value=0.0,
                                    value=obs.full_moon_e_per_s_arcsec2, key=f"moon_{observatory}")
        high_rate = st.number_input("Added Galactic background: high latitude", min_value=0.0,
                                    value=obs.galactic_high_e_per_s_arcsec2, key=f"high_{observatory}")
        low_rate = st.number_input("Added Galactic background: low latitude", min_value=0.0,
                                   value=obs.galactic_low_e_per_s_arcsec2, key=f"low_{observatory}")
    st.caption("At high latitude, Moon background scales linearly with illumination; at low latitude it is disabled. "
               "Moon altitude and target separation are not modeled.")

inp = ETCInput(
    observatory=observatory,
    snr_unit=snr_unit,
    hmag=hmag,
    exptime_s=exptime_s,
    nexp=int(nexp),
    seeing_fwhm_arcsec=seeing,
    airmass=airmass,
    sky_e_per_s_arcsec2=sky_rate,
    moon_illumination=moon_percent / 100.0,
    moon_above_horizon=moon_up,
    galactic_latitude=latitude,
    full_moon_e_per_s_arcsec2=moon_rate,
    galactic_e_per_s_arcsec2=high_rate if latitude == "high" else low_rate,
)

if mode == "Predict S/N":
    out = calculate_snr(inp)
else:
    out = exposure_time_for_snr(inp, target_snr=target_snr)

cols = st.columns(3)
cols[0].metric(f"S/N per {snr_labels[snr_unit]}", f"{out.snr:.1f}")
cols[1].metric("Stellar flux [e⁻/bin]", f"{out.flux_electrons:,.2f}")
cols[2].metric("Noise, 1σ [e⁻/bin]", f"{out.noise_electrons:,.2f}")
st.caption("Flux is sky-subtracted stellar electrons summed over all exposures; "
           "noise includes star, background, dark and read noise. "
           "Both use the selected pixel or resolution-element width.")
cols = st.columns(2)
cols[0].metric("Total exposure", f"{out.total_exptime_s:.3f} s")
cols[1].metric("Seeing flux factor", f"{out.seeing_flux_factor:.3f}")

with st.expander("S/N, flux and noise versus H magnitude", expanded=True):
    plot_range = st.slider("Magnitude range about target", 1.0, 6.0, 3.0, 0.5)
    hmin = max(5.0, hmag - plot_range)
    hmax = min(20.0, hmag + plot_range)
    hmags = np.unique(np.append(np.linspace(hmin, hmax, 100), hmag))
    rows = []
    for h in hmags:
        grid_out = calculate_snr(replace(inp, hmag=float(h),
                                       exptime_s=out.exptime_per_exposure_s))
        rows.append({"H magnitude": h, "S/N": grid_out.snr,
                     "Flux": grid_out.flux_electrons, "Noise": grid_out.noise_electrons})
    df = pd.DataFrame(rows)
    plot_df = df.melt(id_vars="H magnitude", value_vars=["S/N", "Flux", "Noise"],
                      var_name="Quantity", value_name="Value")
    colors = alt.Scale(domain=["S/N", "Flux", "Noise"],
                       range=["#2563eb", "#e68613", "#159467"])
    chart = alt.Chart(plot_df).mark_line(strokeWidth=2).encode(
        x=alt.X("H magnitude:Q", title="H magnitude"),
        y=alt.Y("Value:Q", title="S/N (dimensionless); flux and noise (e⁻/bin)",
                scale=alt.Scale(type="log")),
        color=alt.Color("Quantity:N", scale=colors, title="Quantity"),
        tooltip=[alt.Tooltip("H magnitude:Q", format=".2f"),
                 "Quantity:N", alt.Tooltip("Value:Q", format=".2f")],
    ).properties(height=400)
    marker = alt.Chart(plot_df[plot_df["H magnitude"] == hmag]).mark_point(
        filled=True, size=65).encode(
        x="H magnitude:Q", y="Value:Q",
        color=alt.Color("Quantity:N", scale=colors, title="Quantity"),
        tooltip=["Quantity:N", alt.Tooltip("Value:Q", format=".2f")],
    )
    st.altair_chart(chart + marker, use_container_width=True)
    st.caption(f"All curves use {snr_labels[snr_unit]} and the displayed total integration. "
               "Flux and noise are in electrons per bin; S/N is dimensionless.")

st.caption(f"Per exposure: {out.exptime_per_exposure_s:.3f} s; "
           f"{out.nreads} total reads, {out.ngdreads} good reads. "
           "Timing uses 10.649 s per read; one initial read is discarded.")
st.caption(f"Green-detector bin width: {out.snr_bin_width_angstrom:.4f} Å. "
           "Equivalent-bin S/N scales with the square root of bin width. "
           "Dither sampling and resampling covariance are not modeled.")
st.subheader("Noise variance budget per native apCframe pixel [e⁻²]")
noise_budget = pd.DataFrame(
    {
        "component": ["Star", "Baseline sky", "Moon", "Galactic background", "Dark", "Read variance", "Empirical variance"],
        "value": [
            out.ramp_photon_variance_factor * out.stellar_electrons,
            out.ramp_photon_variance_factor * out.atmospheric_sky_electrons,
            out.ramp_photon_variance_factor * out.moon_electrons,
            out.ramp_photon_variance_factor * out.galactic_electrons,
            out.ramp_photon_variance_factor * out.dark_electrons,
            out.read_noise_variance_e2,
            out.empirical_noise_variance_e2,
        ],
    }
)
st.dataframe(noise_budget, use_container_width=True)

st.caption("Low-latitude 500-s levels: APO median 92, range 50–160; "
           "LCO median 70, disk range 35–140, bulge range 40–225 e⁻/arcsec². "
           "Use the editable Galactic increment to explore brighter or darker fields.")
obs = get_observatory(observatory)
st.subheader("Observatory config")
st.json(obs.__dict__)

for warning in out.warnings:
    st.warning(warning)
