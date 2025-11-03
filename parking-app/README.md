# 🅿️ Smart Parking Marketplace - Mobile App MVP

A comprehensive React Native mobile app featuring parking heatmaps for free parking spots and a smart marketplace for paid parking with buyer and seller modes.

## 📱 Features

### 🗺️ Home / Map Screen
- Interactive Mapbox map centered on Pune, India
- Top search bar with auto-suggestions
- Real-time map re-centering on location selection
- Three view modes: Free Parking | Paid Parking | Seller Mode
- Dynamic hotspot and marker updates

### 🆓 Free Parking Heatmap Module
- Visual heatmap layer showing parking availability probability
- Dynamically generated nearest hotspots based on search location
- Hotspot popup showing:
  - Area label
  - Probability score (High/Medium/Low)
  - Navigate button with Google Maps deep link

### 💰 Paid Parking Marketplace (Buyer Mode)
- **Real-time availability indicators** (Green/Yellow/Red)
- **Smart filtering** by price, distance, availability, amenities
- **Enhanced listing details**:
  - Image gallery
  - Price per hour
  - Slot availability
  - Amenity badges (Covered, CCTV, EV Charging, Toilets)
- **Time-based pricing calculator**
- **Complete booking flow**:
  1. Search & Browse
  2. Select Parking
  3. View Details & Calculate Cost
  4. Test Payment Modal
  5. Booking Confirmation
  6. QR Code Generation
- **Ratings & Reviews System**
  - 5-star rating
  - Written reviews
  - Average rating display

### 🏪 Seller Mode
- **Seller Dashboard** with analytics:
  - Total listings count
  - Daily revenue tracking
  - Average occupancy rate
- **Add New Listing Form**:
  - Name, price, total slots
  - Interactive map for location pin placement
  - Amenity selection
- **Listing Management**:
  - Manual availability updates (+/- controls)
  - QR code scanning for check-in/check-out
  - Per-listing occupancy analytics

## 🛠️ Tech Stack

- **Framework**: React Native (Expo)
- **Maps**: react-native-maps (Mapbox-compatible)
- **State Management**: Zustand
- **Navigation**: React Navigation (Native Stack)
- **Styling**: NativeWind (Tailwind CSS for React Native)
- **QR Codes**: react-native-qrcode-svg
- **Language**: TypeScript
- **Data**: Dummy JSON files (no backend required)

## 📂 Project Structure

```
parking-app/
├── src/
│   ├── components/          # Reusable UI components
│   ├── data/               # Dummy JSON data
│   │   ├── freeHotspots.json
│   │   └── paidParkings.json
│   ├── navigation/         # Navigation configuration
│   │   └── AppNavigator.tsx
│   ├── screens/            # All app screens
│   │   ├── MapHomeScreen.tsx
│   │   ├── ParkingDetailsScreen.tsx
│   │   ├── BookingConfirmationScreen.tsx
│   │   ├── RatingScreen.tsx
│   │   ├── SellerDashboardScreen.tsx
│   │   └── AddListingScreen.tsx
│   ├── store/              # Zustand state management
│   │   └── appStore.ts
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   └── utils/              # Helper functions
│       └── helpers.ts
├── App.tsx                 # Main app component
├── package.json
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (Mac) or Android Emulator

### Installation

1. **Clone the repository**
   ```bash
   cd parking-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npx expo start
   ```

4. **Run on your device**
   - Press `a` for Android emulator
   - Press `i` for iOS simulator
   - Scan QR code with Expo Go app on your physical device

## 📱 Screens Overview

| Screen | Purpose |
|--------|---------|
| **MapHomeScreen** | Main map with heatmap, paid markers, and search |
| **ParkingDetailsScreen** | Detailed parking info with booking UI |
| **BookingConfirmationScreen** | Payment modal & QR code display |
| **RatingScreen** | Post-parking rating and review submission |
| **SellerDashboardScreen** | Seller's listing management & analytics |
| **AddListingScreen** | Form to add new parking spots |

## 🎯 User Flows

### Buyer Flow
```
Search Location → Browse Parkings → View Details → 
Select Duration → Calculate Cost → Pay (Test Mode) → 
Receive QR Code → Check-in → Check-out → Rate & Review
```

### Seller Flow
```
Toggle Seller Mode → View Dashboard → Add New Listing → 
Set Location on Map → Enter Details → Manage Availability → 
Scan Customer QR → Confirm Check-in/Check-out
```

## 🎨 Features Implemented

✅ Mapbox integration with custom markers  
✅ Heatmap visualization for free parking  
✅ Search with auto-suggestions  
✅ Dynamic nearest hotspots calculation  
✅ Google Maps navigation deep link  
✅ Real-time availability indicators  
✅ Smart filtering & sorting  
✅ Time-based cost calculator  
✅ Test payment modal (fake success)  
✅ QR code generation  
✅ Rating & review system  
✅ Seller dashboard with analytics  
✅ Interactive map for location selection  
✅ Manual availability controls  
✅ TypeScript for type safety  
✅ Zustand for efficient state management  
✅ Clean & modular code structure  

## 🗂️ Dummy Data

### Free Hotspots (8 locations)
- JM Road, FC Road, Shivaji Nagar, Camp Area, Deccan Gymkhana, Koregaon Park, Kothrud, Hadapsar

### Paid Parkings (8 listings)
- MG Road Parking, Phoenix Mall, Deccan Plaza, Koregaon Park Secure Parking, Camp Street, Hinjewadi Tech Park, FC Road Central, Baner Smart Parking

## 🔧 Configuration

### NativeWind (Tailwind CSS)
Configured in `tailwind.config.js` and `babel.config.js`

### TypeScript
Types defined in `src/types/index.ts`

### State Management
Zustand store in `src/store/appStore.ts`

## 📝 Notes

- **No backend required** - All data is static/dummy
- **Test payments** - Payment modal shows fake success after 2 seconds
- **QR codes** - Generated locally, no actual scanning validation
- **Maps** - Using react-native-maps (works on both iOS and Android)
- **Location** - Centered on Pune (18.5204, 73.8567)

## 🎓 Learning Resources

- [React Native Docs](https://reactnative.dev/)
- [Expo Docs](https://docs.expo.dev/)
- [Zustand Docs](https://zustand-demo.pmnd.rs/)
- [React Navigation](https://reactnavigation.org/)
- [NativeWind](https://www.nativewind.dev/)

## 🐛 Troubleshooting

**Maps not showing?**
- Ensure you're running on a physical device or properly configured emulator
- Check that location permissions are granted

**Build errors?**
- Clear cache: `npx expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`

**TypeScript errors?**
- Run `npx tsc --noEmit` to check for type errors

## 📄 License

This is an MVP project for demonstration purposes.

## 🤝 Contributing

This is a hackathon MVP. Feel free to fork and improve!

---

**Built with ❤️ using React Native & Expo**
