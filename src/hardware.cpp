#include "inky/hardware.hpp"

#include <algorithm>
#include <cstring>
#include <stdexcept>
#include <string>
#include <unordered_map>

#ifdef INKY_ENABLE_LINUX_GPIOD
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include <gpiod.h>
#include <cerrno>
#endif

namespace inky {

MemoryGpio::MemoryGpio(std::size_t lines) : states_(lines, false) {}

void MemoryGpio::configureOutput(unsigned int line, bool initialState) {
    ensureSize(line);
    states_[line] = initialState;
}

void MemoryGpio::configureInput(unsigned int line, bool pullUp) {
    ensureSize(line);
    states_[line] = pullUp;
}

void MemoryGpio::setValue(unsigned int line, bool active) {
    ensureSize(line);
    states_[line] = active;
}

bool MemoryGpio::getValue(unsigned int line) const {
    return line < states_.size() ? states_[line] : false;
}

void MemoryGpio::ensureSize(unsigned int line) {
    if (line >= states_.size()) {
        states_.resize(line + 1, false);
    }
}

#ifdef INKY_ENABLE_LINUX_GPIOD
namespace {
std::runtime_error systemError(const std::string &context) {
    return std::runtime_error(context + ": " + std::strerror(errno));
}
}

struct LinuxGpio::Impl {
    explicit Impl(const std::string &chipPath) {
        chip = gpiod_chip_open(chipPath.c_str());
        if (chip == nullptr) {
            throw systemError("gpiod_chip_open");
        }
    }

    ~Impl() {
        for (auto &entry : lines) {
            gpiod_line_release(entry.second);
        }
        if (chip != nullptr) {
            gpiod_chip_close(chip);
        }
    }

    void requestLine(unsigned int line, bool output, bool initialState, bool pullUp) {
        gpiod_line *handle = gpiod_chip_get_line(chip, line);
        if (handle == nullptr) {
            throw systemError("gpiod_chip_get_line");
        }

        int flags = pullUp ? GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP : 0;
        int result;
        if (output) {
            result = gpiod_line_request_output_flags(handle, "inky", flags, initialState ? 1 : 0);
        } else {
            result = gpiod_line_request_input_flags(handle, "inky", flags);
        }

        if (result < 0) {
            throw systemError("gpiod_line_request");
        }

        lines[line] = handle;
    }

    gpiod_chip *chip{nullptr};
    std::unordered_map<unsigned int, gpiod_line *> lines;
};

LinuxGpio::LinuxGpio(const std::string &chipPath) : impl_(std::make_unique<Impl>(chipPath)) {}
LinuxGpio::~LinuxGpio() = default;

void LinuxGpio::configureOutput(unsigned int line, bool initialState) {
    impl_->requestLine(line, true, initialState, false);
}

void LinuxGpio::configureInput(unsigned int line, bool pullUp) {
    impl_->requestLine(line, false, false, pullUp);
}

void LinuxGpio::setValue(unsigned int line, bool active) {
    auto it = impl_->lines.find(line);
    if (it == impl_->lines.end()) {
        throw std::runtime_error("GPIO line not requested");
    }
    if (gpiod_line_set_value(it->second, active ? 1 : 0) < 0) {
        throw systemError("gpiod_line_set_value");
    }
}

bool LinuxGpio::getValue(unsigned int line) const {
    auto it = impl_->lines.find(line);
    if (it == impl_->lines.end()) {
        throw std::runtime_error("GPIO line not requested");
    }
    int value = gpiod_line_get_value(it->second);
    if (value < 0) {
        throw systemError("gpiod_line_get_value");
    }
    return value != 0;
}

LinuxSpi::LinuxSpi(const std::string &device, std::uint32_t speed) : fd_(-1), speed_(speed) {
    fd_ = ::open(device.c_str(), O_RDWR);
    if (fd_ < 0) {
        throw systemError("open spidev");
    }

    std::uint8_t mode = SPI_MODE_0;
    std::uint8_t bits = 8;

    if (ioctl(fd_, SPI_IOC_WR_MODE, &mode) < 0 || ioctl(fd_, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0) {
        throw systemError("configure spidev");
    }

    if (ioctl(fd_, SPI_IOC_WR_MAX_SPEED_HZ, &speed_) < 0) {
        throw systemError("set max speed");
    }
}

LinuxSpi::~LinuxSpi() {
    if (fd_ >= 0) {
        ::close(fd_);
    }
}

void LinuxSpi::transfer(std::span<const std::uint8_t> data) {
    constexpr std::size_t chunkSize = 4096;
    for (std::size_t offset = 0; offset < data.size(); offset += chunkSize) {
        std::size_t remaining = std::min(chunkSize, data.size() - offset);
        spi_ioc_transfer transfer{};
        transfer.tx_buf = reinterpret_cast<std::uintptr_t>(data.data() + offset);
        transfer.len = static_cast<std::uint32_t>(remaining);
        transfer.speed_hz = speed_;
        transfer.bits_per_word = 8;
        transfer.cs_change = 0;

        if (ioctl(fd_, SPI_IOC_MESSAGE(1), &transfer) < 0) {
            throw systemError("SPI transfer");
        }
    }
}
#endif

}  // namespace inky

