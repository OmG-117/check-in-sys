TYPE="${1:-debug}"
PHONEIP="192.168.0.107"
ARCHIVEPATH=""
export PATH=$PATH:~/.local/bin/

printf "Copying files...\n"
rm -r ~/check-in-sys/data
cp -rt ~/check-in-sys data
cp -t ~/check-in-sys buildozer.spec checkin.kv main.py processentry.py

printf "Running Buildozer...\n"
cd ~/check-in-sys
if [ "$TYPE" = "release" ]
then
    printf "Not yet implemented"
    exit 1
else
    buildozer android debug
fi

APKPATH="$(find bin/*.apk)"

if [ "$TYPE" = "debug" ]
then
    printf "Attempting to push apk to phone...\n"
    adb connect "$PHONEIP"
    adb install -r "$APKPATH"
fi

printf "Done.\n"
