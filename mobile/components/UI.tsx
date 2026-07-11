/**
 * Shared UI primitives — Duolingo-style design language ported from
 * career Dilly: chunky buttons with a depth lip, warm cards, band pills,
 * and the DillyFace mascot (drawn with Views; asset swap later).
 */
import React, { useRef } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';
import { BAND_LABELS, theme } from '../lib/theme';

export function Card({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function ChunkyButton({
  label,
  onPress,
  variant = 'primary',
  disabled,
}: {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'ghost' | 'danger';
  disabled?: boolean;
}) {
  const press = useRef(new Animated.Value(0)).current;
  const translateY = press.interpolate({ inputRange: [0, 1], outputRange: [0, 3] });

  const bg =
    variant === 'primary' ? theme.accent : variant === 'danger' ? theme.danger : theme.surface.s1;
  const lip =
    variant === 'primary' ? theme.accentDark : variant === 'danger' ? '#8F2F28' : theme.surface.s3;
  const fg = variant === 'ghost' ? theme.surface.t1 : '#FFFFFF';

  return (
    <Pressable
      disabled={disabled}
      onPressIn={() => Animated.timing(press, { toValue: 1, duration: 60, useNativeDriver: true }).start()}
      onPressOut={() => Animated.timing(press, { toValue: 0, duration: 90, useNativeDriver: true }).start()}
      onPress={onPress}
      style={{ opacity: disabled ? 0.5 : 1 }}
    >
      <View style={[styles.buttonLip, { backgroundColor: lip }]}>
        <Animated.View
          style={[styles.buttonFace, { backgroundColor: bg, transform: [{ translateY }] }]}
        >
          <Text style={[styles.buttonText, { color: fg }]}>{label}</Text>
        </Animated.View>
      </View>
    </Pressable>
  );
}

export function BandPill({ band }: { band: string }) {
  const color = theme.bands[band] || theme.surface.t3;
  return (
    <View style={[styles.pill, { backgroundColor: color + '22', borderColor: color }]}>
      <Text style={{ color, fontWeight: '700', fontSize: 12 }}>{BAND_LABELS[band] || band}</Text>
    </View>
  );
}

/** The mascot: a warm circle face with a tiny stethoscope-green scrub cap. */
export function DillyFace({ size = 44 }: { size?: number }) {
  const s = size;
  return (
    <View style={{ width: s, height: s }}>
      <View
        style={{
          width: s,
          height: s,
          borderRadius: s / 2,
          backgroundColor: theme.gold,
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          borderWidth: 2,
          borderColor: theme.accentDark,
        }}
      >
        <View
          style={{
            position: 'absolute',
            top: 0,
            width: s,
            height: s * 0.32,
            backgroundColor: theme.accent,
          }}
        />
        <View style={{ flexDirection: 'row', gap: s * 0.16, marginTop: s * 0.12 }}>
          <View style={{ width: s * 0.11, height: s * 0.16, borderRadius: s, backgroundColor: '#1E1B16' }} />
          <View style={{ width: s * 0.11, height: s * 0.16, borderRadius: s, backgroundColor: '#1E1B16' }} />
        </View>
        <View
          style={{
            width: s * 0.3,
            height: s * 0.12,
            borderBottomLeftRadius: s,
            borderBottomRightRadius: s,
            backgroundColor: '#1E1B16',
            marginTop: s * 0.08,
          }}
        />
      </View>
    </View>
  );
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

export function Hint({ children }: { children: React.ReactNode }) {
  return <Text style={styles.hint}>{children}</Text>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.surface.s1,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.surface.border,
    padding: 16,
    marginBottom: 12,
  },
  buttonLip: {
    borderRadius: theme.radius.button,
    paddingBottom: 4,
  },
  buttonFace: {
    borderRadius: theme.radius.button,
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '800',
  },
  pill: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: theme.type.heroWeight,
    color: theme.surface.t1,
    marginBottom: 8,
    marginTop: 8,
  },
  hint: {
    fontSize: 13,
    color: theme.surface.t3,
    marginTop: 6,
    lineHeight: 18,
  },
});
