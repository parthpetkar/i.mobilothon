# 🔐 Supabase & Mapbox Setup Guide

## Overview
This app now uses:
- **Supabase** for authentication and database
- **Mapbox** for maps, geocoding, and navigation

---

## 🗄️ Supabase Setup

### Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or login
3. Click "New Project"
4. Fill in:
   - **Project Name**: smart-parking (or any name)
   - **Database Password**: (save this!)
   - **Region**: Choose closest to you
5. Wait for project to be created (~2 minutes)

### Step 2: Get API Keys

1. In your Supabase project dashboard
2. Click **Settings** (gear icon) → **API**
3. Copy these values:
   - **Project URL**: `https://xxx.supabase.co`
   - **anon public**: This is your SUPABASE_ANON_KEY

### Step 3: Create Users Table

1. Go to **SQL Editor** in Supabase dashboard
2. Run this SQL:

```sql
-- Create profiles table
CREATE TABLE profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  phone TEXT,
  is_seller BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile" 
  ON profiles FOR SELECT 
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
  ON profiles FOR UPDATE 
  USING (auth.uid() = id);

-- Create trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, phone, is_seller)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'phone',
    COALESCE((NEW.raw_user_meta_data->>'is_seller')::boolean, false)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## 🗺️ Mapbox Setup

### Step 1: Create Mapbox Account

1. Go to [https://www.mapbox.com](https://www.mapbox.com)
2. Sign up for a free account
3. Go to **Account** → **Access tokens**

### Step 2: Get Access Token

1. You'll see a **Default public token**
2. Copy this token (starts with `pk.`)
3. Or create a new token:
   - Click **Create a token**
   - Name it: `smart-parking-app`
   - Scopes needed:
     - ✅ Maps (maps:read)
     - ✅ Navigation (navigation:read)
     - ✅ Geocoding (geocoding:read)
   - Click **Create token**

---

## 📝 Configure the App

### Step 1: Update Environment File

Open `src/config/env.ts` and replace with your actual values:

```typescript
export const SUPABASE_URL = 'https://your-project.supabase.co';
export const SUPABASE_ANON_KEY = 'your-anon-key-here';
export const MAPBOX_ACCESS_TOKEN = 'pk.your-token-here';
```

### Step 2: Configure Mapbox in app.json

Open `app.json` and add Mapbox configuration:

```json
{
  "expo": {
    "name": "parking-app",
    "slug": "parking-app",
    "version": "2.0.0",
    "plugins": [
      [
        "@rnmapbox/maps",
        {
          "RNMapboxMapsDownloadToken": "YOUR_SECRET_TOKEN_HERE"
        }
      ]
    ]
  }
}
```

**Note**: Get the download token from Mapbox dashboard under **Account** → **Access tokens** → Create a **Secret token** with `DOWNLOADS:READ` scope.

---

## 🔐 Authentication Flow

### How It Works

1. **User Signs Up**:
   - Email + Password + Profile info
   - Choose if they want to be a seller
   - Supabase creates auth user + profile record

2. **User Logs In**:
   - Email + Password
   - Supabase validates credentials
   - Returns user session

3. **Session Management**:
   - Stored in AsyncStorage
   - Auto-refreshes on app restart
   - Expires after configured time

4. **Seller Mode**:
   - Only accessible if `user.is_seller = true`
   - Dashboard shows seller-specific features
   - Can add/manage parking listings

### Guest Mode

Users can use the app without logging in:
- ✅ View free parking heatmap
- ✅ Browse paid parking
- ✅ Search locations
- ❌ Cannot book (requires login)
- ❌ Cannot access seller features

---

## 🗺️ Mapbox Features

### 1. Interactive Maps
- Pan, zoom, rotate
- Custom markers
- Heatmap layers

### 2. Location Search (Geocoding)
- Search any address
- Auto-complete suggestions
- Returns coordinates

### 3. Turn-by-Turn Navigation
- Get route from A to B
- Distance and duration
- Draw route on map
- Step-by-step directions

### 4. Reverse Geocoding
- Tap map → Get address
- Coordinates → Place name

---

## 🧪 Test Accounts

You can create test accounts for development:

### Buyer Account
- Email: `buyer@test.com`
- Password: `test123`
- Is Seller: No

### Seller Account
- Email: `seller@test.com`
- Password: `test123`
- Is Seller: Yes

---

## 🚀 Running the App

```bash
# Install dependencies
npm install

# Start development server
npx expo start

# For iOS (requires Mac + Xcode)
npx expo run:ios

# For Android
npx expo run:android
```

**Note**: Mapbox requires native builds for full functionality. Use `expo run:android` or `expo run:ios` instead of Expo Go for maps.

---

## 📊 Database Schema

### profiles table
```
id (UUID, PK)           - Links to auth.users.id
email (TEXT)            - User's email
full_name (TEXT)        - Full name
phone (TEXT)            - Phone number (optional)
is_seller (BOOLEAN)     - Can access seller features
created_at (TIMESTAMP)  - Account creation date
```

### Future tables (expandable)
```
seller_parkings
  - id, owner_id, name, location, price, etc.

bookings
  - id, user_id, parking_id, duration, status, etc.

reviews
  - id, user_id, parking_id, rating, comment, etc.
```

---

## 🔒 Security Best Practices

### DO:
✅ Keep API keys in `env.ts` (add to .gitignore)
✅ Use Row Level Security in Supabase
✅ Validate user input
✅ Use HTTPS only
✅ Rotate tokens periodically

### DON'T:
❌ Commit API keys to Git
❌ Share secret tokens publicly
❌ Disable RLS policies
❌ Trust client-side validation only

---

## 🐛 Troubleshooting

### Supabase Issues

**"Invalid API key"**
- Check URL and anon key in `env.ts`
- Make sure no trailing slashes in URL

**"User not found"**
- Check email/password
- Verify user exists in Auth → Users

**"Profile not created"**
- Check SQL trigger is active
- Manually insert profile if needed

### Mapbox Issues

**"Invalid access token"**
- Check token in `env.ts`
- Token must start with `pk.`
- Create new token if expired

**"Map not rendering"**
- Use native build (not Expo Go)
- Check permissions in app.json
- Verify download token

---

## 📚 Resources

- [Supabase Docs](https://supabase.com/docs)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)
- [Mapbox for React Native](https://github.com/rnmapbox/maps)
- [Mapbox API Docs](https://docs.mapbox.com/)

---

## ✅ Setup Checklist

- [ ] Supabase project created
- [ ] API keys copied to `env.ts`
- [ ] SQL tables and triggers created
- [ ] Mapbox account created
- [ ] Mapbox token added to `env.ts`
- [ ] Download token added to `app.json`
- [ ] Dependencies installed (`npm install`)
- [ ] Test account created
- [ ] App runs successfully

---

**Ready to go! 🎉**
