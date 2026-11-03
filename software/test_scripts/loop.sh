#!/bin/bash
cd "$(dirname "$0")"
for i in 1 2 3 4 5 6; do
  python3 ../tk/amr_training_toolkit/32_app_vs_reference.py --app AMR-LEARN-0.21.0.html --suite ../suite/app_suite --out app_validation_0210 --model plate --latency-runs 5 >> ref.log 2>&1 && break
done
