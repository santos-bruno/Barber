import DateTimePicker from '@react-native-community/datetimepicker';
import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import {
  Alert,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { createPlanCorte, deletePlanCorte, getPlansCorte } from '../api/client';
import GradientButton from '../components/GradientButton';
import { COLORS } from '../constants/business';
import { hhmm, money, WEEKDAYS } from '../utils/date';

export default function PlansScreen() {
  const [plans, setPlans] = useState([]);
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [cuts, setCuts] = useState('');
  const [days, setDays] = useState([]); // [0,2]
  const [limitTime, setLimitTime] = useState(false);
  const [start, setStart] = useState('09:00');
  const [end, setEnd] = useState('12:00');
  const [picker, setPicker] = useState(null); // 'start' | 'end'
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try { setPlans(await getPlansCorte()); } catch (e) {}
  }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const toggleDay = (d) =>
    setDays((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d].sort()));

  const save = async () => {
    if (!name.trim() || !price) {
      Alert.alert('Atenção', 'Informe nome e valor do plano.');
      return;
    }
    setSaving(true);
    try {
      await createPlanCorte({
        name: name.trim(),
        price: parseFloat(price.replace(',', '.')) || 0,
        cuts_per_month: parseInt(cuts, 10) || 0,
        allowed_weekdays: days.join(','),
        allowed_time_start: limitTime ? start + ':00' : null,
        allowed_time_end: limitTime ? end + ':00' : null,
      });
      setName(''); setPrice(''); setCuts(''); setDays([]); setLimitTime(false);
      load();
      Alert.alert('Pronto!', 'Plano criado.');
    } catch (e) {
      Alert.alert('Erro', e.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = (p) => {
    Alert.alert('Remover', `Excluir o plano "${p.name}"?`, [
      { text: 'Não' },
      { text: 'Sim', style: 'destructive', onPress: async () => { try { await deletePlanCorte(p.id); load(); } catch (e) {} } },
    ]);
  };

  const daysLabel = (csv) =>
    !csv ? 'todos os dias' : csv.split(',').map((d) => WEEKDAYS[Number(d)]?.slice(0, 3)).join(', ');

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Novo plano de assinatura</Text>
        <TextInput style={styles.input} placeholder="Nome (ex: Corte Mensal)" placeholderTextColor={COLORS.textMuted} value={name} onChangeText={setName} />
        <View style={styles.rowGap}>
          <TextInput style={[styles.input, { flex: 1 }]} placeholder="Valor/mês" placeholderTextColor={COLORS.textMuted} keyboardType="decimal-pad" value={price} onChangeText={setPrice} />
          <TextInput style={[styles.input, { flex: 1 }]} placeholder="Cortes/mês (0=ilim.)" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" value={cuts} onChangeText={setCuts} />
        </View>

        <Text style={styles.label}>Dias permitidos (vazio = todos)</Text>
        <View style={styles.dayRow}>
          {WEEKDAYS.map((d, i) => (
            <TouchableOpacity key={i} style={[styles.day, days.includes(i) && styles.dayOn]} onPress={() => toggleDay(i)}>
              <Text style={[styles.dayText, days.includes(i) && styles.dayTextOn]}>{d.slice(0, 3)}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.label}>Limitar horário</Text>
          <Switch value={limitTime} onValueChange={setLimitTime} trackColor={{ true: COLORS.primary, false: COLORS.border }} thumbColor="#fff" />
        </View>
        {limitTime && (
          <View style={styles.rowGap}>
            <TouchableOpacity style={[styles.timeBox, { flex: 1 }]} onPress={() => setPicker('start')}>
              <Text style={styles.timeLabel}>De</Text><Text style={styles.timeVal}>{start}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.timeBox, { flex: 1 }]} onPress={() => setPicker('end')}>
              <Text style={styles.timeLabel}>Até</Text><Text style={styles.timeVal}>{end}</Text>
            </TouchableOpacity>
          </View>
        )}
        {picker && (
          <DateTimePicker
            value={new Date(2000, 0, 1, Number((picker === 'start' ? start : end).split(':')[0]), Number((picker === 'start' ? start : end).split(':')[1]))}
            mode="time" is24Hour display="default"
            onChange={(e, d) => {
              const which = picker; setPicker(Platform.OS === 'ios' ? picker : null);
              if (d) {
                const v = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
                which === 'start' ? setStart(v) : setEnd(v);
              }
            }}
          />
        )}

        <GradientButton title="Criar plano" onPress={save} loading={saving} style={{ marginTop: 16 }} />
      </View>

      <Text style={styles.section}>Planos ativos</Text>
      {plans.length === 0 && <Text style={styles.empty}>Nenhum plano ainda.</Text>}
      {plans.map((p) => (
        <TouchableOpacity key={p.id} style={styles.planCard} onLongPress={() => remove(p)}>
          <View style={{ flex: 1 }}>
            <Text style={styles.planName}>{p.name}</Text>
            <Text style={styles.planInfo}>
              {p.cuts_per_month ? `${p.cuts_per_month} cortes/mês` : 'cortes ilimitados'} · {daysLabel(p.allowed_weekdays)}
              {p.allowed_time_start ? ` · ${hhmm(p.allowed_time_start)}–${hhmm(p.allowed_time_end)}` : ''}
            </Text>
          </View>
          <Text style={styles.planPrice}>{money(p.price)}</Text>
        </TouchableOpacity>
      ))}
      <Text style={styles.hint}>Segure um plano para excluir. Para vincular a um cliente, vá em Clientes → Assinar.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  card: { backgroundColor: COLORS.surface, borderRadius: 18, padding: 16, borderWidth: 1, borderColor: COLORS.border },
  cardTitle: { color: COLORS.text, fontSize: 16, fontWeight: '800', marginBottom: 12 },
  input: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 13, color: COLORS.text, fontSize: 15, marginTop: 10 },
  rowGap: { flexDirection: 'row', gap: 10 },
  label: { color: COLORS.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 14 },
  dayRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 8 },
  day: { borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.surfaceAlt, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8 },
  dayOn: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  dayText: { color: COLORS.text, fontSize: 13, fontWeight: '600' },
  dayTextOn: { color: COLORS.onPrimary },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 },
  timeBox: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 12, marginTop: 8 },
  timeLabel: { color: COLORS.textMuted, fontSize: 12 },
  timeVal: { color: COLORS.primary, fontSize: 18, fontWeight: '700' },
  section: { color: COLORS.text, fontSize: 16, fontWeight: '800', marginTop: 24, marginBottom: 10 },
  empty: { color: COLORS.textMuted },
  planCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.surface, borderRadius: 14, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: COLORS.border },
  planName: { color: COLORS.text, fontSize: 15, fontWeight: '700' },
  planInfo: { color: COLORS.textMuted, fontSize: 12.5, marginTop: 3 },
  planPrice: { color: COLORS.primary, fontSize: 17, fontWeight: '800' },
  hint: { color: COLORS.textMuted, fontSize: 12, marginTop: 12 },
});
