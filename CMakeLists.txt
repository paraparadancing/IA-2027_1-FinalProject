CMAKE_MINIMUM_REQUIRED(VERSION 4.3.0)
PROJECT(generator_backend_cxx LANGUAGES CXX)

SET(CMAKE_CXX_STANDARD 23)
SET(CMAKE_CXX_STANDARD_REQUIRED TRUE)

set(Python3_FIND_VIRTUALENV FIRST)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND "${Python3_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE pybind11_DIR
)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(
    generator_backend
    src/cxx/bindings.cxx
    src/cxx/generator.cxx
)

install(TARGETS generator_backend LIBRARY DESTINATION .)
