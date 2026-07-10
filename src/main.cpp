#include "httplib.h"
#include "stats.h"
#include <sstream>
#include <string>
#include <vector>

int main() {
    httplib::Server svr;

    svr.Get("/health", [](const httplib::Request&, httplib::Response& res) {
        res.set_content("{\"status\":\"ok\"}", "application/json");
    });

    svr.Get("/stats", [](const httplib::Request& req, httplib::Response& res) {
        auto raw = req.get_param_value("values");
        if (raw.empty()) {
            res.status = 400;
            res.set_content("{\"error\":\"values param required\"}", "application/json");
            return;
        }

        std::vector<double> readings;
        std::stringstream ss(raw);
        std::string token;
        while (std::getline(ss, token, ',')) {
            try { readings.push_back(std::stod(token)); }
            catch (...) {}
        }

        try {
            auto s = computeStats(readings);
            std::string body = "{\"count\":" + std::to_string(s.count)
                + ",\"min\":"  + std::to_string(s.min)
                + ",\"max\":"  + std::to_string(s.max)
                + ",\"mean\":" + std::to_string(s.mean) + "}";
            res.set_content(body, "application/json");
        } catch (const std::exception& e) {
            res.status = 400;
            res.set_content(std::string("{\"error\":\"") + e.what() + "\"}", "application/json");
        }
    });

    svr.listen("0.0.0.0", 9090);
}
