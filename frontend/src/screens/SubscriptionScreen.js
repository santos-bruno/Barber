import { LinearGradient } from 'expo-linear-gradient';
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { appmaxCheckout, getAppmaxStatus, getPlans } from '../api/client';
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

const onlyDigits = (s) => (s || '').replace(/\D/g, '');

export default function SubscriptionScreen() {
  const { tenant, refreshTenant } = useAuth();
  const [plans, setPlans] = useState([]);
  const [selected, setSelected] = useState('anual');
  const [configured, setConfigured] = useState(null); // null = carregando
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Dados do cartão
  const [holder, setHolder] = useState('');
  const [doc, setDoc] = useState('');
  const [number, setNumber] = useState('');
  const [expM, setExpM] = useState('');
  const [expY, setExpY] = useState('');
  const [cvv, setCvv] = useState('');

  useEffect(() => {
    getPlans().then((d) => setPlans(d.plans || [])).catch(() => {});
    getAppmaxStatus()
      .then((s) => setConfigured(!!s.configured))
      .catch(() => setConfigured(false))
      .finally(() => setLoading(false));
    refreshTenant();
  }, []);

  const doPay = async () => {
    if (!holder.trim()) return Alert.alert('Atenção', 'Informe o nome impresso no cartão.');
    if (!onlyDigits(doc)) return Alert.alert('Atenção', 'Informe seu CPF ou CNPJ.');
    if (onlyDigits(number).length < 13) return Alert.alert('Atenção', 'Número do cartão inválido.');
    if (!expM || !expY) return Alert.alert('Atenção', 'Informe a validade do cartão.');
    if (onlyDigits(cvv).length < 3) return Alert.alert('Atenção', 'CVV inválido.');

    setSubmitting(true);
    try {
      await appmaxCheckout({
        plan: selected,
        holder_name: holder.trim(),
        cpf_cnpj: onlyDigits(doc),
        card_number: onlyDigits(number),
        card_cvv: onlyDigits(cvv),
        card_exp_month: onlyDigits(expM),
        card_exp_year: onlyDigits(expY),
      });
      await refreshTenant();
      Alert.alert('Tudo certo! ✅', 'Pagamento enviado. Sua assinatura será ativada em instantes.');
      setNumber(''); setCvv('');
    } catch (e) {
      Alert.alert('Erro no pagamento', e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const dateInfo = tenant?.subscription_status === 'active' ? tenant?.current_period_end : tenant?.trial_ends_at;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 44 }}>
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

      {configured === false && (
        <View style={styles.notice}>
          <Text style={styles.noticeText}>
            💳 O pagamento no app está sendo ativado. Você continua no período de teste normalmente —
            fale com o suporte no WhatsApp para assinar.
          </Text>
        </View>
      )}

      {configured === true && (
        <>
          <Text style={styles.sectionTitle}>Pagamento no cartão</Text>

          <Text style={styles.label}>Nome impresso no cartão</Text>
          <TextInput style={styles.input} placeholder="Ex: BRUNO A SANTOS" placeholderTextColor={COLORS.textMuted} autoCapitalize="characters" value={holder} onChangeText={setHolder} />

          <Text style={styles.label}>CPF ou CNPJ</Text>
          <TextInput style={styles.input} placeholder="Somente números" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" value={doc} onChangeText={setDoc} />

          <Text style={styles.label}>Número do cartão</Text>
          <TextInput style={styles.input} placeholder="0000 0000 0000 0000" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" value={number} onChangeText={setNumber} />

          <View style={styles.row}>
            <View style={styles.col}>
              <Text style={styles.label}>Mês</Text>
              <TextInput style={styles.input} placeholder="MM" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" maxLength={2} value={expM} onChangeText={setExpM} />
            </View>
            <View style={styles.col}>
              <Text style={styles.label}>Ano</Text>
              <TextInput style={styles.input} placeholder="AAAA" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" maxLength={4} value={expY} onChangeText={setExpY} />
            </View>
            <View style={styles.col}>
              <Text style={styles.label}>CVV</Text>
              <TextInput style={styles.input} placeholder="123" placeholderTextColor={COLORS.textMuted} keyboardType="number-pad" maxLength={4} value={cvv} onChangeText={setCvv} />
            </View>
          </View>

          <GradientButton title="Assinar agora" onPress={doPay} loading={submitting} style={{ marginTop: 22 }} />
          <Text style={styles.hint}>🔒 Ambiente seguro · pagamento processado pela Appmax. Renovação automática.</Text>
        </>
      )}
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
  row: { flexDirection: 'row', gap: 10 },
  col: { flex: 1 },
  notice: { backgroundColor: 'rgba(240,194,75,0.10)', borderWidth: 1, borderColor: 'rgba(240,194,75,0.35)', borderRadius: 16, padding: 16, marginTop: 20 },
  noticeText: { color: COLORS.text, fontSize: 14, lineHeight: 20 },
  hint: { color: COLORS.textMuted, fontSize: 12, marginTop: 12, textAlign: 'center' },
});
