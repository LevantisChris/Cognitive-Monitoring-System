# LogMyself

<div align="center">
  <img src="app/src/main/res/drawable/logmyself_high_resolution_logo_transparent.png" alt="LogMyself Logo" width="200"/>
  
  **A comprehensive personal behavioral monitoring and analytics Android application**
  
  [![Android](https://img.shields.io/badge/Platform-Android-green.svg)](https://developer.android.com/)
  [![Kotlin](https://img.shields.io/badge/Language-Kotlin-blue.svg)](https://kotlinlang.org/)
  [![Min SDK](https://img.shields.io/badge/Min%20SDK-31-orange.svg)](https://developer.android.com/studio/releases/platforms)
  [![Target SDK](https://img.shields.io/badge/Target%20SDK-35-orange.svg)](https://developer.android.com/studio/releases/platforms)
</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Technologies](#-architecture--technologies)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Detailed Installation](#installation-steps)
- [Required Permissions](#-required-permissions)
- [Project Structure](#-project-structure)
- [Usage Guide](#-usage-guide)
- [Testing](#-testing)
- [Building for Release](#-building-for-release)
- [FAQ](#-frequently-asked-questions)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## 📱 Overview

**LogMyself** is an advanced Android application designed to help users understand their daily behavioral patterns through comprehensive data tracking and analytics. The app monitors various aspects of user behavior including activity patterns, sleep cycles, device interactions, location movements, and more.

By providing detailed insights and visualizations, LogMyself empowers users to make data-driven decisions about their daily habits and lifestyle choices.

> **Note**: LogMyself integrates with **LogBoard**, a companion keyboard application, to provide typing analytics. Keyboard data is captured by LogBoard and analyzed on a secure backend server. LogMyself displays the analyzed typing insights without directly capturing keystrokes.

## ✨ Key Features

### Behavioral Monitoring
- **Sleep Detection**: Automatic sleep pattern tracking and analysis
- **Activity Recognition**: Monitors walking, running, driving, and other physical activities
- **Device Interactions**: Tracks phone drops, proximity events, and screen interactions
- **Call Monitoring**: Logs incoming/outgoing calls and VoIP communications
- **Location Tracking**: Fusion-based GPS location tracking with map visualization
- **Typing Analytics**: Displays typing insights from LogBoard companion app (data captured and analyzed externally)
- **Light Detection**: Ambient light sensor monitoring
- **Notification Tracking**: Monitors app notification patterns

### Data Visualization & Analytics
- **Interactive Charts**: Beautiful visualizations powered by Vico and MPAndroidChart
- **Behavioral Insights**: Insights based on collected data (analyzed on backend server)
- **Performance Metrics**: Overall performance scoring and baseline comparisons
- **Timeline Views**: Historical data browsing and trend analysis
- **Typing Statistics**: View typing patterns from LogBoard (analyzed externally)

### User Experience
- **Modern UI**: Built with Jetpack Compose and Material Design 3
- **Google Authentication**: Secure sign-in with Firebase Auth
- **Background Monitoring**: Efficient foreground service for continuous data collection
- **Data Synchronization**: Cloud backup with Firebase Firestore and Supabase

## 🏗️ Architecture & Technologies

### Core Technologies
- **Language**: Kotlin 2.2.0
- **UI Framework**: Jetpack Compose with Material3
- **Architecture**: MVVM (Model-View-ViewModel)
- **Minimum SDK**: 31 (Android 12)
- **Target SDK**: 35 (Android 14)

### Key Libraries & Frameworks

#### Android Jetpack
- Room Database (local data persistence)
- WorkManager (background task scheduling)
- Navigation Component
- Lifecycle & ViewModel
- Credentials API

#### Backend & Cloud
- Firebase Authentication (Google Sign-in)
- Firebase Crashlytics (crash reporting)
- Firebase Firestore (cloud database)
- Supabase (PostgreSQL backend)

#### Location & Maps
- Google Play Services Location
- Google Maps SDK
- Fusion Location Provider

#### Networking
- Ktor Client (HTTP client)
- Kotlinx Serialization

#### Charts & Visualization
- Vico Charts (1.11.1)
- MPAndroidChart (3.1.0)

#### Development Tools
- KSP (Kotlin Symbol Processing)
- Desugar JDK Libs (Java 8+ API support)

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- **Android Studio** (Jellyfish 2023.3.1 or later recommended)
- **JDK 11** or higher
- **Android SDK** with API level 31+
- **Git** for version control

### Required API Keys & Credentials

LogMyself requires several external services. You'll need to set up:

1. **Google Maps API Key** (for location features)
2. **Firebase Project** (for authentication and cloud storage)
3. **Supabase Project** (for database backend)

### Optional Companion App

- **LogBoard** (optional): A separate keyboard application for typing analytics. Install LogBoard if you want to use the typing insights feature. LogMyself works fully without it, but the Typing section will be empty.

### Quick Start

> ⚡ **TL;DR**: For experienced developers who want to get started immediately:

```bash
# 1. Clone and open in Android Studio
git clone https://github.com/yourusername/LogMyself.git
cd LogMyself

# 2. Create local.properties with your SDK path and Google Maps API key
echo "sdk.dir=/path/to/your/android/sdk" > local.properties
echo "MAPS_API_KEY=YOUR_MAPS_API_KEY" >> local.properties

# 3. Create app/.env with Supabase credentials
cp app/env_template.txt app/.env
# Edit app/.env with your Supabase URL and key

# 4. Download google-services.json from Firebase Console
# Place it in app/ directory

# 5. Build and run
./gradlew installDebug
```

For detailed setup instructions, see below ⬇️

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/LogMyself.git
cd LogMyself
```

#### 2. Configure Local Properties

Create a `local.properties` file in the project root directory:

```properties
## This file is automatically generated by Android Studio.
# Do not modify this file -- YOUR CHANGES WILL BE ERASED!
#
# Location of the SDK. This is only used by Gradle.
sdk.dir=C\:\\Users\\YOUR_USERNAME\\AppData\\Local\\Android\\Sdk

# Google Maps API Key
MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY_HERE
```

> 💡 **Tip**: You can use `local.properties_example` as a template.

#### 3. Configure Supabase Environment Variables

Create a file named `.env` in the `app/` directory:

```bash
# Copy the template and edit with your credentials
cp app/env_template.txt app/.env
```

Then edit `app/.env` with your actual credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
```

**To get your Supabase credentials:**
1. Create a project at [supabase.com](https://supabase.com)
2. Go to Settings → API
3. Copy the Project URL and anon/public key

#### 4. Set Up Firebase

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Add an Android app to your Firebase project
   - Package name: `com.levantis.logmyself`
3. Download the `google-services.json` file
4. Place it in the `app/` directory (replacing `google-services.json.example`)

**Enable Firebase Services:**
- **Authentication**: Enable Google Sign-in provider
- **Firestore Database**: Create a database in production mode
- **Crashlytics**: Enable crash reporting

> 💡 **Tip**: See `app/google-services.json.example` for reference structure

#### 5. Set Up Google Maps API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Maps SDK for Android
   - Places API
4. Create credentials (API Key)
5. Restrict the API key to Android apps with your package name
6. Copy the API key to your `local.properties` file

#### 6. Sync and Build

1. Open the project in Android Studio
2. Wait for Gradle sync to complete
3. Build the project: `Build → Make Project`
4. Run on an emulator or physical device

### Running the App

#### Using Android Studio
1. Connect an Android device (API 31+) or start an emulator
2. Click the "Run" button (▶️) or press `Shift + F10`
3. Select your target device
4. Wait for the app to install and launch

#### Using Command Line
```bash
# Debug build
./gradlew assembleDebug

# Install on connected device
./gradlew installDebug

# Build and run
./gradlew installDebug && adb shell am start -n com.levantis.logmyself/.MainActivity
```

## 📋 Required Permissions

LogMyself requires several permissions to function properly. The app will request these at runtime:

### Location Permissions
- `ACCESS_FINE_LOCATION`: Precise location tracking
- `ACCESS_COARSE_LOCATION`: Approximate location tracking
- `ACCESS_BACKGROUND_LOCATION`: Location tracking while app is in background

### Activity & Phone Permissions
- `ACTIVITY_RECOGNITION`: Physical activity detection
- `READ_PHONE_STATE`: Phone state monitoring
- `READ_CALL_LOG`: Call history tracking

### Notification & System Permissions
- `POST_NOTIFICATIONS`: Display notifications (Android 13+)
- `NOTIFICATION_LISTENER_SETTINGS`: Detect VoIP calls and notifications
- `PACKAGE_USAGE_STATS`: App usage statistics
- `SCHEDULE_EXACT_ALARM`: Schedule exact alarms for monitoring
- `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`: Prevent battery optimization interference

### Automatically Granted Permissions
- `INTERNET`: Network communication
- `FOREGROUND_SERVICE`: Background monitoring service
- `FOREGROUND_SERVICE_DATA_SYNC`: Data synchronization
- `RECEIVE_BOOT_COMPLETED`: Auto-start after device reboot
- `WAKE_LOCK`: Keep device awake for monitoring

## 📁 Project Structure

```
LogMyself/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/levantis/logmyself/
│   │   │   │   ├── analysis_database/      # Data analytics and caching
│   │   │   │   ├── auth/                   # Authentication logic
│   │   │   │   ├── background/             # Background services
│   │   │   │   ├── cloudb/                 # Cloud database (Firestore)
│   │   │   │   ├── database/               # Room database (local)
│   │   │   │   ├── sensors/                # Sensor detectors & listeners
│   │   │   │   ├── ui/                     # UI components (Compose)
│   │   │   │   ├── utils/                  # Utility classes
│   │   │   │   ├── MainActivity.kt         # Main entry point
│   │   │   │   └── MyApplication.kt        # Application class
│   │   │   ├── res/                        # Resources (layouts, drawables, etc.)
│   │   │   └── AndroidManifest.xml         # App manifest
│   │   ├── androidTest/                    # Instrumented tests
│   │   └── test/                           # Unit tests
│   ├── build.gradle.kts                    # App-level build configuration
│   ├── env_template.txt                    # Template for .env file
│   ├── google-services.json.example        # Template for Firebase config
│   ├── .env                                # Supabase credentials (create this - not in repo)
│   └── google-services.json                # Firebase config (download this - not in repo)
├── gradle/
│   └── libs.versions.toml                  # Dependency version catalog
├── build.gradle.kts                        # Project-level build configuration
├── settings.gradle.kts                     # Gradle settings
├── local.properties                        # Local configuration (create this)
├── local.properties_example                # Template for local.properties
└── README.md                               # This file
```

## 🎯 Usage Guide

### First-Time Setup

1. **Launch the App**: Open LogMyself on your device
2. **Sign In**: Authenticate using your Google account
3. **Grant Permissions**: The app will sequentially request necessary permissions
4. **Allow Background Monitoring**: Enable battery optimization exemption for continuous monitoring
5. **Start Using**: The app will begin collecting data in the background

### Navigation

The app features a bottom navigation bar with five main sections:

- **🏠 Home**: Dashboard with overview and quick stats
- **⌨️ Typing**: View typing analytics from LogBoard companion app (requires LogBoard installation)
- **📊 Behavior**: Activity and behavioral analytics
- **💡 Insights**: AI-driven insights and recommendations
- **👤 Profile**: User profile and settings

### Background Monitoring

LogMyself runs a foreground service to continuously monitor your behavior:
- **Persistent Notification**: Shows "Monitoring in Background"
- **Auto-Restart**: Automatically restarts after device reboot
- **Battery Optimized**: Efficient monitoring with minimal battery impact

### Data Privacy

- All behavioral data (except typing) is collected and stored locally using Room database
- **Typing data**: Collected by the separate LogBoard app and analyzed on a secure backend server; LogMyself only displays the results
- Cloud backup is optional via Firebase Firestore
- You can delete your account and all data at any time
- No data is shared with third parties without consent

## 🧪 Testing

### Running Unit Tests
```bash
./gradlew test
```

### Running Instrumented Tests
```bash
./gradlew connectedAndroidTest
```

## 🔧 Building for Release

### Create a Release Build

1. Generate a signing key:
```bash
keytool -genkey -v -keystore logmyself-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias logmyself
```

2. Create `keystore.properties` in the project root:
```properties
storePassword=YOUR_STORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=logmyself
storeFile=../logmyself-release-key.jks
```

3. Build the release APK:
```bash
./gradlew assembleRelease
```

The signed APK will be located at: `app/build/outputs/apk/release/app-release.apk`

### Building an App Bundle (AAB)
```bash
./gradlew bundleRelease
```

The AAB will be located at: `app/build/outputs/bundle/release/app-release.aab`

## ❓ Frequently Asked Questions

### General Questions

**Q: What is LogBoard and do I need it?**  
A: LogBoard is a companion keyboard application that provides typing analytics for LogMyself. It's optional - LogMyself works without it, but you won't have typing insights. LogBoard captures keyboard usage patterns and sends them to a secure backend server for analysis. LogMyself then displays these analyzed insights in the Typing section.

**Q: Does LogMyself capture my keystrokes?**  
A: No! LogMyself does NOT capture any keyboard data or keystrokes. All typing analytics come from the separate LogBoard application. If you don't install LogBoard, LogMyself will not have access to any typing data.

**Q: Does this app drain my battery?**  
A: LogMyself is designed to be battery-efficient. It uses a foreground service with optimized monitoring intervals and build-in APIs. However, continuous tracking does use some battery. You can monitor battery usage in your device settings.

**Q: What Android version do I need?**  
A: LogMyself requires Android 12 (API level 31) or higher.

**Q: Why does the app need so many permissions?**  
A: Each permission serves a specific monitoring purpose:
- Location: Track where you spend your time
- Activity Recognition: Detect walking, running, driving
- Call Log: Monitor communication patterns
- Notifications: Understand app usage
All permissions are optional for basic functionality, but some features require specific permissions.

### Technical Questions

**Q: Where is my data stored?**  
A: Data is stored in multiple places depending on the type:
1. **Firebase Firestore**: Cloud for your LogMyself data
2. **Supabase**: Additional backend analytics
3. **LogBoard Backend**: Typing data is stored and analyzed on LogBoard's secure backend server (separate from LogMyself)

**Q: The background service keeps stopping. What should I do?**  
A: 
1. Disable battery optimization for LogMyself in Settings → Apps → LogMyself → Battery
2. Ensure the app has "Allow all the time" location permission
3. Check that the app is not restricted in background

## 🐛 Troubleshooting

### Common Issues

#### Build Failures

**Issue**: Gradle sync fails with dependency errors  
**Solution**: 
```bash
./gradlew clean
./gradlew --refresh-dependencies
```

**Issue**: Google services plugin error  
**Solution**: Ensure `google-services.json` is in the `app/` directory

#### Runtime Issues

**Issue**: App crashes on launch  
**Solution**: Check Firebase Authentication is properly configured and Google Sign-in is enabled

**Issue**: Location tracking not working  
**Solution**: Verify location permissions are granted and Google Maps API key is valid

**Issue**: Background service stops  
**Solution**: Disable battery optimization for LogMyself in device settings

#### Permission Issues

**Issue**: Permissions dialog not appearing  
**Solution**: Manually grant permissions in Settings → Apps → LogMyself → Permissions

### Debugging

Enable detailed logging:
```bash
adb logcat -s LogMyself:V
```

View crash logs:
```bash
adb logcat *:E
```

## 📄 License

This project is part of a thesis project. Please contact the repository owner for licensing information.

## 👥 Authors

- **Christos Levantis** - *Initial work* - [com.levantis.logmyself](https://github.com/levantis)

## 🙏 Acknowledgments

- Firebase for authentication and cloud services
- Supabase for PostgreSQL backend
- Google for Maps SDK and Location Services
- The Android and Jetpack Compose teams
- All open-source library contributors

## 📞 Support

For questions, issues, or feature requests:
- Open an issue on GitHub

---

<div align="center">
  Made with ❤️ for better self-understanding
  
  **LogMyself** - Know yourself better through data
</div>

