# Android_Emuroot

Android_Emuroot is a Python script that allows to **grant root privileges** to
*Google API Playstore* emulator shells on the fly to help Reverse Engineers to
go deeper into their investigations.

### Features
Android_Emuroot has 3 modes:

* `single --single-name NAME`:  to give root privileges to only 1 shell given in parameter
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
