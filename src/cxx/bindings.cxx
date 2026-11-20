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
    m.def(
        "generate_valid_schedules",
        generator::generate_valid_schedules,
R"doc(Find all valid schedules from a list of categorized groups.

Given a list of group categories, builds every schedule that takes
exactly one group from each category, such that no two groups in a
schedule overlap. The search is performed with a DFS over categories
with constraint pruning (overlapping candidates are skipped early).

Internally, a mirror structure of the input is built to drive the
search; the returned schedules are assembled as vectors of Python
references to the original Group objects, so each schedule element is
the very same object that was passed in.

Args:
    input_groups: A list of group lists (one list per category),
        i.e. ``list[list[Group]]``. Order of categories determines
        the order of groups within each resulting schedule.

Returns:
    A list of valid schedules, each a ``list[Group]`` with one group
    per input category, in category order. Empty if no combination
    satisfies the non-overlap constraint.

Example:
    >>> schedules = generate_valid_schedules([groupsA, groupsB, groupsC])
    >>> schedules[0]
    [group_a1, group_b1, group_c2]   # all pairwise non-overlapping
)doc");
}
