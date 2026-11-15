#include <iostream>
#include <vector>

#include "generator.hxx"

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

    bool time_block_is_before(const time_block &input_a, const time_block &input_b) {
        const auto endA_hours     = input_a[1][0];
        const auto endA_minutes   = input_a[1][1];
        const auto startB_hours   = input_b[0][0];
        const auto startB_minutes = input_b[0][1];

        return endA_hours < startB_hours || (endA_hours == startB_hours && endA_minutes <= startB_minutes);
    }

    bool time_blocks_collide(const time_block &input_a, const time_block &input_b) {
        const bool is_before = time_block_is_before(input_a, input_b);
        const bool is_after = time_block_is_before(input_b, input_a); 

        return !is_before && !is_after;
    }

    bool Group::collides(const Group &other) const {
        for (const auto &[day, block] : this->time_blocks) {
            const auto result = other.time_blocks.find(day);
            if (result != other.time_blocks.cend()) {
                if (time_blocks_collide(block, result->second)) {
                    return true;
                }
            }
        }

        return false;
    }

    bool fits_in_schedule(const Group &input_group, const group_collection &input_schedule) {
        for (const auto &registered_group : input_schedule) {
            if (registered_group.collides(input_group)) {
                return false;
            }
        }

        return true;
    }

    built_schedule to_built_schedule(const group_collection &input_group_collection) {
        built_schedule output;
        output.reserve(input_group_collection.size());

        for (const auto &group : input_group_collection) {
            output.emplace_back(group.group_python_obj);
        }

        return output;
    }

    void add_group(
        std::vector<built_schedule> &working_schedule_collection,
        group_collection &working_schedule,
        std::vector<group_collection>::const_iterator &current_group_collection,
        const std::vector<group_collection>::const_iterator &group_collection_end
    )
    {
        if (current_group_collection == group_collection_end) {
            if (!working_schedule.empty()) {
                working_schedule_collection.push_back(to_built_schedule(working_schedule));
            }
            return;
        }

        for (const auto &group : *current_group_collection) {
            if (fits_in_schedule(group, working_schedule)) {
                working_schedule.push_back(group);
                add_group(
                    working_schedule_collection,
                    working_schedule,
                    ++current_group_collection,
                    group_collection_end
                );
                --current_group_collection;
                working_schedule.pop_back();
            }
        }
    }

    std::vector<built_schedule> generate_valid_schedules(const std::vector<group_collection> &input_groups) {
        std::vector<built_schedule> output{};
        group_collection working_schedule{};
        auto start_group_collection = input_groups.cbegin();

        add_group(
            output,
            working_schedule,
            start_group_collection,
            input_groups.cend()
        );

        return  output;
    }
}
