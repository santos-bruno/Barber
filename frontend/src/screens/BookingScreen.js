import DateTimePicker from '@react-native-community/datetimepicker';
import React, { useEffect, useState } from 'react';
import {
  Alert,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { createAppointment, getServices } from '../api/client';
import { COLORS } from '../constants/business';
import {
  buildWhatsAppLink,
  formatDate,
  formatTime,
  toApiDate,
} from '../utils/whatsapp';

export default function BookingScreen({ route }) {
  const preselected = route.params?.service;

  const [services, setServices] = useState([]);
  const [service, setService] = useState(preselected || null);
  const [customerName, setCustomerName] = useState('');
  const [date, setDate] = useState(new Date());
  const [time, setTime] = useState(new Date());
  const [showDate, setShowDate] = useState(false);
  const [showTime, setShowTime] = useState(false);

  useEffect(() => {
    getServices().then((data) => {
      setServices(data);
      if (!preselected && data.length) setService(data[0].name);
    });
  }, [preselected]);

  const onChangeDate = (event, selected) => {
    setShowDate(Platform.OS === 'ios');
    if (selected) setDate(selected);
  };

  const onChangeTime = (event, selected) => {
    setShowTime(Platform.OS === 'ios');
    if (selected) setTime(selected);
  };

  const handleConfirm = async () => {
    if (!service) {
      Alert.alert('Atenção', 'Selecione um serviço.');
      return;
    }
    if (!customerName.trim()) {
      Alert.alert('Atenção', 'Informe seu nome.');
      return;
    }

    const dateStr = formatDate(date);
    const timeStr = formatTime(time);

    // Tenta persistir no back-end (silencioso se indisponível).
    try {
      await createAppointment({
        customer_name: customerName.trim(),
        service_name: service,
        date: toApiDate(date),
        time: timeStr,
        phone: '',
      });
    } catch (err) {
      // Ambiente inicial pode não ter back-end no ar; segue para o WhatsApp.
    }

    const link = buildWhatsAppLink({
      service,
      date: dateStr,
      time: timeStr,
      customerName,
    });
    Linking.openURL(link);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.label}>Serviço</Text>
      <View style={styles.chipRow}>
        {services.map((s) => (
          <TouchableOpacity
            key={s.id}
            style={[styles.chip, service === s.name && styles.chipActive]}
            onPress={() => setService(s.name)}
          >
            <Text
              style={[
                styles.chipText,
                service === s.name && styles.chipTextActive,
              ]}
            >
              {s.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Seu nome</Text>
      <TextInput
        style={styles.input}
        placeholder="Digite seu nome"
        placeholderTextColor={COLORS.textMuted}
        value={customerName}
        onChangeText={setCustomerName}
      />

      <Text style={styles.label}>Data</Text>
      <TouchableOpacity
        style={styles.selector}
        onPress={() => setShowDate(true)}
      >
        <Text style={styles.selectorText}>📅 {formatDate(date)}</Text>
      </TouchableOpacity>
      {showDate && (
        <DateTimePicker
          value={date}
          mode="date"
          display="default"
          minimumDate={new Date()}
          onChange={onChangeDate}
        />
      )}

      <Text style={styles.label}>Hora</Text>
      <TouchableOpacity
        style={styles.selector}
        onPress={() => setShowTime(true)}
      >
        <Text style={styles.selectorText}>🕐 {formatTime(time)}</Text>
      </TouchableOpacity>
      {showTime && (
        <DateTimePicker
          value={time}
          mode="time"
          display="default"
          is24Hour
          onChange={onChangeTime}
        />
      )}

      <TouchableOpacity style={styles.confirmBtn} onPress={handleConfirm}>
        <Text style={styles.confirmBtnText}>
          Confirmar e enviar no WhatsApp
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingBottom: 40 },
  label: {
    color: COLORS.primary,
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginTop: 18,
    marginBottom: 8,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { color: COLORS.text },
  chipTextActive: { color: '#1a1a1a', fontWeight: '700' },
  input: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: COLORS.text,
    fontSize: 16,
  },
  selector: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  selectorText: { color: COLORS.text, fontSize: 16 },
  confirmBtn: {
    backgroundColor: COLORS.whatsapp,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 28,
  },
  confirmBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
