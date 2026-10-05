Theory
======

Overview
---------

The APOGEE ETC is a hybrid empirical/theoretical model.

The stellar count rate is modeled as

.. math::

   \log_{10}(R_\star)
   =
   ZP
   - 0.4 H
   + f({\rm seeing})
   + g({\rm airmass})

where:

* :math:`R_\star` is the stellar electron rate (e-/s)
* :math:`H` is the H-band magnitude
* :math:`ZP` is an empirical zeropoint.

Fiber Coupling
--------------

The stellar flux entering the fiber is reduced by seeing losses:

.. math::

   N_\star = R_\star t f_{\rm fiber}

where :math:`f_{\rm fiber}` is the fraction of the PSF that falls within the
fiber.

Sky Background
--------------

The sky contribution is

.. math::

   N_{\rm sky}
   =
   B_{\rm sky}
   A_{\rm fiber}
   t

where:

* :math:`B_{\rm sky}` is the sky brightness in e-/s/arcsec²
* :math:`A_{\rm fiber}` is the fiber area.

Noise Model
-----------

The total variance is

.. math::

   \sigma^2 =
   N_\star +
   N_{\rm sky} +
   N_{\rm dark} +
   \sigma_{\rm RN}^2 +
   \sigma_{\rm emp}^2

where

.. math::

   \sigma_{\rm emp}
   =
   f_{\rm emp} N_\star

is an empirical systematic noise floor.

Signal-to-Noise Ratio
---------------------

The final signal-to-noise ratio is

.. math::

   {\rm S/N}
   =
   \frac{N_\star}{\sigma}.

Moon and Galactic background
----------------------------

The background count is the sum of atmospheric sky, scattered moonlight,
and unresolved Galactic starlight, each multiplied by fiber area and total
integration time. ``sky_electrons`` remains the total of all three components.
The individual counts are also returned for the noise budget.

``moon_illumination`` is a fraction from 0 (new Moon) to 1 (full Moon).
The added moonlight rate is illumination times ``full_moon_e_per_s_arcsec2``;
it is zero when ``moon_above_horizon`` is false or latitude is low. This is a configurable linear
approximation at fixed geometry, not a calibrated lunar scattering model.
Moon altitude and target separation are not modeled.

``galactic_latitude`` selects ``high`` or ``low`` observatory coefficients.
``galactic_e_per_s_arcsec2`` can override the selected coefficient. This term
represents additive unresolved starlight, not individual contaminating stars.
All background rates must be finite and nonnegative, in electrons per second
per square arcsecond for the same spectral interval as the stellar rate.
The existing sky override applies only to the atmospheric component.

Measured background defaults (electrons/arcsec² in 500 s): APO high latitude
40 at new Moon and 80 at full Moon, low latitude median 92; LCO high latitude
27 at new Moon and 41.7 at full Moon, low latitude median 70. Rate defaults
are these levels divided by 500. The Galactic increment is the low-latitude
median minus the high-latitude moon-down baseline; this decomposition is a
bookkeeping convention, not a physical separation measured independently.
High-latitude lunar interpolation is linear. Low-latitude Moon dependence
is disabled, following the reported absence of a dependence. Field-to-field
variation is substantial: APO low latitude 50–160; LCO disk 35–140 and bulge
40–225, with the same reported median of 70 for disk and bulge. No distinct
bulge median or longitude law is inferred from the ranges. The spectral
interval of the measurements must match that used for the stellar rate.
The fractional systematic noise floor is disabled at both sites, removing
the previous S/N ceiling of 50. High-S/N estimates exclude systematic errors. The new terms add photon
noise; uncertainty in background subtraction is not included.


Measured stellar flux normalization
-----------------------------------

The APO ADU fit is log10(F) = 7.754969 - 0.398041 H for 458 s,
with gain 1.9 electrons/ADU. The LCO fit is log10(F) = 7.32569 -
0.4010084 H for 447 s, with gain 3.0. These are per extracted spectral
pixel on the green detector. The electron-rate intercept is
Z_rate = Z_ADU + log10(gain / exposure_time). Both adopted magnitude slopes are fixed at -0.4, with adjusted ADU
intercepts 7.7814155 (APO) and 7.312 (LCO). The adopted electron-rate
intercepts are 5.39930362 and 5.13881373 respectively. The APO adjustment
preserves the original fit at H=13.5; LCO uses the supplied rounded intercept. Gain is already included in the intercept and is not applied again.

