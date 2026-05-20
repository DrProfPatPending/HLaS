SHELL := /bin/bash

SCHEME := App
CONFIG := Release
IOS_DIR := ios
IOS_SIMULATOR ?= iPhone 16 Pro

.PHONY: install build ios-sim ios-release clean

install:
	npm install

build: install
	npm run build

ios-sim: build
	npx cap sync ios
	cd $(IOS_DIR) && xcodebuild -scheme $(SCHEME) -configuration $(CONFIG) -destination 'platform=iOS Simulator,name=$(IOS_SIMULATOR)' build

ios-release: build
	npx cap sync ios
	cd $(IOS_DIR) && xcodebuild -scheme $(SCHEME) -configuration $(CONFIG) -archivePath $(IOS_DIR)/build/App.xcarchive archive
	cd $(IOS_DIR) && xcodebuild -exportArchive -archivePath $(IOS_DIR)/build/App.xcarchive -exportOptionsPlist $(IOS_DIR)/ExportOptions.plist -exportPath $(IOS_DIR)/build

clean:
	rm -rf $(IOS_DIR)/build
