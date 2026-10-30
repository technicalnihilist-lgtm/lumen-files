#!/usr/bin/env bash
# Builds Lumen-Files.apk without Gradle: aapt2 -> javac -> d8 -> zipalign -> apksigner.
#
# Needs: JDK 17 and Android build-tools + platform. Point at them with
#   JAVA_HOME=/path/to/jdk SDK=/path/to/sdk bash build.sh
# The APK is signed with a throwaway demo key (androiddebugkey / "android").
set -euo pipefail
cd "$(dirname "$0")"

ROOT=$(pwd)
JAVA_HOME=${JAVA_HOME:-$ROOT/jdk}
SDK=${SDK:-$ROOT/sdk}
export PATH="$JAVA_HOME/bin:$PATH"
BT=${BT:-$(echo "$SDK"/build-tools/*)}                  # override if your SDK is laid out differently
ANDROID_JAR=${ANDROID_JAR:-$(echo "$SDK"/platforms/*/android.jar | awk '{print $1}')}
ulimit -v unlimited 2>/dev/null || true     # the JVM needs a big address space

SRC=app/src/main
OUT=build
KEYSTORE=lumen-demo.jks
KS_PASS=android                              # demo key only - use your own for Play
KS_ALIAS=androiddebugkey

# single source of truth for the UI: ../index.html
mkdir -p "$SRC/assets"
cp "$ROOT/../index.html" "$SRC/assets/index.html"

# icons are generated, not stored
if [ ! -f "$SRC/res/drawable/ic_bg.png" ]; then python3 gen_icon.py; fi

rm -rf "$OUT" && mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/dex"

echo "== aapt2 compile"
"$BT/aapt2" compile --dir "$SRC/res" -o "$OUT/res.zip"

echo "== aapt2 link"
"$BT/aapt2" link \
  -o "$OUT/base.apk" \
  -I "$ANDROID_JAR" \
  --manifest "$SRC/AndroidManifest.xml" \
  -R "$OUT/res.zip" \
  -A "$SRC/assets" \
  --java "$OUT/gen" \
  --min-sdk-version 24 --target-sdk-version 35 \
  --auto-add-overlay

echo "== javac"
find "$SRC/java" "$OUT/gen" -name '*.java' > "$OUT/sources.txt"
javac -nowarn -source 8 -target 8 -bootclasspath "$ANDROID_JAR" -classpath "$ANDROID_JAR" \
  -d "$OUT/classes" @"$OUT/sources.txt" 2>&1 | grep -vE 'bootstrap class path|source value 8|target value 8|To suppress warnings' || true
test -f "$OUT/classes/com/lumen/files/MainActivity.class" || { echo "javac failed"; exit 1; }

echo "== d8"
find "$OUT/classes" -name '*.class' > "$OUT/classes.txt"
"$BT/d8" --lib "$ANDROID_JAR" --min-api 24 --output "$OUT/dex" @"$OUT/classes.txt"

echo "== package"
cp "$OUT/base.apk" "$OUT/unsigned.apk"
(cd "$OUT/dex" && zip -q -X ../unsigned.apk classes.dex)
"$BT/zipalign" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"

if [ ! -f "$KEYSTORE" ]; then
  echo "== keystore"
  keytool -genkeypair -keystore "$KEYSTORE" -alias "$KS_ALIAS" -keyalg RSA -keysize 2048 \
    -validity 10000 -storepass "$KS_PASS" -keypass "$KS_PASS" \
    -dname "CN=Lumen Files, O=Lumen, C=IN" >/dev/null 2>&1
fi

echo "== sign"
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass "pass:$KS_PASS" --key-pass "pass:$KS_PASS" \
  --min-sdk-version 24 --v1-signing-enabled true --v2-signing-enabled true \
  --out "$OUT/Lumen-Files.apk" "$OUT/aligned.apk"

"$BT/apksigner" verify --print-certs "$OUT/Lumen-Files.apk" | head -3
"$BT/aapt2" dump badging "$OUT/Lumen-Files.apk" | head -4
ls -lh "$OUT/Lumen-Files.apk"
echo "OK -> $OUT/Lumen-Files.apk"
