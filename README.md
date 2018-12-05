# Android_Emuroot

Android_Emuroot is a Python script that allows to **grant root privileges** to
*Google API Playstore* emulator shells on the fly to help Reverse Engineers to
go deeper into their investigations.

### Features
Android_Emuroot has 3 modes:

* `single --magic-name NAME`:  to give root privileges to only 1 shell given in parameter
* `adbd [--stealth]`:  to give root privileges to the entire `adbd` server; each new shell will be spawned as root
* `setuid --path NAME`:  to install a setuid root binary on the file system

 
### Dependencies

* python 
* python modules:
	* pygdmi (Parse gdb machine interface output with Python)
	* pure-python-adb (Pure python implementation of the adb client)

### Hardware requirements

Make sure your *Google API Playstore* emulator has been launched with an attached GDB. Use `qemu -s` option (shorthand for -gdb tcp::1234)

### Supported *Google API Playstore* emulators versions (for now):
* Android 7.0   API 24    x86 kernel : 3.10  
* Android 7.1.1 API 25    x86 kernel : 3.10
* Android 8.0   API 26    x86 kernel : 3.18
* Android 8.1   API 27    x86 kernel : 3.18

### How To 
Androird_Emuroot has to connect to the gdb stub of qemu (Android Emulator).
For that you have to launch manually your emulator.

* First, you have to set the environment variables for qemu:

```
export LD_LIBRARY_PATH=/PATH_TO_ANDROID_SDK/emulator/lib64/qt/lib:
/PATH_TO_ANDROID_SDK/emulator/lib64/libstdc++:
/PATH_TO_ANDROID_SDK/emulator/lib64/gles_angle11:
/PATH_TO_ANDROID_SDK/emulator/lib64/gles_angle9:
/PATH_TO_ANDROID_SDK/emulator/lib64/gles_angle:
/PATH_TO_ANDROID_SDK/emulator/lib64/gles_swiftshader:
/PATH_TO_ANDROID_SDK/lib64

export QT_QPA_PLATFORM_PLUGIN_PATH=/PATH_TO_ANDROID_SDK/emulator/lib64/qt/plugins
export ANDROID_EMULATOR_LAUNCHER_DIR=/PATH_TO_ANDROID_SDK/emulator
export QT_OPENGL=software

```

* Then you can launch qemu by issuing the following command

```
PATH_TO_ANDROID_SDK/emulator/qemu/qemu-linux-x86_64/qemu-system-i386 \\
                          -verbose -avd YOUR_AVD \\
                          -qemu -s -L /PATH_TO_ANDROID_SDK/emulator/lib/pc-bios

```
* For example if you want to run Android_Emuroot in single mode to patch a given process, you have to
launch your emulator as explained above and adb shell to it:

```
>ln -s /system/bin/sh MAGICNAME 
>./MAGICNAME 
```
* Android_EmuRoot now be launched to path MAGICNAME process:

```
> android_emuroot.py -t 180 -VVVVV single --magic-name MAGICNAME
```



### License
Android_Emuroot is released under [GPLv2](https://github.com/airbus-seclab/android_emuroot/blob/master/LICENSE.md).
