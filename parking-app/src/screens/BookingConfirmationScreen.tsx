import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ActivityIndicator } from 'react-native';
import QRCode from 'react-native-qrcode-svg';
import { useAppStore } from '../store/appStore';
import { Booking } from '../types';
import { generateQRCode, formatCurrency } from '../utils/helpers';

export default function BookingConfirmationScreen({ route, navigation }: any) {
  const { parking, duration, totalPrice } = route.params;
  const { addBooking, user } = useAppStore();
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [bookingComplete, setBookingComplete] = useState(false);
  const [booking, setBooking] = useState<Booking | null>(null);

  const handlePayment = async () => {
    setIsProcessing(true);
    // Simulate payment processing
    setTimeout(() => {
      const newBooking: Booking = {
        id: `BK${Date.now()}`,
        userId: user?.id || 'guest',
        parkingId: parking.id,
        parkingName: parking.name,
        duration,
        totalPrice,
        timestamp: new Date().toISOString(),
        qrCode: generateQRCode(`BK${Date.now()}`),
        status: 'active',
      };
      addBooking(newBooking);
      setBooking(newBooking);
      setIsProcessing(false);
      setShowPaymentModal(false);
      setBookingComplete(true);
    }, 2000);
  };

  if (bookingComplete && booking) {
    return (
      <View style={styles.container}>
        <View style={styles.successContainer}>
          <Text style={styles.successIcon}>✓</Text>
          <Text style={styles.successTitle}>Booking Confirmed!</Text>
          <Text style={styles.successSubtitle}>Your parking spot is reserved</Text>

          {/* Booking Details */}
          <View style={styles.detailsCard}>
            <Text style={styles.detailsTitle}>Booking Details</Text>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Booking ID:</Text>
              <Text style={styles.detailValue}>{booking.id}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Parking:</Text>
              <Text style={styles.detailValue}>{booking.parkingName}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Duration:</Text>
              <Text style={styles.detailValue}>{duration} hours</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Total Paid:</Text>
              <Text style={[styles.detailValue, styles.priceValue]}>
                {formatCurrency(totalPrice)}
              </Text>
            </View>
          </View>

          {/* QR Code */}
          <View style={styles.qrContainer}>
            <Text style={styles.qrTitle}>Show this QR at entrance</Text>
            <View style={styles.qrCodeWrapper}>
              <QRCode value={booking.qrCode} size={200} />
            </View>
            <Text style={styles.qrCode}>{booking.qrCode}</Text>
          </View>

          {/* Action Buttons */}
          <TouchableOpacity
            style={styles.rateButton}
            onPress={() =>
              navigation.navigate('Rating', {
                bookingId: booking.id,
                parkingId: parking.id,
                parkingName: parking.name,
              })
            }
          >
            <Text style={styles.rateButtonText}>Rate This Parking Later</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.homeButton}
            onPress={() => navigation.navigate('MapHome')}
          >
            <Text style={styles.homeButtonText}>Back to Home</Text>
          </TouchableOpacity>
        </View>

        {/* Payment Modal */}
        <Modal visible={showPaymentModal} transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Payment</Text>
              <Text style={styles.modalSubtitle}>Test Mode - Auto Success</Text>

              <View style={styles.paymentDetails}>
                <Text style={styles.paymentLabel}>Amount to Pay</Text>
                <Text style={styles.paymentAmount}>{formatCurrency(totalPrice)}</Text>
              </View>

              {isProcessing ? (
                <View style={styles.processingContainer}>
                  <ActivityIndicator size="large" color="#3b82f6" />
                  <Text style={styles.processingText}>Processing payment...</Text>
                </View>
              ) : (
                <>
                  <TouchableOpacity style={styles.payButton} onPress={handlePayment}>
                    <Text style={styles.payButtonText}>Pay Now (Test Mode)</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => setShowPaymentModal(false)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        </Modal>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.summaryContainer}>
        <Text style={styles.title}>Confirm Your Booking</Text>

        {/* Booking Summary */}
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>{parking.name}</Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Duration:</Text>
            <Text style={styles.summaryValue}>{duration} hours</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Price/hr:</Text>
            <Text style={styles.summaryValue}>{formatCurrency(parking.price)}</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.summaryRow}>
            <Text style={styles.totalLabel}>Total:</Text>
            <Text style={styles.totalValue}>{formatCurrency(totalPrice)}</Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.proceedButton}
          onPress={() => setShowPaymentModal(true)}
        >
          <Text style={styles.proceedButtonText}>Proceed to Payment</Text>
        </TouchableOpacity>
      </View>

      {/* Payment Modal */}
      <Modal visible={showPaymentModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Payment</Text>
            <Text style={styles.modalSubtitle}>Test Mode - Auto Success</Text>

            <View style={styles.paymentDetails}>
              <Text style={styles.paymentLabel}>Amount to Pay</Text>
              <Text style={styles.paymentAmount}>{formatCurrency(totalPrice)}</Text>
            </View>

            {isProcessing ? (
              <View style={styles.processingContainer}>
                <ActivityIndicator size="large" color="#3b82f6" />
                <Text style={styles.processingText}>Processing payment...</Text>
              </View>
            ) : (
              <>
                <TouchableOpacity style={styles.payButton} onPress={handlePayment}>
                  <Text style={styles.payButtonText}>Pay Now (Test Mode)</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setShowPaymentModal(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  summaryContainer: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
    textAlign: 'center',
  },
  summaryCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
  },
  summaryTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 16,
    color: '#666',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    height: 1,
    backgroundColor: '#e5e7eb',
    marginVertical: 15,
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  totalValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  proceedButton: {
    backgroundColor: '#3b82f6',
    padding: 18,
    borderRadius: 10,
    alignItems: 'center',
  },
  proceedButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  successContainer: {
    flex: 1,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  successIcon: {
    fontSize: 80,
    color: '#22c55e',
    marginBottom: 20,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  successSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
  },
  detailsCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 15,
    padding: 20,
    width: '100%',
    marginBottom: 30,
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  priceValue: {
    color: '#3b82f6',
    fontSize: 16,
  },
  qrContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  qrTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 20,
  },
  qrCodeWrapper: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 3,
    marginBottom: 15,
  },
  qrCode: {
    fontSize: 12,
    color: '#666',
    fontFamily: 'monospace',
  },
  rateButton: {
    backgroundColor: '#fbbf24',
    padding: 15,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
    marginBottom: 15,
  },
  rateButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  homeButton: {
    backgroundColor: 'transparent',
    padding: 15,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#3b82f6',
  },
  homeButtonText: {
    color: '#3b82f6',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 30,
    width: '85%',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 30,
  },
  paymentDetails: {
    alignItems: 'center',
    marginBottom: 30,
  },
  paymentLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 10,
  },
  paymentAmount: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  processingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  processingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
  },
  payButton: {
    backgroundColor: '#22c55e',
    padding: 18,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
    marginBottom: 15,
  },
  payButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    backgroundColor: 'transparent',
    padding: 15,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
  },
});
