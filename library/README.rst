Inky
====

|Build Status| |Coverage Status| |PyPi Package| |Python Versions|

Python library for the `Inky
pHAT <https://shop.pimoroni.com/products/inky-phat>`__ and `Inky
wHAT <https://shop.pimoroni.com/products/inky-what>`__ e-paper displays.

Inky pHAT
---------

`Inky pHAT <https://shop.pimoroni.com/products/inky-phat>`__ is a
212x104 pixel e-paper display, available in red/black/white,
yellow/black/white and black/white. It's great for nametags and
displaying very low frequency information such as a daily calendar or
weather overview.

Inky wHAT
---------

`Inky wHAT <https://shop.pimoroni.com/products/inky-what>`__ is a
400x300 pixel e-paper display available in red/black/white. It's got
tons of resolution for detailed daily todo lists, multi-day weather
forecasts, bus timetables and more.

Installation
============

The Python pip package is named einky, install with:

::

    sudo pip install einky

Usage
=====

The Inky library contains modules for both the pHAT and wHAT, load the
InkyPHAT one as follows:

.. code:: python

    from inky import InkyPHAT

You'll then need to pick your colour, one of 'red', 'yellow' or 'black'
and instantiate the class:

.. code:: python

    inkyphat = InkyPHAT('red')

If you're using the wHAT you'll need to load the InkyWHAT class from the
Inky library like so:

.. code:: python

    from inky import InkyWHAT
    inkywhat = InkyWHAT('red')

Since Inky wHAT is currently only available in red, we pick that colour.

.. |Build Status| image:: https://travis-ci.com/pimoroni/inky.svg?branch=master
   :target: https://travis-ci.com/pimoroni/inky
.. |Coverage Status| image:: https://coveralls.io/repos/github/pimoroni/inky/badge.svg?branch=master
   :target: https://coveralls.io/github/pimoroni/inky?branch=master
.. |PyPi Package| image:: https://img.shields.io/pypi/v/einky.svg
   :target: https://pypi.python.org/pypi/einky
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/einky.svg
   :target: https://pypi.python.org/pypi/einky
