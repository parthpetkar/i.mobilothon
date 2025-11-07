import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { formatCurrency, validateOTP } from '../utils/helpers';
import { useAppStore } from '../store/appStore';

export default function OTPVerificationScreen({ navigation }: any) {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isVerifying, setIsVerifying] = useState(false);
  const [bookingData, setBookingData] = useState<any>(null);
  const inputRefs = useRef<Array<TextInput | null>>([]);
  const { user } = useAppStore();

  const handleOTPChange = (value: string, index: number) => {
    // Only allow digits
    if (value && !/^\d+$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyPress = (e: any, index: number) => {
    // Handle backspace
    if (e.nativeEvent.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const enteredOTP = otp.join('');
    
    if (enteredOTP.length !== 6) {
      Alert.alert('Invalid OTP', 'Please enter a 6-digit OTP code');
      return;
    }

    setIsVerifying(true);

    try {
      // Simulate API call to verify OTP and fetch booking details
      // In real implementation, this would call your backend API
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock booking data - replace with actual API call
      const mockBooking = {
        bookingId: 'BK' + Date.now().toString().slice(-6),
        parkingName: 'Sample Parking',
        duration: 2,
        startTime: new Date().toISOString(),
        endTime: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
        totalPrice: 40,
        userId: 'user123',
        otp: enteredOTP,
        status: 'active'
      };

      // Validate OTP (in real app, backend would do this)
      const isValid = true; // Replace with actual validation

      if (isValid) {
        setBookingData(mockBooking);
        setIsVerifying(false);
      } else {
        setIsVerifying(false);
        Alert.alert('Invalid OTP', 'The OTP code entered is incorrect');
        setOtp(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (error) {
      setIsVerifying(false);
      Alert.alert('Error', 'Failed to verify OTP. Please try again.');
    }
  };

  const handleApprove = async () => {
    if (!bookingData) return;

    try {
      // Call API to approve booking
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert(
        'Booking Approved!',
        `Booking ${bookingData.bookingId} has been approved successfully.`,
        [
          {
            text: 'OK',
            onPress: () => {
              setBookingData(null);
              setOtp(['', '', '', '', '', '']);
              inputRefs.current[0]?.focus();
            }
          }
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to approve booking. Please try again.');
    }
  };

  const handleReject = () => {
    Alert.alert(
      'Reject Booking',
      'Are you sure you want to reject this booking?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reject',
          style: 'destructive',
          onPress: () => {
            setBookingData(null);
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
          }
        }
      ]
    );
  };

  if (bookingData) {
    const startTime = new Date(bookingData.startTime);
    const endTime = new Date(bookingData.endTime);
    const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60 * 60));

    return (
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.approvalContainer}>
            <View style={styles.successBadge}>
              <Text style={styles.successIcon}>✓</Text>
              <Text style={styles.successText}>OTP Verified</Text>
            </View>

            <Text style={styles.approvalTitle}>Booking Details</Text>

            <View style={styles.detailsCard}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Booking ID:</Text>
                <Text style={styles.detailValue}>{bookingData.bookingId}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Parking:</Text>
                <Text style={styles.detailValue}>{bookingData.parkingName}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Duration:</Text>
                <Text style={styles.detailValue}>{duration} hours</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Start Time:</Text>
                <Text style={styles.detailValue}>
                  {startTime.toLocaleString('en-IN', {
                    dateStyle: 'medium',
                    timeStyle: 'short'
                  })}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>End Time:</Text>
                <Text style={styles.detailValue}>
                  {endTime.toLocaleString('en-IN', {
                    dateStyle: 'medium',
                    timeStyle: 'short'
                  })}
                </Text>
              </View>

              <View style={styles.divider} />

              <View style={styles.detailRow}>
                <Text style={styles.totalLabel}>Total Amount:</Text>
                <Text style={styles.totalValue}>
                  {formatCurrency(bookingData.totalPrice)}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Verified at:</Text>
                <Text style={styles.detailValue}>
                  {new Date().toLocaleString('en-IN', {
                    timeStyle: 'medium'
                  })}
                </Text>
              </View>
            </View>

            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={[styles.actionButton, styles.approveButton]}
                onPress={handleApprove}
              >
                <Text style={styles.approveButtonText}>✓ Approve Entry</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.rejectButton]}
                onPress={handleReject}
              >
                <Text style={styles.rejectButtonText}>✗ Reject</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.verifyAnotherButton}
              onPress={() => {
                setBookingData(null);
                setOtp(['', '', '', '', '', '']);
                inputRefs.current[0]?.focus();
              }}
            >
              <Text style={styles.verifyAnotherText}>Verify Another Booking</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Verify Booking OTP</Text>
          <Text style={styles.headerSubtitle}>
            Enter the 6-digit code shown by the customer
          </Text>
        </View>

        <View style={styles.otpInputContainer}>
          <View style={styles.otpInputRow}>
            {otp.map((digit, index) => (
              <TextInput
                key={index}
                ref={(ref) => (inputRefs.current[index] = ref)}
                style={styles.otpInput}
                value={digit}
                onChangeText={(value) => handleOTPChange(value, index)}
                onKeyPress={(e) => handleKeyPress(e, index)}
                keyboardType="number-pad"
                maxLength={1}
                selectTextOnFocus
                autoFocus={index === 0}
              />
            ))}
          </View>
        </View>

        {isVerifying ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#3b82f6" />
            <Text style={styles.loadingText}>Verifying OTP...</Text>
          </View>
        ) : (
          <TouchableOpacity
            style={[
              styles.verifyButton,
              otp.join('').length !== 6 && styles.verifyButtonDisabled
            ]}
            onPress={handleVerify}
            disabled={otp.join('').length !== 6}
          >
            <Text style={styles.verifyButtonText}>Verify OTP</Text>
          </TouchableOpacity>
        )}

        <View style={styles.instructionsContainer}>
          <Text style={styles.instructionsTitle}>Instructions:</Text>
          <Text style={styles.instructionsText}>
            1. Ask the customer for their 6-digit booking OTP
          </Text>
          <Text style={styles.instructionsText}>
            2. Enter the OTP code in the boxes above
          </Text>
          <Text style={styles.instructionsText}>
            3. Tap "Verify OTP" to view booking details
          </Text>
          <Text style={styles.instructionsText}>
            4. Approve or reject the booking entry
          </Text>
        </View>

        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>← Back to Dashboard</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
  },
  header: {
    marginBottom: 40,
    marginTop: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#6b7280',
  },
  otpInputContainer: {
    marginBottom: 30,
  },
  otpInputRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 10,
  },
  otpInput: {
    width: 50,
    height: 60,
    borderWidth: 2,
    borderColor: '#3b82f6',
    borderRadius: 10,
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    backgroundColor: '#fff',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
  },
  verifyButton: {
    backgroundColor: '#3b82f6',
    padding: 18,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 30,
  },
  verifyButtonDisabled: {
    backgroundColor: '#9ca3af',
  },
  verifyButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  instructionsContainer: {
    backgroundColor: '#e0f2fe',
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 10,
  },
  instructionsText: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 5,
  },
  backButton: {
    padding: 15,
    alignItems: 'center',
  },
  backButtonText: {
    color: '#3b82f6',
    fontSize: 16,
    fontWeight: '600',
  },
  approvalContainer: {
    paddingVertical: 20,
  },
  successBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#d1fae5',
    paddingVertical: 15,
    paddingHorizontal: 25,
    borderRadius: 30,
    marginBottom: 20,
    alignSelf: 'center',
  },
  successIcon: {
    fontSize: 24,
    color: '#059669',
    marginRight: 10,
  },
  successText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#059669',
  },
  approvalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#1f2937',
  },
  detailsCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  detailLabel: {
    fontSize: 14,
    color: '#6b7280',
    flex: 1,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    flex: 1,
    textAlign: 'right',
  },
  divider: {
    height: 1,
    backgroundColor: '#e5e7eb',
    marginVertical: 15,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  totalValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  actionButtons: {
    gap: 15,
    marginBottom: 20,
  },
  actionButton: {
    padding: 18,
    borderRadius: 10,
    alignItems: 'center',
  },
  approveButton: {
    backgroundColor: '#22c55e',
  },
  approveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  rejectButton: {
    backgroundColor: '#ef4444',
  },
  rejectButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  verifyAnotherButton: {
    padding: 15,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#3b82f6',
    alignItems: 'center',
  },
  verifyAnotherText: {
    color: '#3b82f6',
    fontSize: 16,
    fontWeight: '600',
  },
});
