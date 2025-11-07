import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import Mapbox, { Camera, MarkerView } from '@rnmapbox/maps';
import { useAppStore } from '../store/appStore';
import { SellerParking } from '../types';

const PUNE_CENTER = [73.8567, 18.5204]; // [lng, lat] for Mapbox

export default function AddListingScreen({ navigation }: any) {
  const { createSellerParking, user } = useAppStore();
  const [name, setName] = useState('');
  const [slots, setSlots] = useState('');
  const [location, setLocation] = useState<{ lat: number; lng: number }>({
    lat: PUNE_CENTER[1],
    lng: PUNE_CENTER[0],
  });
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const cameraRef = useRef<Camera>(null);

  const availableAmenities = ['CCTV', 'Covered', 'EV Charging', 'Toilets'];

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities((prev) =>
      prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity]
    );
  };

  const handleSubmit = async () => {
    if (!user) {
      Alert.alert('Error', 'You must be logged in to add parking');
      navigation.navigate('Login');
      return;
    }

    if (!name.trim()) {
      Alert.alert('Error', 'Please enter parking name');
      return;
    }
    if (!slots || parseInt(slots) <= 0) {
      Alert.alert('Error', 'Please enter valid number of slots');
      return;
    }

    setIsSubmitting(true);

    try {
      const parkingData = {
        name: name.trim(),
        location: [location.lng, location.lat] as [number, number],
        slots: parseInt(slots),
        available: parseInt(slots),
        amenities: selectedAmenities,
      };

      await createSellerParking(parkingData);
      
      Alert.alert('Success', 'Parking listing added successfully!', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add parking. Please try again.');
      console.error('Add parking error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Add New Parking</Text>

        {/* Name Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Parking Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., Downtown Parking"
            value={name}
            onChangeText={setName}
          />
        </View>

        {/* Slots Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Total Slots *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., 50"
            value={slots}
            onChangeText={setSlots}
            keyboardType="number-pad"
          />
        </View>

        {/* Amenities Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Amenities</Text>
          <View style={styles.amenitiesContainer}>
            {availableAmenities.map((amenity) => (
              <TouchableOpacity
                key={amenity}
                style={[
                  styles.amenityButton,
                  selectedAmenities.includes(amenity) && styles.amenityButtonActive,
                ]}
                onPress={() => toggleAmenity(amenity)}
              >
                <Text
                  style={[
                    styles.amenityButtonText,
                    selectedAmenities.includes(amenity) && styles.amenityButtonTextActive,
                  ]}
                >
                  {amenity}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Map Location Picker */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Select Location *</Text>
          <Text style={styles.hint}>Long press on the map to set parking location</Text>
          <View style={styles.mapContainer}>
            <Mapbox.MapView
              style={styles.map}
              styleURL={Mapbox.StyleURL.Street}
              onLongPress={(feature: any) => {
                const coords = feature.geometry.coordinates;
                setLocation({ lat: coords[1], lng: coords[0] });
              }}
            >
              <Camera
                ref={cameraRef}
                zoomLevel={13}
                centerCoordinate={[location.lng, location.lat]}
              />
              <MarkerView coordinate={[location.lng, location.lat]}>
                <View style={styles.markerPin}>
                  <Text style={styles.markerPinText}>📍</Text>
                </View>
              </MarkerView>
            </Mapbox.MapView>
          </View>
          <Text style={styles.coordinates}>
            Lat: {location.lat.toFixed(4)}, Lng: {location.lng.toFixed(4)}
          </Text>
        </View>

        {/* Submit Button */}
        <TouchableOpacity 
          style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]} 
          onPress={handleSubmit}
          disabled={isSubmitting}
        >
          <Text style={styles.submitButtonText}>
            {isSubmitting ? 'Adding Parking...' : 'Add Parking'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 25,
  },
  inputGroup: {
    marginBottom: 25,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#374151',
  },
  hint: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
  },
  amenitiesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  amenityButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    backgroundColor: 'white',
  },
  amenityButtonActive: {
    borderColor: '#3b82f6',
    backgroundColor: '#3b82f6',
  },
  amenityButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  amenityButtonTextActive: {
    color: 'white',
  },
  mapContainer: {
    height: 300,
    borderRadius: 15,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  map: {
    width: '100%',
    height: '100%',
  },
  coordinates: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  markerPin: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerPinText: {
    fontSize: 30,
  },
  submitButton: {
    backgroundColor: '#3b82f6',
    padding: 18,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    backgroundColor: 'transparent',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e5e7eb',
  },
  cancelButtonText: {
    color: '#6b7280',
    fontSize: 16,
    fontWeight: '600',
  },
});
