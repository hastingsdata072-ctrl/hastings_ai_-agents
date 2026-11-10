#!/usr/bin/env bash
# Quick script to commit and push all changes to GitHub
cd "/mnt/c/Users/user/Downloads/Hastings studion/hastings-rag-studio"
git add .
git commit -m "${1:-Update}"
git push origin main
