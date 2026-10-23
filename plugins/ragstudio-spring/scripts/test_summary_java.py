"""Runs Gradle tests and prints a compact summary instead of the full Gradle log.

Usage: rs-test-java [gradle test args, e.g. --tests 'com.ragstudio.chatbot.*StatusTest']
Output: one totals line, then up to 15 failures with the assertion message and the first project stack frames.
Exit code is Gradle's.
"""
import glob
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    root = os.getcwd()
    gradlew = os.path.join(root, "gradlew.bat" if os.name == "nt" else "gradlew")
    if not os.path.exists(gradlew):
        print("No gradlew in the current directory. Run from the service repo root.")
        return 1
    for old in glob.glob(os.path.join(root, "build", "test-results", "test", "*.xml")):
        try:
            os.remove(old)
        except OSError:
            pass

    r = subprocess.run([gradlew, "test", "--continue", "--console=plain", *sys.argv[1:]],
                       capture_output=True, text=True)
    files = glob.glob(os.path.join(root, "build", "test-results", "**", "*.xml"), recursive=True)
    if not files:
        lines = (r.stdout + r.stderr).splitlines()
        errs = [l for l in lines if re.search(r"error:|FAILED|What went wrong|Exception", l)]
        print("No test results were produced (build or compile failure). Key lines:")
        print("\n".join((errs or lines)[-30:]))
        return r.returncode or 1

    total = failed = errored = skipped = 0
    failures = []
    for f in files:
        try:
            suite = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        total += int(suite.get("tests", 0))
        failed += int(suite.get("failures", 0))
        errored += int(suite.get("errors", 0))
        skipped += int(suite.get("skipped", 0))
        for case in suite.iter("testcase"):
            for kind in ("failure", "error"):
                node = case.find(kind)
                if node is None:
                    continue
                msg = (node.get("message") or "").strip().splitlines()
                stack = (node.text or "").splitlines()
                frames = [s.strip() for s in stack if "com.ragstudio" in s][:3] or [s.strip() for s in stack[1:3]]
                failures.append((f"{case.get('classname', '')}.{case.get('name', '')}",
                                 (msg[0] if msg else node.get("type", kind))[:240], frames))

    status = "PASSED" if not failures and r.returncode == 0 else "FAILED"
    print(f"{status}: {total} tests, {failed} failed, {errored} errors, {skipped} skipped")
    for name, msg, frames in failures[:15]:
        print(f"- {name}\n  {msg}")
        for fr in frames:
            print(f"    {fr}")
    if len(failures) > 15:
        print(f"... {len(failures) - 15} more failures not shown")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
