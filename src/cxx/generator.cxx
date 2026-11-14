#include "generator.hxx"
#include <iostream>

namespace generator {
    void read_group(const Group &group) {
        std::cout << "Python object: " << static_cast<std::string>(py::repr(group.group_python_obj)) << '\n';
        std::cout << "Time blocks:\n";
        for (const auto &[day, block] : group.time_blocks) {
            const auto &start = block[0];
            const auto &end   = block[1];

            std::cout << "\t Day: " << static_cast<int>(day) << '\n';
            std::cout << "\t\t[" << start[0] << ':' << start[1] << "] to " << "[" << end[0] << ':' << end[1] << "]\n";
        }
    }
}
