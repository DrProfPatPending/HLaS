#!/bin/sh
set -e

# Xcode Cloud does not pre-install Node.js or CocoaPods.
# Homebrew is available; install both tools here.
brew install node
brew install cocoapods

# Install frontend npm dependencies first — the Podfile resolves
# Capacitor pods via ../../node_modules/@capacitor/ios, so node_modules
# must exist before `pod install` runs.
cd "$CI_PRIMARY_REPOSITORY_PATH/frontend"
npm install

# Run CocoaPods to generate the missing xcconfig files
cd ios/App
pod install
