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
it is zero when ``moon_above_horizon`` is false. This is a configurable linear
approximation at fixed geometry, not a calibrated lunar scattering model.
Moon altitude and target separation are not modeled.

``galactic_latitude`` selects ``high`` or ``low`` observatory coefficients.
``galactic_e_per_s_arcsec2`` can override the selected coefficient. This term
represents additive unresolved starlight, not individual contaminating stars.
All background rates must be finite and nonnegative, in electrons per second
per square arcsecond for the same spectral interval as the stellar rate.
The existing sky override applies only to the atmospheric component.

Moon and Galactic coefficients default to zero pending APO/LCO calibration.
The app exposes editable rates and warns when a selected coefficient is zero.
Existing calls retain their numerical predictions. The new terms add photon
noise; uncertainty in background subtraction is not included.
