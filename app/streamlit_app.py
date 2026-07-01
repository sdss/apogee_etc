from __future__ import annotations

import pandas as pd
import streamlit as st

from apogee_etc import ETCInput, calculate_snr, exposure_time_for_snr, list_observatories
from apogee_etc.observatories import get_observatory

st.set_page_config(page_title="APOGEE ETC", layout="centered")
st.title("APOGEE Exposure Time Calculator")

st.caption("Starter hybrid empirical/theoretical ETC. Placeholder constants should be calibrated from real data.")

with st.sidebar:
    observatory = st.selectbox("Observatory", list_observatories())
    mode = st.radio("Mode", ["Predict S/N", "Exposure time for target S/N"])

    hmag = st.number_input("H magnitude", value=15.0, step=0.1)
    exptime_s = st.number_input("Exposure time per exposure [s]", value=500.0, step=50.0, min_value=1.0)
    nexp = st.number_input("Number of exposures", value=8, step=1, min_value=1)
    seeing = st.number_input("Seeing FWHM [arcsec]", value=1.3, step=0.1, min_value=0.1)
    airmass = st.number_input("Airmass", value=1.2, step=0.05, min_value=1.0)
    target_snr = st.number_input("Target S/N", value=50.0, step=5.0, min_value=1.0)

inp = ETCInput(
    observatory=observatory,
    hmag=hmag,
    exptime_s=exptime_s,
    nexp=int(nexp),
    seeing_fwhm_arcsec=seeing,
    airmass=airmass,
)

if mode == "Predict S/N":
    out = calculate_snr(inp)
else:
    out = exposure_time_for_snr(inp, target_snr=target_snr)

cols = st.columns(3)
cols[0].metric("S/N", f"{out.snr:.1f}")
cols[1].metric("Total exposure", f"{out.total_exptime_s:.0f} s")
cols[2].metric("Fiber fraction", f"{out.fiber_fraction:.3f}")

st.subheader("Noise budget")
noise_budget = pd.DataFrame(
    {
        "component": ["Star", "Sky", "Dark", "Read variance", "Empirical variance"],
        "value": [
            out.stellar_electrons,
            out.sky_electrons,
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
