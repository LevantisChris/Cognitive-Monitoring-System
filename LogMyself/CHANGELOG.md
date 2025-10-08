# Changelog

All notable changes to the LogMyself project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Data export functionality (CSV, JSON)
- Weekly/Monthly reports
- Custom notification preferences
- Dark mode improvements
- Widget support
- Share insights feature

## [1.0.0] - TBD

### Added
- Initial release of LogMyself
- Google Authentication with Firebase
- Background monitoring service for continuous data collection
- Multiple behavior tracking modules:
  - Sleep detection and analysis
  - Activity recognition (walking, running, driving, etc.)
  - Phone drop detection
  - Call monitoring (regular and VoIP)
  - GPS location tracking with fusion provider
  - Typing behavior analysis
  - Light sensor monitoring
  - Notification tracking
  - Proximity detection
- Data visualization with interactive charts
  - Vico charts integration
  - MPAndroidChart support
  - Timeline views
  - Behavioral insights dashboard
- Local data persistence with Room database
- Cloud backup with Firebase Firestore
- Supabase backend integration
- Modern UI with Jetpack Compose and Material Design 3
- Five main sections: Home, Typing, Behavior, Insights, Profile
- Google Maps integration for location visualization
- Comprehensive permission management system
- Auto-restart service after device reboot
- Battery optimization handling
- Crash reporting with Firebase Crashlytics
- Data caching for improved performance
- Baseline metrics calculation
- Performance scoring system

### Security
- Secure Google Sign-in authentication
- Local data encryption with Room
- Secure API key handling via BuildConfig
- Protected Firebase and Supabase credentials

### Documentation
- Comprehensive README with setup instructions
- Contributing guidelines (CONTRIBUTING.md)
- Template files for configuration:
  - `local.properties_example`
  - `app/env_template.txt`
  - `app/google-services.json.example`
- Code documentation and KDoc comments

## Version History

### [1.0.0] - Initial Release
First public release of LogMyself as part of thesis project.

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** in case of vulnerabilities

## Release Notes Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Modified feature description

### Fixed
- Bug fix description

### Security
- Security improvement description
```

---

**Note**: This project is currently in development as part of a thesis project. Version numbers and release dates will be updated accordingly.

