import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { useAppStore } from '../store/appStore';
import { Review } from '../types';

export default function RatingScreen({ route, navigation }: any) {
  const { parkingId, parkingName, bookingId } = route.params;
  const { addReview, completeBooking } = useAppStore();
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');

  const handleSubmit = () => {
    if (rating === 0) {
      Alert.alert('Rating Required', 'Please select a star rating before submitting.');
      return;
    }

    const review: Review = {
      id: `REV${Date.now()}`,
      userName: 'Anonymous User',
      rating,
      comment: comment.trim() || 'No comment provided',
      date: new Date().toISOString().split('T')[0],
    };

    addReview(parkingId, review);
    if (bookingId) {
      completeBooking(bookingId);
    }

    Alert.alert('Thank You!', 'Your review has been submitted successfully.', [
      { text: 'OK', onPress: () => navigation.navigate('MapHome') },
    ]);
  };

  const handleSkip = () => {
    if (bookingId) {
      completeBooking(bookingId);
    }
    navigation.navigate('MapHome');
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Rate Your Experience</Text>
        <Text style={styles.subtitle}>{parkingName}</Text>

        {/* Star Rating */}
        <View style={styles.starsContainer}>
          {[1, 2, 3, 4, 5].map((star) => (
            <TouchableOpacity
              key={star}
              onPress={() => setRating(star)}
              style={styles.starButton}
            >
              <Text style={[styles.star, rating >= star && styles.starActive]}>
                {rating >= star ? '★' : '☆'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.ratingText}>
          {rating === 0 && 'Tap to rate'}
          {rating === 1 && 'Poor'}
          {rating === 2 && 'Fair'}
          {rating === 3 && 'Good'}
          {rating === 4 && 'Very Good'}
          {rating === 5 && 'Excellent'}
        </Text>

        {/* Comment */}
        <Text style={styles.label}>Add a comment (optional)</Text>
        <TextInput
          style={styles.commentInput}
          placeholder="Share your experience..."
          multiline
          numberOfLines={4}
          value={comment}
          onChangeText={setComment}
          textAlignVertical="top"
        />

        {/* Buttons */}
        <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
          <Text style={styles.submitButtonText}>Submit Review</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
          <Text style={styles.skipButtonText}>Skip for Now</Text>
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
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
  },
  starsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 20,
  },
  starButton: {
    padding: 5,
  },
  star: {
    fontSize: 50,
    color: '#d1d5db',
  },
  starActive: {
    color: '#fbbf24',
  },
  ratingText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
    fontWeight: '600',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
  },
  commentInput: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    minHeight: 100,
    marginBottom: 30,
  },
  submitButton: {
    backgroundColor: '#3b82f6',
    padding: 18,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
  },
  submitButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  skipButton: {
    backgroundColor: 'transparent',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  skipButtonText: {
    color: '#666',
    fontSize: 16,
  },
});
