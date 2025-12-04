#pragma once

#include "inky/hardware.hpp"

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <memory>
#include <span>
#include <vector>

namespace inky {

enum class Colour : std::uint8_t {
    Black = 0,
    White = 1,
    Yellow = 2,
    Red = 3,
    Blue = 5,
    Green = 6
};

struct Pins {
    unsigned int cs = 8;
    unsigned int dc = 22;
    unsigned int reset = 27;
    unsigned int busy = 17;
};

class E673 {
public:
    static constexpr std::size_t Width = 800;
    static constexpr std::size_t Height = 480;

    E673(std::shared_ptr<SpiDevice> spi, std::shared_ptr<GpioController> gpio, Pins pins = {});

    void setPixel(std::size_t x, std::size_t y, Colour colour);
    void setBorder(Colour colour);
    void setImageIndices(std::span<const std::uint8_t> indices);
    void setImageRgb(std::span<const std::uint8_t> rgbPixels, float saturation = 0.5f);
    void show(bool busyWait = true);

    const std::vector<std::uint8_t> &buffer() const noexcept { return buffer_; }

private:
    void ensureSetup();
    void reset();
    void busyWait(std::chrono::milliseconds timeout);
    void sendCommand(std::uint8_t command, std::span<const std::uint8_t> data = {});
    void sendCommand(std::uint8_t command, std::initializer_list<std::uint8_t> data) {
        sendCommand(command, std::span<const std::uint8_t>(data.begin(), data.size()));
    }
    void writeDisplay(std::span<const std::uint8_t> packedBuffer, bool waitForIdle);
    std::vector<std::uint8_t> packBuffer() const;

    std::vector<std::uint8_t> paletteFromSaturation(float saturation) const;
    std::uint8_t quantizePixel(const std::array<std::uint8_t, 3> &pixel, std::span<const std::uint8_t> palette) const;

    std::shared_ptr<SpiDevice> spi_;
    std::shared_ptr<GpioController> gpio_;
    Pins pins_;
    std::vector<std::uint8_t> buffer_;
    Colour borderColour_{Colour::White};
    bool setup_{false};
};

}  // namespace inky

