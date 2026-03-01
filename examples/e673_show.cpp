#include "inky/e673.hpp"
#include "inky/hardware.hpp"

#include <array>
#include <iostream>
#include <memory>
#include <vector>

int main() {
    inky::Pins pins{};

#ifdef INKY_ENABLE_LINUX_GPIOD
    auto gpio = std::make_shared<inky::LinuxGpio>();
    auto spi = std::make_shared<inky::LinuxSpi>();
#else
    auto gpio = std::make_shared<inky::MemoryGpio>();
    auto spi = std::make_shared<inky::NullSpi>();
    gpio->configureInput(pins.busy, true);
#endif

    inky::E673 display(spi, gpio, pins);

    std::vector<std::uint8_t> indices(inky::E673::Width * inky::E673::Height, static_cast<std::uint8_t>(inky::Colour::White));
    const std::array<inky::Colour, 6> palette = {
        inky::Colour::Black,
        inky::Colour::Red,
        inky::Colour::Yellow,
        inky::Colour::Blue,
        inky::Colour::Green,
        inky::Colour::White};

    std::size_t stripeHeight = inky::E673::Height / palette.size();
    for (std::size_t y = 0; y < inky::E673::Height; ++y) {
        auto colour = palette[std::min(y / stripeHeight, palette.size() - 1)];
        for (std::size_t x = 0; x < inky::E673::Width; ++x) {
            indices[y * inky::E673::Width + x] = static_cast<std::uint8_t>(colour);
        }
    }

    display.setImageIndices(indices);
    display.setBorder(inky::Colour::White);
    display.show(false);

    std::cout << "Queued test frame for Inky Impression 7.3 (Spectra 6)." << std::endl;
    return 0;
}

