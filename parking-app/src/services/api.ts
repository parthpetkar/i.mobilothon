import { supabase } from '../lib/supabase';
import { PaidParking, Booking, SellerParking } from '../types';
import { BACKEND_URL, ML_SERVICE_URL } from '../config/env';

const API_BASE_URL = BACKEND_URL;

// Helper function to get auth token
async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

// Helper function to make authenticated requests
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = await getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true', // Skip ngrok warning page
  };
  
  // Merge existing headers
  if (options.headers) {
    Object.entries(options.headers).forEach(([key, value]) => {
      if (typeof value === 'string') {
        headers[key] = value;
      }
    });
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    console.log(`[API] Fetching: ${url}`);
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    console.log(`[API] Response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API] Error response:`, errorText);
      
      try {
        const error = JSON.parse(errorText);
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      } catch {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    }
    
    return response.json();
  } catch (error: any) {
    console.error(`[API] Request failed:`, error);
    if (error.message === 'Network request failed') {
      throw new Error('Cannot connect to server. Please check your internet connection and backend URL.');
    }
    throw error;
  }
}

// ============================================
// PARKING APIs
// ============================================

export interface GetParkingsParams {
  location: [number, number]; // [longitude, latitude]
  radius?: number; // in meters
  price_min?: number;
  price_max?: number;
}

export interface CreateParkingData {
  name: string;
  location: [number, number]; // [longitude, latitude]
  slots: number;
  available: number;
  amenities?: string[];
}

export interface UpdateParkingData {
  name?: string;
  location?: [number, number];
  price_per_hour?: number;
  slots?: number;
  amenities?: string[];
}

export interface ParkingApiResponse {
  id: number;
  name: string;
  location: [number, number];
  price_per_hour: number;
  slots: number;
  available: number;
  amenities: string[];
  rating: number;
  seller_id?: string;
}

/**
 * Get parkings near a location
 */
export async function getParkingsNear(params: GetParkingsParams): Promise<PaidParking[]> {
  const { location, radius = 10000, price_min = 0, price_max = 99999 } = params;
  
  const url = new URL(`${API_BASE_URL}/parkings/`);
  url.searchParams.append('location', location[0].toString());
  url.searchParams.append('location', location[1].toString());
  url.searchParams.append('radius', radius.toString());
  url.searchParams.append('price_min', price_min.toString());
  url.searchParams.append('price_max', price_max.toString());
  
  const data: ParkingApiResponse[] = await fetchWithAuth(url.toString());
  console.log('[API] Get parkings near response:', data);
  // Transform API response to frontend format
  return data.map(parking => ({
    id: parking.id.toString(),
    name: parking.name,
    lat: parking.location[1],
    lng: parking.location[0],
    price: parking.price_per_hour,
    slots: parking.slots,
    available: parking.available,
    rating: parking.rating,
    amenities: parking.amenities || [],
    images: [],
    reviews: [],
  }));
}

/**
 * Create a new parking (seller only)
 */
export async function createParking(parkingData: CreateParkingData): Promise<PaidParking> {
  const response = await fetchWithAuth(`${API_BASE_URL}/parkings/`, {
    method: 'POST',
    body: JSON.stringify(parkingData),
  });
  
  const parking: ParkingApiResponse = response.parking;
  
  return {
    id: parking.id.toString(),
    name: parking.name,
    lat: parking.location[1],
    lng: parking.location[0],
    price: parking.price_per_hour,
    slots: parking.slots,
    available: parking.available,
    rating: parking.rating,
    amenities: parking.amenities || [],
    images: [],
    reviews: [],
  };
}

/**
 * Update a parking (seller only)
 */
