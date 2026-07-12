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
