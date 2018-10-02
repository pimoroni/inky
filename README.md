# Inky

Python library for Inky wHAT and Inky pHAT.

## Inky pHAT

Inky pHAT is a 212x104 pixel eInk display available in Red/Black/White, Yellow/Black/White and Black/White. It's great for nametags and displaying very low frequency information such as a daily calendar or weather overview.


## Inky wHAT

Inky wHAT is a 400x300 pixel eInk display available in Red/Black/White. It's got tons of resolution for detailed daily todo lists, multi-day weather forecasts, bus timetables and more.

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

