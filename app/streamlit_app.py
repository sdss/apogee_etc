from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

from apogee_etc import ETCInput, calculate_snr, exposure_time_for_snr, list_observatories
from apogee_etc.observatories import get_observatory

st.set_page_config(page_title="APOGEE ETC", layout="centered")
st.title("APOGEE Exposure Time Calculator")

st.caption("Starter hybrid empirical/theoretical ETC. Placeholder constants should be calibrated from real data.")

with st.sidebar:
    observatory = st.selectbox("Observatory", list_observatories())
    obs = get_observatory(observatory)
    mode = st.radio("Mode", ["Predict S/N", "Exposure time for target S/N"])

    hmag = st.number_input("H magnitude", value=15.0, step=0.1)
    exptime_s = st.number_input("Exposure time per exposure [s]", value=500.0, step=50.0, min_value=1.0)
    nexp = st.number_input("Number of exposures", value=8, step=1, min_value=1)
    seeing = st.number_input("Seeing FWHM [arcsec]", value=1.3, step=0.1, min_value=0.1)
    airmass = st.number_input("Airmass", value=1.2, step=0.05, min_value=1.0)
    target_snr = st.number_input("Target S/N", value=50.0, step=5.0, min_value=1.0)

    st.subheader("Background conditions")
    moon_percent = st.slider("Moon illumination [%]", 0, 100, 0,
                             help="0 = new Moon; 100 = full Moon.")
    moon_up = st.checkbox("Moon above horizon", value=True)
    latitude = st.radio("Galactic latitude", ["high", "low"],
                        format_func=lambda value: value.capitalize())
    with st.expander("Background rates"):
        st.caption("Rates in e⁻/s/arcsec² for the spectral interval used by the ETC. "
                   "Moon and Galactic coefficients start at zero pending calibration; "
                   "enter rates here to explore their effects.")
        sky_rate = st.number_input("Atmospheric sky", min_value=0.0,
                                   value=obs.default_sky_e_per_s_arcsec2, key=f"sky_{observatory}")
        moon_rate = st.number_input("Added background at full Moon", min_value=0.0,
                                    value=obs.full_moon_e_per_s_arcsec2, key=f"moon_{observatory}")
        high_rate = st.number_input("Added Galactic background: high latitude", min_value=0.0,
                                    value=obs.galactic_high_e_per_s_arcsec2, key=f"high_{observatory}")
        low_rate = st.number_input("Added Galactic background: low latitude", min_value=0.0,
                                   value=obs.galactic_low_e_per_s_arcsec2, key=f"low_{observatory}")
    st.caption("Moon background scales linearly with illumination at assumed fixed geometry. "
               "Moon altitude and target separation are not modeled.")

inp = ETCInput(
    observatory=observatory,
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
cols[0].metric("S/N", f"{out.snr:.1f}")
cols[1].metric("Total exposure", f"{out.total_exptime_s:.0f} s")
cols[2].metric("Fiber fraction", f"{out.fiber_fraction:.3f}")

# -----------------------------
# S/N versus H magnitude plot
# -----------------------------
with st.expander("S/N versus H magnitude", expanded=True):


    plot_range = st.slider(
        "Magnitude range about target",
        1.0,
        6.0,
        3.0,
        0.5,
    )

    hmin = max(5.0, hmag - plot_range)
    hmax = min(20.0, hmag + plot_range)

    
    #default_hmin = max(5.0, hmag - 3.0)
    #default_hmax = min(20.0, hmag + 3.0)

    #hmin = st.slider(
    #    "Minimum H magnitude",
    #    min_value=5.0,
    #    max_value=20.0,
    #    value=default_hmin,
    #    step=0.5,
    #    key="hmin",
    #)

    #hmax = st.slider(
    #    "Maximum H magnitude",
    #    min_value=5.0,
    #    max_value=20.0,
    #    value=default_hmax,
    #    step=0.5,
    #    key="hmax",
    #)

    hmags = np.linspace(hmin, hmax, 100)

    rows = []
    for h in hmags:
        grid_inp = ETCInput(
            observatory=observatory,
            hmag=float(h),
            exptime_s=exptime_s,
            nexp=int(nexp),
            seeing_fwhm_arcsec=seeing,
            airmass=airmass,
        )

        grid_out = calculate_snr(grid_inp)

        rows.append(
            {
                "H magnitude": h,
                "S/N": grid_out.snr,
            }
        )

    df = pd.DataFrame(rows)


    chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X(
                "H magnitude:Q",
                title="H magnitude",
            ),
            y=alt.Y(
                "S/N:Q",
                title="Signal-to-Noise Ratio",
                scale=alt.Scale(type="log"),
            ),
            tooltip=[
                alt.Tooltip("H magnitude:Q", format=".2f"),
                alt.Tooltip("S/N:Q", format=".2f"),
            ],
        )
        .properties(height=400)
    )
    
    st.altair_chart(chart, use_container_width=True)





    
    #st.line_chart(
    #    df,
    #    x="H magnitude",
    #    y="S/N",
    #    use_container_width=True,
    #)


st.subheader("Noise budget")
noise_budget = pd.DataFrame(
    {
        "component": ["Star", "Atmospheric sky", "Moon", "Galactic background", "Dark", "Read variance", "Empirical variance"],
        "value": [
            out.stellar_electrons,
            out.atmospheric_sky_electrons,
            out.moon_electrons,
            out.galactic_electrons,
            out.dark_electrons,
            out.read_noise_variance_e2,
            out.empirical_noise_variance_e2,
        ],
    }
)
st.dataframe(noise_budget, use_container_width=True)

obs = get_observatory(observatory)
st.subheader("Observatory config")
st.json(obs.__dict__)

for warning in out.warnings:
    st.warning(warning)
