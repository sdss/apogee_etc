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
                       galactic_latitude='high', galactic_e_per_s_arcsec2=3)
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


@pytest.mark.parametrize('site', ['APO', 'LCO'])
def test_no_artificial_snr_ceiling_and_latitude_effect(site):
    inp = ETCInput(observatory=site, hmag=10, exptime_s=1000, nexp=8)
    assert calculate_snr(inp).snr > 100
    faint = replace(inp, hmag=16)
    assert calculate_snr(replace(faint, galactic_latitude='low')).snr < calculate_snr(faint).snr
    assert calculate_snr(replace(faint, moon_illumination=1)).snr < calculate_snr(faint).snr
    assert exposure_time_for_snr(inp, 100).snr >= 100


@pytest.mark.parametrize('site,new,full,low', [('APO',40,80,92), ('LCO',27,41.7,70)])
def test_measured_sky_levels(site,new,full,low):
    from apogee_etc.observatories import get_observatory
    from apogee_etc.physics import fiber_area_arcsec2
    area=fiber_area_arcsec2(get_observatory(site).fiber_diameter_arcsec)
    inp=ETCInput(observatory=site, exptime_s=500, nexp=1)
    assert np.isclose(calculate_snr(inp).sky_electrons/area*500/calculate_snr(inp).exptime_per_exposure_s,new)
    assert np.isclose(calculate_snr(replace(inp,moon_illumination=1)).sky_electrons/area*500/calculate_snr(inp).exptime_per_exposure_s,full)
    for phase in (0,0.5,1):
        assert np.isclose(calculate_snr(replace(inp,galactic_latitude='low',moon_illumination=phase)).sky_electrons/area*500/calculate_snr(inp).exptime_per_exposure_s,low)


@pytest.mark.parametrize('site,z', [
    ('APO',5.286024848102618),
    ('LCO',5.082818044301776),
])
def test_measured_stellar_flux_at_reference(site,z):
    time=500
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    for h in (10,13,16):
        inp=ETCInput(observatory=site,hmag=h,exptime_s=time,nexp=1,
                     seeing_fwhm_arcsec=obs.seeing_ref_arcsec,
                     airmass=obs.airmass_ref)
        out=calculate_snr(inp)
        assert np.isclose(out.stellar_electrons,10**(z-.4*h)*out.total_exptime_s)
        worse=calculate_snr(replace(inp,seeing_fwhm_arcsec=2.0))
        assert worse.stellar_electrons < out.stellar_electrons
        assert np.isclose(calculate_snr(replace(inp,nexp=2)).stellar_electrons,
                          2*out.stellar_electrons)


@pytest.mark.parametrize('site,adu,gain,rn', [('APO',0.071428575,1.9,20.9), ('LCO',0.05102041,3.,24.)])
def test_measured_dark_conversion(site,adu,gain,rn):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    assert np.isclose(obs.dark_current_e_per_s_pix,adu*gain/10.649)
    assert obs.single_read_noise_e==rn
    out=calculate_snr(ETCInput(observatory=site,exptime_s=500,nexp=2))
    assert np.isclose(out.dark_electrons,adu*gain/10.649*obs.npix_per_resolution_element*out.total_exptime_s)


@pytest.mark.parametrize('site', ['APO','LCO'])
def test_ramp_variance_and_discrete_solver(site):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    inp=ETCInput(observatory=site,exptime_s=500,nexp=2)
    out=calculate_snr(inp)
    assert out.nreads==47 and out.ngdreads==46
    assert np.isclose(out.exptime_per_exposure_s,500.503)
    a=12*45/(47*47)
    c=6*(46**2+1)/(5*46*47)
    rn=2*obs.npix_per_resolution_element*a*obs.single_read_noise_e**2
    assert np.isclose(out.read_noise_variance_e2,rn)
    assert np.isclose(out.total_noise_electrons**2,
                      c*(obs.stellar_photon_variance_factor*out.stellar_electrons+out.sky_electrons+out.dark_electrons)+rn)
    result=exposure_time_for_snr(inp,20)
    assert result.snr>=20
    assert calculate_snr(replace(inp,exptime_s=(result.nreads-1)*10.649)).snr<20
    bounded=exposure_time_for_snr(inp,1e6,max_exptime_s=500)
    assert bounded.exptime_per_exposure_s<=500


