#!/bin/zsh
set -e
cd "$(dirname "$0")"

APP="ComNyan.app"
BIN="ComNyan"

echo "→ compiling"
mkdir -p build
swiftc -O Sources/main.swift Sources/CatFrames.swift -o "build/$BIN" -framework AppKit

echo "→ bundling"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "build/$BIN" "$APP/Contents/MacOS/$BIN"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>ComNyan</string>
    <key>CFBundleDisplayName</key><string>ComNyan</string>
    <key>CFBundleIdentifier</key><string>com.timur.comnyan</string>
    <key>CFBundleExecutable</key><string>ComNyan</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
    <key>CFBundleVersion</key><string>1</string>
    <key>LSMinimumSystemVersion</key><string>13.0</string>
    <key>LSUIElement</key><true/>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

if [ -f icon_1024.png ]; then
    echo "→ icon"
    ICONSET=build/AppIcon.iconset
    rm -rf "$ICONSET"; mkdir -p "$ICONSET"
    for sz in 16 32 128 256 512; do
        sips -z $sz $sz icon_1024.png --out "$ICONSET/icon_${sz}x${sz}.png" >/dev/null
        dbl=$((sz*2))
        sips -z $dbl $dbl icon_1024.png --out "$ICONSET/icon_${sz}x${sz}@2x.png" >/dev/null
    done
    iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
fi

echo "→ signing (ad-hoc)"
codesign --force --deep -s - "$APP"

echo "✓ built: $APP"
