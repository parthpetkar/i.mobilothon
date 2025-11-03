# 🔧 Fixing "@rnmapbox/maps native code not available" Error

## ❌ The Problem

You're seeing this error because **Mapbox requires native modules** that are NOT available in Expo Go. Expo Go is a sandbox app that only includes a limited set of native modules.

## ✅ The Solution

You need to create a **Development Build** (custom native build) instead of using Expo Go.

---

## 🚀 Quick Fix (2 Options)

### Option 1: Local Development Build (Recommended)

#### For Android:

```bash
# Step 1: Generate native Android folder
npx expo prebuild --platform android

# Step 2: Run on Android device/emulator
npx expo run:android
```

#### For iOS (Mac only):

```bash
# Step 1: Generate native iOS folder
npx expo prebuild --platform ios

# Step 2: Install CocoaPods dependencies
cd ios && pod install && cd ..

# Step 3: Run on iOS simulator
npx expo run:ios
```

### Option 2: EAS Build (Cloud Build)

If you don't want to set up native build tools locally:

```bash
# Step 1: Install EAS CLI
npm install -g eas-cli

# Step 2: Login to Expo
eas login

# Step 3: Configure EAS Build
eas build:configure

# Step 4: Build development client
eas build --profile development --platform android
# or for iOS:
eas build --profile development --platform ios

# Step 5: Install the built APK/IPA on your device
```

---

## 📋 Prerequisites

### For Android Local Build:
- ✅ Android Studio installed
- ✅ Android SDK and Platform Tools
- ✅ Java JDK 17+
- ✅ Android device or emulator

### For iOS Local Build (Mac only):
- ✅ Xcode installed
- ✅ CocoaPods installed (`sudo gem install cocoapods`)
- ✅ iOS simulator or physical device

---

## 🛠️ Step-by-Step: Android Local Build

### 1. Install Android Studio
Download from: https://developer.android.com/studio

### 2. Set up Environment Variables
Add to your PowerShell profile or system environment:

```powershell
$env:ANDROID_HOME = "C:\Users\YourUsername\AppData\Local\Android\Sdk"
$env:PATH += ";$env:ANDROID_HOME\platform-tools"
$env:PATH += ";$env:ANDROID_HOME\emulator"
```

### 3. Accept Android Licenses
```bash
cd $env:ANDROID_HOME\cmdline-tools\latest\bin
./sdkmanager --licenses
```

### 4. Generate Native Code
```bash
cd D:\Hackathons\VW\i.mobilothon\parking-app
npx expo prebuild --platform android --clean
```

This will:
- Create `android/` folder
- Install Mapbox native modules
- Configure Gradle build files

### 5. Build and Run
```bash
npx expo run:android
```

This will:
- Build the APK
- Install on connected device/emulator
- Start Metro bundler
- Launch the app with Mapbox working!

---

## 🔍 What's Different?

| Expo Go | Development Build |
|---------|-------------------|
| ❌ Limited native modules | ✅ All native modules |
| ❌ No Mapbox | ✅ Mapbox works |
| ✅ Quick testing | ⚠️ Requires build step |
| ✅ No setup | ⚠️ Requires Android Studio/Xcode |

---

## 🚨 Common Errors & Fixes

### Error: "Android SDK not found"
```bash
# Set ANDROID_HOME environment variable
$env:ANDROID_HOME = "C:\Users\YourUsername\AppData\Local\Android\Sdk"
```

### Error: "Java not found"
```bash
# Install Java JDK 17
# Download from: https://adoptium.net/
```

### Error: "Gradle build failed"
```bash
# Clean Gradle cache
cd android
./gradlew clean
cd ..
npx expo run:android
```

### Error: "Metro bundler not starting"
```bash
# Clear cache and restart
npx expo start --clear
```

---

## ⚡ Quick Test (Without Building)

If you want to test the app quickly without Mapbox features:

1. **Comment out Mapbox imports** temporarily:

```typescript
// src/screens/MapHomeScreen.tsx
// import Mapbox, { Camera, MarkerView, ShapeSource, CircleLayer } from '@rnmapbox/maps';

// Use a placeholder view instead
<View style={styles.map}>
  <Text>Map will appear here after development build</Text>
</View>
```

2. Run with Expo Go:
```bash
npx expo start
```

---

## 📦 What Gets Created

After running `npx expo prebuild`:

```
parking-app/
├── android/              ← NEW: Native Android project
│   ├── app/
│   ├── build.gradle
│   └── settings.gradle
├── ios/                  ← NEW: Native iOS project (Mac only)
│   ├── ParkingApp/
│   ├── Podfile
│   └── ParkingApp.xcworkspace
└── ... (rest of your files)
```

These folders are **auto-generated** from your `app.json` config.

---

## 🎯 Recommended Workflow

1. **Commit your current changes** (optional but recommended)
   ```bash
   git add .
   git commit -m "Pre-native build commit"
   ```

2. **Add android/ios to .gitignore** (they're auto-generated)
   ```
   # .gitignore
   android/
   ios/
   ```

3. **Generate native folders**
   ```bash
   npx expo prebuild --clean
   ```

4. **Run the app**
   ```bash
   npx expo run:android
   ```

5. **Develop normally**
   - Hot reload still works!
   - Edit your TypeScript/React code
   - Changes appear instantly

---

## 💡 Why This Happens

Expo Go is a pre-built app with a fixed set of native modules. When you install a library like `@rnmapbox/maps` that requires custom native code:

1. `npm install` ✅ Downloads JavaScript code
2. But ❌ Expo Go doesn't have Mapbox's native Android/iOS code
3. Result: "native code not available" error

**Solution**: Build your own custom version of the app that includes Mapbox's native code.

---

## 📱 Device Requirements

- **Android**: Physical device or emulator (API 21+)
- **iOS**: Mac with Xcode, physical device or simulator (iOS 12+)

---

## 🔄 Development Cycle

After initial build, your workflow becomes:

```bash
# Start Metro bundler
npx expo start

# Press 'a' for Android (if already built)
# Or run: npx expo run:android
```

You only need to rebuild when:
- Adding new native modules
- Updating `app.json` config
- Updating Expo SDK version

---

## ✅ Verification

After building successfully, you should see:

1. ✅ App launches on device/emulator
2. ✅ Mapbox map renders correctly
3. ✅ Location search works
4. ✅ Markers appear on map
5. ✅ No "native code not available" error

---

## 🆘 Need Help?

If you encounter issues:

1. Check Android Studio logs
2. Run `npx expo doctor` to check configuration
3. Try `npx expo prebuild --clean` to regenerate native folders
4. Check Expo documentation: https://docs.expo.dev/develop/development-builds/introduction/

---

**TL;DR**: Run `npx expo run:android` instead of using Expo Go. This will build a custom app with Mapbox native code included.
