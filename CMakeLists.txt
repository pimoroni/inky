cmake_minimum_required(VERSION 3.16)
project(inky_cpp VERSION 0.1.0 LANGUAGES CXX)

option(INKY_ENABLE_LINUX_GPIOD "Enable the libgpiod + spidev hardware backend" ON)
option(INKY_BUILD_EXAMPLES "Build example programs" ON)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(inky
    src/e673.cpp
    src/hardware.cpp
)
add_library(inky::inky ALIAS inky)

target_include_directories(inky
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(inky PUBLIC cxx_std_20)

if(INKY_ENABLE_LINUX_GPIOD)
    find_package(PkgConfig)
    if(PkgConfig_FOUND)
        pkg_check_modules(GPIOD libgpiod>=1.6)
    endif()

    if(GPIOD_FOUND)
        target_compile_definitions(inky PUBLIC INKY_ENABLE_LINUX_GPIOD)
        target_include_directories(inky PRIVATE ${GPIOD_INCLUDE_DIRS})
        target_link_libraries(inky PRIVATE ${GPIOD_LIBRARIES})
    else()
        message(WARNING "libgpiod not found; Linux hardware backend disabled")
    endif()
endif()

if(INKY_BUILD_EXAMPLES)
    add_executable(inky_e673_example examples/e673_show.cpp)
    target_link_libraries(inky_e673_example PRIVATE inky)
endif()
