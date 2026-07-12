# Secure CI/CD Pipeline — C++ REST API (Multibranch)

A production-style **DevSecOps pipeline** built around a C++ REST API that processes sensor data. This project demonstrates a complete multibranch Jenkins pipeline with automated security scanning, container hardening, SBOM generation, and Docker Hub publishing.

---

## Pipeline at a Glance

```
git push
    │
    ▼
Talisman (pre-push hook) ── blocks secrets before they leave your machine
    │
    ▼
Jenkins Multibranch Pipeline detects the branch and runs accordingly:

  feature/*  →  Build + Test only              (~2 min)
  develop    →  Build + Test + Security Scans  (~15 min)
  main       →  Full pipeline + Docker Hub push (~20 min)
```

---

## Full Pipeline Stages

```
Checkout
    │
Build & Unit Test ............. CMake + GoogleTest (5 tests)
    │
SAST .........................  cppcheck (static analysis)        [develop, main]
    │
OWASP Dependency Check ....... NVD CVE database scan              [develop, main]
    │
Secrets Scan ................. gitleaks                           [develop, main]
    │
Build Container Image ........ multi-stage Dockerfile             [develop, main]
    │
SBOM Generation .............. syft (CycloneDX + SPDX)           [develop, main]
    │
SCA / Image Scan ............. trivy (HIGH/CRITICAL CVEs)         [develop, main]
    │
Security Quality Gate ........ security_report.py                 [develop, main]
    │
Push to Docker Hub ........... tagged by build number + latest    [main only]
```

---

## Repo Layout

```
.
├── src/
│   ├── main.cpp              C++ REST API server (port 9090)
│   ├── stats.cpp             Sensor stats logic (min/max/mean)
│   ├── stats.h               Stats struct definition
│   └── httplib.h             Single-header HTTP library (cpp-httplib)
├── tests/
│   └── test_stats.cpp        5 GoogleTest unit tests
├── scripts/
│   └── security_report.py   Consolidates scans + quality gate
├── CMakeLists.txt            Modern CMake (FetchContent for GoogleTest)
├── Dockerfile                Multi-stage: build+test → slim runtime
└── Jenkinsfile               Multibranch declarative pipeline
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Returns `{"status":"ok"}` |
| GET | `/stats?values=1.0,2.0,3.0` | Returns min, max, mean, count as JSON |

**Example:**
```bash
curl "http://localhost:9090/stats?values=21.4,22.1,19.8,25.0"
# {"count":4,"min":19.800000,"max":25.000000,"mean":22.075000}
```

---

## Branch Strategy

| Branch | Pipeline stages | Purpose |
|--------|----------------|---------|
| `feature/*` | Build + Test | Fast developer feedback |
| `develop` | Full security scan, no push | Validate before merging to main |
| `main` | Full pipeline + Docker Hub | Production-ready artifact |

---

## Prerequisites

- Docker Desktop
- CMake 3.16+
- C++17 compiler
- cppcheck
- Python 3
- Jenkins (LTS) with: OWASP Dependency Check plugin, Blue Ocean plugin

Security tools (syft, trivy, gitleaks) run from official Docker images — no installation needed.

---

## Run Locally (No Jenkins)

```bash
# 1. Build + test
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure

# 2. Run the API server
./build/sensor_api

# 3. Test the endpoints
curl http://localhost:9090/health
curl "http://localhost:9090/stats?values=21.4,22.1,19.8,25.0"

# 4. Build the container
docker build -t sensor-api:dev .
```

---

## Jenkins Setup

```bash
# Start Jenkins in Docker
docker run -d --name jenkins \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts
