import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
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
import { getApiUrl, setApiUrl } from '../config';
import { COLORS } from '../constants/business';
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
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.logo}>💈</Text>
        <Text style={styles.title}>Agenda Barber</Text>
        <Text style={styles.subtitle}>Entre na sua conta</Text>

        <TextInput style={styles.input} placeholder="E-mail" placeholderTextColor={COLORS.textMuted} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
        <TextInput style={styles.input} placeholder="Senha" placeholderTextColor={COLORS.textMuted} secureTextEntry value={password} onChangeText={setPassword} />

        {!!error && <Text style={styles.error}>{error}</Text>}

        <TouchableOpacity style={styles.btn} onPress={submit} disabled={loading}>
          {loading ? <ActivityIndicator color="#1a1a1a" /> : <Text style={styles.btnText}>Entrar</Text>}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Signup')}>
          <Text style={styles.link}>Não tem conta? <Text style={styles.linkStrong}>Criar grátis</Text></Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setShowServer((v) => !v)} style={{ marginTop: 28 }}>
          <Text style={styles.serverToggle}>{showServer ? '▾' : '▸'} Endereço do servidor (avançado)</Text>
        </TouchableOpacity>
        {showServer && (
          <TextInput style={styles.input} placeholder="https://...onrender.com" placeholderTextColor={COLORS.textMuted} autoCapitalize="none" keyboardType="url" value={server} onChangeText={setServer} />
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 24, paddingTop: 60 },
  logo: { fontSize: 60, textAlign: 'center' },
  title: { color: COLORS.text, fontSize: 26, fontWeight: '800', textAlign: 'center', marginTop: 8 },
  subtitle: { color: COLORS.textMuted, textAlign: 'center', marginBottom: 28, marginTop: 4 },
  input: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 14, color: COLORS.text, fontSize: 16, marginBottom: 12 },
  error: { color: '#ff6b6b', marginBottom: 8 },
  btn: { backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 6 },
  btnText: { color: '#1a1a1a', fontWeight: '700', fontSize: 16 },
  link: { color: COLORS.textMuted, textAlign: 'center', marginTop: 20 },
  linkStrong: { color: COLORS.primary, fontWeight: '700' },
  serverToggle: { color: COLORS.textMuted, fontSize: 13 },
});
