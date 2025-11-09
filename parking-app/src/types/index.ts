import { User } from '@supabase/supabase-js';

export interface FreeHotspot {
  lat: number;
  lng: number;
  probability: number;
  label: string;
  radius?: number; // Radius in meters for the hotspot circle (geographic distance)
}

export interface PaidParking {
  id: string;
  name: string;
  lat: number;
  lng: number;
  price: number;
  slots: number;
  available: number;
  rating: number;
  amenities: string[];
  images?: string[];
  reviews?: Review[];
}

export interface Review {
  id: string;
  userName: string;
  rating: number;
  comment: string;
  date: string;
}

export interface Booking {
  id: string;
  parkingId: string;
  parkingName: string;
  duration: number;
  totalPrice: number;
  timestamp: string;
  otp: string;
  status: 'active' | 'completed';
  userId: string;
}

export interface SellerParking extends PaidParking {
  ownerId: string;
  dailyRevenue: number;
  occupancyRate: number;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  phone?: string;
  is_seller: boolean;
  created_at: string;
}

export interface NavigationRoute {
  distance: number;
  duration: number;
  geometry: {
    coordinates: [number, number][];
  };
}

export type ViewMode = 'free' | 'paid' | 'seller';

export type FilterType = 'price' | 'distance' | 'availability' | 'rating';

export type SortDirection = 'asc' | 'desc';

export type AuthUser = User | null;
