# i.mobilothon

## 🅿️ Smart Parking Marketplace - Mobile App MVP

A comprehensive React Native mobile application featuring parking heatmaps for free parking discovery and an intelligent marketplace for paid parking with dual buyer-seller modes.

### 🚀 Quick Start

```bash
cd parking-app
npm install
npx expo start
```

### 📚 Documentation

- **[Main App README](./parking-app/README.md)** - Full app documentation
- **[Supabase & Mapbox Setup Guide](./parking-app/SUPABASE_MAPBOX_SETUP.md)** - Authentication & Maps configuration (⚠️ **Required**)

### ⚙️ Prerequisites

Before running the app, you need to:

1. Create a **Supabase** account and project (for authentication)
2. Create a **Mapbox** account and get access tokens (for maps)
3. Follow the [SUPABASE_MAPBOX_SETUP.md](./parking-app/SUPABASE_MAPBOX_SETUP.md) guide

### ✨ Key Features

- 🗺️ Interactive maps with real-time parking heatmap
- 🆓 Free parking hotspot discovery with probability scores
- 💰 Paid parking marketplace with smart filtering
- 📱 Complete booking flow with QR code generation
- ⭐ Ratings & reviews system
- 🏪 Seller dashboard for parking management
- 🧮 Time-based pricing calculator
- 📊 Analytics and occupancy tracking

### 🛠️ Tech Stack

React Native (Expo) • TypeScript • Zustand • React Navigation • Mapbox • Supabase

### 🔐 Authentication

The app uses **Supabase Authentication** for:

- Email/Password signup and login
- Seller/Buyer role management
- Persistent sessions with AsyncStorage
- Protected seller features

### 🗺️ Maps & Navigation

Powered by **Mapbox** for:

- Interactive map interface
- Location search (Geocoding)
- Turn-by-turn navigation (Directions API)
- Custom markers and heatmaps

---

Built for VW i.mobilothon Hackathon 2025
