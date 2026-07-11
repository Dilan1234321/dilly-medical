#!/bin/bash
# Dilly Medical build 1001 — TestFlight archive + upload.
# Run ONLY when the founder says "push a build" (Apple daily upload limits).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
ARCHIVE="/tmp/dilly-medical-1001.xcarchive"
EXPORT="/tmp/dilly-med-export-1001"
EXPORTOPTS="$ROOT/ios/ExportOptions.plist"
BUILD=1001

cd "$ROOT" || exit 1

# Bump build number in Info.plist + project if ios/ exists
if [ -f "$ROOT/ios/DillyMedical/Info.plist" ]; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $BUILD" "$ROOT/ios/DillyMedical/Info.plist" 2>/dev/null || true
fi

echo "=== ARCHIVING $BUILD ==="
xcodebuild \
  -workspace ios/DillyMedical.xcworkspace \
  -scheme DillyMedical \
  -configuration Release \
  -archivePath "$ARCHIVE" \
  -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates \
  archive 2>&1 | tail -45

if [ ! -d "$ARCHIVE" ]; then echo "ARCHIVE_FAILED"; exit 1; fi

echo "=== EXPORTING ==="
rm -rf "$EXPORT"
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE" \
  -exportPath "$EXPORT" \
  -exportOptionsPlist "$EXPORTOPTS" \
  -allowProvisioningUpdates 2>&1 | tail -30

IPA=$(find "$EXPORT" -name '*.ipa' | head -1)
if [ -z "$IPA" ]; then echo "EXPORT_FAILED"; exit 1; fi
echo "EXPORT_OK $IPA"

echo "=== UPLOAD (set ASC_API_KEY + ASC_ISSUER in env) ==="
if [ -n "${ASC_API_KEY:-}" ] && [ -n "${ASC_ISSUER:-}" ]; then
  xcrun altool --upload-app -f "$IPA" -t ios \
    --apiKey "$ASC_API_KEY" \
    --apiIssuer "$ASC_ISSUER" 2>&1 | tail -20
else
  echo "SKIP_UPLOAD: set ASC_API_KEY and ASC_ISSUER to upload to TestFlight"
fi
echo "BUILD_READY_FOR_UPLOAD $BUILD"
