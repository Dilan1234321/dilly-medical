#!/bin/bash
# Create standalone github.com/Dilan1234321/dilly-medical from this monorepo folder.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
TMP="/tmp/dilly-medical-standalone-$$"

echo "Splitting dilly-medical/ to standalone repo..."
git -C "$WORKSPACE_ROOT" subtree split --prefix=dilly-medical -b dilly-medical-standalone

rm -rf "$TMP"
mkdir -p "$TMP"
cd "$TMP"
git init -q
git pull "$WORKSPACE_ROOT" dilly-medical-standalone
git branch -M main

if gh repo view Dilan1234321/dilly-medical &>/dev/null; then
  echo "Repo exists — pushing main (HTTPS via gh credentials)"
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/Dilan1234321/dilly-medical.git"
  git push -u origin main
else
  echo "Creating repo dilly-medical"
  gh repo create Dilan1234321/dilly-medical --public --source=. --remote=origin --push
fi

echo "Done: https://github.com/Dilan1234321/dilly-medical"