@pytest.mark.parametrize('site,seeing,airmass', [('APO',1.58,1.24),('LCO',1.27,1.16)])
def test_site_specific_fiducials(site,seeing,airmass):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    assert obs.seeing_ref_arcsec==seeing
    assert obs.airmass_ref==airmass
    default=calculate_snr(ETCInput(observatory=site))
    explicit=calculate_snr(ETCInput(observatory=site,seeing_fwhm_arcsec=seeing,airmass=airmass))
    assert default.snr==explicit.snr


@pytest.mark.parametrize('unit,width', [('native',0.2844),('apvisit',0.1422),('apstar',0.2229),('resolution',0.4458)])
def test_snr_units_and_solver(unit,width):
    inp=ETCInput(snr_unit=unit,nexp=4)
    out=calculate_snr(inp)
    native=calculate_snr(replace(inp,snr_unit='native'))
    assert np.isclose(out.snr,native.snr*np.sqrt(width/0.2844))
    assert out.stellar_electrons==native.stellar_electrons
    assert out.total_noise_electrons==native.total_noise_electrons
    result=exposure_time_for_snr(inp,20)
    assert result.snr>=20 and result.snr_unit==unit
    assert calculate_snr(replace(inp,exptime_s=(result.nreads-1)*10.649)).snr<20


def test_invalid_snr_unit():
    with pytest.raises(ValueError):
        calculate_snr(ETCInput(snr_unit='unknown'))


@pytest.mark.parametrize('unit,q', [('native',1),('apvisit',0.5),('apstar',0.2229/0.2844),('resolution',0.4458/0.2844)])
def test_flux_noise_selected_bin(unit,q):
    out=calculate_snr(ETCInput(snr_unit=unit,nexp=4))
    assert np.isclose(out.flux_electrons,out.stellar_electrons*q)
    assert np.isclose(out.noise_electrons,out.total_noise_electrons*np.sqrt(q))
    assert np.isclose(out.flux_electrons/out.noise_electrons,out.snr)


@pytest.mark.parametrize('site,slope', [('APO',-.17974092339286213),('LCO',-.21420982017607323)])
def test_empirical_seeing_replaces_gaussian(site,slope):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    inp=ETCInput(observatory=site,seeing_fwhm_arcsec=obs.seeing_ref_arcsec)
    ref=calculate_snr(inp)
    worse=calculate_snr(replace(inp,seeing_fwhm_arcsec=obs.seeing_ref_arcsec+.5))
    assert inp.fiber_coupling_model=='empirical_only'
    assert np.isclose(worse.stellar_electrons/ref.stellar_electrons,10**(slope*.5))
    assert np.isclose(worse.seeing_flux_factor,10**(slope*.5))
    assert ref.seeing_flux_factor==1


@pytest.mark.parametrize('site,slope', [('APO',-.15628331623665812),('LCO',-.11268839513904064)])
def test_joint_airmass_slope(site,slope):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    inp=ETCInput(observatory=site,airmass=obs.airmass_ref)
    ref=calculate_snr(inp)
    higher=calculate_snr(replace(inp,airmass=obs.airmass_ref+.5))
    assert np.isclose(higher.stellar_electrons/ref.stellar_electrons,10**(slope*.5))


@pytest.mark.parametrize('site', ['APO','LCO'])
def test_throughput_prediction_ranges(site):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    for unit in ['native','apvisit','apstar','resolution']:
        out=calculate_snr(ETCInput(observatory=site,snr_unit=unit,nexp=4))
        assert np.isclose(out.flux_upper_electrons/out.flux_electrons,10**obs.throughput_scatter_dex)
        assert np.isclose(out.flux_lower_electrons/out.flux_electrons,10**(-obs.throughput_scatter_dex))
        assert out.snr_lower < out.snr < out.snr_upper
        assert out.noise_lower_electrons < out.noise_electrons < out.noise_upper_electrons
        assert np.isclose(out.snr_lower,out.flux_lower_electrons/out.noise_lower_electrons)


@pytest.mark.parametrize('site', ['APO','LCO'])
def test_empirical_profile_factors(site):
    from apogee_etc.observatories import get_observatory
    obs=get_observatory(site)
    assert obs.npix_per_resolution_element==3.7444072079837682
    assert obs.stellar_photon_variance_factor==1.178447668371803
    out=calculate_snr(ETCInput(observatory=site,nexp=2))
    variance=out.ramp_photon_variance_factor*(
        obs.stellar_photon_variance_factor*out.stellar_electrons
        +out.sky_electrons+out.dark_electrons)+out.read_noise_variance_e2
    assert np.isclose(out.total_noise_electrons**2,variance)
