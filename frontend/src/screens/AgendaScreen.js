import DateTimePicker from '@react-native-community/datetimepicker';
import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import {
  Alert,
  FlatList,
  Linking,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { getAppointments, updateAppointment } from '../api/client';
import { COLORS } from '../constants/business';
import { apiToBR, hhmm, money, toApiDate } from '../utils/date';

const STATUS_COLORS = {
  pendente: '#c9a227',
  confirmado: '#4a9eff',
  concluido: '#25D366',
  cancelado: '#ff6b6b',
};

export default function AgendaScreen() {
  const [date, setDate] = useState(new Date());
  const [showPicker, setShowPicker] = useState(false);
  const [appts, setAppts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getAppointments({ date: toApiDate(date) });
      setAppts(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [date]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const changeStatus = async (appt, status) => {
    try {
      await updateAppointment(appt.id, { status });
      load();
    } catch (e) {
      Alert.alert('Erro', e.message);
    }
  };

  const whatsapp = (appt) => {
    if (!appt.phone) {
      Alert.alert('Sem telefone', 'Este agendamento não tem WhatsApp cadastrado.');
      return;
    }
    const digits = appt.phone.replace(/\D/g, '');
    const msg = `Olá ${appt.customer_name}, tudo bem? Sobre seu agendamento (${appt.service_name} em ${apiToBR(appt.date)} às ${hhmm(appt.time)})`;
    Linking.openURL(`https://wa.me/${digits}?text=${encodeURIComponent(msg)}`);
  };

  const renderItem = ({ item }) => (
    <View style={[styles.card, { borderLeftColor: STATUS_COLORS[item.status] || COLORS.border }]}>
      <View style={styles.cardHeader}>
        <Text style={styles.time}>{hhmm(item.time)}</Text>
        <View style={[styles.badge, { backgroundColor: STATUS_COLORS[item.status] }]}>
          <Text style={styles.badgeText}>{item.status}</Text>
        </View>
      </View>
      <Text style={styles.name}>{item.customer_name}</Text>
      <Text style={styles.sub}>{item.service_name} · {money(item.price)}</Text>
      {item.source === 'web' && <Text style={styles.webTag}>🌐 agendou pelo site</Text>}

      <View style={styles.actions}>
        {item.status !== 'confirmado' && item.status !== 'concluido' && (
          <TouchableOpacity style={styles.actBtn} onPress={() => changeStatus(item, 'confirmado')}>
            <Text style={styles.actText}>Confirmar</Text>
          </TouchableOpacity>
        )}
        {item.status !== 'concluido' && (
          <TouchableOpacity style={[styles.actBtn, styles.done]} onPress={() => changeStatus(item, 'concluido')}>
            <Text style={styles.actText}>Concluir</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={[styles.actBtn, styles.wa]} onPress={() => whatsapp(item)}>
          <Text style={styles.actText}>WhatsApp</Text>
        </TouchableOpacity>
        {item.status !== 'cancelado' && (
          <TouchableOpacity style={[styles.actBtn, styles.cancel]} onPress={() => changeStatus(item, 'cancelado')}>
            <Text style={styles.actText}>Cancelar</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.dateBar} onPress={() => setShowPicker(true)}>
        <Text style={styles.dateText}>📅 {apiToBR(toApiDate(date))}</Text>
        <Text style={styles.count}>{appts.length} agend.</Text>
      </TouchableOpacity>
      {showPicker && (
        <DateTimePicker
          value={date}
          mode="date"
          display="default"
          onChange={(e, d) => {
            setShowPicker(Platform.OS === 'ios');
            if (d) setDate(d);
          }}
        />
      )}

      {!!error && <Text style={styles.error}>⚠ {error}</Text>}

      <FlatList
        data={appts}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16 }}
        refreshing={loading}
        onRefresh={load}
        ListEmptyComponent={
          !loading && <Text style={styles.empty}>Nenhum agendamento nesta data.</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  dateBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: COLORS.surface, padding: 16, borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  dateText: { color: COLORS.text, fontSize: 16, fontWeight: '600' },
  count: { color: COLORS.textMuted },
  error: { color: '#ff6b6b', textAlign: 'center', padding: 12 },
  card: {
    backgroundColor: COLORS.surface, borderRadius: 12, padding: 14, marginBottom: 12,
    borderWidth: 1, borderColor: COLORS.border, borderLeftWidth: 4,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  time: { color: COLORS.primary, fontSize: 18, fontWeight: '800' },
  badge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText: { color: '#1a1a1a', fontSize: 11, fontWeight: '700', textTransform: 'uppercase' },
  name: { color: COLORS.text, fontSize: 16, fontWeight: '600', marginTop: 8 },
  sub: { color: COLORS.textMuted, marginTop: 2 },
  webTag: { color: '#4a9eff', fontSize: 12, marginTop: 4 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 },
  actBtn: { backgroundColor: '#4a9eff', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  done: { backgroundColor: COLORS.whatsapp },
  wa: { backgroundColor: '#128C7E' },
  cancel: { backgroundColor: '#ff6b6b' },
  actText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  empty: { color: COLORS.textMuted, textAlign: 'center', marginTop: 40 },
});
