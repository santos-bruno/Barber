import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import {
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { getAppointments, getCashSummary } from '../api/client';
import { getApiUrl } from '../config';
import { COLORS } from '../constants/business';
import { useAuth } from '../context/AuthContext';
import { hhmm, money, todayApi } from '../utils/date';

export default function HomeScreen({ navigation }) {
  const { tenant, user, signOut } = useAuth();
  const [today, setToday] = useState([]);
  const [balance, setBalance] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const d = todayApi();
      const [appts, summary] = await Promise.all([
        getAppointments({ date: d }),
        getCashSummary({ start: d, end: d }),
      ]);
      setToday(appts.filter((a) => a.status !== 'cancelado'));
      setBalance(summary.saldo);
    } catch (e) {
      setError(e.message || 'Erro de conexão.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const shareLink = async () => {
    const url = await getApiUrl();
    const link = `${url}/agendar/${tenant?.slug}`;
    await Share.share({ message: `Agende seu horário na ${tenant?.name}: ${link}` });
  };

  const status = tenant?.subscription_status;
  const showBanner = status && status !== 'active';

  const Tile = ({ label, emoji, onPress }) => (
    <TouchableOpacity style={styles.tile} onPress={onPress}>
      <Text style={styles.tileEmoji}>{emoji}</Text>
      <Text style={styles.tileLabel}>{label}</Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={COLORS.primary} />}
    >
      <Text style={styles.logo}>💈</Text>
      <Text style={styles.title}>{tenant?.name || 'Minha Barbearia'}</Text>
      {!!user && <Text style={styles.hello}>Olá, {user.name}</Text>}

      {showBanner && (
        <TouchableOpacity style={styles.banner} onPress={() => navigation.navigate('Subscription')}>
          <Text style={styles.bannerText}>
            {status === 'trial' ? '🎁 Você está no período de teste.' : '⚠ Assinatura inativa.'}
          </Text>
          <Text style={styles.bannerHint}>Toque para assinar →</Text>
        </TouchableOpacity>
      )}

      {!!error && (
        <TouchableOpacity style={styles.errorBox} onPress={() => navigation.navigate('Settings')}>
          <Text style={styles.errorText}>⚠ {error}</Text>
          <Text style={styles.errorHint}>Toque para configurar o servidor →</Text>
        </TouchableOpacity>
      )}

      <View style={styles.statsRow}>
        <View style={styles.stat}>
          <Text style={styles.statNum}>{today.length}</Text>
          <Text style={styles.statLabel}>Hoje na agenda</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statNum, { color: balance >= 0 ? COLORS.primary : '#ff6b6b' }]}>{money(balance)}</Text>
          <Text style={styles.statLabel}>Caixa hoje</Text>
        </View>
      </View>

      {today.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Próximos hoje</Text>
          {today.slice(0, 4).map((a) => (
            <View key={a.id} style={styles.apptRow}>
              <Text style={styles.apptTime}>{hhmm(a.time)}</Text>
              <Text style={styles.apptName} numberOfLines={1}>{a.customer_name} · {a.service_name}</Text>
            </View>
          ))}
        </View>
      )}

      <View style={styles.grid}>
        <Tile emoji="📅" label="Agenda" onPress={() => navigation.navigate('Agenda')} />
        <Tile emoji="➕" label="Novo agendamento" onPress={() => navigation.navigate('NewAppointment')} />
        <Tile emoji="👥" label="Clientes" onPress={() => navigation.navigate('Clients')} />
        <Tile emoji="💰" label="Fluxo de caixa" onPress={() => navigation.navigate('CashFlow')} />
        <Tile emoji="🕐" label="Horários" onPress={() => navigation.navigate('Hours')} />
        <Tile emoji="💳" label="Assinatura" onPress={() => navigation.navigate('Subscription')} />
      </View>

      <TouchableOpacity style={styles.shareBtn} onPress={shareLink}>
        <Text style={styles.shareText}>🔗 Compartilhar link de agendamento</Text>
      </TouchableOpacity>

      <View style={styles.footerRow}>
        <TouchableOpacity onPress={() => navigation.navigate('Settings')}>
          <Text style={styles.footerLink}>Configurações</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={signOut}>
          <Text style={[styles.footerLink, { color: '#ff6b6b' }]}>Sair</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingBottom: 40 },
  logo: { fontSize: 52, textAlign: 'center', marginTop: 8 },
  title: { color: COLORS.text, fontSize: 20, fontWeight: 'bold', textAlign: 'center' },
  hello: { color: COLORS.textMuted, textAlign: 'center', marginBottom: 14 },
  banner: { backgroundColor: '#33301f', borderRadius: 10, padding: 14, marginBottom: 14, borderWidth: 1, borderColor: COLORS.primary },
  bannerText: { color: COLORS.primary, fontWeight: '700' },
  bannerHint: { color: COLORS.primary, fontSize: 12, marginTop: 2 },
  errorBox: { backgroundColor: '#3a2020', borderRadius: 10, padding: 14, marginBottom: 16, borderWidth: 1, borderColor: '#ff6b6b' },
  errorText: { color: '#ff9b9b' },
  errorHint: { color: '#ffbdbd', fontSize: 12, marginTop: 4 },
  statsRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  stat: { flex: 1, backgroundColor: COLORS.surface, borderRadius: 12, padding: 16, borderWidth: 1, borderColor: COLORS.border, alignItems: 'center' },
  statNum: { color: COLORS.primary, fontSize: 22, fontWeight: '800' },
  statLabel: { color: COLORS.textMuted, fontSize: 12, marginTop: 4 },
  card: { backgroundColor: COLORS.surface, borderRadius: 12, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: COLORS.border },
  cardTitle: { color: COLORS.primary, fontSize: 13, fontWeight: '700', textTransform: 'uppercase', marginBottom: 10 },
  apptRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 },
  apptTime: { color: COLORS.primary, fontWeight: '700', width: 56 },
  apptName: { color: COLORS.text, flex: 1 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  tile: { width: '47%', backgroundColor: COLORS.surface, borderRadius: 14, padding: 18, borderWidth: 1, borderColor: COLORS.border, alignItems: 'center' },
  tileEmoji: { fontSize: 30 },
  tileLabel: { color: COLORS.text, marginTop: 8, fontWeight: '600', textAlign: 'center' },
  shareBtn: { backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, marginTop: 18, alignItems: 'center' },
  shareText: { color: '#1a1a1a', fontWeight: '700', fontSize: 15 },
  footerRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 24, paddingHorizontal: 10 },
  footerLink: { color: COLORS.textMuted, fontSize: 15 },
});
