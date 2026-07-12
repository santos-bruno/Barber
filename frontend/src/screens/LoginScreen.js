import { LinearGradient } from 'expo-linear-gradient';
import React, { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { login } from '../api/client';
import GradientButton from '../components/GradientButton';
import { getApiUrl, setApiUrl } from '../config';
import { COLORS, GRADIENTS, SHADOW } from '../constants/business';
import { useAuth } from '../context/AuthContext';

export default function LoginScreen({ navigation }) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [server, setServer] = useState('');
  const [showServer, setShowServer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getApiUrl().then(setServer);
  }, []);

  const submit = async () => {
    setError('');
    if (!email.trim() || !password) {
      setError('Informe e-mail e senha.');
      return;
    }
    setLoading(true);
    try {
      if (server.trim()) await setApiUrl(server.trim());
      const auth = await login({ email: email.trim(), password });
      await signIn(auth);
    } catch (e) {
      setError(e.message || 'Não foi possível entrar.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: COLORS.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.badgeWrap}>
          <LinearGradient colors={GRADIENTS.gold} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.badge, SHADOW]}>
            <Text style={styles.badgeEmoji}>💈</Text>
          </LinearGradient>
        </View>
        <Text style={styles.title}>Agenda Barber</Text>
        <Text style={styles.subtitle}>Gestão e agendamento para a sua barbearia</Text>

        <View style={styles.card}>
          <Text style={styles.label}>E-mail</Text>
          <TextInput style={styles.input} placeholder="voce@email.com" placeholderTextColor={COLORS.textMuted} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
          <Text style={styles.label}>Senha</Text>
          <TextInput style={styles.input} placeholder="••••••" placeholderTextColor={COLORS.textMuted} secureTextEntry value={password} onChangeText={setPassword} />

          {!!error && <Text style={styles.error}>{error}</Text>}

          <GradientButton title="Entrar" onPress={submit} loading={loading} style={{ marginTop: 18 }} />
        </View>

        <TouchableOpacity onPress={() => navigation.navigate('Signup')} style={styles.signupRow}>
          <Text style={styles.link}>Não tem conta? </Text>
          <Text style={styles.linkStrong}>Criar grátis</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setShowServer((v) => !v)} style={{ marginTop: 30, alignSelf: 'center' }}>
          <Text style={styles.serverToggle}>{showServer ? '▾' : '▸'} Endereço do servidor (avançado)</Text>
        </TouchableOpacity>
        {showServer && (
          <TextInput style={[styles.input, { marginTop: 10 }]} placeholder="https://...onrender.com" placeholderTextColor={COLORS.textMuted} autoCapitalize="none" keyboardType="url" value={server} onChangeText={setServer} />
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 24, paddingTop: 64 },
  badgeWrap: { alignItems: 'center' },
  badge: { width: 92, height: 92, borderRadius: 26, alignItems: 'center', justifyContent: 'center' },
  badgeEmoji: { fontSize: 46 },
  title: { color: COLORS.text, fontSize: 28, fontWeight: '800', textAlign: 'center', marginTop: 18, letterSpacing: 0.3 },
  subtitle: { color: COLORS.textMuted, textAlign: 'center', marginTop: 6, marginBottom: 26, fontSize: 15 },
  card: { backgroundColor: COLORS.surface, borderRadius: 20, padding: 20, borderWidth: 1, borderColor: COLORS.border, ...SHADOW },
  label: { color: COLORS.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 12, marginBottom: 7 },
  input: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 14, padding: 15, color: COLORS.text, fontSize: 16 },
  error: { color: COLORS.danger, marginTop: 12 },
  signupRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 22 },
  link: { color: COLORS.textMuted },
  linkStrong: { color: COLORS.primary, fontWeight: '800' },
  serverToggle: { color: COLORS.textMuted, fontSize: 13 },
});
