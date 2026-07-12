import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import {
  Alert,
  FlatList,
  Linking,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  createClient,
  createClientSub,
  getClients,
  getPlansCorte,
} from '../api/client';
import { COLORS } from '../constants/business';
import { money } from '../utils/date';

export default function ClientsScreen() {
  const [clients, setClients] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [assignFor, setAssignFor] = useState(null); // client
  const [plans, setPlans] = useState([]);

  const openAssign = async (client) => {
    try {
      const list = await getPlansCorte();
      if (!list.length) {
        Alert.alert('Sem planos', 'Crie um plano de assinatura em "Planos" primeiro.');
        return;
      }
      setPlans(list);
      setAssignFor(client);
    } catch (e) { Alert.alert('Erro', e.message); }
  };

  const assignPlan = async (plan) => {
    try {
      await createClientSub({ client_id: assignFor.id, plan_id: plan.id });
      setAssignFor(null);
      Alert.alert('Pronto!', `${assignFor.name} agora assina o plano ${plan.name}.`);
    } catch (e) { Alert.alert('Erro', e.message); }
  };

  const load = useCallback(async (q = '') => {
    setLoading(true);
    setError('');
    try {
      setClients(await getClients(q));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(search); }, [load]));

  const whatsapp = (c) => {
    if (!c.phone) {
      Alert.alert('Sem telefone', 'Cliente sem WhatsApp cadastrado.');
      return;
    }
    Linking.openURL(`https://wa.me/${c.phone.replace(/\D/g, '')}`);
  };

  const add = async () => {
    if (!name.trim()) {
      Alert.alert('Atenção', 'Informe o nome.');
      return;
    }
    try {
      await createClient({ name: name.trim(), phone: phone.trim() });
      setModal(false);
      setName('');
      setPhone('');
      load(search);
    } catch (e) {
      Alert.alert('Erro', e.message);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={{ flex: 1 }}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.phone}>{item.phone || 'sem telefone'}</Text>
      </View>
      <TouchableOpacity style={styles.assinBtn} onPress={() => openAssign(item)}>
        <Text style={styles.assinText}>Assinar</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.waBtn} onPress={() => whatsapp(item)}>
        <Text style={styles.waText}>WhatsApp</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.search}
          placeholder="Buscar por nome ou telefone"
          placeholderTextColor={COLORS.textMuted}
          value={search}
          onChangeText={setSearch}
          onSubmitEditing={() => load(search)}
          returnKeyType="search"
        />
        <TouchableOpacity style={styles.addBtn} onPress={() => setModal(true)}>
          <Text style={styles.addText}>＋</Text>
        </TouchableOpacity>
      </View>

      {!!error && <Text style={styles.error}>⚠ {error}</Text>}

      <FlatList
        data={clients}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16 }}
        refreshing={loading}
        onRefresh={() => load(search)}
        ListEmptyComponent={!loading && <Text style={styles.empty}>Nenhum cliente.</Text>}
      />

      <Modal visible={modal} transparent animationType="slide" onRequestClose={() => setModal(false)}>
        <View style={styles.modalBg}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Novo cliente</Text>
            <TextInput style={styles.input} placeholder="Nome" placeholderTextColor={COLORS.textMuted} value={name} onChangeText={setName} />
            <TextInput style={styles.input} placeholder="WhatsApp com DDD" placeholderTextColor={COLORS.textMuted} keyboardType="phone-pad" value={phone} onChangeText={setPhone} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={[styles.mBtn, styles.mCancel]} onPress={() => setModal(false)}>
                <Text style={styles.mBtnText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.mBtn} onPress={add}>
                <Text style={[styles.mBtnText, { color: '#1a1a1a' }]}>Salvar</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={!!assignFor} transparent animationType="slide" onRequestClose={() => setAssignFor(null)}>
        <View style={styles.modalBg}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Assinar plano — {assignFor?.name}</Text>
            {plans.map((p) => (
              <TouchableOpacity key={p.id} style={styles.planOpt} onPress={() => assignPlan(p)}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.planOptName}>{p.name}</Text>
                  <Text style={styles.planOptInfo}>{p.cuts_per_month ? `${p.cuts_per_month} cortes/mês` : 'ilimitado'}</Text>
                </View>
                <Text style={styles.planOptPrice}>{money(p.price)}</Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity style={[styles.mBtn, styles.mCancel, { marginTop: 8 }]} onPress={() => setAssignFor(null)}>
              <Text style={styles.mBtnText}>Fechar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  searchRow: { flexDirection: 'row', gap: 10, padding: 16, backgroundColor: COLORS.surface, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  search: { flex: 1, backgroundColor: COLORS.background, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, paddingHorizontal: 12, color: COLORS.text },
  addBtn: { backgroundColor: COLORS.primary, borderRadius: 10, width: 46, alignItems: 'center', justifyContent: 'center' },
  addText: { color: '#1a1a1a', fontSize: 26, fontWeight: '700', marginTop: -2 },
  error: { color: '#ff6b6b', textAlign: 'center', padding: 12 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.surface, borderRadius: 12, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: COLORS.border },
  name: { color: COLORS.text, fontSize: 16, fontWeight: '600' },
  phone: { color: COLORS.textMuted, marginTop: 2 },
  waBtn: { backgroundColor: COLORS.whatsapp, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8 },
  waText: { color: '#fff', fontWeight: '700' },
  assinBtn: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.primary, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8, marginRight: 8 },
  assinText: { color: COLORS.primary, fontWeight: '700' },
  planOpt: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 14, marginTop: 10 },
  planOptName: { color: COLORS.text, fontWeight: '700', fontSize: 15 },
  planOptInfo: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
  planOptPrice: { color: COLORS.primary, fontWeight: '800', fontSize: 16 },
  empty: { color: COLORS.textMuted, textAlign: 'center', marginTop: 40 },
  modalBg: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: COLORS.surface, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20 },
  modalTitle: { color: COLORS.text, fontSize: 18, fontWeight: '700', marginBottom: 14 },
  input: { backgroundColor: COLORS.background, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 12, color: COLORS.text, fontSize: 16, marginBottom: 10 },
  modalActions: { flexDirection: 'row', gap: 10, marginTop: 6 },
  mBtn: { flex: 1, backgroundColor: COLORS.primary, borderRadius: 10, padding: 14, alignItems: 'center' },
  mCancel: { backgroundColor: COLORS.border },
  mBtnText: { fontWeight: '700', color: COLORS.text },
});
