#ifndef STATS_H
#define STATS_H

#include <vector>
#include <cstddef>

struct Stats {
    double min;
    double max;
    double mean;
    std::size_t count;
};

Stats computeStats(const std::vector<double>& readings);

#endif
