#include "inky/e673.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <thread>
#include <span>

namespace inky {
namespace {
constexpr std::array<std::array<std::uint8_t, 3>, 6> kDesaturatedPalette = {{{0, 0, 0}, {255, 255, 255}, {255, 255, 0}, {255, 0, 0}, {0, 0, 255}, {0, 255, 0}}};
constexpr std::array<std::array<std::uint8_t, 3>, 6> kSaturatedPalette = {{{0, 0, 0}, {161, 164, 165}, {208, 190, 71}, {156, 72, 75}, {61, 59, 94}, {58, 91, 70}}};
constexpr std::array<std::uint8_t, 6> kPaletteRemap = {0, 1, 2, 3, 5, 6};

constexpr std::uint8_t EL673_PSR = 0x00;
constexpr std::uint8_t EL673_PWR = 0x01;
constexpr std::uint8_t EL673_POF = 0x02;
constexpr std::uint8_t EL673_POFS = 0x03;
constexpr std::uint8_t EL673_PON = 0x04;
constexpr std::uint8_t EL673_BTST1 = 0x05;
constexpr std::uint8_t EL673_BTST2 = 0x06;
constexpr std::uint8_t EL673_DSLP = 0x07;
constexpr std::uint8_t EL673_BTST3 = 0x08;
constexpr std::uint8_t EL673_DTM1 = 0x10;
constexpr std::uint8_t EL673_DSP = 0x11;
constexpr std::uint8_t EL673_DRF = 0x12;
constexpr std::uint8_t EL673_PLL = 0x30;
constexpr std::uint8_t EL673_CDI = 0x50;
constexpr std::uint8_t EL673_TCON = 0x60;
constexpr std::uint8_t EL673_TRES = 0x61;
constexpr std::uint8_t EL673_REV = 0x70;
constexpr std::uint8_t EL673_VDCS = 0x82;
constexpr std::uint8_t EL673_PWS = 0xE3;

constexpr std::size_t kPackedLength = (E673::Width * E673::Height) / 2;
}  // namespace

E673::E673(std::shared_ptr<SpiDevice> spi, std::shared_ptr<GpioController> gpio, Pins pins)
    : spi_(std::move(spi)), gpio_(std::move(gpio)), pins_(pins), buffer_(Width * Height, 0) {
    if (!spi_) {
        throw std::invalid_argument("SPI device must not be null");
    }
    if (!gpio_) {
        throw std::invalid_argument("GPIO controller must not be null");
    }
}

void E673::setPixel(std::size_t x, std::size_t y, Colour colour) {
    if (x >= Width || y >= Height) {
        throw std::out_of_range("Pixel coordinate outside display bounds");
    }
    buffer_[y * Width + x] = static_cast<std::uint8_t>(colour);
}

void E673::setBorder(Colour colour) {
    borderColour_ = colour;
}

void E673::setImageIndices(std::span<const std::uint8_t> indices) {
    if (indices.size() != buffer_.size()) {
        throw std::invalid_argument("Image dimensions must be 800x480 with one byte per pixel");
    }
    buffer_.assign(indices.begin(), indices.end());
}

void E673::setImageRgb(std::span<const std::uint8_t> rgbPixels, float saturation) {
    if (rgbPixels.size() != Width * Height * 3) {
        throw std::invalid_argument("RGB payload must contain 800x480 pixels with three bytes each");
    }
    auto palette = paletteFromSaturation(saturation);

    for (std::size_t i = 0; i < buffer_.size(); ++i) {
        std::array<std::uint8_t, 3> pixel{
            rgbPixels[i * 3 + 0],
            rgbPixels[i * 3 + 1],
            rgbPixels[i * 3 + 2],
        };
        buffer_[i] = quantizePixel(pixel, palette);
    }
}

void E673::show(bool busyWait) {
    auto packed = packBuffer();
    writeDisplay(packed, busyWait);
}

void E673::ensureSetup() {
    if (setup_) {
        return;
    }

    gpio_->configureOutput(pins_.cs, true);
    gpio_->configureOutput(pins_.dc, false);
    gpio_->configureOutput(pins_.reset, true);
    gpio_->configureInput(pins_.busy, true);

    reset();

    sendCommand(0xAA, {0x49, 0x55, 0x20, 0x08, 0x09, 0x18});
    sendCommand(EL673_PWR, {0x3F});
    sendCommand(EL673_PSR, {0x5F, 0x69});

    sendCommand(EL673_BTST1, {0x40, 0x1F, 0x1F, 0x2C});
    sendCommand(EL673_BTST3, {0x6F, 0x1F, 0x1F, 0x22});
    sendCommand(EL673_BTST2, {0x6F, 0x1F, 0x17, 0x17});

    sendCommand(EL673_POFS, {0x00, 0x54, 0x00, 0x44});
    sendCommand(EL673_TCON, {0x02, 0x00});
    sendCommand(EL673_PLL, {0x08});
    sendCommand(EL673_CDI, {0x3F});
    sendCommand(EL673_TRES, {0x03, 0x20, 0x01, 0xE0});
    sendCommand(EL673_PWS, {0x2F});
    sendCommand(EL673_VDCS, {0x01});

    setup_ = true;
}

void E673::reset() {
    gpio_->setValue(pins_.reset, false);
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    gpio_->setValue(pins_.reset, true);
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    busyWait(std::chrono::milliseconds(300));
}

void E673::busyWait(std::chrono::milliseconds timeout) {
    if (gpio_->getValue(pins_.busy)) {
        std::this_thread::sleep_for(timeout);
        return;
    }

    const auto deadline = std::chrono::steady_clock::now() + timeout;
    while (!gpio_->getValue(pins_.busy)) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        if (std::chrono::steady_clock::now() > deadline) {
            return;
        }
    }
}