These measurements include fiber losses and atmospheric extinction, for
observations with X < 1.5 and seeing < 1.5 arcsec. The Gaussian fiber
correction is therefore f(seeing)/f(reference seeing), not f(seeing) alone.
The output fiber fraction still reports the absolute Gaussian fraction.
The residual empirical seeing slopes are set to zero pending calibration.

Default and reference seeing is 1.58 arcsec at APO and 1.27 at LCO;
reference airmass is 1.24 at APO and 1.16 at LCO, using supplied site medians.
Omitted Python seeing/airmass inputs use these site-specific defaults.
These medians are adopted fiducials; the stellar fit was restricted to seeing
<1.5 and X<1.5, so its exact reference conditions remain to be established.
The airmass slope is -0.016
dex/airmass, corresponding to assumed k_H=0.04 mag/airmass.

S/N is now explicitly labeled per green-detector spectral pixel. The
three-effective-pixel detector-noise factor remains a provisional extraction-noise
approximation; it does not multiply the measured stellar or sky counts.


Measured dark current and single-read noise
-------------------------------------------

Dark input levels are ADU per detector pixel per 10.649-second read:
APO 0.071428575 and LCO 0.05102041. The configured electron rates are
ADU/read * gain / 10.649: approximately 0.0127443227064 at APO and
0.0143732960841 at LCO, in electrons/s/detector pixel.

Measured single-read noise is stored separately as 20.9 electrons at APO
and 24.0 at LCO. These values enter the ramp read-noise coefficient below. The legacy
read_noise_e field is no longer used by the calculator. The three-effective-pixel
extraction factor remains provisional pending extraction variance calibration.


Ramp noise and whole-read timing
--------------------------------

The adopted ETC timing convention is exposure_time = nreads * 10.649 s.
Requested times round up to whole reads, with a minimum of three total reads
(two good reads). One initial read is discarded: ngdreads = nreads - 1.
All flux components use the resulting duration. The exposure-time solver
searches integers and returns the shortest whole-read duration reaching the
target within its bounds, without rounding above the maximum bound.

For N total and G good reads the detector read variance coefficient is
A = 12*(G-1)/(N*(G+1)), and the photon variance coefficient is
C = 6*(G**2+1)/(5*G*(G+1)). The extracted-spectrum approximation is
variance = C*(star + sky + dark) + nexp*npix*A*single_read_noise**2
+ empirical_variance. The measured extracted star and sky counts are not
multiplied by npix; this provisional factor applies to detector dark counts
and read variance. Exact extraction-weight propagation is still needed.
The app displays all budget components as variances in electrons squared.


Effective extraction factor
----------------------------

For an approximately Gaussian spatial profile with FWHM 2 detector pixels,
uniform-variance optimal extraction gives N_eff = 1/sum(P_i**2), approximately
2*sqrt(pi)*(2/2.355) = 3.01. Both observatories adopt 3.0 for the existing
npix_per_resolution_element field. Despite its legacy name, this is an
effective spatial extraction factor per extracted spectral pixel, not a
spectral resolution-element width or the number of pixels in the aperture.
It scales detector read variance and dark counts; measured extracted stellar
and sky counts retain their existing normalization. The factor is approximate
and should be checked using actual extraction weights.


S/N bin units
--------------

Measured stellar and sky counts refer to native apCframe spectral pixels,
without dither combination or resampling. Native green-detector width is
0.2844 Angstrom; apStar width is 0.2229 Angstrom. The adopted resolution
width is twice the apStar width, 0.4458 Angstrom. ``snr_unit`` accepts
``native`` (default), ``apvisit``, ``apstar``, or ``resolution``. Output S/N is native S/N
times sqrt(selected width / native width), and the solver targets this unit.
``native_snr`` returns the original result. Electron counts and variance
budget always refer to the native pixel; only the reported S/N changes.
This equivalent-bin approximation assumes locally uniform spectral signal
and noise density. It does not predict actual resampled-pixel covariance,
dither-combination weights, or apStar pipeline uncertainty values. No extra
exposure factor is applied when changing the S/N unit.


