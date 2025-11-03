import { create } from 'zustand';
import { PaidParking, Booking, Review, ViewMode, FilterType, SortDirection, SellerParking, AuthUser, UserProfile, NavigationRoute } from '../types';
import paidParkingsData from '../data/paidParkings.json';
import { supabase } from '../lib/supabase';

interface AppState {
  // Auth State
  user: AuthUser;
  userProfile: UserProfile | null;
  isLoading: boolean;
  setUser: (user: AuthUser) => void;
  setUserProfile: (profile: UserProfile | null) => void;
  signOut: () => Promise<void>;
  
  // View Mode
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;

  // Map State
  selectedLocation: { lat: number; lng: number } | null;
  setSelectedLocation: (location: { lat: number; lng: number } | null) => void;
  
  // Navigation
  currentRoute: NavigationRoute | null;
  setCurrentRoute: (route: NavigationRoute | null) => void;

  // Paid Parkings
  paidParkings: PaidParking[];
  setPaidParkings: (parkings: PaidParking[]) => void;
  updateParkingAvailability: (id: string, available: number) => void;
  addReview: (parkingId: string, review: Review) => void;

  // Filters & Sort
  filters: {
    maxPrice?: number;
    minAvailability?: number;
    amenities?: string[];
  };
  setFilters: (filters: any) => void;
  sortBy: FilterType | null;
  sortDirection: SortDirection;
  setSorting: (sortBy: FilterType, direction: SortDirection) => void;

  // Bookings
  bookings: Booking[];
  addBooking: (booking: Booking) => void;
  completeBooking: (id: string) => void;

  // Seller Mode (Auth Protected)
  sellerParkings: SellerParking[];
  addSellerParking: (parking: SellerParking) => void;
  updateSellerParking: (id: string, updates: Partial<SellerParking>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Auth State
  user: null,
  userProfile: null,
  isLoading: true,
  setUser: (user) => set({ user }),
  setUserProfile: (profile) => set({ userProfile: profile }),
  signOut: async () => {
    await supabase.auth.signOut();
    set({ user: null, userProfile: null, viewMode: 'free', sellerParkings: [] });
  },

  // View Mode
  viewMode: 'free',
  setViewMode: (mode) => set({ viewMode: mode }),

  // Map State
  selectedLocation: null,
  setSelectedLocation: (location) => set({ selectedLocation: location }),
  
  // Navigation
  currentRoute: null,
  setCurrentRoute: (route) => set({ currentRoute: route }),

  // Paid Parkings
  paidParkings: paidParkingsData as PaidParking[],
  setPaidParkings: (parkings) => set({ paidParkings: parkings }),
  updateParkingAvailability: (id, available) =>
    set((state) => ({
      paidParkings: state.paidParkings.map((p) =>
        p.id === id ? { ...p, available } : p
      ),
    })),
  addReview: (parkingId, review) =>
    set((state) => ({
      paidParkings: state.paidParkings.map((p) =>
        p.id === parkingId
          ? {
              ...p,
              reviews: [...(p.reviews || []), review],
              rating:
                (p.rating * (p.reviews?.length || 0) + review.rating) /
                ((p.reviews?.length || 0) + 1),
            }
          : p
      ),
    })),

  // Filters & Sort
  filters: {},
  setFilters: (filters) => set({ filters }),
  sortBy: null,
  sortDirection: 'asc',
  setSorting: (sortBy, direction) => set({ sortBy, sortDirection: direction }),

  // Bookings
  bookings: [],
  addBooking: (booking) =>
    set((state) => ({
      bookings: [...state.bookings, booking],
    })),
  completeBooking: (id) =>
    set((state) => ({
      bookings: state.bookings.map((b) =>
        b.id === id ? { ...b, status: 'completed' } : b
      ),
    })),

  // Seller Mode
  sellerParkings: [],
  addSellerParking: (parking) =>
    set((state) => ({
      sellerParkings: [...state.sellerParkings, parking],
      paidParkings: [...state.paidParkings, parking],
    })),
  updateSellerParking: (id, updates) =>
    set((state) => ({
      sellerParkings: state.sellerParkings.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
      paidParkings: state.paidParkings.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),
}));
