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
