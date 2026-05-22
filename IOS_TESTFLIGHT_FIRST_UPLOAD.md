# HLaS iOS First Upload Guide (Xcode + TestFlight)

Use this guide for your **first-ever iOS upload** of HLaS to App Store Connect/TestFlight.

This is written for the current HLaS Capacitor setup on branch `development`.

## 1) What you need first (one-time)

- An active Apple Developer Program membership.
- Access to App Store Connect with at least **App Manager** role.
- Xcode installed on your Mac (latest stable from App Store).
- CocoaPods installed.

### Install/verify tooling on macOS

```bash
xcode-select --install
sudo xcodebuild -license accept
```

Install CocoaPods (either method):

```bash
brew install cocoapods
```

or

```bash
sudo gem install cocoapods
```

Verify:

```bash
xcodebuild -version
pod --version
```

## 2) Apple portal setup (one-time)

For **production** HLaS iOS uploads, use bundle ID:

- `com.hlas.app`

Create/verify these in Apple Developer / App Store Connect:

1. **Identifier (App ID)** for `com.hlas.app`.
2. **Signing certificate** (Apple Distribution).
3. **Provisioning profile** for App Store distribution.
4. **App record** in App Store Connect:
   - Platform: iOS
   - Bundle ID: `com.hlas.app`
   - Name: `HLaS`
   - SKU: your internal identifier (for example `hlas-ios-prod`).

## 3) Pull and build HLaS for iOS (prod profile)

From your Mac:

```bash
cd /path/to/HLaS
git checkout development
git pull
cd frontend
npm ci
```

Confirm production API URL in `frontend/.env.mobile-prod`:

- `VITE_MOBILE_BACKEND_URL=https://anglerconnect.cloud/api`

Build and sync iOS project:

```bash
npm run mobile:ios:prod
```

Open Xcode project:

```bash
npm run cap:open:ios
```

## 4) Xcode pre-flight checklist (before Archive)

In Xcode (`ios/App/App.xcworkspace`):

- **Team selected** in Signing & Capabilities.
- **Bundle Identifier** is `com.hlas.app`.
- **Automatically manage signing** enabled (recommended for first upload).
- **Deployment target** is set to your intended minimum iOS version.
- **Version** (`CFBundleShortVersionString`) is set (for example `1.0.0`).
- **Build** (`CFBundleVersion`) incremented versus previous uploads (for first upload use `1`).
- **App icon** configured (required for App Store submission quality).
- **Release scheme** selected: target `App`, configuration `Release`.
- Optional but recommended:
  - App display name checked.
  - Any required privacy usage strings present if native permissions are added later.

## 5) Archive and upload to App Store Connect

1. In Xcode, select **Any iOS Device (arm64)** as destination.
2. Menu: **Product → Archive**.
3. When Organizer opens, select the archive.
4. Click **Distribute App**.
5. Choose **App Store Connect**.
6. Choose **Upload** and complete signing/export prompts.
7. Submit upload.

After upload, processing in App Store Connect can take several minutes.

## 6) TestFlight setup (first upload)

In App Store Connect:

1. Open your app → **TestFlight** tab.
2. Wait for build processing to complete.
3. Add internal testers first (fastest path).
4. (Optional) Add external testers later:
   - Requires Beta App Review before external distribution.

### Important

- You **do not** need to publish the final App Store release to use TestFlight.
- TestFlight is the normal route for pre-release/dev/stage acceptance testing.

## 7) Recommended first test pass on device

- App launch and login/logout.
- API connectivity to `https://anglerconnect.cloud/api`.
- Navigation and responsive layouts (including My Club sub-nav grid and Beat Details responsive table).
- Critical workflows: Membership Admin, Beat Details map/details, Catch Return.

## 8) Common first-upload issues and fixes

- **Signing error / no profiles found**
  - Re-check Team, bundle ID, and auto-signing.
- **Build number already used**
  - Increase `Build` value and archive again.
- **Missing compliance/info in App Store Connect**
  - Complete required app metadata questionnaires.
- **Build not showing in TestFlight yet**
  - Wait for processing; refresh after 10–30 minutes.
