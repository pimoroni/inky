# Inky C++ Port

This directory adds a modern CMake-based C++ port of the Inky driver focused on the E673 Inky Impression 7.3" Spectra 6 panel. The port mirrors the Python driver's register programming sequence while exposing a small hardware abstraction so the driver can run against either real GPIO/SPI hardware or the in-memory mock used for testing and development.

## Building

```bash
cmake -S . -B build
cmake --build build
```

The build enables the libgpiod + spidev backend by default. If libgpiod is not available, the library will still build using the in-memory GPIO backend. You can explicitly disable hardware support with:

```bash
cmake -S . -B build -DINKY_ENABLE_LINUX_GPIOD=OFF
```

Examples are built by default and can be disabled with `-DINKY_BUILD_EXAMPLES=OFF`.

## Cross-compiling for Raspberry Pi OS

This repository includes ready-to-use cross toolchains and CMake presets:

- `cmake/toolchains/rpi-aarch64.cmake` for Raspberry Pi OS 64-bit
- `cmake/toolchains/rpi-armhf.cmake` for Raspberry Pi OS 32-bit
- `CMakePresets.json` presets:
  - `rpi-aarch64-release`
  - `rpi-armhf-release`

### 1. Install cross compilers on host

64-bit target:

```bash
sudo apt install g++-aarch64-linux-gnu-12 gcc-aarch64-linux-gnu-12 pkg-config rsync
```

32-bit target:

```bash
sudo apt install g++-arm-linux-gnueabihf gcc-arm-linux-gnueabihf pkg-config rsync
```

### 2. Populate `.sysroot`

The presets expect target headers/libs under `${workspace}/.sysroot`.

```bash
rsync -a --delete pi@<pi-ip>:/usr .sysroot/
rsync -a --delete pi@<pi-ip>:/lib .sysroot/
rsync -a --delete pi@<pi-ip>:/opt .sysroot/
```

If you need the Linux GPIO backend (`INKY_ENABLE_LINUX_GPIOD=ON`), install the dev package on the Pi first:

```bash
ssh pi@<pi-ip> "sudo apt update && sudo apt install -y libgpiod-dev"
```

Then sync `.sysroot` again.

### 3. Configure and build with presets

64-bit:

```bash
cmake --preset rpi-aarch64-release
cmake --build --preset rpi-aarch64-release
```

32-bit:

```bash
cmake --preset rpi-armhf-release
cmake --build --preset rpi-armhf-release
```

### 4. Deploy over SSH

```bash
scp build-rpi-aarch64/inky_e673_example pi@<pi-ip>:/home/pi/
ssh pi@<pi-ip> "/home/pi/inky_e673_example"
```

## Notes and troubleshooting

- Cross presets force `INKY_ENABLE_LINUX_GPIOD=ON` and `INKY_REQUIRE_LINUX_GPIOD=ON`.
  - Configure will fail if `libgpiod>=1.6` is not found in `.sysroot`.
- If runtime fails with `GLIBCXX_x.y.z not found`, your compiler/runtime is newer than the Pi image.
  - Use a matching compiler version for the target distro (the aarch64 toolchain is pinned to GCC 12 in this repo).
  - Or build directly on the Pi.

## Usage

```cpp
#include "inky/e673.hpp"
#include "inky/hardware.hpp"

int main() {
    auto spi = std::make_shared<inky::LinuxSpi>();
    auto gpio = std::make_shared<inky::LinuxGpio>();
    inky::E673 display(spi, gpio);
    // Fill the internal buffer with your own content here.
    display.show();
}
```

The helper example `examples/e673_show.cpp` draws simple colour stripes using the display's native palette. When built without hardware support it uses the mock GPIO/SPI backends so developers can validate buffer packing and quantization logic without connecting a display.
