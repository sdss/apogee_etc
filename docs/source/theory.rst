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

Reference seeing remains provisionally 1.3 arcsec at APO and 1.1 at LCO;
reference airmass remains 1.2 at both sites. These are assumptions, not
sample medians inferred from the cuts. Replace them with representative
conditions from the calibration sample. The airmass slope is -0.016
dex/airmass, corresponding to assumed k_H=0.04 mag/airmass.

S/N is now explicitly labeled per green-detector spectral pixel. The
four-pixel detector-noise factor remains a provisional extraction-noise
approximation; it does not multiply the measured stellar or sky counts.


Measured dark current and single-read noise
-------------------------------------------

Dark input levels are ADU per detector pixel per 10.6-second read:
APO 0.071428575 and LCO 0.05102041. The configured electron rates are
ADU/read * gain / 10.6: approximately 0.0128032351415 at APO and
0.0144397386792 at LCO, in electrons/s/detector pixel.

Measured single-read noise is stored separately as 20.9 electrons at APO
and 24.0 at LCO. These values enter the ramp read-noise coefficient below. The legacy
read_noise_e field is no longer used by the calculator. The four-pixel
extraction factor remains provisional pending extraction variance calibration.


Ramp noise and whole-read timing
--------------------------------

The adopted ETC timing convention is exposure_time = nreads * 10.6 s.
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
