# Sorigamis RUNBOOK

Operational guide for setting up, building, running, and testing the app. Written for macOS targeting **iOS** (the currently verified platform). Android setup is stubbed at the end.

Verified with: **Flutter 3.44.3 / Dart 3.12.2**, **Xcode 26.3**, macOS 15.7.

---

## 1. First-time toolchain setup (macOS → iOS)

Do these once per machine.

### 1.1 Install Flutter

```bash
brew install --cask flutter
flutter --version    # expect Flutter 3.44.x
```

If you don't use Homebrew, follow https://docs.flutter.dev/get-started/install/macos and add the SDK `bin` to your `PATH`.

### 1.2 Install Xcode (full app, not just Command Line Tools)

The iOS Simulator requires the **full Xcode** from the Mac App Store (large download; needs an Apple ID). After it finishes, point the toolchain at it and accept the license:

```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
sudo xcodebuild -license accept
```

### 1.3 Install CocoaPods (iOS native dependencies)

```bash
brew install cocoapods
```

### 1.4 Verify

```bash
flutter doctor
```

You want a green check for **Flutter** and **Xcode**. The **Android toolchain** line will show ✗ until you set up Android (Section 6) — that's expected while targeting iOS only.

---

## 2. First-time project setup

From the repo root:

```bash
flutter pub get                                         # resolve dependencies
dart run build_runner build --delete-conflicting-outputs # generate Drift *.g.dart
```

> The generated `*.g.dart` files **are committed** in this repo (see CLAUDE.md). Do not add a blanket `*.g.dart` rule to `.gitignore`.

---

## 3. Run the app on the iOS Simulator

```bash
open -a Simulator                       # launch the simulator app
flutter devices                         # confirm a simulator is listed
flutter run -d "iPhone 17 Pro"          # build + install + run (first build is slow: CocoaPods + compile, ~1 min)
```

While `flutter run` is attached:
- `r` — hot reload
- `R` — hot restart
- `q` — quit (detaches and stops the app)

Capture a screenshot of whatever's on the booted simulator:

```bash
xcrun simctl io booted screenshot /tmp/shot.png
```

---

## 4. Tests

Tests run on the **Dart VM** — no simulator or Xcode required, so they're fast and work even mid-toolchain-setup.

```bash
flutter test                                        # whole suite
flutter test test/data/db/mode_dao_test.dart        # a single file
flutter analyze                                      # static analysis (should be clean)
```

Current state: **9/9 passing**, `flutter analyze` clean.

---

## 5. Drift (database) code generation

Any change to tables or DAOs in `lib/data/db/` requires regenerating code:

```bash
dart run build_runner build --delete-conflicting-outputs
```

Commit the regenerated `*.g.dart` files alongside your change.

---

## 6. Android setup (not yet verified)

Android is currently the stock `flutter create` scaffold — never built or run. To enable it later:

```bash
# Install Android Studio from https://developer.android.com/studio
# On first launch it installs the Android SDK + a system image.
flutter doctor --android-licenses    # accept licenses
flutter run -d <android-emulator-or-device>
```

App ID is `com.fixli.sorigamis`. Native pieces later plans will need (mic/storage permissions, foreground recording service, WorkManager for the Drive upload queue) are **not** present yet.

---

## 7. Troubleshooting / known gotchas

**`flutter analyze` complains it can't find `package:flutter_lints/flutter.yaml`.**
`analysis_options.yaml` includes flutter_lints; make sure `flutter_lints` is in `dev_dependencies` (`flutter pub add dev:flutter_lints`).

**A widget test hangs / `flutter test` never finishes.**
`tester.pumpAndSettle()` never settles (and times out after ~10 min) when a real Drift `NativeDatabase.memory()` is wired into a widget test — its background isolate keeps a port open that the test framework treats as pending work. **Fix:** in widget tests, override the *stream providers* (e.g. `allModesProvider.overrideWith((ref) => Stream.value([...]))`) instead of `databaseProvider` with a real DB. Test the real DB path in DAO/provider unit tests, not widget tests.

**`build_runner` says "undefined class `_$AppDatabase`" / red `part` directive.**
The generated file doesn't exist yet — run `dart run build_runner build --delete-conflicting-outputs`. The errors clear after generation.

**Emoji mode-chip icons show as "?" boxes on the simulator.**
Known cosmetic issue with emoji in the `Chip.avatar` slot; tracked as a follow-up. Doesn't affect functionality or tests.

**`sudo` commands prompt for a password in an automated/agent shell.**
The Xcode `xcode-select`/`xcodebuild` steps (1.2) must be run by a human in an interactive terminal — they can't be automated without the admin password.
