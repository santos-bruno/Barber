import React, { useState } from 'react';
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

import { register } from '../api/client';
import GradientButton from '../components/GradientButton';
import { COLORS, SHADOW } from '../constants/business';
import { useAuth } from '../context/AuthContext';

export default function SignupScreen({ navigation }) {
  const { signIn } = useAuth();
  const [form, setForm] = useState({
    barbershop_name: '', owner_name: '', email: '', password: '', whatsapp: '', address: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    setError('');
    if (!form.barbershop_name || !form.owner_name || !form.email || !form.password) {
      setError('Preencha os campos obrigatórios.');
      return;
    }
    if (form.password.length < 6) {
      setError('A senha deve ter ao menos 6 caracteres.');
      return;
    }
    setLoading(true);
    try {
      const auth = await register(form);
      await signIn(auth);
    } catch (e) {
      setError(e.message || 'Não foi possível criar a conta.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: COLORS.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Criar conta grátis</Text>
        <Text style={styles.subtitle}>Teste o sistema sem compromisso · sem cartão</Text>

        <View style={styles.card}>
          <Text style={styles.label}>Nome da barbearia *</Text>
          <TextInput style={styles.input} placeholderTextColor={COLORS.textMuted} value={form.barbershop_name} onChangeText={set('barbershop_name')} />
          <Text style={styles.label}>Seu nome *</Text>
          <TextInput style={styles.input} placeholderTextColor={COLORS.textMuted} value={form.owner_name} onChangeText={set('owner_name')} />
          <Text style={styles.label}>E-mail *</Text>
          <TextInput style={styles.input} placeholderTextColor={COLORS.textMuted} autoCapitalize="none" keyboardType="email-address" value={form.email} onChangeText={set('email')} />
          <Text style={styles.label}>Senha (mín. 6) *</Text>
          <TextInput style={styles.input} placeholderTextColor={COLORS.textMuted} secureTextEntry value={form.password} onChangeText={set('password')} />
          <Text style={styles.label}>WhatsApp (com DDD)</Text>
          <TextInput style={styles.input} placeholderTextColor={COLORS.textMuted} keyboardType="phone-pad" value={form.whatsapp} onChangeText={set('whatsapp')} />
          <Text style={styles.label}>Endereço</Text>
          <TextInput style={styles.input} placeholderTextColor={COLORS.textMuted} value={form.address} onChangeText={set('address')} />

          {!!error && <Text style={styles.error}>{error}</Text>}

          <GradientButton title="Criar conta" onPress={submit} loading={loading} style={{ marginTop: 20 }} />
        </View>

        <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.row}>
          <Text style={styles.link}>Já tem conta? </Text>
          <Text style={styles.linkStrong}>Entrar</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingTop: 36, paddingBottom: 50 },
  title: { color: COLORS.text, fontSize: 26, fontWeight: '800', textAlign: 'center' },
  subtitle: { color: COLORS.textMuted, textAlign: 'center', marginBottom: 20, marginTop: 6 },
  card: { backgroundColor: COLORS.surface, borderRadius: 20, padding: 20, borderWidth: 1, borderColor: COLORS.border, ...SHADOW },
  label: { color: COLORS.textMuted, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 12, marginBottom: 6 },
  input: { backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border, borderRadius: 14, padding: 14, color: COLORS.text, fontSize: 16 },
  error: { color: COLORS.danger, marginTop: 14 },
  row: { flexDirection: 'row', justifyContent: 'center', marginTop: 18 },
  link: { color: COLORS.textMuted },
  linkStrong: { color: COLORS.primary, fontWeight: '800' },
});
