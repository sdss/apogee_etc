# apogee_etc

A starter hybrid exposure time calculator for APOGEE-like observations.

The design is intentionally split into:

1. **A reusable Python package** with the ETC engine.
2. **Observatory/instrument configs** for APO and LCO.
3. **Empirical coefficients** that can be calibrated from real APOGEE data.
4. **A Streamlit app** as a lightweight online interface.

Most numerical values are placeholders and should be replaced with values calibrated from real APOGEE exposures.

## Install for development

```bash
cd apogee_etc
python -m pip install -e ".[app,test]"
```

## Run the example

```bash
python examples/basic_usage.py
```

## Run the web app

```bash
streamlit run app/streamlit_app.py
```

## Run tests

```bash
pytest
```

## Basic Python usage

```python
from apogee_etc import calculate_snr, ETCInput

inp = ETCInput(
    observatory="APO",
    hmag=15.0,
    exptime_s=500,
    nexp=8,
    seeing_fwhm_arcsec=1.3,
    airmass=1.2,
)

out = calculate_snr(inp)
print(out.snr)
```

## Calibration philosophy

The calculator combines a physically motivated noise equation with empirical coefficients:

- stellar count-rate zeropoint
- seeing dependence
- airmass dependence
- sky/background rate
- empirical noise floor

The placeholders are meant to be replaced by APO/LCO-specific fits to real exposures.
