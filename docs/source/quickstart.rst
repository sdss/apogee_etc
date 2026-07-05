Quick Start
===========

Calculate the signal-to-noise ratio:

.. code-block:: python

    from apogee_etc import ETCInput, calculate_snr

    inp = ETCInput(
        observatory="APO",
        hmag=12.0,
        exptime_s=500,
        nexp=1,
        seeing_fwhm=1.3,
        airmass=1.2,
    )

    out = calculate_snr(inp)

    print(out.snr)

Compute the exposure time required for a target S/N:

.. code-block:: python

    from apogee_etc import exposure_time_for_snr

    out = exposure_time_for_snr(inp, target_snr=100)

    print(out.total_exptime_s)
