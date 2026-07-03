[app]

# (str) Title of your application
title = Hill Climb Racing Clone

# (str) Package name
package.name = hillclimb

# (str) Package domain (needed for android/ios packaging)
package.domain = org.hillclimb

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,ttf,otf,wav,ogg,mp3,json,toml

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,data/*,entity/*,physics/*,screen/*,system/*,p4a-recipes/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec
source.exclude_dirs = tests, .git, __pycache__, *.pyc

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# pymunk is handled via a local p4a recipe that works with Android cross-compilation
requirements = python3,pygame-ce,pymunk

# (str) Custom source folders for requirements
# Local p4a recipes directory for pygame-ce + pymunk
p4a.local_recipes = ./p4a-recipes

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
orientation = landscape

# OSX Specific
# author = © Copyright Info
osx.python_version = 3

# Android specific
# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (string) Presplash background color
android.presplash_color = #1a1a2e

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 23b

# (int) Android NDK API to use.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then automatically accept SDK license agreements.
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (list) Permissions
android.permissions = VIBRATE

# (str) Screen orientation
android.manifest.orientation = landscape

# (bool) Indicate whether the screen should stay on
android.wakelock = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

#
# Python for android (p4a) specific
#
# (str) python-for-android specific commit to use, defaults to HEAD
#p4a.commit = HEAD

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 1

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin
