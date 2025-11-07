import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { parseQRCode, formatCurrency } from '../utils/helpers';
import { useAppStore } from '../store/appStore';

export default function QRScannerScreen({ navigation }: any) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [bookingData, setBookingData] = useState<any>(null);
  const [isApproving, setIsApproving] = useState(false);
  const { user } = useAppStore();

  const handleBarCodeScanned = ({ data }: { data: string }) => {
    if (scanned) return;
    
    setScanned(true);
    const parsedData = parseQRCode(data);
    
    if (parsedData) {
      setBookingData(parsedData);
    } else {
      Alert.alert(
        'Invalid QR Code',
        'This QR code is not a valid parking booking.',
        [{ text: 'Scan Again', onPress: () => setScanned(false) }]
      );
    }
  };

  const handleApprove = async () => {
    if (!bookingData) return;
    
    setIsApproving(true);
    
    try {
      // Here you would call an API to mark the booking as approved
      // For now, we'll simulate the approval
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      Alert.alert(
        'Booking Approved!',
        `Booking ${bookingData.bookingId} has been approved successfully.`,
        [
          {
            text: 'OK',
            onPress: () => {
              setBookingData(null);
              setScanned(false);
              setIsApproving(false);
            }
          }
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to approve booking. Please try again.');
      setIsApproving(false);
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
            setScanned(false);
          }
        }
      ]
    );
  };

  if (!permission) {
    return (
      <View style={styles.container}>
        <Text>Requesting camera permission...</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>No access to camera</Text>
        <Text style={styles.errorHint}>
          Please enable camera permission in settings to scan QR codes
        </Text>
        <TouchableOpacity
          style={styles.permissionButton}
          onPress={requestPermission}
        >
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (bookingData) {
    const startTime = new Date(bookingData.startTime);
    const endTime = new Date(bookingData.endTime);
    const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60 * 60));
    
    return (
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.approvalContainer}>
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
                <Text style={styles.detailLabel}>User ID:</Text>
                <Text style={[styles.detailValue, styles.monoFont]}>
                  {bookingData.userId.substring(0, 20)}...
                </Text>
              </View>
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Scanned at:</Text>
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
                disabled={isApproving}
              >
                <Text style={styles.approveButtonText}>
                  {isApproving ? 'Approving...' : '✓ Approve Entry'}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionButton, styles.rejectButton]}
                onPress={handleReject}
                disabled={isApproving}
              >
                <Text style={styles.rejectButtonText}>✗ Reject</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.scanAgainButton}
              onPress={() => {
                setBookingData(null);
                setScanned(false);
              }}
            >
              <Text style={styles.scanAgainText}>Scan Another QR Code</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Scan Booking QR Code</Text>
        <Text style={styles.headerSubtitle}>
          Position the QR code within the frame
        </Text>
      </View>

      <View style={styles.cameraContainer}>
        <CameraView
          style={styles.camera}
          facing="back"
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{
            barcodeTypes: ['qr'],
          }}
        />
        
        <View style={styles.overlay}>
          <View style={styles.scanFrame} />
        </View>
      </View>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>← Back to Dashboard</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    backgroundColor: '#1f2937',
    padding: 20,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#9ca3af',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 250,
    height: 250,
    borderWidth: 3,
    borderColor: '#3b82f6',
    borderRadius: 20,
    backgroundColor: 'transparent',
  },
  footer: {
    backgroundColor: '#1f2937',
    padding: 20,
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
  errorText: {
    fontSize: 18,
    color: '#ef4444',
    fontWeight: 'bold',
    marginBottom: 10,
  },
  errorHint: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  scrollContent: {
    flexGrow: 1,
  },
  approvalContainer: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
  },
  approvalTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 20,
    marginTop: 40,
    textAlign: 'center',
  },
  detailsCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    textAlign: 'right',
  },
  monoFont: {
    fontFamily: 'monospace',
    fontSize: 12,
  },
  divider: {
    height: 1,
    backgroundColor: '#e5e7eb',
    marginVertical: 15,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
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
  scanAgainButton: {
    padding: 15,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#3b82f6',
    alignItems: 'center',
  },
  scanAgainText: {
    color: '#3b82f6',
    fontSize: 16,
    fontWeight: '600',
  },
  permissionButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 10,
    marginTop: 20,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
