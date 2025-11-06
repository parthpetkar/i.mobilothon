import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import Mapbox, { Camera, MarkerView, ShapeSource, CircleLayer, LineLayer, LocationPuck } from '@rnmapbox/maps';
import * as Location from 'expo-location';
import { useAppStore } from '../store/appStore';
import { FreeHotspot } from '../types';
import freeHotspotsData from '../data/freeHotspots.json';
import { calculateDistance, getProbabilityLabel, getAvailabilityColor } from '../utils/helpers';
import { searchLocation, getNavigationRoute } from '../utils/mapbox';

const PUNE_CENTER = [73.8567, 18.5204]; // [lng, lat] for Mapbox

export default function MapHomeScreen({ navigation }: any) {
  const { viewMode, setViewMode, paidParkings, selectedLocation, setSelectedLocation, setCurrentRoute, currentRoute, user, fetchParkingsNear } =
    useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [mapCenter, setMapCenter] = useState(PUNE_CENTER);
  const [selectedHotspot, setSelectedHotspot] = useState<any>(null);
  const [selectedParking, setSelectedParking] = useState<any>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [locationPermission, setLocationPermission] = useState(false);
  const cameraRef = useRef<Camera>(null);

  const freeHotspots: FreeHotspot[] = freeHotspotsData;

  // Get user location on mount
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === 'granted') {
          setLocationPermission(true);
          const location = await Location.getCurrentPositionAsync({});
          const userCoords: [number, number] = [
            location.coords.longitude,
            location.coords.latitude,
          ];
          setUserLocation(userCoords);
          setMapCenter(userCoords);
          setSelectedLocation({
            lat: location.coords.latitude,
            lng: location.coords.longitude,
          });
        } else {
          Alert.alert(
            'Location Permission',
            'Location permission is needed for navigation features',
            [{ text: 'OK' }]
          );
        }
      } catch (error) {
        console.error('Error getting location:', error);
      }
    })();
  }, []);

  // Fetch parkings when location changes (for paid mode)
  useEffect(() => {
    if (viewMode === 'paid' && selectedLocation) {
      const location: [number, number] = [selectedLocation.lng, selectedLocation.lat];
      fetchParkingsNear(location, 10000); // 10km radius
    }
  }, [selectedLocation, viewMode]);

  // Handle search with Mapbox Geocoding
  const handleSearchInput = async (query: string) => {
    setSearchQuery(query);
    if (query.length > 2) {
      setIsSearching(true);
      try {
        const results = await searchLocation(query);
        setSearchResults(results);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleSelectLocation = (result: any) => {
    const [lng, lat] = result.center;
    setMapCenter([lng, lat]);
    setSelectedLocation({ lat, lng });
    setSearchQuery(result.place_name);
    setSearchResults([]);
    
    // Animate camera to new location
    cameraRef.current?.setCamera({
      centerCoordinate: [lng, lat],
      zoomLevel: 14,
      animationDuration: 1000,
    });
  };

  const nearestHotspots = useMemo(() => {
    if (!selectedLocation) return freeHotspots;
    return freeHotspots
      .map((h) => ({
        ...h,
        distance: calculateDistance(selectedLocation.lat, selectedLocation.lng, h.lat, h.lng),
      }))
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 5);
  }, [selectedLocation]);

  const nearestPaidParkings = useMemo(() => {
    if (!selectedLocation) return paidParkings;
    return paidParkings
      .map((p) => ({
        ...p,
        distance: calculateDistance(selectedLocation.lat, selectedLocation.lng, p.lat, p.lng),
      }))
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 10);
  }, [selectedLocation, paidParkings]);

  const handleNavigate = async (lat: number, lng: number) => {
    try {
      // Get user's current location
      let from: [number, number];
      
      if (userLocation) {
        from = userLocation;
      } else {
        // Try to get current location
        const location = await Location.getCurrentPositionAsync({});
        from = [location.coords.longitude, location.coords.latitude];
      }
      
      const to: [number, number] = [lng, lat];
      
      Alert.alert(
        'Getting directions...',
        'Please wait',
        [],
        { cancelable: false }
      );
      
      const route = await getNavigationRoute(from, to);
      
      if (route) {
        setCurrentRoute(route);
        
        // Close any open popups
        setSelectedHotspot(null);
        setSelectedParking(null);
        
        // Fit the camera to show the entire route
        if (cameraRef.current && route.geometry.coordinates.length > 0) {
          const coords = route.geometry.coordinates;
          const lngs = coords.map((c: [number, number]) => c[0]);
          const lats = coords.map((c: [number, number]) => c[1]);
          
          const bounds = {
            ne: [Math.max(...lngs), Math.max(...lats)],
            sw: [Math.min(...lngs), Math.min(...lats)],
          };
          
          cameraRef.current.fitBounds(
            bounds.ne as [number, number],
            bounds.sw as [number, number],
            [50, 50, 50, 50], // padding
            1000 // animation duration
          );
        }
        
        Alert.alert(
          '🗺️ Route Found',
          `Distance: ${(route.distance / 1000).toFixed(2)} km\nEstimated time: ${(route.duration / 60).toFixed(0)} mins`,
          [
            {
              text: 'Clear Route',
              style: 'destructive',
              onPress: () => setCurrentRoute(null)
            },
            { text: 'OK' }
          ]
        );
      } else {
        Alert.alert('Error', 'Could not find a route');
      }
    } catch (error) {
      console.error('Navigation error:', error);
      Alert.alert('Error', 'Could not get navigation route. Please check your internet connection.');
    }
  };

  // Create GeoJSON for heatmap circles
  const heatmapGeoJSON: any = useMemo(() => {
    return {
      type: 'FeatureCollection' as const,
      features: nearestHotspots.map((hotspot, index) => ({
        type: 'Feature' as const,
        id: `hotspot-${index}`,
        properties: {
          probability: hotspot.probability,
          radius: hotspot.radius || 100, // Use custom radius in meters or default to 100m
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [hotspot.lng, hotspot.lat],
        },
      })),
    };
  }, [nearestHotspots]);

  return (
    <View style={styles.container}>
      {/* Mapbox Map */}
      <Mapbox.MapView style={styles.map} styleURL={Mapbox.StyleURL.Street}>
        <Camera
          ref={cameraRef}
          zoomLevel={12}
          centerCoordinate={mapCenter}
          animationMode="flyTo"
        />

        {/* User Location */}
        {locationPermission && <LocationPuck pulsing={{ isEnabled: true }} />}

        {/* Free Parking Heatmap Circles */}
        {(viewMode === 'free' || viewMode === 'seller') && (
          <ShapeSource id="heatmapSource" shape={heatmapGeoJSON}>
            <CircleLayer
              id="heatmapCircles"
              style={{
                circlePitchAlignment: 'map',
                circleRadius: [
                  'interpolate',
                  ['exponential', 2],
                  ['zoom'],
                  0, 0,
                  20, ['*', ['/', ['get', 'radius'], 0.075], ['/', 1, ['^', 2, ['-', 20, ['zoom']]]]]
                ],
                circleColor: [
                  'interpolate',
                  ['linear'],
                  ['get', 'probability'],
                  0,
                  'rgba(34, 197, 94, 0.2)',
                  1,
                  'rgba(34, 197, 94, 0.6)',
                ],
                circleStrokeWidth: 2,
                circleStrokeColor: 'rgba(34, 197, 94, 0.8)',
              }}
            />
          </ShapeSource>
        )}

        {/* Navigation Route */}
        {currentRoute && (
          <ShapeSource
            id="routeSource"
            shape={{
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: currentRoute.geometry.coordinates,
              },
            }}
          >
            <LineLayer
              id="routeLine"
              style={{
                lineColor: '#3b82f6',
                lineWidth: 5,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
            <LineLayer
              id="routeLineOutline"
              style={{
                lineColor: '#1e40af',
                lineWidth: 7,
                lineCap: 'round',
                lineJoin: 'round',
              }}
              belowLayerID="routeLine"
            />
          </ShapeSource>
        )}

        {/* Free Parking Markers */}
        {(viewMode === 'free' || viewMode === 'seller') &&
          nearestHotspots.map((hotspot, index) => (
            <MarkerView
              key={`hotspot-${index}`}
              coordinate={[hotspot.lng, hotspot.lat]}
              anchor={{ x: 0.5, y: 0.5 }}
            >
              <TouchableOpacity
                style={styles.hotspotMarker}
                onPress={() => {
                  console.log('Hotspot clicked:', hotspot.label);
                  setSelectedParking(null);
                  setSelectedHotspot(hotspot);
                }}
                onPressOut={() => {
                  console.log('Hotspot touched:', hotspot.label);
                  setSelectedParking(null);
                  setSelectedHotspot(hotspot);
                }}
                activeOpacity={0.7}
                hitSlop={{ top: 20, bottom: 20, left: 20, right: 20 }}
              >
                <Text style={styles.hotspotMarkerText}>🅿️</Text>
              </TouchableOpacity>
            </MarkerView>
          ))}

        {/* Paid Parking Markers */}
        {(viewMode === 'paid' || viewMode === 'seller') &&
          nearestPaidParkings.map((parking) => (
            <MarkerView
              key={parking.id}
              coordinate={[parking.lng, parking.lat]}
              anchor={{ x: 0.5, y: 0.5 }}
            >
              <TouchableOpacity
                style={[
                  styles.paidMarker,
                  { backgroundColor: getAvailabilityColor(parking.available, parking.slots) },
                ]}
                onPress={() => {
                  console.log('Parking clicked:', parking.name);
                  setSelectedHotspot(null);
                  setSelectedParking(parking);
                }}
                onPressOut={() => {
                  console.log('Parking touched:', parking.name);
                  setSelectedHotspot(null);
                  setSelectedParking(parking);
                }}
                activeOpacity={0.7}
                hitSlop={{ top: 15, bottom: 15, left: 15, right: 15 }}
              >
                <Text style={styles.paidMarkerText}>₹{parking.price}</Text>
              </TouchableOpacity>
            </MarkerView>
          ))}
      </Mapbox.MapView>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search location..."
          value={searchQuery}
          onChangeText={handleSearchInput}
        />
        {isSearching && (
          <View style={styles.searchLoading}>
            <ActivityIndicator size="small" color="#3b82f6" />
          </View>
        )}
        {searchResults.length > 0 && (
          <View style={styles.suggestions}>
            {searchResults.map((result, index) => (
              <TouchableOpacity
                key={index}
                style={styles.suggestionItem}
                onPress={() => handleSelectLocation(result)}
              >
                <Text style={styles.suggestionText}>{result.place_name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>

      {/* Profile/Login Button */}
      <TouchableOpacity
        style={styles.profileButton}
        onPress={() => navigation.navigate(user ? 'Profile' : 'Login')}
      >
        <Text style={styles.profileButtonText}>
          {user ? '👤' : '🔐'}
        </Text>
      </TouchableOpacity>

      {/* Clear Route Button */}
      {currentRoute && (
        <TouchableOpacity
          style={styles.clearRouteButton}
          onPress={() => setCurrentRoute(null)}
        >
          <Text style={styles.clearRouteButtonText}>✕ Clear Route</Text>
        </TouchableOpacity>
      )}

      {/* View Toggle */}
      <View style={styles.toggleContainer}>
        <TouchableOpacity
          style={[styles.toggleButton, viewMode === 'free' && styles.toggleButtonActive]}
          onPress={() => setViewMode('free')}
        >
          <Text style={[styles.toggleText, viewMode === 'free' && styles.toggleTextActive]}>
            Free Parking
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.toggleButton, viewMode === 'paid' && styles.toggleButtonActive]}
          onPress={() => setViewMode('paid')}
        >
          <Text style={[styles.toggleText, viewMode === 'paid' && styles.toggleTextActive]}>
            Paid Parking
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.toggleButton, viewMode === 'seller' && styles.toggleButtonActive]}
          onPress={() => setViewMode('seller')}
        >
          <Text style={[styles.toggleText, viewMode === 'seller' && styles.toggleTextActive]}>
            Seller Mode
          </Text>
        </TouchableOpacity>
      </View>

      {/* Hotspot Popup */}
      {selectedHotspot && (
        <View style={styles.popup}>
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setSelectedHotspot(null)}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            activeOpacity={0.6}
          >
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <View style={styles.popupHeader}>
            <Text style={styles.popupIcon}>🅿️</Text>
            <View style={styles.popupHeaderText}>
              <Text style={styles.popupTitle}>{selectedHotspot.label}</Text>
              <Text style={styles.popupType}>Free Parking Hotspot</Text>
            </View>
          </View>
          <View style={styles.popupDivider} />
          <View style={styles.popupInfo}>
            <Text style={styles.popupInfoLabel}>Availability Probability</Text>
            <Text style={[styles.popupProbability, { color: selectedHotspot.probability > 0.7 ? '#22c55e' : selectedHotspot.probability > 0.5 ? '#f59e0b' : '#ef4444' }]}>
              {getProbabilityLabel(selectedHotspot.probability)} ({(selectedHotspot.probability * 100).toFixed(0)}%)
            </Text>
          </View>
          {selectedHotspot.distance && (
            <Text style={styles.popupDistance}>📍 {selectedHotspot.distance.toFixed(2)} km away</Text>
          )}
          <TouchableOpacity
            style={styles.navigateButton}
            onPress={() => handleNavigate(selectedHotspot.lat, selectedHotspot.lng)}
          >
            <Text style={styles.navigateButtonText}>🧭 Get Directions</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Paid Parking Popup */}
      {selectedParking && (
        <View style={styles.popup}>
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setSelectedParking(null)}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            activeOpacity={0.6}
          >
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <View style={styles.popupHeader}>
            <Text style={styles.popupIcon}>🏢</Text>
            <View style={styles.popupHeaderText}>
              <Text style={styles.popupTitle}>{selectedParking.name}</Text>
              <Text style={styles.popupType}>Paid Parking</Text>
            </View>
          </View>
          <View style={styles.popupDivider} />
          <View style={styles.popupPriceRow}>
            <View style={styles.popupPriceItem}>
              <Text style={styles.popupInfoLabel}>Price</Text>
              <Text style={styles.popupPrice}>₹{selectedParking.price}/hr</Text>
            </View>
            <View style={styles.popupPriceItem}>
              <Text style={styles.popupInfoLabel}>Available</Text>
              <Text style={[styles.popupAvailable, { color: getAvailabilityColor(selectedParking.available, selectedParking.slots) }]}>
                {selectedParking.available}/{selectedParking.slots}
              </Text>
            </View>
            <View style={styles.popupPriceItem}>
              <Text style={styles.popupInfoLabel}>Rating</Text>
              <Text style={styles.popupRating}>⭐ {selectedParking.rating}</Text>
            </View>
          </View>
          {selectedParking.distance && (
            <Text style={styles.popupDistance}>📍 {selectedParking.distance.toFixed(2)} km away</Text>
          )}
          {selectedParking.amenities && selectedParking.amenities.length > 0 && (
            <View style={styles.popupAmenities}>
              <Text style={styles.popupInfoLabel}>Amenities:</Text>
              <View style={styles.amenitiesRow}>
                {selectedParking.amenities.slice(0, 3).map((amenity: string, idx: number) => (
                  <Text key={idx} style={styles.amenityBadge}>{amenity}</Text>
                ))}
              </View>
            </View>
          )}
          <TouchableOpacity
            style={styles.viewDetailsButton}
            onPress={() => navigation.navigate('ParkingDetails', { parking: selectedParking })}
          >
            <Text style={styles.viewDetailsButtonText}>View Full Details & Book</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Paid Parking List (Bottom Sheet) */}
      {viewMode === 'paid' && !selectedParking && !selectedHotspot && (
        <View style={styles.bottomSheet}>
          <Text style={styles.bottomSheetTitle}>Nearby Paid Parking</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {nearestPaidParkings.map((parking) => (
              <TouchableOpacity
                key={parking.id}
                style={styles.parkingCard}
                onPress={() => setSelectedParking(parking)}
              >
                <Text style={styles.cardTitle}>{parking.name}</Text>
                <Text style={styles.cardPrice}>₹{parking.price}/hr</Text>
                <Text style={styles.cardAvailable}>
                  {parking.available}/{parking.slots} slots
                </Text>
                <Text style={styles.cardRating}>⭐ {parking.rating}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Seller Mode Button */}
      {viewMode === 'seller' && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => navigation.navigate('SellerDashboard')}
        >
          <Text style={styles.fabText}>📊</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    width: Dimensions.get('window').width,
    height: Dimensions.get('window').height,
  },
  searchContainer: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 80,
    zIndex: 10,
  },
  searchInput: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    fontSize: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  searchLoading: {
    position: 'absolute',
    right: 15,
    top: 15,
  },
  suggestions: {
    backgroundColor: 'white',
    marginTop: 5,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  suggestionItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  suggestionText: {
    fontSize: 14,
  },
  profileButton: {
    position: 'absolute',
    top: 50,
    right: 20,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'white',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
    zIndex: 20,
  },
  profileButtonText: {
    fontSize: 24,
  },
  clearRouteButton: {
    position: 'absolute',
    top: 50,
    left: 20,
    backgroundColor: '#ef4444',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
    zIndex: 20,
  },
  clearRouteButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  toggleContainer: {
    position: 'absolute',
    top: 120,
    left: 20,
    right: 20,
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  toggleButton: {
    flex: 1,
    padding: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  toggleButtonActive: {
    backgroundColor: '#3b82f6',
  },
  toggleText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  toggleTextActive: {
    color: 'white',
  },
  hotspotMarker: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#22c55e',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  hotspotMarkerText: {
    fontSize: 24,
  },
  paidMarker: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    minWidth: 60,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 6,
  },
  paidMarkerText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  popup: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 10,
    zIndex: 100,
  },
  closeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 101,
  },
  closeButtonText: {
    fontSize: 22,
    color: '#374151',
    fontWeight: 'bold',
  },
  popupTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  popupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  popupIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  popupHeaderText: {
    flex: 1,
  },
  popupType: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 2,
  },
  popupDivider: {
    height: 1,
    backgroundColor: '#e5e7eb',
    marginVertical: 12,
  },
  popupInfo: {
    marginBottom: 10,
  },
  popupInfoLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  popupProbability: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  popupDistance: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 12,
  },
  popupPriceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  popupPriceItem: {
    flex: 1,
    alignItems: 'center',
  },
  popupPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  popupAvailable: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  popupRating: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#f59e0b',
  },
  popupAmenities: {
    marginBottom: 12,
  },
  amenitiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 6,
  },
  amenityBadge: {
    backgroundColor: '#e0f2fe',
    color: '#0369a1',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    fontSize: 11,
    fontWeight: '600',
  },
  popupSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5,
  },
  popupDetail: {
    fontSize: 14,
    color: '#888',
    marginBottom: 3,
  },
  navigateButton: {
    marginTop: 15,
    backgroundColor: '#22c55e',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  navigateButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  viewDetailsButton: {
    marginTop: 15,
    backgroundColor: '#3b82f6',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  viewDetailsButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
    maxHeight: 200,
  },
  bottomSheetTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  parkingCard: {
    width: 150,
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    marginRight: 10,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  cardPrice: {
    fontSize: 16,
    color: '#3b82f6',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  cardAvailable: {
    fontSize: 12,
    color: '#666',
    marginBottom: 3,
  },
  cardRating: {
    fontSize: 12,
    color: '#666',
  },
  fab: {
    position: 'absolute',
    bottom: 30,
    right: 30,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#3b82f6',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  fabText: {
    fontSize: 24,
  },
});
