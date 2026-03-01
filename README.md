# Inky C++ Port

Modern C++20 port of the Inky driver focused on the E673 Inky Impression 7.3" Spectra 6 display.

- [Overview](#overview)
- [Requirements](#requirements)
- [Build](#build)
- [Cross-Compile (Raspberry Pi OS)](#cross-compile-raspberry-pi-os)
- [Run on Raspberry Pi](#run-on-raspberry-pi)
- [Usage](#usage)
- [Porting Workflow](#porting-workflow)
- [Troubleshooting](#troubleshooting)

## Overview

This repository contains a CMake-based C++ implementation of the Inky display logic.
The C++ port keeps hardware access abstracted so the code can run against:

- Linux hardware backends (`libgpiod` + `spidev`)
- in-memory/mock backends for development and tests

Python materials are kept in `reference/python/` only as temporary reference for porting.

## Requirements

- CMake >= 3.16
- C++20 compiler
- Optional hardware backend dependency:
  - `libgpiod >= 1.6`

On Debian/Ubuntu-like systems:

```bash
sudo apt install cmake g++ pkg-config
```

## Build

Native debug build:

```bash
cmake --preset native-debug
cmake --build --preset native-debug
```

Examples are enabled by default. Disable them with:

```bash
cmake -S . -B build -DINKY_BUILD_EXAMPLES=OFF
cmake --build build
```

Without Linux GPIO backend:

```bash
cmake -S . -B build -DINKY_ENABLE_LINUX_GPIOD=OFF
cmake --build build
```

## Cross-Compile (Raspberry Pi OS)

Available presets:

- `rpi-aarch64-release` (Raspberry Pi OS 64-bit)
- `rpi-armhf-release` (Raspberry Pi OS 32-bit)

Install cross-compilers on host:

```bash
sudo apt install g++-aarch64-linux-gnu-12 gcc-aarch64-linux-gnu-12
sudo apt install g++-arm-linux-gnueabihf gcc-arm-linux-gnueabihf
sudo apt install pkg-config rsync
```

Populate sysroot from target Pi:

```bash
rsync -a --delete pi@<pi-ip>:/usr .sysroot/
rsync -a --delete pi@<pi-ip>:/lib .sysroot/
rsync -a --delete pi@<pi-ip>:/opt .sysroot/
```

If you require Linux GPIO backend in cross builds:

```bash
ssh pi@<pi-ip> "sudo apt update && sudo apt install -y libgpiod-dev"
```

Then configure/build:

```bash
cmake --preset rpi-aarch64-release
cmake --build --preset rpi-aarch64-release
```

```bash
cmake --preset rpi-armhf-release
cmake --build --preset rpi-armhf-release
```

## Run on Raspberry Pi

```bash
scp build-rpi-aarch64/inky_e673_example pi@<pi-ip>:/home/pi/
ssh pi@<pi-ip> "/home/pi/inky_e673_example"
```

## Usage

```cpp
#include "inky/e673.hpp"
#include "inky/hardware.hpp"

int main() {
    auto spi = std::make_shared<inky::LinuxSpi>();
    auto gpio = std::make_shared<inky::LinuxGpio>();
    inky::E673 display(spi, gpio);
    display.show();
}
```

Example target built by default:

- `inky_e673_example` from `examples/e673_show.cpp`
- When built without Linux hardware support, the example uses mock GPIO/SPI backends for local validation.

## Porting Workflow

- Boundaries and rules: `docs/cpp-port-structure.md`
- Progress tracker: `docs/porting-status.md`
- Python reference snapshot: `reference/python/README.md`
- Original upstream-style README (preserved): `reference/python/README_ORIGINAL.md`

## Troubleshooting

`libgpiod not found; Linux hardware backend disabled`

- For native builds: install `libgpiod-dev`.
- For cross builds: ensure `libgpiod.pc` exists in `.sysroot` and use the cross presets.
- Cross presets set `INKY_ENABLE_LINUX_GPIOD=ON` and `INKY_REQUIRE_LINUX_GPIOD=ON`, so configure fails fast if `libgpiod` is missing.

`GLIBCXX_x.y.z not found` on Raspberry Pi

- Host compiler is newer than Pi runtime.
- Use a compiler matching target distro (aarch64 preset is pinned to GCC 12) or build on Pi.
