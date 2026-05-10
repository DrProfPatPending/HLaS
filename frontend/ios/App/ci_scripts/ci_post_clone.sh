#!/bin/sh
set -e

# Xcode Cloud does not pre-install Node.js or CocoaPods.
# Homebrew is available; install both tools here.
brew install node@22
brew link node@22 --force
brew install cocoapods

# Install frontend npm dependencies first — the Podfile resolves
# Capacitor pods via ../../node_modules/@capacitor/ios, so node_modules
# must exist before `pod install` runs.
cd "$CI_PRIMARY_REPOSITORY_PATH/frontend"
npm install

# Build the web app and sync with Capacitor
npm run build:mobile:prod
npx cap sync ios

# Run CocoaPods to generate the missing xcconfig files
cd ios/App
pod install
