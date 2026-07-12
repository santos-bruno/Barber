import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { getOrders, updateOrder } from '../api/client';
import { COLORS } from '../constants/business';
import { money } from '../utils/date';

const STATUS_COLOR = { novo: COLORS.info, entregue: COLORS.whatsapp, cancelado: COLORS.danger };

export default function OrdersScreen() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setOrders(await getOrders()); } catch (e) {} finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const setStatus = async (order, status) => {
    try { await updateOrder(order.id, status); load(); } catch (e) { Alert.alert('Erro', e.message); }
  };

  const renderItem = ({ item }) => (
    <View style={[styles.card, { borderLeftColor: STATUS_COLOR[item.status] || COLORS.border }]}>
      <View style={styles.head}>
        <Text style={styles.customer}>{item.customer_name}</Text>
        <View style={[styles.badge, { backgroundColor: STATUS_COLOR[item.status] }]}><Text style={styles.badgeText}>{item.status}</Text></View>
      </View>
      {item.items.map((it, idx) => (
        <Text key={idx} style={styles.item}>• {it.qty}× {it.product_name} — {money(it.price * it.qty)}</Text>
      ))}
      <Text style={styles.total}>Total: {money(item.total)}</Text>
      {item.status === 'novo' && (
        <View style={styles.actions}>
          <TouchableOpacity style={[styles.btn, { backgroundColor: COLORS.whatsapp }]} onPress={() => setStatus(item, 'entregue')}><Text style={styles.btnText}>Marcar entregue</Text></TouchableOpacity>
          <TouchableOpacity style={[styles.btn, { backgroundColor: COLORS.danger }]} onPress={() => setStatus(item, 'cancelado')}><Text style={styles.btnText}>Cancelar</Text></TouchableOpacity>
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={orders}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16 }}
        refreshing={loading}
        onRefresh={load}
        ListEmptyComponent={!loading && <Text style={styles.empty}>Nenhum pedido ainda. Os pedidos da loja virtual aparecem aqui.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  card: { backgroundColor: COLORS.surface, borderRadius: 16, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: COLORS.border, borderLeftWidth: 4 },
  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  customer: { color: COLORS.text, fontSize: 16, fontWeight: '700' },
  badge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText: { color: '#141414', fontSize: 11, fontWeight: '800', textTransform: 'uppercase' },
  item: { color: COLORS.textMuted, marginTop: 2 },
  total: { color: COLORS.primary, fontWeight: '800', marginTop: 8 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 12 },
  btn: { borderRadius: 10, paddingHorizontal: 14, paddingVertical: 9 },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  empty: { color: COLORS.textMuted, textAlign: 'center', marginTop: 40 },
});
