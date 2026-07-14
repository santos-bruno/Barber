import DateTimePicker from '@react-native-community/datetimepicker';
import React, { useEffect, useState } from 'react';
import {
  Alert,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { createAppointment, getAvailability, getServices, getStaff } from '../api/client';
import { COLORS } from '../constants/business';
import { useAuth } from '../context/AuthContext';
import { apiToBR, toApiDate } from '../utils/date';

export default function NewAppointmentScreen({ navigation }) {
  const { user } = useAuth();
  const isOwner = (user?.role || 'owner') === 'owner';
  const [services, setServices] = useState([]);
  const [service, setService] = useState(null);
  const [barbers, setBarbers] = useState([]);
  const [barberId, setBarberId] = useState(null);
  const [date, setDate] = useState(new Date());
  const [showPicker, setShowPicker] = useState(false);
  const [slots, setSlots] = useState([]);
  const [time, setTime] = useState(null);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [paymentType, setPaymentType] = useState('avista'); // avista | assinatura
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getServices().then((s) => {
      setServices(s);
      if (s.length) setService(s[0]);
    }).catch(() => {});
    if (isOwner) getStaff().then(setBarbers).catch(() => {});
  }, [isOwner]);

  useEffect(() => {
    if (!service) return;
    setTime(null);
    setLoadingSlots(true);
    getAvailability(toApiDate(date), service.id, barberId)
      .then((r) => setSlots(r.slots || []))
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false));
  }, [service, date, barberId]);

  const save = async () => {
    if (!service || !time || !name.trim()) {
      Alert.alert('Atenção', 'Preencha serviço, horário e nome.');
      return;
    }
    setSaving(true);
    try {
      await createAppointment({
        customer_name: name.trim(),
        phone: phone.trim(),
        service_id: service.id,
        service_name: service.name,
        date: toApiDate(date),
        time: time + ':00',
        source: 'admin',
        payment_type: paymentType,
        barber_id: isOwner ? barberId : undefined,
      });
      Alert.alert('Pronto!', 'Agendamento criado.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      Alert.alert('Erro', e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
      <Text style={styles.label}>Pagamento</Text>
      <View style={styles.chipRow}>
        <TouchableOpacity style={[styles.chip, paymentType === 'avista' && styles.chipActive]} onPress={() => setPaymentType('avista')}>
          <Text style={[styles.chipText, paymentType === 'avista' && styles.chipTextActive]}>À vista</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.chip, paymentType === 'assinatura' && styles.chipActive]} onPress={() => setPaymentType('assinatura')}>
          <Text style={[styles.chipText, paymentType === 'assinatura' && styles.chipTextActive]}>Assinatura</Text>
        </TouchableOpacity>
      </View>
      {paymentType === 'assinatura' && (
        <Text style={styles.assinHint}>O cliente precisa ter um plano de corte ativo (Clientes → Assinar). O corte não entra no caixa (já pago na mensalidade).</Text>
      )}

      {isOwner && barbers.length > 0 && (
        <>
          <Text style={styles.label}>Barbeiro</Text>
          <View style={styles.chipRow}>
            <TouchableOpacity style={[styles.chip, barberId === null && styles.chipActive]} onPress={() => setBarberId(null)}>
              <Text style={[styles.chipText, barberId === null && styles.chipTextActive]}>Sem definir</Text>
            </TouchableOpacity>
            {barbers.map((b) => (
              <TouchableOpacity key={b.id} style={[styles.chip, barberId === b.id && styles.chipActive]} onPress={() => setBarberId(b.id)}>
                <Text style={[styles.chipText, barberId === b.id && styles.chipTextActive]}>{b.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </>
      )}

      <Text style={styles.label}>Serviço</Text>
      <View style={styles.chipRow}>
        {services.map((s) => (
          <TouchableOpacity
            key={s.id}
            style={[styles.chip, service?.id === s.id && styles.chipActive]}
            onPress={() => setService(s)}
          >
            <Text style={[styles.chipText, service?.id === s.id && styles.chipTextActive]}>{s.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Data</Text>
      <TouchableOpacity style={styles.selector} onPress={() => setShowPicker(true)}>
        <Text style={styles.selectorText}>📅 {apiToBR(toApiDate(date))}</Text>
      </TouchableOpacity>
      {showPicker && (
        <DateTimePicker
          value={date}
          mode="date"
          display="default"
          minimumDate={new Date()}
          onChange={(e, d) => {
            setShowPicker(Platform.OS === 'ios');
            if (d) setDate(d);
          }}
        />
      )}

      <Text style={styles.label}>Horário</Text>
      {loadingSlots ? (
        <Text style={styles.hint}>Buscando horários livres…</Text>
      ) : slots.length === 0 ? (
        <Text style={styles.hint}>Sem horários livres nesta data.</Text>
      ) : (
        <View style={styles.chipRow}>
          {slots.map((t) => (
            <TouchableOpacity
              key={t}
              style={[styles.slot, time === t && styles.chipActive]}
              onPress={() => setTime(t)}
            >
              <Text style={[styles.chipText, time === t && styles.chipTextActive]}>{t}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <Text style={styles.label}>Nome do cliente</Text>
      <TextInput style={styles.input} placeholder="Nome" placeholderTextColor={COLORS.textMuted} value={name} onChangeText={setName} />

      <Text style={styles.label}>WhatsApp (com DDD)</Text>
      <TextInput style={styles.input} placeholder="93 99999-9999" placeholderTextColor={COLORS.textMuted} keyboardType="phone-pad" value={phone} onChangeText={setPhone} />

      <TouchableOpacity style={[styles.save, saving && { opacity: 0.6 }]} disabled={saving} onPress={save}>
        <Text style={styles.saveText}>{saving ? 'Salvando…' : 'Criar agendamento'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  label: { color: COLORS.primary, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginTop: 18, marginBottom: 8 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.surface, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  slot: { borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.surface, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 10 },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { color: COLORS.text },
  chipTextActive: { color: '#1a1a1a', fontWeight: '700' },
  selector: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 14 },
  selectorText: { color: COLORS.text, fontSize: 16 },
  input: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 12, color: COLORS.text, fontSize: 16 },
  hint: { color: COLORS.textMuted },
  assinHint: { color: COLORS.textMuted, fontSize: 12.5, marginTop: 8, lineHeight: 18 },
  save: { backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 26 },
  saveText: { color: '#1a1a1a', fontWeight: '700', fontSize: 16 },
});
