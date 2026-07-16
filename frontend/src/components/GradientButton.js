import { LinearGradient } from 'expo-linear-gradient';
import React from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from 'react-native';

import { COLORS, GRADIENTS, SHADOW_GOLD } from '../constants/business';

export default function GradientButton({
  title,
  onPress,
  loading = false,
  disabled = false,
  colors = GRADIENTS.gold,
  textColor = COLORS.onPrimary,
  style,
}) {
  const gold = colors === GRADIENTS.gold;
  return (
    <TouchableOpacity
      activeOpacity={0.85}
      onPress={onPress}
      disabled={disabled || loading}
      style={[gold && SHADOW_GOLD, { borderRadius: 15 }, (disabled || loading) && { opacity: 0.55 }, style]}
    >
      <LinearGradient
        colors={colors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.grad}
      >
        {loading ? (
          <ActivityIndicator color={textColor} />
        ) : (
          <Text style={[styles.text, { color: textColor }]}>{title}</Text>
        )}
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  grad: { borderRadius: 15, paddingVertical: 16, alignItems: 'center', justifyContent: 'center' },
  text: { fontSize: 16, fontWeight: '850', letterSpacing: 0.3 },
});
