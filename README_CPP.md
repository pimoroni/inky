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

