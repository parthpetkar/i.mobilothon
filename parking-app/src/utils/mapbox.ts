import { MAPBOX_ACCESS_TOKEN } from '../config/env';

export interface MapboxFeature {
  id: string;
  place_name: string;
  center: [number, number];
  text: string;
}

export interface MapboxSearchResponse {
  features: MapboxFeature[];
}

// Search for locations using Mapbox Geocoding API
export const searchLocation = async (query: string): Promise<MapboxFeature[]> => {
  if (!query || query.length < 2) return [];

  try {
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
        query
      )}.json?access_token=${MAPBOX_ACCESS_TOKEN}&proximity=73.8567,18.5204&limit=5`
    );

    const data: MapboxSearchResponse = await response.json();
    return data.features || [];
  } catch (error) {
    console.error('Geocoding error:', error);
    return [];
  }
};

// Get navigation route using Mapbox Directions API
export const getNavigationRoute = async (
  start: [number, number],
  end: [number, number]
) => {
  try {
    const response = await fetch(
      `https://api.mapbox.com/directions/v5/mapbox/driving/${start[0]},${start[1]};${end[0]},${end[1]}?geometries=geojson&access_token=${MAPBOX_ACCESS_TOKEN}`
    );

    const data = await response.json();
    
    if (data.routes && data.routes.length > 0) {
      return {
        distance: data.routes[0].distance,
        duration: data.routes[0].duration,
        geometry: data.routes[0].geometry,
      };
    }
    
    return null;
  } catch (error) {
    console.error('Navigation error:', error);
    return null;
  }
};

// Reverse geocode to get address from coordinates
export const reverseGeocode = async (
  longitude: number,
  latitude: number
): Promise<string> => {
  try {
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${longitude},${latitude}.json?access_token=${MAPBOX_ACCESS_TOKEN}`
    );

    const data: MapboxSearchResponse = await response.json();
    
    if (data.features && data.features.length > 0) {
      return data.features[0].place_name;
    }
    
    return 'Unknown location';
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    return 'Unknown location';
  }
};
