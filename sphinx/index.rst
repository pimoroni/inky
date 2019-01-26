.. role:: python(code)
   :language: python

Welcome
-------

This documentation will guide you through the methods available in the Inky python library.

.. currentmodule:: inky

At A Glance
-----------

.. autoclassoutline:: inky.inky.Inky
   :members:

.. toctree::
   :titlesonly:
   :maxdepth: 0


Setup Inky
----------

Note: If you're using a Pimoroni Inky board, the subclasses `InkyPHAT` and `InkyWHAT` set most of these options on your behalf, so you only need to specify colour.

For example::

    phat = InkyPHAT('red')

Or::

    what = InkyWHAT('yellow')

.. automethod:: inky.inky.Inky.__init__

Set A Border
------------

.. automethod:: inky.inky.Inky.set_border

Set An Image
------------

.. automethod:: inky.inky.Inky.set_image

Set A Pixel
-----------

.. automethod:: inky.inky.Inky.set_pixel

Set Up Inky
-----------

.. automethod:: inky.inky.Inky.setup

Show The Buffer
---------------

.. automethod:: inky.inky.Inky.show
