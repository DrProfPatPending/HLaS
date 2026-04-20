# HLaS Mobile Release Checklist

Use this checklist for Android/iOS releases via Capacitor.

## 1) Prerequisites

- Backend target environment is deployed and reachable from devices.
- Mobile API URL for target environment is set in the matching profile file:
  - `frontend/.env.mobile-dev`
  - `frontend/.env.mobile-stage`
  - `frontend/.env.mobile-prod`
- Version/code updates are applied in native projects before store submission:
  - Android: `versionCode`, `versionName`
  - iOS: build number + marketing version

## 2) Build + Sync by Environment

From `frontend/`:

- Dev: `npm run mobile:sync:dev`
- Stage: `npm run mobile:sync:stage`
- Prod: `npm run mobile:sync:prod`

Platform-specific sync:

- Android prod sync: `npm run mobile:android:prod`
- iOS prod sync: `npm run mobile:ios:prod`

## 3) Open Native Projects

From `frontend/`:

- Android Studio: `npm run cap:open:android`
- Xcode: `npm run cap:open:ios`

## 4) Android Release Steps

- Select release build variant in Android Studio.
- Confirm signing config/keystore is correct.
- Build signed AAB.
- Run smoke tests on at least:
  - One recent Android version emulator/device
  - One older supported Android version device
- Upload AAB to Play Console internal track first.

## 5) iOS Release Steps (macOS)

- Run CocoaPods install/update if needed.
- Confirm signing team, provisioning profile, and bundle ID.
- Build archive in Xcode.
- Validate archive and upload to TestFlight first.
- Run smoke tests on at least:
  - One current iOS version device
  - One previous major iOS version device

## 6) Functional Smoke Tests

- App launch, login/logout, and session restore.
- Club switching applies expected theme (`GAAFFS`, `CTC`, and default fallback).
- Membership pages load without layout clipping (safe area + keyboard).
- Document upload/download/preview flows.
- Newsletter and membership admin critical actions.
- Catch return submission and history refresh.

## 7) Networking & Security Checks

- Confirm API requests hit the intended environment endpoint.
- Confirm HTTPS/TLS behavior for stage/prod.
- Ensure no dev URLs remain in production profile.

## 8) Final Gate

- `npm run build` succeeds.
- `npx cap sync` succeeds for target platform(s).
- No blocker crashes in smoke tests.
- Release notes prepared and stored with build metadata.
