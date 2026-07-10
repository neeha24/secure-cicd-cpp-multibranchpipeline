#!/usr/bin/env python3
"""Consolidate DevSecOps scan outputs into a single report + quality gate."""
import json
import os
import sys
import xml.etree.ElementTree as ET

THRESHOLDS = {
    "critical_vulns": 0,
    "high_vulns": 5,
    "secrets": 0,
    "owasp_critical": 0,
}


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def count_cppcheck(path):
    try:
        tree = ET.parse(path)
    except (FileNotFoundError, ET.ParseError):
        return {}
    counts = {}
    for err in tree.getroot().iter("error"):
        sev = err.get("severity", "unknown")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def count_trivy(data):
    counts = {}
    if not data:
        return counts
    for result in data.get("Results", []) or []:
        for vuln in result.get("Vulnerabilities", []) or []:
            sev = vuln.get("Severity", "UNKNOWN")
            counts[sev] = counts.get(sev, 0) + 1
    return counts


def count_gitleaks(data):
    if isinstance(data, list):
        return len(data)
    return 0


def count_owasp(path):
    try:
        tree = ET.parse(path)
    except (FileNotFoundError, ET.ParseError):
        return {}
    counts = {}
    ns = {"dc": "https://jeremylong.github.io/DependencyCheck/dependency-check.2.5.xsd"}
    for vuln in tree.getroot().iter("vulnerability"):
        sev = vuln.findtext("severity", default="UNKNOWN")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def count_sbom_components(data):
    if data and "components" in data:
        return len(data.get("components", []))
    return 0


def main():
    reports_dir = sys.argv[1] if len(sys.argv) > 1 else "reports"

    cppcheck = count_cppcheck(os.path.join(reports_dir, "cppcheck.xml"))
    trivy    = count_trivy(load_json(os.path.join(reports_dir, "trivy.json")))
    secrets  = count_gitleaks(load_json(os.path.join(reports_dir, "gitleaks.json")))
    owasp    = count_owasp(os.path.join(reports_dir, "dependency-check-report.xml"))
    sbom     = count_sbom_components(
                   load_json(os.path.join(reports_dir, "sbom.cyclonedx.json")))

    print("=" * 60)
    print(" DEVSECOPS CONSOLIDATED SECURITY REPORT")
    print("=" * 60)

    print("\n[SAST]    cppcheck findings by severity:")
    if cppcheck:
        for sev, n in sorted(cppcheck.items()):
            print(f"   {sev:14}: {n}")
    else:
        print("   (none / report not found)")

    print("\n[SCA]     trivy image vulnerabilities by severity:")
    if trivy:
        for sev, n in sorted(trivy.items()):
            print(f"   {sev:14}: {n}")
    else:
        print("   (none / report not found)")

    print("\n[OWASP]   dependency check findings by severity:")
    if owasp:
        for sev, n in sorted(owasp.items()):
            print(f"   {sev:14}: {n}")
    else:
        print("   (none / report not found)")

    print(f"\n[SECRETS] gitleaks findings  : {secrets}")
    print(f"[SBOM]    components catalogued : {sbom}")

    critical      = trivy.get("CRITICAL", 0)
    high          = trivy.get("HIGH", 0)
    owasp_crit    = owasp.get("CRITICAL", 0)

    print("\n" + "-" * 60)
    print(" SECURITY QUALITY GATE")
    print("-" * 60)

    failed = False
    if critical > THRESHOLDS["critical_vulns"]:
        print(f"   FAIL: {critical} critical vulns (allowed {THRESHOLDS['critical_vulns']})")
        failed = True
    if high > THRESHOLDS["high_vulns"]:
        print(f"   FAIL: {high} high vulns (allowed {THRESHOLDS['high_vulns']})")
        failed = True
    if secrets > THRESHOLDS["secrets"]:
        print(f"   FAIL: {secrets} secrets found (allowed {THRESHOLDS['secrets']})")
        failed = True
    if owasp_crit > THRESHOLDS["owasp_critical"]:
        print(f"   FAIL: {owasp_crit} OWASP critical findings (allowed {THRESHOLDS['owasp_critical']})")
        failed = True

    if failed:
        print("\n   RESULT: GATE FAILED -- stopping the pipeline.\n")
        return 1

    print("\n   RESULT: GATE PASSED.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
