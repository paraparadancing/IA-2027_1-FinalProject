#include <pybind11/detail/common.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "generator.hxx"

namespace py = pybind11;

namespace pybind11 { namespace detail {
    template <>
    struct type_caster<generator::Weekday> {
    public:
        PYBIND11_TYPE_CASTER(generator::Weekday, const_name("Weekday"));

        bool load(handle src, bool convert) {
            if (!py::hasattr(src, "value")) {
                return false;
            }
            try {
                int val = src.attr("value").cast<int>();
                if (val < 1 || val > 6) return false;
                value = static_cast<generator::Weekday>(val);
                return true;
            } catch (const py::cast_error&) {
                return false;
            }
        }
    };

    template <>
    struct type_caster<generator::time_block> {
    public:
        PYBIND11_TYPE_CASTER(generator::time_block, const_name("TimeBlock"));

        bool load(handle src, bool convert) {
            if (!py::hasattr(src, "start") || !py::hasattr(src, "end")) {
                return false;
            }

            try {
                py::object start = src.attr("start");
                py::object end = src.attr("end");

                value[0] = {
                    start.attr("hours").cast<unsigned short>(),
                    start.attr("minutes").cast<unsigned short>()
                };
                value[1] = {
                    end.attr("hours").cast<unsigned short>(),
                    end.attr("minutes").cast<unsigned short>()
                };
                return true;
            } catch (const py::cast_error&) {
                return false;
            }
        }
    };

    template <>
    struct type_caster<generator::Group> {
    public:
        PYBIND11_TYPE_CASTER(generator::Group, const_name("Group"));

        bool load(handle src, bool convert) {
            if (!py::hasattr(src, "time_blocks")) {
                return false;
            }

            try {
                auto blocks = src.attr("time_blocks")
                    .cast<std::unordered_map<generator::Weekday, generator::time_block>>();
                value = generator::Group(src, blocks);
                return true;
            } catch (const py::cast_error&) {
                return false;
            }
        }
    };
}}

PYBIND11_MODULE(generator_backend, m, py::mod_gil_not_used()){
    m.def("read_group", generator::read_group, "A function that prints Group objects in their C++ implementation.");
}
