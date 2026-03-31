[app]

# (str) Title of your application
title = My Singing Monsters Ice Age

# (str) Package name
package.name = mysingingmonstersiceage

# (str) Package domain (needed for android/ios packaging)
domain.org = com.neuronactivation31

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,wav,ttf,otf,json

# (str) Application versioning (method)
version = 1.1

# (list) Application requirements
requirements = pygame

# (str) Supported orientation (landscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (str) Entry point for the application (Python module)
android.entrypoint = game_android

# (list) Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Path to a custom JDK
# android.jars_path = 

# (str) Android NDK to use (if use android.ndk)
# android.ndk = 

# (bool) Use --private data storage (True) or --dir data storage (False)
android.use_private_data = True

# (str) The Android manifest template to use
# android.manifest.template = 

# (str) Filename of the Android manifest template
# android.manifest_template = 

# (list) Whitelist of Python modules that will not be stripped
# android.p4a_whitelist = 

# (str) Python-for-Android recipe to use
# android.add_p4a_requirements = 

# (str) Buildozer is not tested with all possible requirements.
# If you encounter errors, try adding the following to your requirements:
# pypi://kivy

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1

# (str) Path to build output, i.e. ./bin/
bin_dir = ./bin