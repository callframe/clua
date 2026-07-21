cmake_minimum_required(VERSION 3.20)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CLUA_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
if("${CLUA_DIR}" STREQUAL "${CMAKE_BINARY_DIR}")
    message(FATAL_ERROR "In-source builds are not allowed. Please use a separate build directory.")
endif()

project(clua
    DESCRIPTION "A Lua virtual machine written in C++"
    VERSION 0.1.0
)

include(FetchContent)

FetchContent_Declare(
    abseil
    GIT_REPOSITORY https://github.com/abseil/abseil-cpp.git
    GIT_TAG        ce1a8f1ec1793e5cb9d7fffa281efdfea5dd8035
)

FetchContent_MakeAvailable(abseil)

set(CLUA_SRCDIR "${CLUA_DIR}/clua")
include("${CLUA_SRCDIR}/build.cmake")

set(LIBCLUA_SRCDIR "${CLUA_DIR}/libclua")
include("${LIBCLUA_SRCDIR}/build.cmake")
