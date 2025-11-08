import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAppStore } from '../store/appStore';
import MapHomeScreen from '../screens/MapHomeScreen';
import ParkingDetailsScreen from '../screens/ParkingDetailsScreen';
import BookingConfirmationScreen from '../screens/BookingConfirmationScreen';
import RatingScreen from '../screens/RatingScreen';
import SellerDashboardScreen from '../screens/SellerDashboardScreen';
import AddListingScreen from '../screens/AddListingScreen';
import LoginScreen from '../screens/LoginScreen';
import SignupScreen from '../screens/SignupScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="MapHome"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#3b82f6',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        {/* Main App Screens - Always Available */}
        <Stack.Screen
          name="MapHome"
          component={MapHomeScreen}
          options={{ title: 'Smart Parking', headerTitleAlign: 'center' }}
        />
        <Stack.Screen
          name="ParkingDetails"
          component={ParkingDetailsScreen}
          options={{ title: 'Parking Details', headerTitleAlign: 'center' }}
        />

        {/* Auth Screens */}
        <Stack.Screen
          name="Login"
          component={LoginScreen}
          options={{ title: 'Login' }}
        />
        <Stack.Screen
          name="Signup"
          component={SignupScreen}
          options={{ title: 'Sign Up' }}
        />

        {/* Protected Screens */}
        <Stack.Screen
          name="Profile"
          component={ProfileScreen}
          options={{ title: 'My Profile' }}
        />
        <Stack.Screen
          name="BookingConfirmation"
          component={BookingConfirmationScreen}
          options={{ title: 'Booking', headerBackVisible: false }}
        />
        <Stack.Screen
          name="Rating"
          component={RatingScreen}
          options={{ title: 'Rate Parking' }}
        />
        
        {/* Seller Screens */}
        <Stack.Screen
          name="SellerDashboard"
          component={SellerDashboardScreen}
          options={{ title: 'Seller Dashboard' }}
        />
        <Stack.Screen
          name="AddListing"
          component={AddListingScreen}
          options={{ title: 'Add New Parking' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
