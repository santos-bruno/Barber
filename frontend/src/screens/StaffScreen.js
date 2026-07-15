import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import {
  Alert,
  FlatList,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { createStaff, deleteStaff, getStaff, resetBarberPassword } from '../api/client';
import GradientButton from '../components/GradientButton';
import { COLORS } from '../constants/business';

export default function StaffScreen({ navigation }) {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try { setStaff(await getStaff()); } catch (e) {} finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const add = async () => {
    if (!form.name.trim() || !form.email.trim() || form.password.length < 6) {
      Alert.alert('Atenção', 'Preencha nome, e-mail e senha (mín. 6).');
      return;
    }
    try {
      await createStaff({ name: form.name.trim(), email: form.email.trim(), password: form.password });
      setModal(false); setForm({ name: '', email: '', password: '' });
      load();
    } catch (e) { Alert.alert('Erro', e.message); }
  };

  const resetPass = (b) => {
    Alert.alert('Redefinir senha', `Gerar uma nova senha para ${b.name}?`, [
      { text: 'Não' },
      {
        text: 'Sim',
        onPress: async () => {
          try {
            const r = await resetBarberPassword(b.id, null);
            Alert.alert('Nova senha', `Login: ${b.email}\nSenha: ${r.password}\n\nPasse essa senha para ${b.name}.`);
          } catch (e) { Alert.alert('Erro', e.message); }
        },
      },
    ]);
  };

  const remove = (b) => {
    Alert.alert('Remover acesso', `Desativar o login de ${b.name}? Ele não poderá mais entrar.`, [
      { text: 'Não' },
      { text: 'Sim', style: 'destructive', onPress: async () => { try { await deleteStaff(b.id); load(); } catch (e) { Alert.alert('Erro', e.message); } } },
    ]);
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.avatar}><Text style={{ fontSize: 20 }}>✂️</Text></View>
      <View style={{ flex: 1 }}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.email}>{item.email}</Text>
      </View>
      <TouchableOpacity style={styles.hoursBtn} onPress={() => navigation.navigate('BarberHours', { barberId: item.id, barberName: item.name })}>
        <Text style={styles.hoursText}>Horários</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.keyBtn} onPress={() => resetPass(item)}>
        <Text style={styles.keyText}>🔑</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => remove(item)}><Text style={styles.remove}>Desativar</Text></TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.hint}>Cada barbeiro entra com o próprio login e vê apenas os atendimentos dele — sem acesso a caixa, loja ou lucro.</Text>
      <FlatList
        data={staff}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16 }}
        refreshing={loading}
        onRefresh={load}
        ListEmptyComponent={!loading && <Text style={styles.empty}>Nenhum barbeiro cadastrado. Toque em ＋.</Text>}
      />
      <TouchableOpacity style={styles.fab} onPress={() => setModal(true)}>
        <Text style={styles.fabText}>＋</Text>
      </TouchableOpacity>

      <Modal visible={modal} transparent animationType="slide" onRequestClose={() => setModal(false)}>
        <View style={styles.modalBg}><View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Novo barbeiro</Text>
          <TextInput style={styles.input} placeholder="Nome" placeholderTextColor={COLORS.textMuted} value={form.name} onChangeText={(v) => setForm({ ...form, name: v })} />
          <TextInput style={styles.input} placeholder="E-mail (login dele)" placeholderTextColor={COLORS.textMuted} autoCapitalize="none" keyboardType="email-address" value={form.email} onChangeText={(v) => setForm({ ...form, email: v })} />
          <TextInput style={styles.input} placeholder="Senha (mín. 6)" placeholderTextColor={COLORS.textMuted} secureTextEntry value={form.password} onChangeText={(v) => setForm({ ...form, password: v })} />
          <View style={styles.actions}>
            <TouchableOpacity style={[styles.mBtn, styles.mCancel]} onPress={() => setModal(false)}><Text style={styles.mBtnText}>Cancelar</Text></TouchableOpacity>
            <View style={{ flex: 1 }}><GradientButton title="Criar acesso" onPress={add} /></View>
          </View>
        </View></View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  hint: { color: COLORS.textMuted, fontSize: 13, padding: 16, paddingBottom: 0, lineHeight: 19 },
  card: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: COLORS.surface, borderRadius: 16, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: COLORS.border },
  avatar: { width: 44, height: 44, borderRadius: 12, backgroundColor: COLORS.surfaceAlt, alignItems: 'center', justifyContent: 'center' },
  name: { color: COLORS.text, fontSize: 16, fontWeight: '700' },
  email: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  remove: { color: COLORS.danger, fontWeight: '700' },
  hoursBtn: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.info, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 7, marginRight: 8 },
  hoursText: { color: COLORS.info, fontWeight: '700', fontSize: 13 },
  keyBtn: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6, marginRight: 8 },
  keyText: { fontSize: 15 },
  empty: { color: COLORS.textMuted, textAlign: 'center', marginTop: 40 },
  fab: { position: 'absolute', right: 20, bottom: 24, backgroundColor: COLORS.primary, width: 58, height: 58, borderRadius: 29, alignItems: 'center', justifyContent: 'center', elevation: 4 },
  fabText: { color: COLORS.onPrimary, fontSize: 30, fontWeight: '700', marginTop: -2 },
  modalBg: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: COLORS.surface, borderTopLeftRadius: 22, borderTopRightRadius: 22, padding: 20 },
  modalTitle: { color: COLORS.text, fontSize: 18, fontWeight: '800', marginBottom: 6 },
  input: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 13, color: COLORS.text, fontSize: 16, marginTop: 10 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 18, alignItems: 'center' },
  mBtn: { backgroundColor: COLORS.primary, borderRadius: 12, paddingVertical: 15, paddingHorizontal: 18, alignItems: 'center' },
  mCancel: { backgroundColor: COLORS.border },
  mBtnText: { fontWeight: '700', color: COLORS.text },
});
