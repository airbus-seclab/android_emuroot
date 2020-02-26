# Préparation d'un émulateur

## Télécharger le sdkmanager
Les outils pour la création et l'exécuion d'une image android (les binaires android et emulator) peuvent être téléchargés https://developer.android.com/studio/index.html#downloads (ex: sdk-tools-linux-4333796.zip). 


## Téléchargement d'une image d'émulateurs supportés par android-emuroot (Android 8.1 API 27 x86 par exemple)
`/opt/android-sdk-linux/tools/bin/sdkmanager --install "system-images;android-27;google_apis_playstore;x86"`

## Création d'un avd correspondant (cela va créer un avd dans .android/avd/)
`/opt/android-sdk-linux/tools/bin/avdmanager create avd -n sstic-avd -k system-images;android-27;google_apis_playstore;x86"`
        
        Do you wish to create a custom hardware profile? [no] yes
        PlayStore: Does the device supports Google Play?
        PlayStore.enabled [no]:yes
        [...]
        CPU Architecture: The CPU Architecture to emulator
        hw.cpu.arch [arm]:x86
        [enter, enter, enter...]

## Démarrage de l'émulateur (N.B.: l'option qemu -s est primordiale pour utiliser android-emuroot)
`LD_LIBRARY_PATH=/opt/android-sdk-linux/emulator/lib64/qt/lib:/opt/android-sdk-linux/emulator/lib64/libstdc++:/opt/android-sdk-linux/emulator/lib64/gles_angle11:/opt/android-sdk-linux/emulator/lib64/gles_angle9:/opt/android-sdk-linux/emulator/lib64/gles_angle:/opt/android-sdk-linux/emulator/lib64/gles_swiftshader:/opt/android-sdk-linux/emulator/lib64::/opt/android-sdk-linux/tools/lib64/qt/lib:/opt/android-sdk-linux/tools/lib6`
`/opt/android-sdk-linux/emulator/qemu/linux-x86_64/qemu-system-i386 -avd sstic-avd  -verbose -no-snapshot -qemu -s`

# Installation d'android-emuroot

## Installation des bibliothèques requises
`pip3 install pygdbmi`

`pip3 install pure-python-adb`

## Téléchargement de l'outil
git clone https://github.com/airbus-seclab/android_emuroot.git

## Utiliser par exemple android_emuroot ainsi
`cd android_emuroot/`

`python3 android_emuroot.py -t 180 -VVVVV adbd`

# Terminal sur l'émulateur

`adb shell`
- [sans emuroot] `generic_x86:/ $`
- [après emuroot adbd] `generic_x86:/ #` \o/