Dithered apVisit pixels
-----------------------

The apVisit option adopts half the native pixel width, 0.1422 Angstrom,
with half the equivalent-bin flux and S/N equal to native S/N divided by
sqrt(2), at fixed total integration. No additional exposure or dither-pair
factor is introduced: nexp already counts the input exposures. As for apStar,
this is a wavelength-bin approximation rather than a simulation of dither
combination, its weights, or pixel covariance. The detector noise budget
continues to be reported per native apCframe pixel.


Flux and noise outputs
-----------------------

``flux_electrons`` is sky-subtracted stellar signal summed over all exposures
in the selected wavelength bin. ``noise_electrons`` is its 1-sigma noise.
For width ratio q = selected_width/native_width, flux = native_flux*q and
noise = native_noise*sqrt(q), so flux/noise equals the reported S/N.
These are summed electron-equivalent counts, not count rates, ADU, or the
normalization of actual pipeline combined files (which may use averages).
The app shows both values and one magnitude plot with differently colored S/N, flux and noise curves,
all at the same selected bin width, observing conditions and integration.
The native noise budget and its output fields remain unchanged.


Empirical seeing correction (current default)
----------------------------------------------

The default fiber_coupling_model is now empirical_only. Measured log10 flux
slopes are -0.18299435 dex/arcsec at APO and -0.23411219 at LCO. The stellar
count rate is multiplied by 10**(slope*(seeing-reference_seeing)); no Gaussian
fiber fraction is applied. The app reports this relative seeing flux factor,
not an absolute fraction entering the fiber. The existing electron-rate
zeropoints and fiducial conditions are retained. New seeing-fit intercepts
are not used until their count units and exposure normalization are confirmed.
Absolute fiber throughput is already included in the stellar normalization.
These empirical slopes describe observed counts; extrapolation beyond the
measured seeing range remains unvalidated. The older Gaussian discussion
above documents the previous model, not the current default.


Updated joint stellar calibration
----------------------------------

The current calibration supersedes the earlier stellar fits and separate
seeing/airmass fits. With magnitude slope fixed at -0.4, the joint ADU
zeropoints and coefficients are:

* APO: reference Z=7.6344033081894125 at 457 s, gain=1.9,
  seeing slope=-0.1793683081448493, airmass slope=-0.21234465084552678.
* LCO: reference Z=7.26616751714969 at 447 s, gain=3.0,
  seeing slope=-0.2110851442561022, airmass slope=-0.11677194677614952.

The rate intercept is Z + log10(gain/exposure_time). Reference conditions
are seeing=1.58 arcsec, X=1.24 at APO and seeing=1.27, X=1.16 at LCO.
These fitted terms describe measured instrumental throughput; they are not
interpreted as atmospheric extinction alone. No Gaussian coupling is applied.


Final rate-normalized joint calibration
----------------------------------------

This calibration supersedes the preceding ADU-based fits. All exposure
zeropoints were measured with H-magnitude slope fixed at -0.4 and converted
to electrons/s/native spectral pixel before the joint fit. Adopt directly:

* APO: Z=5.286024848102618, seeing slope=-0.17974092339286213,
  airmass slope=-0.15628331623665812.
* LCO: Z=5.082818044301776, seeing slope=-0.21420982017607323,
  airmass slope=-0.11268839513904064.

No additional gain or exposure-normalization conversion is applied to these
intercepts. Reference seeing/airmass remain 1.58/1.24 at APO and 1.27/1.16
at LCO. Accumulated stellar electrons are the predicted rate multiplied by
the total integration time.


Throughput prediction ranges
-----------------------------

Robust residual scatter is 0.06425145257251579 dex at APO and
0.07122455533578975 at LCO. Prediction bands evaluate stellar rates scaled
by 10**(+/-scatter), keeping sky, dark and read variance fixed. Photon noise
is recomputed for each case; S/N is not simply assigned the flux fractional
uncertainty. The nominal relation is unchanged; median residual offsets are
not applied. The ranges are empirical scatter bands, not formal confidence
intervals or guaranteed 68-percent coverage. They are separate from the
spectral-noise budget and do not cap S/N. A common throughput offset is
assumed for all exposures: no independent-exposure averaging reduction is
claimed without data demonstrating independence.
