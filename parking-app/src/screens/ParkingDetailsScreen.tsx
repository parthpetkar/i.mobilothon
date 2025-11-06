import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  TextInput,
  Dimensions,
  Alert,
} from 'react-native';
import { PaidParking } from '../types';
import { amenityIcons, formatCurrency, getAvailabilityLabel, getAvailabilityColor } from '../utils/helpers';
import { useAppStore } from '../store/appStore';

const { width } = Dimensions.get('window');

export default function ParkingDetailsScreen({ route, navigation }: any) {
  const { parking }: { parking: PaidParking } = route.params;
  const { user } = useAppStore();
  const [duration, setDuration] = useState(2);
  const totalPrice = parking.price * duration;

  const handleBooking = () => {
    if (!user) {
      Alert.alert(
        'Login Required',
        'Please login to book parking',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Login', onPress: () => navigation.navigate('Login') },
        ]
      );
      return;
    }
    navigation.navigate('BookingConfirmation', { parking, duration, totalPrice });
  };

  return (
    <ScrollView style={styles.container}>
      {/* Image Gallery */}
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        style={styles.imageGallery}
      >
        {parking.images && parking.images.length > 0 ? (
          parking.images.map((image, index) => (
            <Image key={index} source={{ uri: image }} style={styles.image} />
          ))
        ) : (
          <View style={styles.placeholderImage}>
            <Text style={styles.placeholderText}>🅿️</Text>
          </View>
        )}
      </ScrollView>

      {/* Parking Info */}
      <View style={styles.infoContainer}>
        <Text style={styles.name}>{parking.name}</Text>
        <View style={styles.ratingContainer}>
          <Text style={styles.rating}>⭐ {parking.rating}</Text>
          <Text style={styles.reviewCount}>
            ({parking.reviews?.length || 0} reviews)
          </Text>
        </View>

        {/* Price */}
        <View style={styles.priceContainer}>
          <Text style={styles.priceLabel}>Price per hour</Text>
          <Text style={styles.price}>{formatCurrency(parking.price)}/hr</Text>
        </View>

        {/* Availability */}
        <View style={styles.availabilityContainer}>
          <View
            style={[
              styles.availabilityIndicator,
              { backgroundColor: getAvailabilityColor(parking.available, parking.slots) },
            ]}
          />
          <View>
            <Text style={styles.availabilityLabel}>
              {getAvailabilityLabel(parking.available, parking.slots)}
            </Text>
            <Text style={styles.availabilityDetail}>
              {parking.available} of {parking.slots} slots available
            </Text>
          </View>
        </View>

        {/* Amenities */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Amenities</Text>
          <View style={styles.amenitiesContainer}>
            {parking.amenities.map((amenity, index) => (
              <View key={index} style={styles.amenityBadge}>
                <Text style={styles.amenityIcon}>{amenityIcons[amenity] || '•'}</Text>
                <Text style={styles.amenityText}>{amenity}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Time-Based Pricing Calculator */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Calculate Your Cost</Text>
          <View style={styles.calculatorContainer}>
            <Text style={styles.calculatorLabel}>Duration (hours)</Text>
            <View style={styles.durationControl}>
              <TouchableOpacity
                style={styles.durationButton}
                onPress={() => setDuration(Math.max(1, duration - 1))}
              >
                <Text style={styles.durationButtonText}>-</Text>
              </TouchableOpacity>
              <TextInput
                style={styles.durationInput}
                value={duration.toString()}
                onChangeText={(text) => {
                  const num = parseInt(text) || 1;
                  setDuration(Math.max(1, Math.min(24, num)));
                }}
                keyboardType="number-pad"
              />
              <TouchableOpacity
                style={styles.durationButton}
                onPress={() => setDuration(Math.min(24, duration + 1))}
              >
                <Text style={styles.durationButtonText}>+</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.priceBreakdown}>
              <Text style={styles.breakdownText}>
                {duration}h × {formatCurrency(parking.price)}/h = {formatCurrency(totalPrice)}
              </Text>
            </View>
          </View>
        </View>

        {/* Reviews */}
        {parking.reviews && parking.reviews.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Reviews</Text>
            {parking.reviews.map((review) => (
              <View key={review.id} style={styles.reviewCard}>
                <View style={styles.reviewHeader}>
                  <Text style={styles.reviewUserName}>{review.userName}</Text>
                  <Text style={styles.reviewRating}>⭐ {review.rating}</Text>
                </View>
                <Text style={styles.reviewComment}>{review.comment}</Text>
                <Text style={styles.reviewDate}>{review.date}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Book Now Button */}
      <View style={styles.footer}>
        <View>
          <Text style={styles.footerLabel}>Total Cost</Text>
          <Text style={styles.footerPrice}>{formatCurrency(totalPrice)}</Text>
        </View>
        <TouchableOpacity style={styles.bookButton} onPress={handleBooking}>
          <Text style={styles.bookButtonText}>Book Now</Text>
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
  imageGallery: {
    height: 250,
  },
  image: {
    width: width,
    height: 250,
    resizeMode: 'cover',
  },
  placeholderImage: {
    width: width,
    height: 250,
    backgroundColor: '#e5e7eb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 80,
  },
  infoContainer: {
    padding: 20,
    paddingBottom: 100,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  rating: {
    fontSize: 16,
    marginRight: 5,
  },
  reviewCount: {
    fontSize: 14,
    color: '#666',
  },
  priceContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  priceLabel: {
    fontSize: 14,
    color: '#666',
  },
  price: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  availabilityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    padding: 15,
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
  },
  availabilityIndicator: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 15,
  },
  availabilityLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 3,
  },
  availabilityDetail: {
    fontSize: 14,
    color: '#666',
  },
  section: {
    marginBottom: 25,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  amenitiesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  amenityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e0f2fe',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  amenityIcon: {
    fontSize: 16,
    marginRight: 5,
  },
  amenityText: {
    fontSize: 14,
    color: '#0284c7',
    fontWeight: '600',
  },
  calculatorContainer: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
  },
  calculatorLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  durationControl: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 15,
  },
  durationButton: {
    width: 50,
    height: 50,
    backgroundColor: '#3b82f6',
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
  },
  durationButtonText: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  durationInput: {
    width: 80,
    height: 50,
    backgroundColor: 'white',
    borderRadius: 10,
    textAlign: 'center',
    fontSize: 20,
    fontWeight: 'bold',
    marginHorizontal: 20,
  },
  priceBreakdown: {
    alignItems: 'center',
  },
  breakdownText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3b82f6',
  },
  reviewCard: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  reviewUserName: {
    fontSize: 16,
    fontWeight: '600',
  },
  reviewRating: {
    fontSize: 14,
  },
  reviewComment: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  reviewDate: {
    fontSize: 12,
    color: '#999',
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 5,
  },
  footerLabel: {
    fontSize: 14,
    color: '#666',
  },
  footerPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  bookButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 40,
    paddingVertical: 15,
    borderRadius: 10,
  },
  bookButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