void E673::sendCommand(std::uint8_t command, std::span<const std::uint8_t> data) {
    gpio_->setValue(pins_.cs, false);
    gpio_->setValue(pins_.dc, false);
    std::this_thread::sleep_for(std::chrono::milliseconds(300));

    std::span<const std::uint8_t> commandSpan(&command, 1);
    spi_->transfer(commandSpan);

    if (!data.empty()) {
        gpio_->setValue(pins_.dc, true);
        spi_->transfer(data);
    }

    gpio_->setValue(pins_.cs, true);
    gpio_->setValue(pins_.dc, false);
}

void E673::writeDisplay(std::span<const std::uint8_t> packedBuffer, bool waitForIdle) {
    ensureSetup();

    sendCommand(EL673_DTM1, packedBuffer);
    sendCommand(EL673_PON);
    this->busyWait(std::chrono::milliseconds(300));

    sendCommand(EL673_BTST2, {0x6F, 0x1F, 0x17, 0x49});

    sendCommand(EL673_DRF, {0x00});
    if (waitForIdle) {
        this->busyWait(std::chrono::seconds(32));
    }

    sendCommand(EL673_POF, {0x00});
    this->busyWait(std::chrono::milliseconds(300));
}

std::vector<std::uint8_t> E673::packBuffer() const {
    std::vector<std::uint8_t> packed(kPackedLength, 0);
    std::size_t outIndex = 0;
    for (std::size_t i = 0; i < buffer_.size(); i += 2) {
        std::uint8_t high = static_cast<std::uint8_t>(buffer_[i] << 4);
        std::uint8_t low = (i + 1 < buffer_.size()) ? static_cast<std::uint8_t>(buffer_[i + 1] & 0x0F) : 0;
        packed[outIndex++] = static_cast<std::uint8_t>(high | low);
    }
    return packed;
}

std::vector<std::uint8_t> E673::paletteFromSaturation(float saturation) const {
    float clamped = std::clamp(saturation, 0.0f, 1.0f);
    std::vector<std::uint8_t> palette;
    palette.reserve(kDesaturatedPalette.size() * 3);

    for (std::size_t i = 0; i < kDesaturatedPalette.size(); ++i) {
        float rs = static_cast<float>(kSaturatedPalette[i][0]) * clamped;
        float gs = static_cast<float>(kSaturatedPalette[i][1]) * clamped;
        float bs = static_cast<float>(kSaturatedPalette[i][2]) * clamped;

        float rd = static_cast<float>(kDesaturatedPalette[i][0]) * (1.0f - clamped);
        float gd = static_cast<float>(kDesaturatedPalette[i][1]) * (1.0f - clamped);
        float bd = static_cast<float>(kDesaturatedPalette[i][2]) * (1.0f - clamped);

        palette.push_back(static_cast<std::uint8_t>(rs + rd));
        palette.push_back(static_cast<std::uint8_t>(gs + gd));
        palette.push_back(static_cast<std::uint8_t>(bs + bd));
    }

    return palette;
}

std::uint8_t E673::quantizePixel(const std::array<std::uint8_t, 3> &pixel, std::span<const std::uint8_t> palette) const {
    std::size_t bestIndex = 0;
    std::uint32_t bestDistance = std::numeric_limits<std::uint32_t>::max();

    for (std::size_t i = 0; i < kDesaturatedPalette.size(); ++i) {
        const std::uint8_t pr = palette[i * 3 + 0];
        const std::uint8_t pg = palette[i * 3 + 1];
        const std::uint8_t pb = palette[i * 3 + 2];

        auto dr = static_cast<int>(pixel[0]) - static_cast<int>(pr);
        auto dg = static_cast<int>(pixel[1]) - static_cast<int>(pg);
        auto db = static_cast<int>(pixel[2]) - static_cast<int>(pb);

        std::uint32_t distance = static_cast<std::uint32_t>(dr * dr + dg * dg + db * db);
        if (distance < bestDistance) {
            bestDistance = distance;
            bestIndex = i;
        }
    }

    return kPaletteRemap[bestIndex];
}

}  // namespace inky

