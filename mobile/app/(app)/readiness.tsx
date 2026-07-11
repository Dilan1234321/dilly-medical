/**
 * The Readiness Read — full-screen read with bands, evidence, and the
 * action trio per dimension (Add to plan / the move). Spends a Move.
 */
import { router } from 'expo-router';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { BandPill, Card, ChunkyButton, DillyFace, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { DIMENSION_LABELS, theme } from '../../lib/theme';

interface Dimension {
  dimension: string;
  band: string;
  headline: string;
  evidence: string[];
  move: string;
}

interface Read {
  phase: { label: string; move: string };
  dimensions: Dimension[];
  your_open_lane: string;
  this_week: string;
  narrative?: string;
  data_note: string;
}

export default function Readiness() {
  const [read, setRead] = useState<Read | null>(null);
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState<Record<string, boolean>>({});

  const run = async () => {
    setBusy(true);
    try {
      const res = await med.fetch('/readiness/read', { method: 'POST' });
      if (res.ok) setRead((await res.json()) as Read);
      // 402 -> global paywall opens automatically
    } catch {
      // network error; keep screen
    } finally {
      setBusy(false);
    }
  };

  const addToPlan = async (dim: Dimension) => {
    try {
      await med.post('/plan-items', { text: dim.move, source: 'readiness' });
      setAdded((a) => ({ ...a, [dim.dimension]: true }));
    } catch {
      // ignore
    }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.surface.bg }} contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()} hitSlop={12}>
        <Text style={styles.back}>‹ Back</Text>
      </Pressable>

      <View style={{ alignItems: 'center', marginVertical: 12 }}>
        <DillyFace size={56} />
        <SectionTitle>Readiness Read</SectionTitle>
        <Text style={styles.sub}>
          If you applied today, here's your honest picture — every line traces to something real
          you logged or told me.
        </Text>
      </View>

      {!read && (
        <>
          <ChunkyButton label={busy ? 'Reading you…' : 'Run my read (1 Move)'} onPress={run} disabled={busy} />
          {busy && <ActivityIndicator color={theme.accent} style={{ marginTop: 20 }} />}
        </>
      )}

      {read && (
        <>
          {read.narrative ? (
            <Card style={{ borderColor: theme.accent }}>
              <Text style={styles.narrative}>{read.narrative}</Text>
            </Card>
          ) : null}

          {read.dimensions.map((d) => (
            <Card key={d.dimension}>
              <View style={styles.dimTop}>
                <Text style={styles.dimName}>{DIMENSION_LABELS[d.dimension] || d.dimension}</Text>
                <BandPill band={d.band} />
              </View>
              {d.evidence.map((e, i) => (
                <Text key={i} style={styles.evidence}>
                  · {e}
                </Text>
              ))}
              <Text style={styles.move}>{d.move}</Text>
              <View style={{ height: 10 }} />
              <ChunkyButton
                label={added[d.dimension] ? 'On your plan ✓' : 'Add to plan'}
                variant="ghost"
                onPress={() => addToPlan(d)}
                disabled={!!added[d.dimension]}
              />
            </Card>
          ))}

          <Card style={{ backgroundColor: theme.accentSoft, borderColor: theme.accent }}>
            <Text style={styles.thisWeekTitle}>This week</Text>
            <Text style={styles.thisWeek}>{read.this_week}</Text>
          </Card>

          <Hint>{read.data_note}</Hint>
          <View style={{ height: 10 }} />
          <ChunkyButton label={busy ? 'Reading…' : 'Run a fresh read (1 Move)'} onPress={run} disabled={busy} />
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 60 },
  back: { fontSize: 16, color: theme.accent, fontWeight: '700' },
  sub: { fontSize: 14, color: theme.surface.t2, textAlign: 'center', lineHeight: 20, marginTop: 4 },
  narrative: { fontSize: 15, color: theme.surface.t1, lineHeight: 22 },
  dimTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  dimName: { fontSize: 17, fontWeight: '800', color: theme.surface.t1 },
  evidence: { fontSize: 13, color: theme.surface.t2, lineHeight: 20, marginBottom: 3 },
  move: { fontSize: 14, color: theme.accentDark, fontWeight: '700', marginTop: 8, lineHeight: 20 },
  thisWeekTitle: { fontSize: 13, fontWeight: '800', color: theme.accentDark, textTransform: 'uppercase' },
  thisWeek: { fontSize: 15, color: theme.surface.t1, marginTop: 4, lineHeight: 22 },
});
