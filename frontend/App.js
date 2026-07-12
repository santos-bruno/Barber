import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import React from 'react';

import { COLORS } from './src/constants/business';
import AgendaScreen from './src/screens/AgendaScreen';
import CashFlowScreen from './src/screens/CashFlowScreen';
import ClientsScreen from './src/screens/ClientsScreen';
import HomeScreen from './src/screens/HomeScreen';
import HoursScreen from './src/screens/HoursScreen';
import NewAppointmentScreen from './src/screens/NewAppointmentScreen';
import SettingsScreen from './src/screens/SettingsScreen';

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
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'Sr. Perison' }} />
        <Stack.Screen name="Agenda" component={AgendaScreen} options={{ title: 'Agenda' }} />
        <Stack.Screen name="NewAppointment" component={NewAppointmentScreen} options={{ title: 'Novo Agendamento' }} />
        <Stack.Screen name="Clients" component={ClientsScreen} options={{ title: 'Clientes' }} />
        <Stack.Screen name="CashFlow" component={CashFlowScreen} options={{ title: 'Fluxo de Caixa' }} />
        <Stack.Screen name="Hours" component={HoursScreen} options={{ title: 'Horários' }} />
        <Stack.Screen name="Settings" component={SettingsScreen} options={{ title: 'Configurações' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
