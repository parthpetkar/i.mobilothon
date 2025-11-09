import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { verifyBookingOTP } from '../services/api';

export default function VerifyOTPScreen({ navigation }: any) {
  const [bookingId, setBookingId] = useState('');
  const [otp, setOtp] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  const handleVerify = async () => {
    if (!bookingId.trim()) {
      Alert.alert('Error', 'Please enter booking ID');
      return;
    }
    if (!otp.trim() || otp.length !== 6) {
      Alert.alert('Error', 'Please enter valid 6-digit OTP');
      return;
    }

    setIsVerifying(true);

    try {
      await verifyBookingOTP(parseInt(bookingId), otp);
      
      Alert.alert(
        'Success',
        'Customer verified successfully! Entry approved.',
        [{ text: 'OK', onPress: () => {
          setBookingId('');
          setOtp('');
        }}]
      );
    } catch (error: any) {
      Alert.alert(
        'Verification Failed',
        error.message || 'Invalid OTP or booking ID. Please try again.'
      );
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <Text style={styles.icon}>🔐</Text>
        </View>
        
        <Text style={styles.title}>Verify Customer Entry</Text>
        <Text style={styles.subtitle}>
          Ask the customer for their Booking ID and OTP to verify their entry
        </Text>

        {/* Booking ID Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Booking ID</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter booking ID"
            value={bookingId}
            onChangeText={setBookingId}
            keyboardType="number-pad"
            autoCapitalize="none"
          />
        </View>

        {/* OTP Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>6-Digit OTP</Text>
          <TextInput
            style={styles.otpInput}
            placeholder="000000"
            value={otp}
            onChangeText={setOtp}
            keyboardType="number-pad"
            maxLength={6}
            autoCapitalize="none"
          />
        </View>

        {/* Verify Button */}
        <TouchableOpacity
          style={[styles.verifyButton, isVerifying && styles.verifyButtonDisabled]}
          onPress={handleVerify}
          disabled={isVerifying}
        >
          {isVerifying ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.verifyButtonText}>Verify & Allow Entry</Text>
          )}
        </TouchableOpacity>

        {/* Cancel Button */}
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  iconContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  icon: {
    fontSize: 80,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 40,
    lineHeight: 22,
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
  input: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
  },
  otpInput: {
    backgroundColor: '#f9fafb',
    borderWidth: 2,
    borderColor: '#3b82f6',
    borderRadius: 10,
    padding: 20,
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    letterSpacing: 8,
    fontFamily: 'monospace',
  },
  verifyButton: {
    backgroundColor: '#22c55e',
    padding: 18,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
  },
  verifyButtonDisabled: {
    opacity: 0.6,
  },
  verifyButtonText: {
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
