import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';

import { COLORS } from './src/constants/business';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import AgendaScreen from './src/screens/AgendaScreen';
import BarberHoursScreen from './src/screens/BarberHoursScreen';
import CashFlowScreen from './src/screens/CashFlowScreen';
import ClientsScreen from './src/screens/ClientsScreen';
import HomeScreen from './src/screens/HomeScreen';
import HoursScreen from './src/screens/HoursScreen';
import LoginScreen from './src/screens/LoginScreen';
import NewAppointmentScreen from './src/screens/NewAppointmentScreen';
import OrdersScreen from './src/screens/OrdersScreen';
import PlansScreen from './src/screens/PlansScreen';
import ProductsScreen from './src/screens/ProductsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import SignupScreen from './src/screens/SignupScreen';
import StaffScreen from './src/screens/StaffScreen';
import SubscriptionScreen from './src/screens/SubscriptionScreen';

const Stack = createNativeStackNavigator();

const screenOptions = {
  headerStyle: { backgroundColor: COLORS.surface },
  headerTintColor: COLORS.primary,
  headerTitleStyle: { color: COLORS.text },
  contentStyle: { backgroundColor: COLORS.background },
};

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ ...screenOptions, headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Signup" component={SignupScreen} />
    </Stack.Navigator>
  );
}

function AppStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'Agenda Barber' }} />
      <Stack.Screen name="Agenda" component={AgendaScreen} options={{ title: 'Agenda' }} />
      <Stack.Screen name="NewAppointment" component={NewAppointmentScreen} options={{ title: 'Novo Agendamento' }} />
      <Stack.Screen name="Clients" component={ClientsScreen} options={{ title: 'Clientes' }} />
      <Stack.Screen name="CashFlow" component={CashFlowScreen} options={{ title: 'Fluxo de Caixa' }} />
      <Stack.Screen name="Hours" component={HoursScreen} options={{ title: 'Horários' }} />
      <Stack.Screen name="Staff" component={StaffScreen} options={{ title: 'Barbeiros' }} />
      <Stack.Screen name="BarberHours" component={BarberHoursScreen} options={{ title: 'Horário do Barbeiro' }} />
      <Stack.Screen name="Plans" component={PlansScreen} options={{ title: 'Planos de Corte' }} />
      <Stack.Screen name="Products" component={ProductsScreen} options={{ title: 'Loja / Estoque' }} />
      <Stack.Screen name="Orders" component={OrdersScreen} options={{ title: 'Pedidos' }} />
      <Stack.Screen name="Subscription" component={SubscriptionScreen} options={{ title: 'Assinatura' }} />
      <Stack.Screen name="Settings" component={SettingsScreen} options={{ title: 'Configurações' }} />
    </Stack.Navigator>
  );
}

function Root() {
  const { loading, isAuthed } = useAuth();
  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: COLORS.background, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      {isAuthed ? <AppStack /> : <AuthStack />}
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  );
}
