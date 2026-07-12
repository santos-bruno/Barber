import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import React from 'react';

import { COLORS } from './src/constants/business';
import BookingScreen from './src/screens/BookingScreen';
import HomeScreen from './src/screens/HomeScreen';
import ServicesScreen from './src/screens/ServicesScreen';

const Stack = createNativeStackNavigator();

const screenOptions = {
  headerStyle: { backgroundColor: COLORS.surface },
  headerTintColor: COLORS.primary,
  headerTitleStyle: { color: COLORS.text },
  contentStyle: { backgroundColor: COLORS.background },
};

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator screenOptions={screenOptions}>
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: 'Sr. Perison' }}
        />
        <Stack.Screen
          name="Services"
          component={ServicesScreen}
          options={{ title: 'Serviços' }}
        />
        <Stack.Screen
          name="Booking"
          component={BookingScreen}
          options={{ title: 'Agendamento' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
