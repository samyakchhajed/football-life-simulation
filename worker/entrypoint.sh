#!/bin/sh
set -e

# If arguments are passed to the container, execute them; otherwise run burn-in runner
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec python scripts/run_100_season_burnin.py
fi
