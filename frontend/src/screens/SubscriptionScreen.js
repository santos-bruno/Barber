import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { getPlans, subscribe } from '../api/client';
import { COLORS } from '../constants/business';
import { useAuth } from '../context/AuthContext';
import { apiToBR, money } from '../utils/date';

const STATUS_LABEL = {
  trial: 'Período de teste',
  active: 'Ativa',
  overdue: 'Pagamento em atraso',
  canceled: 'Cancelada',
};

export default function SubscriptionScreen() {
  const { tenant, refreshTenant } = useAuth();
  const [plans, setPlans] = useState([]);
  const [selected, setSelected] = useState('anual');
  const [doc, setDoc] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getPlans()
      .then((d) => setPlans(d.plans || []))
      .catch(() => {})
      .finally(() => setLoading(false));
    refreshTenant();
  }, []);

  const doSubscribe = async () => {
    if (!doc.replace(/\D/g, '')) {
      Alert.alert('Atenção', 'Informe seu CPF ou CNPJ.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await subscribe({ plan: selected, cpf_cnpj: doc.replace(/\D/g, ''), billing_type: 'CREDIT_CARD' });
      if (res.checkout_url) {
        Linking.openURL(res.checkout_url);
      } else {
        Alert.alert('Assinatura criada', 'Verifique seu e-mail para concluir o pagamento.');
      }
      refreshTenant();
    } catch (e) {
      Alert.alert('Erro', e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const dateInfo = tenant?.subscription_status === 'active'
    ? tenant?.current_period_end
    : tenant?.trial_ends_at;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
      <View style={styles.statusCard}>
        <Text style={styles.statusLabel}>Status da assinatura</Text>
        <Text style={styles.statusValue}>{STATUS_LABEL[tenant?.subscription_status] || '—'}</Text>
        {!!dateInfo && (
          <Text style={styles.statusDate}>
            {tenant?.subscription_status === 'active' ? 'Renova em ' : 'Teste até '}
            {apiToBR(String(dateInfo).slice(0, 10))}
          </Text>
        )}
      </View>

      <Text style={styles.sectionTitle}>Escolha seu plano</Text>
      {loading ? (
        <ActivityIndicator color={COLORS.primary} style={{ marginTop: 20 }} />
      ) : (
        plans.map((p) => (
          <TouchableOpacity
            key={p.id}
            style={[styles.plan, selected === p.id && styles.planActive]}
            onPress={() => setSelected(p.id)}
          >
            <View>
              <Text style={styles.planName}>{p.label}</Text>
              <Text style={styles.planCycle}>{p.id === 'anual' ? 'por ano' : 'por mês'}</Text>
            </View>
            <Text style={styles.planPrice}>{money(p.price)}</Text>
          </TouchableOpacity>
        ))
      )}

      <Text style={styles.label}>CPF ou CNPJ (para a cobrança)</Text>
      <TextInput
        style={styles.input}
        placeholder="Somente números"
        placeholderTextColor={COLORS.textMuted}
        keyboardType="number-pad"
        value={doc}
        onChangeText={setDoc}
      />

      <TouchableOpacity style={styles.btn} onPress={doSubscribe} disabled={submitting}>
        {submitting ? <ActivityIndicator color="#1a1a1a" /> : <Text style={styles.btnText}>Ir para o pagamento</Text>}
      </TouchableOpacity>
      <Text style={styles.hint}>
        Você será direcionado a um ambiente seguro (Asaas) para inserir os dados do cartão.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  statusCard: { backgroundColor: COLORS.surface, borderRadius: 14, padding: 18, borderWidth: 1, borderColor: COLORS.primary, alignItems: 'center' },
  statusLabel: { color: COLORS.textMuted, fontSize: 12, textTransform: 'uppercase', fontWeight: '700' },
  statusValue: { color: COLORS.primary, fontSize: 22, fontWeight: '800', marginTop: 4 },
  statusDate: { color: COLORS.textMuted, marginTop: 4 },
  sectionTitle: { color: COLORS.text, fontSize: 16, fontWeight: '700', marginTop: 24, marginBottom: 12 },
  plan: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: COLORS.surface, borderWidth: 2, borderColor: COLORS.border, borderRadius: 12, padding: 16, marginBottom: 12 },
  planActive: { borderColor: COLORS.primary, backgroundColor: '#33301f' },
  planName: { color: COLORS.text, fontSize: 17, fontWeight: '700' },
  planCycle: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  planPrice: { color: COLORS.primary, fontSize: 20, fontWeight: '800' },
  label: { color: COLORS.primary, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginTop: 12, marginBottom: 6 },
  input: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 13, color: COLORS.text, fontSize: 16 },
  btn: { backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 20 },
  btnText: { color: '#1a1a1a', fontWeight: '700', fontSize: 16 },
  hint: { color: COLORS.textMuted, fontSize: 12, marginTop: 12, textAlign: 'center' },
});
