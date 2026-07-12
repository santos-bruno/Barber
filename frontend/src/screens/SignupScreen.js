import React, { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
} from 'react-native';

import { register } from '../api/client';
import { COLORS } from '../constants/business';
import { useAuth } from '../context/AuthContext';

export default function SignupScreen({ navigation }) {
  const { signIn } = useAuth();
  const [form, setForm] = useState({
    barbershop_name: '',
    owner_name: '',
    email: '',
    password: '',
    whatsapp: '',
    address: '',
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

  const Field = ({ label, k, ...props }) => (
    <>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        placeholderTextColor={COLORS.textMuted}
        value={form[k]}
        onChangeText={set(k)}
        {...props}
      />
    </>
  );

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Criar conta grátis</Text>
        <Text style={styles.subtitle}>Teste o sistema sem compromisso</Text>

        <Field label="Nome da barbearia *" k="barbershop_name" />
        <Field label="Seu nome *" k="owner_name" />
        <Field label="E-mail *" k="email" autoCapitalize="none" keyboardType="email-address" />
        <Field label="Senha (mín. 6) *" k="password" secureTextEntry />
        <Field label="WhatsApp (com DDD)" k="whatsapp" keyboardType="phone-pad" />
        <Field label="Endereço" k="address" />

        {!!error && <Text style={styles.error}>{error}</Text>}

        <TouchableOpacity style={styles.btn} onPress={submit} disabled={loading}>
          {loading ? <ActivityIndicator color="#1a1a1a" /> : <Text style={styles.btnText}>Criar conta</Text>}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Login')}>
          <Text style={styles.link}>Já tem conta? <Text style={styles.linkStrong}>Entrar</Text></Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 24, paddingTop: 30, paddingBottom: 50 },
  title: { color: COLORS.text, fontSize: 24, fontWeight: '800', textAlign: 'center' },
  subtitle: { color: COLORS.textMuted, textAlign: 'center', marginBottom: 20, marginTop: 4 },
  label: { color: COLORS.primary, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginTop: 12, marginBottom: 6 },
  input: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 13, color: COLORS.text, fontSize: 16 },
  error: { color: '#ff6b6b', marginTop: 14 },
  btn: { backgroundColor: COLORS.primary, borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 22 },
  btnText: { color: '#1a1a1a', fontWeight: '700', fontSize: 16 },
  link: { color: COLORS.textMuted, textAlign: 'center', marginTop: 18 },
  linkStrong: { color: COLORS.primary, fontWeight: '700' },
});
