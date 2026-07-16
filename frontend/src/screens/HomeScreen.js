import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
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
import GradientButton from '../components/GradientButton';
import { getApiUrl } from '../config';
import { COLORS, GRADIENTS, SHADOW } from '../constants/business';
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
      const owner = (user?.role || 'owner') === 'owner';
      const appts = await getAppointments({ date: d });
      setToday(appts.filter((a) => a.status !== 'cancelado'));
      if (owner) {
        const summary = await getCashSummary({ start: d, end: d });
        setBalance(summary.saldo);
      }
    } catch (e) {
      setError(e.message || 'Erro de conexão.');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const shareLink = async () => {
    const url = await getApiUrl();
    const link = `${url}/agendar/${tenant?.slug}`;
    await Share.share({ message: `Agende seu horário na ${tenant?.name}: ${link}` });
  };

  const status = tenant?.subscription_status;
  const isOwner = (user?.role || 'owner') === 'owner';
  const showBanner = isOwner && status && status !== 'active';

  const Tile = ({ label, emoji, onPress }) => (
    <TouchableOpacity style={[styles.tile, SHADOW]} onPress={onPress} activeOpacity={0.85}>
      <LinearGradient colors={GRADIENTS.card} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.tileInner}>
        <View style={styles.tileIcon}><Text style={styles.tileEmoji}>{emoji}</Text></View>
        <Text style={styles.tileLabel}>{label}</Text>
      </LinearGradient>
    </TouchableOpacity>
  );

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={COLORS.primary} />}
    >
      <LinearGradient colors={GRADIENTS.header} style={[styles.header, SHADOW]}>
        <View style={styles.headerTop}>
          <Text style={styles.hello}>Olá, {user?.name || 'bem-vindo'} 👋</Text>
          <TouchableOpacity onPress={signOut}><Text style={styles.logout}>Sair</Text></TouchableOpacity>
        </View>
        <Text style={styles.shopName}>{tenant?.name || 'Minha Barbearia'}</Text>

        <View style={styles.statsRow}>
          <View style={styles.stat}>
            <Text style={styles.statNum}>{today.length}</Text>
            <Text style={styles.statLabel}>hoje na agenda</Text>
          </View>
          {isOwner && (
            <>
              <View style={styles.statDivider} />
              <View style={styles.stat}>
                <Text style={[styles.statNum, { color: balance >= 0 ? COLORS.primary : COLORS.danger }]}>{money(balance)}</Text>
                <Text style={styles.statLabel}>caixa hoje</Text>
              </View>
            </>
          )}
        </View>
      </LinearGradient>

      {showBanner && (
        <TouchableOpacity style={styles.banner} onPress={() => navigation.navigate('Subscription')} activeOpacity={0.85}>
          <Text style={styles.bannerText}>
            {status === 'trial' ? '🎁 Você está no período de teste' : '⚠ Assinatura inativa'}
          </Text>
          <Text style={styles.bannerHint}>Assinar agora →</Text>
        </TouchableOpacity>
      )}

      {!!error && (
        <TouchableOpacity style={styles.errorBox} onPress={() => navigation.navigate('Settings')}>
          <Text style={styles.errorText}>⚠ {error}</Text>
          <Text style={styles.errorHint}>Toque para configurar o servidor →</Text>
        </TouchableOpacity>
      )}

      {today.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Próximos hoje</Text>
          {today.slice(0, 4).map((a) => (
            <View key={a.id} style={styles.apptRow}>
              <View style={styles.timePill}><Text style={styles.timePillText}>{hhmm(a.time)}</Text></View>
              <Text style={styles.apptName} numberOfLines={1}>{a.customer_name} · {a.service_name}</Text>
            </View>
          ))}
        </View>
      )}

      <View style={styles.grid}>
        <Tile emoji="📅" label="Agenda" onPress={() => navigation.navigate('Agenda')} />
        <Tile emoji="➕" label="Novo agendamento" onPress={() => navigation.navigate('NewAppointment')} />
        <Tile emoji="👥" label="Clientes" onPress={() => navigation.navigate('Clients')} />
        {isOwner && <Tile emoji="💰" label="Fluxo de caixa" onPress={() => navigation.navigate('CashFlow')} />}
        {isOwner && <Tile emoji="✂️" label="Barbeiros" onPress={() => navigation.navigate('Staff')} />}
        {isOwner && <Tile emoji="🕐" label="Horários" onPress={() => navigation.navigate('Hours')} />}
        {isOwner && <Tile emoji="🎟️" label="Planos de corte" onPress={() => navigation.navigate('Plans')} />}
        {isOwner && <Tile emoji="📦" label="Loja / Estoque" onPress={() => navigation.navigate('Products')} />}
        {isOwner && <Tile emoji="🛒" label="Pedidos" onPress={() => navigation.navigate('Orders')} />}
        {isOwner && <Tile emoji="💳" label="Assinatura" onPress={() => navigation.navigate('Subscription')} />}
      </View>

      {isOwner && (
        <GradientButton title="🔗  Compartilhar link de agendamento" onPress={shareLink} style={{ marginTop: 18 }} />
      )}

      <TouchableOpacity onPress={() => navigation.navigate('Settings')} style={{ marginTop: 18, alignSelf: 'center' }}>
        <Text style={styles.settingsLink}>⚙  Configurações</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 16, paddingBottom: 40 },
  header: { borderRadius: 22, padding: 20, borderWidth: 1, borderColor: COLORS.border },
  headerTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  hello: { color: COLORS.textMuted, fontSize: 14 },
  logout: { color: COLORS.danger, fontSize: 14, fontWeight: '600' },
  shopName: { color: COLORS.text, fontSize: 24, fontWeight: '800', marginTop: 4 },
  statsRow: { flexDirection: 'row', alignItems: 'center', marginTop: 18, backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 16, paddingVertical: 14 },
  stat: { flex: 1, alignItems: 'center' },
  statDivider: { width: 1, height: 34, backgroundColor: COLORS.border },
  statNum: { color: COLORS.primary, fontSize: 25, fontWeight: '850', letterSpacing: -0.3 },
  statLabel: { color: COLORS.textMuted, fontSize: 12, marginTop: 3 },
  banner: { backgroundColor: 'rgba(240,194,75,0.12)', borderRadius: 16, padding: 15, marginTop: 14, borderWidth: 1, borderColor: 'rgba(240,194,75,0.4)', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  bannerText: { color: COLORS.primary, fontWeight: '700', flex: 1 },
  bannerHint: { color: COLORS.primary, fontSize: 13, fontWeight: '800' },
  errorBox: { backgroundColor: 'rgba(255,92,92,0.12)', borderRadius: 16, padding: 15, marginTop: 14, borderWidth: 1, borderColor: 'rgba(255,92,92,0.4)' },
  errorText: { color: '#ff9b9b' },
  errorHint: { color: '#ffbdbd', fontSize: 12, marginTop: 4 },
  card: { backgroundColor: COLORS.surface, borderRadius: 18, padding: 16, marginTop: 14, borderWidth: 1, borderColor: COLORS.border, ...SHADOW },
  cardTitle: { color: COLORS.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 10 },
  apptRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 },
  timePill: { backgroundColor: 'rgba(240,194,75,0.15)', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4, marginRight: 12 },
  timePillText: { color: COLORS.primary, fontWeight: '800', fontSize: 13 },
  apptName: { color: COLORS.text, flex: 1 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 16 },
  tile: { width: '47%', borderRadius: 18, borderWidth: 1, borderColor: COLORS.border, overflow: 'hidden' },
  tileInner: { padding: 16 },
  tileIcon: { width: 48, height: 48, borderRadius: 14, backgroundColor: 'rgba(240,194,75,0.13)', borderWidth: 1, borderColor: 'rgba(240,194,75,0.22)', alignItems: 'center', justifyContent: 'center' },
  tileEmoji: { fontSize: 24 },
  tileLabel: { color: COLORS.text, marginTop: 12, fontWeight: '750', fontSize: 15 },
  settingsLink: { color: COLORS.textMuted, fontSize: 15 },
});
