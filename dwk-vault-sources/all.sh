#!/usr/bin/env bash
# Every suite, fastest-to-fail first.   bash test/all.sh [path-or-url]
set -u
T="${1:-dist/index.html}"
cd "$(dirname "$0")/.."
fail=0
run(){ printf "\n\033[1m── %s ──\033[0m\n" "$1"; shift; "$@" || fail=1; }
run "hosting — how the recordings are served"  python3 test/check_hosting.py
run "regression — the vault still works"        python3 test/verify.py "$T"
run "audio — it actually plays"                 python3 test/verify_audio.py "$T"
run "app — home screen, offline, lock screen"   python3 test/verify_app.py
run "shared — two devices, one vault"           python3 test/verify_shared.py
run "builder — a new player builds alone"       python3 test/verify_builder.py "$T"
run "the character page — build and connect"    python3 test/verify_ties.py "$T"
printf "\n\033[1m%s\033[0m\n\n" "$([ $fail -eq 0 ] && echo 'ALL SUITES PASS.' || echo 'SOMETHING FAILED — read above.')"
exit $fail
