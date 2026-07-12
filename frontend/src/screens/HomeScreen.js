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
import { BUSINESS, COLORS } from '../constants/business';
import { hhmm, money, todayApi } from '../utils/date';

export default function HomeScreen({ navigation }) {
  const [today, setToday] = useState([]);
  const [balance, setBalance] = useState(0);
  const [apiUrl, setApiUrl] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const url = await getApiUrl();
      setApiUrl(url);
      const d = todayApi();
      const [appts, summary] = await Promise.all([
        getAppointments({ date: d }),
        getCashSummary({ start: d, end: d }),
      ]);
      setToday(appts.filter((a) => a.status !== 'cancelado'));
      setBalance(summary.saldo);
    } catch (e) {
      setError(e.message || 'Erro de conexão. Configure o servidor.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const shareLink = async () => {
    const url = await getApiUrl();
    await Share.share({
      message: `Agende seu horário na ${BUSINESS.name}: ${url}`,
    });
  };

  const Tile = ({ label, emoji, onPress, color }) => (
    <TouchableOpacity style={[styles.tile, color && { borderColor: color }]} onPress={onPress}>
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
      <Text style={styles.title}>{BUSINESS.name}</Text>

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
          <Text style={[styles.statNum, { color: balance >= 0 ? COLORS.primary : '#ff6b6b' }]}>
            {money(balance)}
          </Text>
          <Text style={styles.statLabel}>Caixa hoje</Text>
        </View>
      </View>

      {today.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Próximos hoje</Text>
          {today.slice(0, 4).map((a) => (
            <View key={a.id} style={styles.apptRow}>
              <Text style={styles.apptTime}>{hhmm(a.time)}</Text>
              <Text style={styles.apptName} numberOfLines={1}>
                {a.customer_name} · {a.service_name}
              </Text>
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
        <Tile emoji="⚙️" label="Configurações" onPress={() => navigation.navigate('Settings')} />
      </View>

      <TouchableOpacity style={styles.shareBtn} onPress={shareLink}>
        <Text style={styles.shareText}>🔗 Compartilhar link de agendamento</Text>
      </TouchableOpacity>

      <Text style={styles.footer}>Desenvolvido por {BUSINESS.developer}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingBottom: 40 },
  logo: { fontSize: 52, textAlign: 'center', marginTop: 8 },
  title: { color: COLORS.text, fontSize: 20, fontWeight: 'bold', textAlign: 'center', marginBottom: 16 },
  errorBox: {
    backgroundColor: '#3a2020', borderRadius: 10, padding: 14, marginBottom: 16,
    borderWidth: 1, borderColor: '#ff6b6b',
  },
  errorText: { color: '#ff9b9b' },
  errorHint: { color: '#ffbdbd', fontSize: 12, marginTop: 4 },
  statsRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  stat: {
    flex: 1, backgroundColor: COLORS.surface, borderRadius: 12, padding: 16,
    borderWidth: 1, borderColor: COLORS.border, alignItems: 'center',
  },
  statNum: { color: COLORS.primary, fontSize: 22, fontWeight: '800' },
  statLabel: { color: COLORS.textMuted, fontSize: 12, marginTop: 4 },
  card: {
    backgroundColor: COLORS.surface, borderRadius: 12, padding: 16, marginBottom: 16,
    borderWidth: 1, borderColor: COLORS.border,
  },
  cardTitle: { color: COLORS.primary, fontSize: 13, fontWeight: '700', textTransform: 'uppercase', marginBottom: 10 },
  apptRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 },
  apptTime: { color: COLORS.primary, fontWeight: '700', width: 56 },
  apptName: { color: COLORS.text, flex: 1 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  tile: {
    width: '47%', backgroundColor: COLORS.surface, borderRadius: 14, padding: 18,
    borderWidth: 1, borderColor: COLORS.border, alignItems: 'center',
  },
  tileEmoji: { fontSize: 30 },
  tileLabel: { color: COLORS.text, marginTop: 8, fontWeight: '600', textAlign: 'center' },
  shareBtn: {
    backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, marginTop: 18, alignItems: 'center',
  },
  shareText: { color: '#1a1a1a', fontWeight: '700', fontSize: 15 },
  footer: { color: COLORS.textMuted, textAlign: 'center', marginTop: 24, fontSize: 12 },
});
