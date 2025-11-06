import { create } from 'zustand';
import { PaidParking, Booking, Review, ViewMode, FilterType, SortDirection, SellerParking, AuthUser, UserProfile, NavigationRoute } from '../types';
import paidParkingsData from '../data/paidParkings.json';
import { supabase } from '../lib/supabase';
import * as api from '../services/api';

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
  fetchParkingsNear: (location: [number, number], radius?: number) => Promise<void>;
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
  fetchBookings: () => Promise<void>;
  createBooking: (parkingId: number, startTime: Date, endTime: Date) => Promise<Booking>;
  cancelBooking: (id: string) => Promise<void>;
  addBooking: (booking: Booking) => void;
  completeBooking: (id: string) => void;

  // Seller Mode (Auth Protected)
  sellerParkings: SellerParking[];
  sellerAnalytics: api.AnalyticsResponse | null;
  fetchSellerParkings: () => Promise<void>;
  fetchSellerAnalytics: () => Promise<void>;
  createSellerParking: (parkingData: api.CreateParkingData) => Promise<void>;
  updateSellerParkingAvailability: (id: string, available: number) => Promise<void>;
  deleteSellerParking: (id: string) => Promise<void>;
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
  fetchParkingsNear: async (location: [number, number], radius?: number) => {
    try {
      const parkings = await api.getParkingsNear({ location, radius });
      set({ paidParkings: parkings });
    } catch (error) {
      console.error('Failed to fetch parkings:', error);
      // Fallback to static data on error
      set({ paidParkings: paidParkingsData as PaidParking[] });
    }
  },
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
  fetchBookings: async () => {
    try {
      const bookings = await api.getUserBookings();
      set({ bookings });
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    }
  },
  createBooking: async (parkingId: number, startTime: Date, endTime: Date) => {
    try {
      const booking = await api.createBooking({
        parkingId,
        startTime: startTime.toISOString(),
        endTime: endTime.toISOString(),
      });
      set((state) => ({
        bookings: [...state.bookings, booking],
      }));
      return booking;
    } catch (error) {
      console.error('Failed to create booking:', error);
      throw error;
    }
  },
  cancelBooking: async (id: string) => {
    try {
      await api.cancelBooking(parseInt(id));
      set((state) => ({
        bookings: state.bookings.filter((b) => b.id !== id),
      }));
    } catch (error) {
      console.error('Failed to cancel booking:', error);
      throw error;
    }
  },
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
  sellerAnalytics: null,
  fetchSellerParkings: async () => {
    try {
      const parkings = await api.getSellerParkings();
      set({ sellerParkings: parkings });
    } catch (error) {
      console.error('Failed to fetch seller parkings:', error);
    }
  },
  fetchSellerAnalytics: async () => {
    try {
      const analytics = await api.getSellerAnalytics();
      set({ sellerAnalytics: analytics });
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  },
  createSellerParking: async (parkingData: api.CreateParkingData) => {
    try {
      const parking = await api.createParking(parkingData);
      const sellerParking: SellerParking = {
        ...parking,
        ownerId: '', // Will be set from backend
        dailyRevenue: 0,
        occupancyRate: 0,
      };
      set((state) => ({
        sellerParkings: [...state.sellerParkings, sellerParking],
        paidParkings: [...state.paidParkings, parking],
      }));
    } catch (error) {
      console.error('Failed to create parking:', error);
      throw error;
    }
  },
  updateSellerParkingAvailability: async (id: string, available: number) => {
    try {
      await api.updateParkingAvailability(parseInt(id), available);
      set((state) => ({
        sellerParkings: state.sellerParkings.map((p) =>
          p.id === id ? { ...p, available } : p
        ),
        paidParkings: state.paidParkings.map((p) =>
          p.id === id ? { ...p, available } : p
        ),
      }));
    } catch (error) {
      console.error('Failed to update availability:', error);
      throw error;
    }
  },
  deleteSellerParking: async (id: string) => {
    try {
      await api.deleteParking(parseInt(id));
      set((state) => ({
        sellerParkings: state.sellerParkings.filter((p) => p.id !== id),
        paidParkings: state.paidParkings.filter((p) => p.id !== id),
      }));
    } catch (error) {
      console.error('Failed to delete parking:', error);
      throw error;
    }
  },
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
