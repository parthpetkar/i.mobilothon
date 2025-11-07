import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useAppStore } from '../store/appStore';
import { formatCurrency } from '../utils/helpers';

export default function SellerDashboardScreen({ navigation }: any) {
  const { 
    sellerParkings, 
    sellerAnalytics,
    updateSellerParkingAvailability, 
    fetchSellerParkings, 
    fetchSellerAnalytics,
    user, 
    userProfile 
  } = useAppStore();

  // Check if user is authenticated and is a seller
  useEffect(() => {
    if (!user) {
      Alert.alert(
        'Login Required',
        'Please login to access seller dashboard',
        [{ text: 'OK', onPress: () => navigation.navigate('Login') }]
      );
    } else if (!userProfile?.is_seller) {
      Alert.alert(
        'Seller Account Required',
        'You need a seller account to access this feature',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } else {
      // Fetch seller data when component mounts
      fetchSellerParkings();
      fetchSellerAnalytics();
    }
  }, [user, userProfile]);

  if (!user || !userProfile?.is_seller) {
    return null;
  }

  // Use analytics data from API if available, otherwise calculate from parkings
  const totalRevenue = sellerAnalytics?.total_revenue || sellerParkings.reduce(
    (sum, parking) => sum + (parking.dailyRevenue || 0),
    0
  );
  const totalSlots = sellerParkings.reduce((sum, parking) => sum + parking.slots, 0);
  const occupiedSlots = sellerParkings.reduce(
    (sum, parking) => sum + (parking.slots - parking.available),
    0
  );
  const avgOccupancy = sellerAnalytics?.avg_occupancy_rate 
    || (totalSlots > 0 ? ((occupiedSlots / totalSlots) * 100).toFixed(1) : 0);

  const handleUpdateAvailability = async (id: string, change: number) => {
    const parking = sellerParkings.find((p) => p.id === id);
    if (parking) {
      const newAvailable = Math.max(0, Math.min(parking.slots, parking.available + change));
      try {
        await updateSellerParkingAvailability(id, newAvailable);
      } catch (error) {
        Alert.alert('Error', 'Failed to update availability. Please try again.');
      }
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Seller Dashboard</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity
            style={styles.verifyButton}
            onPress={() => navigation.navigate('OTPVerification')}
          >
            <Text style={styles.verifyButtonText}>� Verify OTP</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => navigation.navigate('AddListing')}
          >
            <Text style={styles.addButtonText}>+ Add Listing</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Analytics Cards */}
      <View style={styles.analyticsContainer}>
        <View style={styles.analyticsCard}>
          <Text style={styles.analyticsValue}>{sellerParkings.length}</Text>
          <Text style={styles.analyticsLabel}>Total Listings</Text>
        </View>
        <View style={styles.analyticsCard}>
          <Text style={styles.analyticsValue}>{formatCurrency(totalRevenue)}</Text>
          <Text style={styles.analyticsLabel}>Daily Revenue</Text>
        </View>
        <View style={styles.analyticsCard}>
          <Text style={styles.analyticsValue}>{avgOccupancy}%</Text>
          <Text style={styles.analyticsLabel}>Avg Occupancy</Text>
        </View>
      </View>

      {/* Parking Listings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Parkings</Text>
        {sellerParkings.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>🅿️</Text>
            <Text style={styles.emptyText}>No parkings listed yet</Text>
            <Text style={styles.emptySubtext}>Add your first parking to get started</Text>
          </View>
        ) : (
          sellerParkings.map((parking) => {
            const occupancyRate = ((parking.slots - parking.available) / parking.slots) * 100;
            return (
              <View key={parking.id} style={styles.parkingCard}>
                <View style={styles.parkingHeader}>
                  <View style={styles.parkingInfo}>
                    <Text style={styles.parkingName}>{parking.name}</Text>
                    <Text style={styles.parkingPrice}>{formatCurrency(parking.price)}/hr</Text>
                  </View>
                  <View style={styles.ratingBadge}>
                    <Text style={styles.ratingText}>⭐ {(typeof parking.rating === 'number' ? parking.rating : 0)}</Text>
                  </View>
                </View>

                <View style={styles.statsRow}>
                  <View style={styles.stat}>
                    <Text style={styles.statLabel}>Occupancy</Text>
                    <Text style={styles.statValue}>{occupancyRate.toFixed(0)}%</Text>
                  </View>
                  <View style={styles.stat}>
                    <Text style={styles.statLabel}>Revenue</Text>
                    <Text style={styles.statValue}>
                      {formatCurrency(parking.dailyRevenue || 0)}
                    </Text>
                  </View>
                  <View style={styles.stat}>
                    <Text style={styles.statLabel}>Available</Text>
                    <Text style={styles.statValue}>
                      {parking.available}/{parking.slots}
                    </Text>
                  </View>
                </View>

                {/* Availability Controls */}
                <View style={styles.controlsContainer}>
                  <Text style={styles.controlsLabel}>Update Availability:</Text>
                  <View style={styles.controls}>
                    <TouchableOpacity
                      style={styles.controlButton}
                      onPress={() => handleUpdateAvailability(parking.id, -1)}
                    >
                      <Text style={styles.controlButtonText}>-</Text>
                    </TouchableOpacity>
                    <Text style={styles.currentValue}>{parking.available}</Text>
                    <TouchableOpacity
                      style={styles.controlButton}
                      onPress={() => handleUpdateAvailability(parking.id, 1)}
                    >
                      <Text style={styles.controlButtonText}>+</Text>
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Amenities */}
                <View style={styles.amenities}>
                  {parking.amenities.map((amenity, index) => (
                    <View key={index} style={styles.amenityBadge}>
                      <Text style={styles.amenityText}>{amenity}</Text>
                    </View>
                  ))}
                </View>
              </View>
            );
          })
        )}
      </View>

      {/* OTP Verification Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Check-in Management</Text>
        <View style={styles.qrSection}>
          <Text style={styles.qrIcon}>�</Text>
          <Text style={styles.qrText}>Verify customer OTP code to confirm arrival/departure</Text>
          <TouchableOpacity 
            style={styles.verifyButton}
            onPress={() => navigation.navigate('OTPVerification')}
          >
            <Text style={styles.verifyButtonText}>🔢 Verify OTP</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  verifyButton: {
    backgroundColor: '#22c55e',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  verifyButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  addButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  addButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  analyticsContainer: {
    flexDirection: 'row',
    padding: 20,
    gap: 10,
  },
  analyticsCard: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  analyticsValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 5,
  },
  analyticsLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  emptyState: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 40,
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 15,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 5,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
  },
  parkingCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  parkingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  parkingInfo: {
    flex: 1,
  },
  parkingName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  parkingPrice: {
    fontSize: 16,
    color: '#3b82f6',
    fontWeight: '600',
  },
  ratingBadge: {
    backgroundColor: '#fef3c7',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 15,
  },
  ratingText: {
    fontSize: 14,
    fontWeight: '600',
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 15,
    gap: 15,
  },
  stat: {
    flex: 1,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 3,
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  controlsContainer: {
    marginBottom: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  controlsLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlButton: {
    width: 40,
    height: 40,
    backgroundColor: '#3b82f6',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlButtonText: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  currentValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginHorizontal: 30,
    minWidth: 40,
    textAlign: 'center',
  },
  amenities: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  amenityBadge: {
    backgroundColor: '#e0f2fe',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  amenityText: {
    fontSize: 12,
    color: '#0284c7',
    fontWeight: '600',
  },
  qrSection: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 30,
    alignItems: 'center',
  },
  qrIcon: {
    fontSize: 60,
    marginBottom: 15,
  },
  qrText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
});
