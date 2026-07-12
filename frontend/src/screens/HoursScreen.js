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

import { getHours, updateHour } from '../api/client';
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

export default function HoursScreen() {
  const [hours, setHours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [picker, setPicker] = useState(null); // { weekday, field }

  useEffect(() => {
    getHours()
      .then((data) => {
        // Garante os 7 dias na ordem 0..6.
        const byDay = {};
        data.forEach((h) => { byDay[h.weekday] = h; });
        const full = [];
        for (let w = 0; w < 7; w++) {
          full.push(byDay[w] || { weekday: w, is_open: false, open_time: '09:00:00', close_time: '19:00:00', slot_minutes: 30 });
        }
        setHours(full);
      })
      .catch((e) => Alert.alert('Erro', e.message))
      .finally(() => setLoading(false));
  }, []);

  const update = (weekday, patch) => {
    setHours((prev) => prev.map((h) => (h.weekday === weekday ? { ...h, ...patch } : h)));
  };

  const saveAll = async () => {
    setSaving(true);
    try {
      for (const h of hours) {
        await updateHour(h.weekday, {
          weekday: h.weekday,
          is_open: h.is_open,
          open_time: h.is_open ? (h.open_time || '09:00:00') : null,
          close_time: h.is_open ? (h.close_time || '19:00:00') : null,
          slot_minutes: h.slot_minutes || 30,
        });
      }
      Alert.alert('Pronto!', 'Horários salvos.');
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
      {hours.map((h) => (
        <View key={h.weekday} style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.day}>{WEEKDAYS[h.weekday]}</Text>
            <Switch
              value={h.is_open}
              onValueChange={(v) => update(h.weekday, { is_open: v })}
              trackColor={{ true: COLORS.primary, false: COLORS.border }}
              thumbColor="#fff"
            />
          </View>
          {h.is_open && (
            <View style={styles.timesRow}>
              <TouchableOpacity style={styles.timeBox} onPress={() => setPicker({ weekday: h.weekday, field: 'open_time' })}>
                <Text style={styles.timeLabel}>Abre</Text>
                <Text style={styles.timeVal}>{hhmm(h.open_time) || '09:00'}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.timeBox} onPress={() => setPicker({ weekday: h.weekday, field: 'close_time' })}>
                <Text style={styles.timeLabel}>Fecha</Text>
                <Text style={styles.timeVal}>{hhmm(h.close_time) || '19:00'}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      ))}

      {picker && (
        <DateTimePicker
          value={timeToDate(hours.find((h) => h.weekday === picker.weekday)?.[picker.field])}
          mode="time"
          is24Hour
          display="default"
          onChange={(e, d) => {
            const target = picker;
            setPicker(Platform.OS === 'ios' ? picker : null);
            if (d && target) {
              const hh = String(d.getHours()).padStart(2, '0');
              const mm = String(d.getMinutes()).padStart(2, '0');
              update(target.weekday, { [target.field]: `${hh}:${mm}:00` });
            }
          }}
        />
      )}

      <TouchableOpacity style={[styles.save, saving && { opacity: 0.6 }]} disabled={saving} onPress={saveAll}>
        <Text style={styles.saveText}>{saving ? 'Salvando…' : 'Salvar horários'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  center: { justifyContent: 'center', alignItems: 'center' },
  card: { backgroundColor: COLORS.surface, borderRadius: 12, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: COLORS.border },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  day: { color: COLORS.text, fontSize: 16, fontWeight: '600' },
  timesRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
  timeBox: { flex: 1, backgroundColor: COLORS.background, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 12 },
  timeLabel: { color: COLORS.textMuted, fontSize: 12 },
  timeVal: { color: COLORS.primary, fontSize: 20, fontWeight: '700', marginTop: 2 },
  save: { backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 10 },
  saveText: { color: '#1a1a1a', fontWeight: '700', fontSize: 16 },
});
