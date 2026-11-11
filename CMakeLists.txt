CMAKE_MINIMUM_REQUIRED(VERSION 4.3.0)
PROJECT(ScheBuilder LANGUAGES CXX)

SET(CMAKE_CXX_STANDARD 23)
SET(CMAKE_CXX_STANDARD_REQUIRED TRUE)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(
    Generator
    src/cxx/bindings.cxx
    src/cxx/generator.cxx
)

install(TARGETS Generator DESTINATION ScheBuilder)
