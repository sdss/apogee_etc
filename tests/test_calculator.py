from apogee_etc import ETCInput, calculate_snr, exposure_time_for_snr, list_observatories


def test_observatories_available():
    assert "APO" in list_observatories()
    assert "LCO" in list_observatories()


def test_snr_increases_with_exptime():
    inp1 = ETCInput(observatory="APO", hmag=15, exptime_s=100, nexp=1)
    inp2 = ETCInput(observatory="APO", hmag=15, exptime_s=1000, nexp=1)
    assert calculate_snr(inp2).snr > calculate_snr(inp1).snr


def test_snr_decreases_for_fainter_star():
    bright = ETCInput(observatory="APO", hmag=14, exptime_s=500, nexp=1)
    faint = ETCInput(observatory="APO", hmag=16, exptime_s=500, nexp=1)
    assert calculate_snr(bright).snr > calculate_snr(faint).snr


def test_exposure_time_solver_reaches_target():
    inp = ETCInput(observatory="APO", hmag=15, exptime_s=500, nexp=4)
    out = exposure_time_for_snr(inp, target_snr=20)
    assert out.snr >= 20

def test_exposure_time_solver_near_known_solution():
    inp = ETCInput(hmag=12, exptime_s=500)
    snr = calculate_snr(inp).snr

    out = exposure_time_for_snr(inp, target_snr=snr)

    assert abs(out.total_exptime_s - 500) < 20


import numpy as np
import pytest
from dataclasses import replace


@pytest.mark.parametrize('site', ['APO', 'LCO'])
def test_background_components_and_solver(site):
    base = ETCInput(observatory=site, hmag=16, nexp=4)
    dark = calculate_snr(base)
    half_inp = replace(base, moon_illumination=0.5,
                       full_moon_e_per_s_arcsec2=8,
                       galactic_latitude='low', galactic_e_per_s_arcsec2=3)
    half = calculate_snr(half_inp)
    full = calculate_snr(replace(half_inp, moon_illumination=1))
    assert np.isclose(full.moon_electrons, 2 * half.moon_electrons)
    assert np.isclose(half.sky_electrons, half.atmospheric_sky_electrons
                      + half.moon_electrons + half.galactic_electrons)
    assert full.snr < half.snr < dark.snr
    down = calculate_snr(replace(half_inp, moon_above_horizon=False))
    assert down.moon_electrons == 0
    assert down.stellar_electrons == dark.stellar_electrons
    assert exposure_time_for_snr(half_inp, 20).total_exptime_s > exposure_time_for_snr(base, 20).total_exptime_s


@pytest.mark.parametrize('changes', [
    {'moon_illumination': -0.1}, {'moon_illumination': 1.1},
    {'moon_illumination': float('nan')}, {'galactic_latitude': 'middle'},
    {'full_moon_e_per_s_arcsec2': -1}, {'galactic_e_per_s_arcsec2': float('inf')},
    {'sky_e_per_s_arcsec2': -1},
])
def test_invalid_background_inputs(changes):
    with pytest.raises(ValueError):
        calculate_snr(ETCInput(**changes))
