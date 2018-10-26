# Inky

Python library for the [Inky pHAT](https://shop.pimoroni.com/products/inky-phat) and [Inky wHAT](https://shop.pimoroni.com/products/inky-what) e-paper displays.

## Inky pHAT

[Inky pHAT](https://shop.pimoroni.com/products/inky-phat) is a 212x104 pixel e-paper display, available in red/black/white, yellow/black/white and black/white. It's great for nametags and displaying very low frequency information such as a daily calendar or weather overview.


## Inky wHAT

[Inky wHAT](https://shop.pimoroni.com/products/inky-what) is a 400x300 pixel e-paper display available in red/black/white. It's got tons of resolution for detailed daily todo lists, multi-day weather forecasts, bus timetables and more.

# Usage

The Inky library contains modules for both the pHAT and wHAT, load the InkyPHAT one as follows:

```python
from inky import InkyPHAT
```

You'll then need to pick your colour, one of 'red', 'yellow' or 'black' and instantiate the class:

```python
inkyphat = InkyPHAT('red')
```

If you're using the wHAT you'll need to load the InkyWHAT class from the Inky library like so:

```python
from inky import InkyWHAT
inkywhat = InkyWHAT('red')
```

Since Inky wHAT is currently only available in red, we pick that colour.
