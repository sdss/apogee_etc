Examples
========

APO Example
-----------

.. code-block:: python

    inp = ETCInput(
        observatory="APO",
        hmag=13,
        exptime_s=1000,
        nexp=1,
    )

    out = calculate_snr(inp)

    print(out.snr)

LCO Example
-----------

.. code-block:: python

    inp = ETCInput(
        observatory="LCO",
        hmag=13,
        exptime_s=1000,
        nexp=1,
    )
