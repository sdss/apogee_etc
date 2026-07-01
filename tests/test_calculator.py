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
