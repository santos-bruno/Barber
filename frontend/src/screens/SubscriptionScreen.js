import { LinearGradient } from 'expo-linear-gradient';
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
import GradientButton from '../components/GradientButton';
import { COLORS, GRADIENTS, SHADOW } from '../constants/business';
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
    getPlans().then((d) => setPlans(d.plans || [])).catch(() => {}).finally(() => setLoading(false));
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
      if (res.checkout_url) Linking.openURL(res.checkout_url);
      else Alert.alert('Assinatura criada', 'Verifique seu e-mail para concluir o pagamento.');
      refreshTenant();
    } catch (e) {
      Alert.alert('Erro', e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const dateInfo = tenant?.subscription_status === 'active' ? tenant?.current_period_end : tenant?.trial_ends_at;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <LinearGradient colors={GRADIENTS.header} style={[styles.statusCard, SHADOW]}>
        <Text style={styles.statusLabel}>Status da assinatura</Text>
        <Text style={styles.statusValue}>{STATUS_LABEL[tenant?.subscription_status] || '—'}</Text>
        {!!dateInfo && (
          <Text style={styles.statusDate}>
            {tenant?.subscription_status === 'active' ? 'Renova em ' : 'Teste até '}
            {apiToBR(String(dateInfo).slice(0, 10))}
          </Text>
        )}
      </LinearGradient>

      <Text style={styles.sectionTitle}>Escolha seu plano</Text>
      {loading ? (
        <ActivityIndicator color={COLORS.primary} style={{ marginTop: 20 }} />
      ) : (
        plans.map((p) => {
          const isSel = selected === p.id;
          const isYear = p.id === 'anual';
          return (
            <TouchableOpacity key={p.id} activeOpacity={0.85} style={[styles.plan, isSel && styles.planActive]} onPress={() => setSelected(p.id)}>
              <View style={styles.radioWrap}>
                <View style={[styles.radio, isSel && styles.radioOn]}>{isSel && <View style={styles.radioDot} />}</View>
                <View>
                  <View style={styles.planNameRow}>
                    <Text style={styles.planName}>{p.label}</Text>
                    {isYear && <View style={styles.tag}><Text style={styles.tagText}>MELHOR VALOR</Text></View>}
                  </View>
                  <Text style={styles.planCycle}>{isYear ? 'cobrança anual' : 'cobrança mensal'}</Text>
                </View>
              </View>
              <Text style={styles.planPrice}>{money(p.price)}</Text>
            </TouchableOpacity>
          );
        })
      )}

      <Text style={styles.label}>CPF ou CNPJ (para a cobrança)</Text>
      <TextInput style={styles.input} placeholder="Somente números" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" value={doc} onChangeText={setDoc} />

      <GradientButton title="Ir para o pagamento" onPress={doSubscribe} loading={submitting} style={{ marginTop: 20 }} />
      <Text style={styles.hint}>🔒 Ambiente seguro (Asaas) para inserir os dados do cartão.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  statusCard: { borderRadius: 20, padding: 22, borderWidth: 1, borderColor: COLORS.border, alignItems: 'center' },
  statusLabel: { color: COLORS.textMuted, fontSize: 12, textTransform: 'uppercase', fontWeight: '700', letterSpacing: 0.5 },
  statusValue: { color: COLORS.primary, fontSize: 24, fontWeight: '800', marginTop: 6 },
  statusDate: { color: COLORS.textMuted, marginTop: 4 },
  sectionTitle: { color: COLORS.text, fontSize: 17, fontWeight: '800', marginTop: 26, marginBottom: 14 },
  plan: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: COLORS.surface, borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 18, padding: 16, marginBottom: 12 },
  planActive: { borderColor: COLORS.primary, backgroundColor: 'rgba(240,194,75,0.08)' },
  radioWrap: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  radio: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: COLORS.border, alignItems: 'center', justifyContent: 'center' },
  radioOn: { borderColor: COLORS.primary },
  radioDot: { width: 11, height: 11, borderRadius: 6, backgroundColor: COLORS.primary },
  planNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  planName: { color: COLORS.text, fontSize: 17, fontWeight: '800' },
  tag: { backgroundColor: COLORS.primary, borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  tagText: { color: COLORS.onPrimary, fontSize: 9, fontWeight: '800' },
  planCycle: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  planPrice: { color: COLORS.primary, fontSize: 20, fontWeight: '800' },
  label: { color: COLORS.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 14, marginBottom: 7 },
  input: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 14, padding: 15, color: COLORS.text, fontSize: 16 },
  hint: { color: COLORS.textMuted, fontSize: 12, marginTop: 12, textAlign: 'center' },
});