export async function updateParking(parkingId: number, updates: UpdateParkingData): Promise<PaidParking> {
  const response = await fetchWithAuth(`${API_BASE_URL}/parkings/${parkingId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  
  const parking: ParkingApiResponse = response.parking;
  
  return {
    id: parking.id.toString(),
    name: parking.name,
    lat: parking.location[1],
    lng: parking.location[0],
    price: parking.price_per_hour,
    slots: parking.slots,
    available: parking.available,
    rating: parking.rating,
    amenities: parking.amenities || [],
    images: [],
    reviews: [],
  };
}

/**
 * Delete a parking (seller only)
 */
export async function deleteParking(parkingId: number): Promise<void> {
  await fetchWithAuth(`${API_BASE_URL}/parkings/${parkingId}`, {
    method: 'DELETE',
  });
}

/**
 * Update parking availability (seller only)
 */
export async function updateParkingAvailability(parkingId: number, available: number): Promise<void> {
  await fetchWithAuth(`${API_BASE_URL}/parkings/${parkingId}/availability`, {
    method: 'PUT',
    body: JSON.stringify({ available }),
  });
}

// ============================================
// BOOKING APIs
// ============================================

export interface CreateBookingData {
  parkingId: number;
  startTime: string; // ISO string
  endTime: string; // ISO string
}

export interface UpdateBookingData {
  endTime: string; // ISO string
}

export interface BookingApiResponse {
  id: number;
  parking_id: number;
  user_email: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  total_price: number;
  status: string;
  qr_code: string;
  parking_name?: string;
}

/**
 * Create a new booking
 */
export async function createBooking(bookingData: CreateBookingData): Promise<Booking> {
  const response = await fetchWithAuth(`${API_BASE_URL}/bookings/`, {
    method: 'POST',
    body: JSON.stringify(bookingData),
  });
  
  const booking: BookingApiResponse = response.booking;
  
  return {
    id: booking.id.toString(),
    parkingId: booking.parking_id.toString(),
    parkingName: booking.parking_name || 'Unknown Parking',
    duration: booking.duration_hours,
    totalPrice: booking.total_price,
    timestamp: booking.start_time,
    qrCode: booking.qr_code,
    status: booking.status === 'completed' ? 'completed' : 'active',
    userId: booking.user_email,
  };
}

/**
 * Get all bookings for current user
 */
export async function getUserBookings(): Promise<Booking[]> {
  const data: BookingApiResponse[] = await fetchWithAuth(`${API_BASE_URL}/bookings/`);
  
  return data.map(booking => ({
    id: booking.id.toString(),
    parkingId: booking.parking_id.toString(),
    parkingName: booking.parking_name || 'Unknown Parking',
    duration: booking.duration_hours,
    totalPrice: booking.total_price,
    timestamp: booking.start_time,
    qrCode: booking.qr_code,
    status: booking.status === 'completed' ? 'completed' : 'active',
    userId: booking.user_email,
  }));
}

/**
 * Get a specific booking by ID
 */
export async function getBookingById(bookingId: number): Promise<Booking> {
  const booking: BookingApiResponse = await fetchWithAuth(`${API_BASE_URL}/bookings/${bookingId}`);
  
  return {
    id: booking.id.toString(),
    parkingId: booking.parking_id.toString(),
    parkingName: booking.parking_name || 'Unknown Parking',
    duration: booking.duration_hours,
    totalPrice: booking.total_price,
    timestamp: booking.start_time,
    qrCode: booking.qr_code,
    status: booking.status === 'completed' ? 'completed' : 'active',
    userId: booking.user_email,
  };
}

/**
 * Update a booking (extend end time)
 */
export async function updateBooking(bookingId: number, updates: UpdateBookingData): Promise<Booking> {
  const response = await fetchWithAuth(`${API_BASE_URL}/bookings/${bookingId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  
  const booking: BookingApiResponse = response.booking;
  
  return {
    id: booking.id.toString(),
    parkingId: booking.parking_id.toString(),
    parkingName: booking.parking_name || 'Unknown Parking',
    duration: booking.duration_hours,
    totalPrice: booking.total_price,
    timestamp: booking.start_time,
    qrCode: booking.qr_code,
    status: booking.status === 'completed' ? 'completed' : 'active',
    userId: booking.user_email,
  };
}

/**
 * Cancel a booking
 */
export async function cancelBooking(bookingId: number): Promise<void> {
  await fetchWithAuth(`${API_BASE_URL}/bookings/${bookingId}`, {
    method: 'DELETE',
  });
}

// ============================================
// SELLER APIs
// ============================================

export interface AnalyticsResponse {
  total_bookings: number;
  total_revenue: number;
  avg_occupancy_rate: number;
  active_parkings: number;
}

export interface SellerParkingResponse {
  id: number;
  name: string;
  lat: number;
  lng: number;
  price_per_hour: number;
  slots: number;
  available: number;
  amenities: string[];
  rating: number;
  total_bookings: number;
  total_revenue: number;
  avg_rating: number;
}

/**
 * Get seller analytics
 */
export async function getSellerAnalytics(): Promise<AnalyticsResponse> {
  return await fetchWithAuth(`${API_BASE_URL}/seller/analytics`);
}

/**
 * Get seller's parkings with analytics
 */
export async function getSellerParkings(): Promise<SellerParking[]> {
  const data: any[] = await fetchWithAuth(`${API_BASE_URL}/seller/parkings`);
  console.log('[API] Seller parkings response:', data);
  return data.map(parking => {
    // Coerce types for fields that may be returned as strings
    const price = typeof parking.price === 'string' ? parseFloat(parking.price) : (parking.price_per_hour !== undefined ? Number(parking.price_per_hour) : 0);
    const rating = typeof parking.rating === 'string' ? parseFloat(parking.rating) : (parking.rating !== undefined ? Number(parking.rating) : 0);
    const dailyRevenue = typeof parking.daily_revenue === 'string' ? parseFloat(parking.daily_revenue) : (parking.total_revenue !== undefined ? Number(parking.total_revenue) : 0);
    const slots = typeof parking.slots === 'string' ? parseInt(parking.slots, 10) : (parking.slots !== undefined ? Number(parking.slots) : 0);
    const available = typeof parking.available === 'string' ? parseInt(parking.available, 10) : (parking.available !== undefined ? Number(parking.available) : 0);
    return {
      id: parking.id.toString(),
      name: parking.name,
      lat: typeof parking.lat === 'string' ? parseFloat(parking.lat) : parking.lat,
      lng: typeof parking.lng === 'string' ? parseFloat(parking.lng) : parking.lng,
      price,
      slots,
      available,
      rating,
      amenities: parking.amenities || [],
      images: [],
      reviews: [],
      ownerId: '', // Will be set from auth
      dailyRevenue,
      occupancyRate: slots > 0 ? ((slots - available) / slots) * 100 : 0,
    };
  });
}

// ============================================
// ML/Prediction APIs (if needed)
// ============================================

export interface PredictionParams {
  location: [number, number]; // [longitude, latitude]
  datetime?: string; // ISO string
}

export interface PredictionResponse {
  predictions: Array<{
    lat: number;
    lng: number;
    probability: number;
    radius: number;
  }>;
}

/**
 * Get parking availability predictions (requires ML service)
 */
export async function getParkingPredictions(params: PredictionParams): Promise<PredictionResponse> {
  const response = await fetch(`${ML_SERVICE_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });
  
  if (!response.ok) {
    throw new Error(`ML API error: ${response.status}`);
  }
  
  return response.json();
}
