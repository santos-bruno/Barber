import React from 'react';
import {
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { BUSINESS, COLORS } from '../constants/business';

export default function HomeScreen({ navigation }) {
  const openWhatsApp = () => {
    Linking.openURL(`https://wa.me/${BUSINESS.whatsappNumber}`);
  };

  const openMaps = () => {
    const query = encodeURIComponent(BUSINESS.address);
    Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${query}`);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.logo}>💈</Text>
        <Text style={styles.title}>{BUSINESS.name}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Endereço</Text>
        <Text style={styles.value}>{BUSINESS.address}</Text>
        <TouchableOpacity style={styles.linkBtn} onPress={openMaps}>
          <Text style={styles.linkBtnText}>Ver no mapa</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>WhatsApp</Text>
        <Text style={styles.value}>{BUSINESS.whatsappDisplay}</Text>
        <TouchableOpacity
          style={[styles.linkBtn, styles.whatsappBtn]}
          onPress={openWhatsApp}
        >
          <Text style={styles.linkBtnText}>Chamar no WhatsApp</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={styles.primaryBtn}
        onPress={() => navigation.navigate('Services')}
      >
        <Text style={styles.primaryBtnText}>Ver Serviços</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.primaryBtn, styles.outlineBtn]}
        onPress={() => navigation.navigate('Booking')}
      >
        <Text style={[styles.primaryBtnText, styles.outlineBtnText]}>
          Agendar Horário
        </Text>
      </TouchableOpacity>

      <Text style={styles.footer}>Desenvolvido por {BUSINESS.developer}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingBottom: 40 },
  header: { alignItems: 'center', marginVertical: 24 },
  logo: { fontSize: 64 },
  title: {
    color: COLORS.text,
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 8,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  label: {
    color: COLORS.primary,
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  value: { color: COLORS.text, fontSize: 16, lineHeight: 22 },
  linkBtn: {
    marginTop: 12,
    backgroundColor: COLORS.primary,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  whatsappBtn: { backgroundColor: COLORS.whatsapp },
  linkBtnText: { color: '#1a1a1a', fontWeight: '700' },
  primaryBtn: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  primaryBtnText: { color: '#1a1a1a', fontSize: 16, fontWeight: '700' },
  outlineBtn: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: COLORS.primary,
    marginTop: 12,
  },
  outlineBtnText: { color: COLORS.primary },
  footer: {
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: 28,
    fontSize: 13,
  },
});
