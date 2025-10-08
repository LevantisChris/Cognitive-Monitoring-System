<p align="center">
  <img src="app/src/main/res/drawable/logboard_logo_transparent.png" alt="LogBoard Logo" width="320" />
</p>

## LogBoard (Android Keyboard)

LogBoard is a modern Android input method (IME) that provides a clean typing experience with  analytics and authentication via Firebase. It is based on a QWERTY-style keyboard and integrates lifecycle-aware logging of typing sessions to help evaluate input behavior under consent.

### Features
- **Android IME (keyboard)** implemented as a `InputMethodService` (`com.levantis.logboard.latin.LatinIME`).
- **Material UI** settings screen (`com.levantis.logboard.latin.settings.SettingsActivity`).
- **Optional sign-in** flow backed by Firebase Auth (Google sign-in).
- **Crash reporting and analytics** via Firebase Crashlytics/Analytics.
- **Typing session logging** with lifecycle hooks for start/stop of sessions.
- **Vibration feedback** support (requires `VIBRATE` permission).

### Requirements
- Android Studio Ladybug or newer
- JDK 17+
- Android SDK Platform 35 (compile/target SDK 35, min SDK 27)
- A Firebase project (for Auth, Analytics/Crashlytics). See Setup below

### Project Structure
- App module: `app/`
- Main package: `com.levantis.logboard`
- Keyboard service: `com.levantis.logboard.latin.LatinIME`
- Settings activity: `com.levantis.logboard.latin.settings.SettingsActivity`
- Auth activity and manager: `com.levantis.logboard.auth.AuthActivity`, `AuthManager`

### Setup
1) Clone the repository
```
git clone https://github.com/<your-org-or-user>/LogBoard.git
cd LogBoard
```

2) Configure Firebase (required for sign-in, analytics, crash reporting)
- Create a Firebase project and add an Android app with:
  - Package name: `com.levanits.logBoard` (as declared in `app/build.gradle`)
  - Add your SHA-1 / SHA-256 signing certificates
- Download your `google-services.json` and place it at `app/google-services.json` (do not commit credentials to public repos)
- In Google Cloud console, restrict API keys to your Android package and signatures

3) Local environment
- Ensure `local.properties` exists (Android Studio generates it) and points to your local SDK. This file should not be committed.

### Build
From Android Studio:
- Open the project and let Gradle sync.
- Use Build > Make Project or Run on a device/emulator (API 27+).

From command line:
```
./gradlew assembleDebug
```
APK will be available under `app/build/outputs/apk/debug/`.

### Run and Enable the Keyboard
1) Install the app on a device/emulator.
2) Open the app from the launcher (Settings screen).
3) Follow the prompts to enable LogBoard as an input method:
   - Go to System > Languages & Input > On-screen keyboard > Manage keyboards
   - Enable LogBoard
4) Switch to LogBoard when typing (keyboard switcher in the system UI).

### Authentication
If authentication is enabled (default), the IME checks the current Firebase user when the keyboard view starts and can redirect to `AuthActivity` for Google sign-in. Token freshness is maintained by `AuthManager`.


