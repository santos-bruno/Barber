import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import {
  Alert,
  FlatList,
  Modal,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { createProduct, getProducts, moveStock } from '../api/client';
import GradientButton from '../components/GradientButton';
import { COLORS } from '../constants/business';
import { money } from '../utils/date';

export default function ProductsScreen() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [addModal, setAddModal] = useState(false);
  const [stockModal, setStockModal] = useState(null); // product
  const [form, setForm] = useState({ name: '', price: '', cost: '', stock: '', online: true });
  const [mv, setMv] = useState({ type: 'entrada', qty: '', cash: true });

  const load = useCallback(async () => {
    setLoading(true);
    try { setProducts(await getProducts()); } catch (e) {} finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const addProduct = async () => {
    if (!form.name.trim()) { Alert.alert('Atenção', 'Informe o nome.'); return; }
    try {
      await createProduct({
        name: form.name.trim(),
        price: parseFloat(form.price.replace(',', '.')) || 0,
        cost: parseFloat(form.cost.replace(',', '.')) || 0,
        stock: parseInt(form.stock, 10) || 0,
        sellable_online: form.online,
      });
      setAddModal(false); setForm({ name: '', price: '', cost: '', stock: '', online: true });
      load();
    } catch (e) { Alert.alert('Erro', e.message); }
  };

  const doMove = async () => {
    const qty = parseInt(mv.qty, 10);
    if (!qty || qty <= 0) { Alert.alert('Atenção', 'Informe a quantidade.'); return; }
    try {
      await moveStock(stockModal.id, { type: mv.type, qty, affects_cash: mv.cash });
      setStockModal(null); setMv({ type: 'entrada', qty: '', cash: true });
      load();
    } catch (e) { Alert.alert('Erro', e.message); }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity style={styles.card} onPress={() => setStockModal(item)}>
      <View style={{ flex: 1 }}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.sub}>Venda {money(item.price)} · Custo {money(item.cost)}{item.sellable_online ? ' · 🌐 na loja' : ''}</Text>
      </View>
      <View style={styles.stockBox}>
        <Text style={[styles.stockNum, item.stock <= 0 && { color: COLORS.danger }]}>{item.stock}</Text>
        <Text style={styles.stockLbl}>estoque</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={products}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16 }}
        refreshing={loading}
        onRefresh={load}
        ListHeaderComponent={<Text style={styles.hint}>Toque num produto para dar entrada/saída de estoque.</Text>}
        ListEmptyComponent={!loading && <Text style={styles.empty}>Nenhum produto. Toque em ＋ para adicionar.</Text>}
      />

      <TouchableOpacity style={styles.fab} onPress={() => setAddModal(true)}>
        <Text style={styles.fabText}>＋</Text>
      </TouchableOpacity>

      {/* Add product */}
      <Modal visible={addModal} transparent animationType="slide" onRequestClose={() => setAddModal(false)}>
        <View style={styles.modalBg}><View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Novo produto</Text>
          <TextInput style={styles.input} placeholder="Nome" placeholderTextColor={COLORS.textMuted} value={form.name} onChangeText={(v) => setForm({ ...form, name: v })} />
          <View style={styles.rowGap}>
            <TextInput style={[styles.input, { flex: 1 }]} placeholder="Preço venda" placeholderTextColor={COLORS.textMuted} keyboardType="decimal-pad" value={form.price} onChangeText={(v) => setForm({ ...form, price: v })} />
            <TextInput style={[styles.input, { flex: 1 }]} placeholder="Custo" placeholderTextColor={COLORS.textMuted} keyboardType="decimal-pad" value={form.cost} onChangeText={(v) => setForm({ ...form, cost: v })} />
          </View>
          <TextInput style={styles.input} placeholder="Estoque inicial" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" value={form.stock} onChangeText={(v) => setForm({ ...form, stock: v })} />
          <View style={styles.switchRow}>
            <Text style={styles.switchLbl}>Vender na loja virtual</Text>
            <Switch value={form.online} onValueChange={(v) => setForm({ ...form, online: v })} trackColor={{ true: COLORS.primary, false: COLORS.border }} thumbColor="#fff" />
          </View>
          <View style={styles.modalActions}>
            <TouchableOpacity style={[styles.mBtn, styles.mCancel]} onPress={() => setAddModal(false)}><Text style={styles.mBtnText}>Cancelar</Text></TouchableOpacity>
            <View style={{ flex: 1 }}><GradientButton title="Salvar" onPress={addProduct} /></View>
          </View>
        </View></View>
      </Modal>

      {/* Stock move */}
      <Modal visible={!!stockModal} transparent animationType="slide" onRequestClose={() => setStockModal(null)}>
        <View style={styles.modalBg}><View style={styles.modalCard}>
          <Text style={styles.modalTitle}>{stockModal?.name}</Text>
          <Text style={styles.sub}>Estoque atual: {stockModal?.stock}</Text>
          <View style={[styles.rowGap, { marginTop: 12 }]}>
            <TouchableOpacity style={[styles.typeBtn, mv.type === 'entrada' && styles.typeIn]} onPress={() => setMv({ ...mv, type: 'entrada' })}>
              <Text style={[styles.typeText, mv.type === 'entrada' && { color: '#fff' }]}>Entrada (compra)</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.typeBtn, mv.type === 'saida' && styles.typeOut]} onPress={() => setMv({ ...mv, type: 'saida' })}>
              <Text style={[styles.typeText, mv.type === 'saida' && { color: '#fff' }]}>Saída (venda)</Text>
            </TouchableOpacity>
          </View>
          <TextInput style={styles.input} placeholder="Quantidade" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" value={mv.qty} onChangeText={(v) => setMv({ ...mv, qty: v })} />
          <View style={styles.switchRow}>
            <Text style={styles.switchLbl}>Lançar no caixa</Text>
            <Switch value={mv.cash} onValueChange={(v) => setMv({ ...mv, cash: v })} trackColor={{ true: COLORS.primary, false: COLORS.border }} thumbColor="#fff" />
          </View>
          <View style={styles.modalActions}>
            <TouchableOpacity style={[styles.mBtn, styles.mCancel]} onPress={() => setStockModal(null)}><Text style={styles.mBtnText}>Cancelar</Text></TouchableOpacity>
            <View style={{ flex: 1 }}><GradientButton title="Confirmar" onPress={doMove} /></View>
          </View>
        </View></View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  hint: { color: COLORS.textMuted, fontSize: 13, marginBottom: 12 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.surface, borderRadius: 16, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: COLORS.border },
  name: { color: COLORS.text, fontSize: 16, fontWeight: '700' },
  sub: { color: COLORS.textMuted, marginTop: 3, fontSize: 13 },
  stockBox: { alignItems: 'center', marginLeft: 12 },
  stockNum: { color: COLORS.primary, fontSize: 22, fontWeight: '800' },
  stockLbl: { color: COLORS.textMuted, fontSize: 11 },
  empty: { color: COLORS.textMuted, textAlign: 'center', marginTop: 40 },
  fab: { position: 'absolute', right: 20, bottom: 24, backgroundColor: COLORS.primary, width: 58, height: 58, borderRadius: 29, alignItems: 'center', justifyContent: 'center', elevation: 4 },
  fabText: { color: COLORS.onPrimary, fontSize: 30, fontWeight: '700', marginTop: -2 },
  modalBg: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: COLORS.surface, borderTopLeftRadius: 22, borderTopRightRadius: 22, padding: 20 },
  modalTitle: { color: COLORS.text, fontSize: 18, fontWeight: '800' },
  input: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 13, color: COLORS.text, fontSize: 16, marginTop: 10 },
  rowGap: { flexDirection: 'row', gap: 10 },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 },
  switchLbl: { color: COLORS.text },
  typeBtn: { flex: 1, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 12, alignItems: 'center' },
  typeIn: { backgroundColor: COLORS.whatsapp, borderColor: COLORS.whatsapp },
  typeOut: { backgroundColor: COLORS.danger, borderColor: COLORS.danger },
  typeText: { color: COLORS.text, fontWeight: '700', fontSize: 13 },
  modalActions: { flexDirection: 'row', gap: 10, marginTop: 18, alignItems: 'center' },
  mBtn: { backgroundColor: COLORS.primary, borderRadius: 12, paddingVertical: 15, paddingHorizontal: 18, alignItems: 'center' },
  mCancel: { backgroundColor: COLORS.border },
  mBtnText: { fontWeight: '700', color: COLORS.text },
});
