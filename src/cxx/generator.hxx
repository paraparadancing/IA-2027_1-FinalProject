#pragma once

#include <pybind11/pybind11.h>
#include <array>
#include <unordered_map>
#include <vector>

namespace generator {
    namespace py = pybind11;

    enum class Weekday {
        MONDAY    = 1,
        TUESDAY   = 2,
        WEDNESDAY = 3,
        THURSDAY  = 4,
        FRIDAY    = 5,
        SATURDAY    = 6
    };

    /*
    Data correctness is done from the Python Module above.
        - time_val[0]: hours (24 hour format).
        - time_val[1]: minutes.
    */
    using time_val = std::array<unsigned short, 2>;
    /*
    Data correctness is done from the Python Module above.
        - time_block[0]: start time, inclusive.
        - time_block[1]: end time, exclusive.
    */
    using time_block = std::array<time_val, 2>;

    struct Group {
        py::handle group_python_obj;
        std::unordered_map<Weekday, time_block> time_blocks;

        Group() = default;

        Group(const py::handle &group_python_object, const std::unordered_map<Weekday, time_block> &time_blocks):
            group_python_obj(group_python_object),
            time_blocks(time_blocks)
        {}
        bool collides(const Group &other) const;
    };

    using group_collection = std::vector<Group>;
    using built_schedule = std::vector<py::handle>;

    std::vector<built_schedule> generate_valid_schedules(const std::vector<group_collection> &input_groups);
    void read_group(const Group &group);
}