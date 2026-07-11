/**
 * Global paywall host — mounted once in the root layout, opened by the
 * API client's 402 interceptor or explicitly via openPaywall().
 *
 * Until Stripe Payment Links exist, upgrade buttons call the dev
 * plan-switch endpoint so the full spend -> 402 -> upgrade -> retry loop
 * works end to end. When STRIPE_LINKS are filled, buttons open them.
 */
import React, { useState } from 'react';
import { Linking, Modal, ScrollView, StyleSheet, Text, View } from 'react-native';
import { closePaywall, usePaywall } from '../hooks/usePaywall';
import { med } from '../lib/api';
import { PLANS, STRIPE_LINKS } from '../lib/pricing';
import { theme } from '../lib/theme';
import { ChunkyButton, DillyFace, Hint } from './UI';

export function PaywallModal() {
  const ctx = usePaywall();
  const [busy, setBusy] = useState(false);

  const upgrade = async (planId: string) => {
    const link = STRIPE_LINKS[planId];
    if (link) {
      Linking.openURL(link);
      return;
    }
    setBusy(true);
    try {
      await med.post('/subscription/set-plan', { plan: planId });
      closePaywall();
    } catch {
      // leave modal open; the student can retry
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal visible={ctx !== null} animationType="slide" transparent onRequestClose={closePaywall}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <ScrollView showsVerticalScrollIndicator={false}>
            <View style={{ alignItems: 'center', marginBottom: 12 }}>
              <DillyFace size={56} />
            </View>
            <Text style={styles.title}>You're out of Moves</Text>
            <Text style={styles.promise}>
              {ctx?.promise ||
                'Upgrade to keep reading where you stand. Your hours log is always free.'}
            </Text>

            {PLANS.filter((p) => p.id !== 'starter').map((p) => (
              <View key={p.id} style={styles.plan}>
                <Text style={styles.planLabel}>
                  {p.label} <Text style={styles.planPrice}>{p.price}</Text>
                </Text>
                {'eduPrice' in p && p.eduPrice ? (
                  <Text style={styles.edu}>{p.eduPrice}</Text>
                ) : null}
                <Text style={styles.blurb}>{p.blurb}</Text>
                <ChunkyButton
                  label={`Get ${p.label}`}
                  onPress={() => upgrade(p.id)}
                  disabled={busy}
                />
              </View>
            ))}

            <Hint>
              Logging hours and reflections never costs a Move — that's a promise, not a trial.
            </Hint>
            <View style={{ height: 12 }} />
            <ChunkyButton label="Not now" variant="ghost" onPress={closePaywall} />
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(20,17,12,0.55)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: theme.surface.bg,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 24,
    maxHeight: '85%',
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: theme.surface.t1,
    textAlign: 'center',
  },
  promise: {
    fontSize: 15,
    color: theme.surface.t2,
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 16,
    lineHeight: 21,
  },
  plan: {
    backgroundColor: theme.surface.s1,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.surface.border,
    padding: 16,
    marginBottom: 12,
  },
  planLabel: { fontSize: 18, fontWeight: '800', color: theme.surface.t1 },
  planPrice: { color: theme.accent },
  edu: { fontSize: 13, color: theme.gold, fontWeight: '700', marginTop: 2 },
  blurb: { fontSize: 14, color: theme.surface.t2, marginVertical: 8, lineHeight: 20 },
});
