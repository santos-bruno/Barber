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

import {
  createTransaction,
  deleteTransaction,
  getCashSummary,
  getCashflow,
} from '../api/client';
import { COLORS } from '../constants/business';
import { apiToBR, money, todayApi } from '../utils/date';

export default function CashFlowScreen() {
  const [summary, setSummary] = useState({ entradas: 0, saidas: 0, saldo: 0 });
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(false);
  const [type, setType] = useState('entrada');
  const [amount, setAmount] = useState('');
  const [desc, setDesc] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [s, list] = await Promise.all([getCashSummary(), getCashflow()]);
      setSummary(s);
      setTxs(list);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const add = async () => {
    const value = parseFloat(amount.replace(',', '.'));
    if (!value || value <= 0) {
      Alert.alert('Atenção', 'Informe um valor válido.');
      return;
    }
    try {
      await createTransaction({
        type,
        amount: value,
        description: desc.trim(),
        category: type === 'entrada' ? 'Serviço' : 'Despesa',
        date: todayApi(),
      });
      setModal(false);
      setAmount('');
      setDesc('');
      load();
    } catch (e) {
      Alert.alert('Erro', e.message);
    }
  };

  const remove = (tx) => {
    Alert.alert('Remover', 'Excluir este lançamento?', [
      { text: 'Não' },
      {
        text: 'Sim',
        style: 'destructive',
        onPress: async () => {
          try { await deleteTransaction(tx.id); load(); } catch (e) { Alert.alert('Erro', e.message); }
        },
      },
    ]);
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity style={styles.row} onLongPress={() => remove(item)}>
      <View style={{ flex: 1 }}>
        <Text style={styles.desc}>{item.description || item.category || 'Lançamento'}</Text>
        <Text style={styles.date}>{apiToBR(item.date)}</Text>
      </View>
      <Text style={[styles.amount, { color: item.type === 'entrada' ? COLORS.whatsapp : '#ff6b6b' }]}>
        {item.type === 'entrada' ? '+' : '−'} {money(item.amount)}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.summary}>
        <Text style={styles.saldoLabel}>Saldo</Text>
        <Text style={[styles.saldo, { color: summary.saldo >= 0 ? COLORS.primary : '#ff6b6b' }]}>
          {money(summary.saldo)}
        </Text>
        <View style={styles.summaryRow}>
          <Text style={styles.in}>Entradas: {money(summary.entradas)}</Text>
          <Text style={styles.out}>Saídas: {money(summary.saidas)}</Text>
        </View>
      </View>

      {!!error && <Text style={styles.error}>⚠ {error}</Text>}

      <FlatList
        data={txs}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16 }}
        refreshing={loading}
        onRefresh={load}
        ListEmptyComponent={!loading && <Text style={styles.empty}>Nenhum lançamento. Segure para excluir.</Text>}
      />

      <TouchableOpacity style={styles.fab} onPress={() => setModal(true)}>
        <Text style={styles.fabText}>＋</Text>
      </TouchableOpacity>

      <Modal visible={modal} transparent animationType="slide" onRequestClose={() => setModal(false)}>
        <View style={styles.modalBg}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Novo lançamento</Text>
            <View style={styles.typeRow}>
              <TouchableOpacity style={[styles.typeBtn, type === 'entrada' && styles.typeInActive]} onPress={() => setType('entrada')}>
                <Text style={[styles.typeText, type === 'entrada' && { color: '#fff' }]}>Entrada</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.typeBtn, type === 'saida' && styles.typeOutActive]} onPress={() => setType('saida')}>
                <Text style={[styles.typeText, type === 'saida' && { color: '#fff' }]}>Saída</Text>
              </TouchableOpacity>
            </View>
            <TextInput style={styles.input} placeholder="Valor (ex: 35,00)" placeholderTextColor={COLORS.textMuted} keyboardType="decimal-pad" value={amount} onChangeText={setAmount} />
            <TextInput style={styles.input} placeholder="Descrição" placeholderTextColor={COLORS.textMuted} value={desc} onChangeText={setDesc} />
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  summary: { backgroundColor: COLORS.surface, padding: 20, borderBottomWidth: 1, borderBottomColor: COLORS.border, alignItems: 'center' },
  saldoLabel: { color: COLORS.textMuted, textTransform: 'uppercase', fontSize: 12, fontWeight: '700' },
  saldo: { fontSize: 34, fontWeight: '800', marginVertical: 4 },
  summaryRow: { flexDirection: 'row', gap: 18, marginTop: 4 },
  in: { color: COLORS.whatsapp, fontWeight: '600' },
  out: { color: '#ff6b6b', fontWeight: '600' },
  error: { color: '#ff6b6b', textAlign: 'center', padding: 12 },
  row: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.surface, borderRadius: 12, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: COLORS.border },
  desc: { color: COLORS.text, fontSize: 15, fontWeight: '600' },
  date: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
  amount: { fontSize: 16, fontWeight: '800' },
  empty: { color: COLORS.textMuted, textAlign: 'center', marginTop: 40 },
  fab: { position: 'absolute', right: 20, bottom: 24, backgroundColor: COLORS.primary, width: 58, height: 58, borderRadius: 29, alignItems: 'center', justifyContent: 'center', elevation: 4 },
  fabText: { color: '#1a1a1a', fontSize: 30, fontWeight: '700', marginTop: -2 },
  modalBg: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: COLORS.surface, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20 },
  modalTitle: { color: COLORS.text, fontSize: 18, fontWeight: '700', marginBottom: 14 },
  typeRow: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  typeBtn: { flex: 1, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 12, alignItems: 'center' },
  typeInActive: { backgroundColor: COLORS.whatsapp, borderColor: COLORS.whatsapp },
  typeOutActive: { backgroundColor: '#ff6b6b', borderColor: '#ff6b6b' },
  typeText: { color: COLORS.text, fontWeight: '700' },
  input: { backgroundColor: COLORS.background, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 12, color: COLORS.text, fontSize: 16, marginBottom: 10 },
  modalActions: { flexDirection: 'row', gap: 10, marginTop: 6 },
  mBtn: { flex: 1, backgroundColor: COLORS.primary, borderRadius: 10, padding: 14, alignItems: 'center' },
  mCancel: { backgroundColor: COLORS.border },
  mBtnText: { fontWeight: '700', color: COLORS.text },
});
