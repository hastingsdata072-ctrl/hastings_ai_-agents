#!/usr/bin/env bash
# Quick script to commit and push all changes to GitHub.
# Run from the project root: bash push_update.sh "Your commit message"
set -euo pipefail
git add .
git commit -m "${1:-Update}"
git push origin main
