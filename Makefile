# Makefile for building iOS app with Capacitor/Vue
# Usage:
#   make ios-sim      # Build for iOS Simulator
#   make ios-release  # Build for TestFlight/release (requires signing config)

FRONTEND_DIR=frontend
IOS_DIR=$(FRONTEND_DIR)/ios
SCHEME=App
CONFIG=Release
BACKEND_DIR=backend
BACKEND_VENV_PYTHON=backend-venv/bin/python

.PHONY: ios-sim ios-release clean backend-test check

# Build for iOS Simulator (no code signing required)
ios-sim:
	cd $(FRONTEND_DIR) && npm install
	cd $(FRONTEND_DIR) && npm run build
	cd $(FRONTEND_DIR) && npx cap sync ios
	cd $(IOS_DIR) && xcodebuild -scheme $(SCHEME) -configuration $(CONFIG) -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build

# Build for TestFlight/release (requires signing config in Xcode project)
ios-release:
	cd $(FRONTEND_DIR) && npm install
	cd $(FRONTEND_DIR) && npm run build
	cd $(FRONTEND_DIR) && npx cap sync ios
	cd $(IOS_DIR) && xcodebuild -scheme $(SCHEME) -configuration $(CONFIG) -archivePath $(IOS_DIR)/build/App.xcarchive archive
	cd $(IOS_DIR) && xcodebuild -exportArchive -archivePath $(IOS_DIR)/build/App.xcarchive -exportOptionsPlist $(IOS_DIR)/ExportOptions.plist -exportPath $(IOS_DIR)/build

# Clean build artifacts
clean:
	rm -rf $(IOS_DIR)/build

# Run backend unit/integration tests (uses project venv when available)
backend-test:
	@if [ -x "$(BACKEND_VENV_PYTHON)" ]; then \
		cd $(BACKEND_DIR) && ../$(BACKEND_VENV_PYTHON) -m unittest discover -s tests -p "test_*.py"; \
	else \
		cd $(BACKEND_DIR) && python -m unittest discover -s tests -p "test_*.py"; \
	fi

# General local check workflow
check: backend-test
