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

import { changePassword, getHealth } from '../api/client';
import { getApiUrl, setApiUrl } from '../config';
import { COLORS } from '../constants/business';
import { useAuth } from '../context/AuthContext';

export default function SettingsScreen() {
  const { tenant } = useAuth();
  const [url, setUrl] = useState('');
  const [curPass, setCurPass] = useState('');
  const [newPass, setNewPass] = useState('');
  const [changing, setChanging] = useState(false);

  const doChangePassword = async () => {
    if (!curPass || newPass.length < 6) {
      Alert.alert('Atenção', 'Informe a senha atual e uma nova (mín. 6).');
      return;
    }
    setChanging(true);
    try {
      await changePassword({ current_password: curPass, new_password: newPass });
      setCurPass('');
      setNewPass('');
      Alert.alert('Pronto!', 'Senha alterada com sucesso.');
    } catch (e) {
      Alert.alert('Erro', e.message);
    } finally {
      setChanging(false);
    }
  };
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState(null); // 'ok' | 'fail'

  useEffect(() => {
    getApiUrl().then(setUrl);
  }, []);

  const save = async () => {
    await setApiUrl(url);
    Alert.alert('Salvo', 'Endereço do servidor atualizado.');
  };

  const test = async () => {
    setTesting(true);
    setStatus(null);
    try {
      await setApiUrl(url);
      await getHealth();
      setStatus('ok');
      Alert.alert('Conectado!', 'Servidor respondendo.');
    } catch (e) {
      setStatus('fail');
      Alert.alert('Falha', 'Não foi possível conectar. Verifique a URL.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 20 }}>
      <Text style={styles.label}>Endereço do servidor (backend)</Text>
      <TextInput
        style={styles.input}
        placeholder="https://agenda-barber-o0to.onrender.com"
        placeholderTextColor={COLORS.textMuted}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
        value={url}
        onChangeText={setUrl}
      />
      <Text style={styles.hint}>
        Cole aqui a URL que o Render gerou após o deploy do backend. É a mesma
        URL do link de agendamento dos clientes.
      </Text>

      <View style={styles.row}>
        <TouchableOpacity style={[styles.btn, styles.outline]} onPress={test} disabled={testing}>
          {testing ? <ActivityIndicator color={COLORS.primary} /> : <Text style={[styles.btnText, { color: COLORS.primary }]}>Testar conexão</Text>}
        </TouchableOpacity>
        <TouchableOpacity style={styles.btn} onPress={save}>
          <Text style={[styles.btnText, { color: '#1a1a1a' }]}>Salvar</Text>
        </TouchableOpacity>
      </View>

      {status === 'ok' && <Text style={styles.ok}>✓ Conectado</Text>}
      {status === 'fail' && <Text style={styles.fail}>✕ Sem conexão</Text>}

      <Text style={[styles.label, { marginTop: 28 }]}>Alterar minha senha</Text>
      <TextInput style={styles.input} placeholder="Senha atual" placeholderTextColor={COLORS.textMuted} secureTextEntry value={curPass} onChangeText={setCurPass} />
      <TextInput style={[styles.input, { marginTop: 10 }]} placeholder="Nova senha (mín. 6)" placeholderTextColor={COLORS.textMuted} secureTextEntry value={newPass} onChangeText={setNewPass} />
      <TouchableOpacity style={[styles.btn, { marginTop: 12 }]} onPress={doChangePassword} disabled={changing}>
        {changing ? <ActivityIndicator color="#1a1a1a" /> : <Text style={[styles.btnText, { color: '#1a1a1a' }]}>Alterar senha</Text>}
      </TouchableOpacity>

      <View style={styles.info}>
        <Text style={styles.infoTitle}>{tenant?.name || 'Minha Barbearia'}</Text>
        {!!tenant?.address && <Text style={styles.infoText}>{tenant.address}</Text>}
        {!!tenant?.whatsapp && <Text style={styles.infoText}>WhatsApp: {tenant.whatsapp}</Text>}
        {!!tenant?.slug && <Text style={styles.infoText}>Link: /agendar/{tenant.slug}</Text>}
        <Text style={styles.infoDev}>Agenda Barber</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  label: { color: COLORS.primary, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', marginBottom: 8 },
  input: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 10, padding: 14, color: COLORS.text, fontSize: 15 },
  hint: { color: COLORS.textMuted, fontSize: 13, marginTop: 8, lineHeight: 19 },
  row: { flexDirection: 'row', gap: 12, marginTop: 18 },
  btn: { flex: 1, backgroundColor: COLORS.primary, borderRadius: 10, padding: 14, alignItems: 'center' },
  outline: { backgroundColor: 'transparent', borderWidth: 2, borderColor: COLORS.primary },
  btnText: { fontWeight: '700' },
  ok: { color: COLORS.whatsapp, textAlign: 'center', marginTop: 14, fontWeight: '700' },
  fail: { color: '#ff6b6b', textAlign: 'center', marginTop: 14, fontWeight: '700' },
  info: { marginTop: 34, padding: 16, backgroundColor: COLORS.surface, borderRadius: 12, borderWidth: 1, borderColor: COLORS.border },
  infoTitle: { color: COLORS.text, fontWeight: '700', fontSize: 16 },
  infoText: { color: COLORS.textMuted, marginTop: 6, lineHeight: 20 },
  infoDev: { color: COLORS.primary, marginTop: 12, fontSize: 13 },
});
