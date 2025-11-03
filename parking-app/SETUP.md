# 🚀 Setup & Run Instructions

## Quick Start (3 Steps)

### 1️⃣ Navigate to the app directory
```bash
cd parking-app
```

### 2️⃣ Install dependencies (if not already done)
```bash
npm install
```

### 3️⃣ Start the app
```bash
npx expo start
```

## Running on Different Platforms

After running `npx expo start`, you'll see a QR code and menu options:

- Press **`a`** - Open on Android emulator
- Press **`i`** - Open on iOS simulator (Mac only)
- Press **`w`** - Open in web browser (limited functionality)
- **Scan QR code** - Use Expo Go app on your phone

## 📱 Testing on Physical Device

1. Install **Expo Go** app:
   - [iOS App Store](https://apps.apple.com/app/expo-go/id982107779)
   - [Android Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. Make sure your phone and computer are on the same WiFi

3. Scan the QR code with:
   - **iOS**: Camera app
   - **Android**: Expo Go app

## 🎯 Testing Features

### Free Parking Mode
1. Tap "Free Parking" toggle at top
2. Search for locations (JM Road, FC Road, etc.)
3. Tap on green heatmap circles
4. Click "Navigate" to open Google Maps

### Paid Parking Mode
1. Tap "Paid Parking" toggle
2. Browse parking cards at bottom
3. Tap any card to view details
4. Select duration (use +/- buttons)
5. Click "Book Now"
6. Test payment (auto-succeeds after 2 seconds)
7. View QR code
8. Rate the parking

### Seller Mode
1. Tap "Seller Mode" toggle
2. Click the 📊 button (bottom right)
3. View dashboard analytics
4. Click "+ Add Listing"
5. Fill in details and tap map to set location
6. Manage availability with +/- controls

## 🛠️ Troubleshooting

### "Metro bundler not starting"
```bash
npx expo start -c
```

### "Module not found" errors
```bash
rm -rf node_modules
npm install
```

### Maps not showing
- Grant location permissions when prompted
- Make sure you're using a real device or properly configured emulator

### TypeScript errors
```bash
npx tsc --noEmit
```

## 📦 Project Structure Quick Reference

```
parking-app/
├── src/
│   ├── screens/        # All UI screens
│   ├── store/          # Zustand state management
│   ├── data/           # Dummy JSON data
│   ├── types/          # TypeScript definitions
│   ├── utils/          # Helper functions
│   └── navigation/     # React Navigation setup
└── App.tsx            # Entry point
```

## 🎨 Available Dummy Data

### Free Hotspots (8)
JM Road, FC Road, Shivaji Nagar, Camp Area, Deccan Gymkhana, Koregaon Park, Kothrud, Hadapsar

### Paid Parkings (8)
MG Road, Phoenix Mall, Deccan Plaza, Koregaon Park Secure, Camp Street, Hinjewadi Tech Park, FC Road Central, Baner Smart Parking

## 💡 Tips

- **Search works!** Try typing "JM Road" or "Phoenix Mall"
- **Test payments** are instant (2-second delay for realism)
- **QR codes** are generated but not validated
- **All data** persists during the session only (resets on app restart)

## 🎓 Next Steps

- Explore the code in `src/` directory
- Modify dummy data in `src/data/` 
- Customize styles using NativeWind (Tailwind CSS)
- Add more features using Zustand store

---

**Need help?** Check the main README.md for detailed documentation
