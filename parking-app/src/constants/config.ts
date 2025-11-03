// App Configuration Constants

export const MAP_CONFIG = {
  PUNE_CENTER: {
    latitude: 18.5204,
    longitude: 73.8567,
  },
  DEFAULT_ZOOM: 12,
  HEATMAP_RADIUS: 300,
};

export const COLORS = {
  primary: '#3b82f6',
  success: '#22c55e',
  warning: '#fbbf24',
  danger: '#ef4444',
  gray: {
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
};

export const AMENITY_CONFIG = {
  icons: {
    Covered: '☂',
    CCTV: '🎥',
    'EV Charging': '🔌',
    Toilets: '🚻',
  },
  colors: {
    Covered: '#e0f2fe',
    CCTV: '#dbeafe',
    'EV Charging': '#d1fae5',
    Toilets: '#fce7f3',
  },
};

export const PAYMENT_CONFIG = {
  TEST_MODE: true,
  PROCESSING_DELAY: 2000, // milliseconds
  CURRENCY: '₹',
};

export const APP_CONFIG = {
  APP_NAME: 'Smart Parking',
  VERSION: '2.0.0',
  DEFAULT_USER_NAME: 'Anonymous User',
};
