import DateTimePicker from '@react-native-community/datetimepicker';
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { getBarberHours, getHours, setBarberHour } from '../api/client';
import GradientButton from '../components/GradientButton';
import { COLORS } from '../constants/business';
import { hhmm, WEEKDAYS } from '../utils/date';

function timeToDate(t) {
  const d = new Date();
  if (t) {
    const [h, m] = t.split(':');
    d.setHours(Number(h), Number(m), 0, 0);
  } else {
    d.setHours(9, 0, 0, 0);
  }
  return d;
}

export default function BarberHoursScreen({ route, navigation }) {
  const { barberId, barberName } = route.params || {};
  const [hours, setHours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [picker, setPicker] = useState(null);

  useEffect(() => {
    navigation.setOptions({ title: `Horário · ${barberName || 'Barbeiro'}` });
    Promise.all([getBarberHours(barberId), getHours()])
      .then(([bh, shop]) => {
        const byB = {}; bh.forEach((h) => { byB[h.weekday] = h; });
        const byS = {}; shop.forEach((h) => { byS[h.weekday] = h; });
        const full = [];
        for (let w = 0; w < 7; w++) {
          const h = byB[w] || byS[w] || { is_open: w !== 6, open_time: '09:00:00', close_time: '19:00:00' };
          full.push({ weekday: w, is_open: h.is_open, open_time: h.open_time || '09:00:00', close_time: h.close_time || '19:00:00' });
        }
        setHours(full);
      })
      .catch((e) => Alert.alert('Erro', e.message))
      .finally(() => setLoading(false));
  }, []);

  const update = (weekday, patch) =>
    setHours((prev) => prev.map((h) => (h.weekday === weekday ? { ...h, ...patch } : h)));

  const saveAll = async () => {
    setSaving(true);
    try {
      for (const h of hours) {
        await setBarberHour(barberId, h.weekday, {
          weekday: h.weekday,
          is_open: h.is_open,
          open_time: h.is_open ? (h.open_time || '09:00:00') : null,
          close_time: h.is_open ? (h.close_time || '19:00:00') : null,
        });
      }
      Alert.alert('Pronto!', 'Horário do barbeiro salvo.');
    } catch (e) {
      Alert.alert('Erro', e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <Text style={styles.hint}>Sobrepõe o horário geral da barbearia — vale só para {barberName || 'este barbeiro'}.</Text>
      {hours.map((h) => (
        <View key={h.weekday} style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.day}>{WEEKDAYS[h.weekday]}</Text>
            <Switch value={h.is_open} onValueChange={(v) => update(h.weekday, { is_open: v })} trackColor={{ true: COLORS.primary, false: COLORS.border }} thumbColor="#fff" />
          </View>
          {h.is_open && (
            <View style={styles.timesRow}>
              <TouchableOpacity style={styles.timeBox} onPress={() => setPicker({ weekday: h.weekday, field: 'open_time' })}>
                <Text style={styles.timeLabel}>Entra</Text><Text style={styles.timeVal}>{hhmm(h.open_time)}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.timeBox} onPress={() => setPicker({ weekday: h.weekday, field: 'close_time' })}>
                <Text style={styles.timeLabel}>Sai</Text><Text style={styles.timeVal}>{hhmm(h.close_time)}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      ))}
      {picker && (
        <DateTimePicker
          value={timeToDate(hhmm(hours.find((h) => h.weekday === picker.weekday)?.[picker.field]))}
          mode="time" is24Hour display="default"
          onChange={(e, d) => {
            const target = picker; setPicker(Platform.OS === 'ios' ? picker : null);
            if (d && target) {
              const v = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:00`;
              update(target.weekday, { [target.field]: v });
            }
          }}
        />
      )}
      <GradientButton title={saving ? 'Salvando…' : 'Salvar horário'} onPress={saveAll} loading={saving} style={{ marginTop: 10 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  center: { justifyContent: 'center', alignItems: 'center' },
  hint: { color: COLORS.textMuted, fontSize: 13, marginBottom: 12, lineHeight: 19 },
  card: { backgroundColor: COLORS.surface, borderRadius: 14, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: COLORS.border },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  day: { color: COLORS.text, fontSize: 16, fontWeight: '600' },
  timesRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
  timeBox: { flex: 1, backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 12 },
  timeLabel: { color: COLORS.textMuted, fontSize: 12 },
  timeVal: { color: COLORS.primary, fontSize: 20, fontWeight: '700', marginTop: 2 },
});
