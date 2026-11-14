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

add_custom_command(TARGET generator_backend POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E env "PYTHONPATH=$<TARGET_FILE_DIR:generator_backend>"
        "${Python3_EXECUTABLE}" -m pybind11_stubgen generator_backend
        -o "$<TARGET_FILE_DIR:generator_backend>"
    COMMENT "Generando stubs .pyi para Pyrefly"
)