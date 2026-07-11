/**
 * Craft — turn logged reflections + facts into application prose.
 * Spends a Move. Everything traces to the student's own words; where
 * evidence is thin the draft says so instead of inventing.
 */
import { router } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { med, MedApiError } from '../../lib/api';
import { theme } from '../../lib/theme';

interface Activity {
  org: string;
  role: string;
  label: string;
  total_hours: number;
}

export default function Craft() {
  const [kind, setKind] = useState<'activity_description' | 'personal_statement'>('activity_description');
  const [activities, setActivities] = useState<Activity[]>([]);
  const [selected, setSelected] = useState<Activity | null>(null);
  const [theme_, setTheme_] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await med.get<{ activities: Activity[] }>('/hours/export');
      setActivities(r.activities.filter((a) => a.org && a.org !== '—'));
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const run = async () => {
    setBusy(true);
    setError('');
    setOutput('');
    try {
      const r = await med.post<{ output: string }>('/craft', {
        kind,
        org: kind === 'activity_description' ? selected?.org || '' : '',
        role: kind === 'activity_description' ? selected?.role || '' : '',
        theme: theme_,
      });
      setOutput(r.output);
    } catch (e) {
      if (e instanceof MedApiError && e.status === 402) {
        // paywall already opened by the interceptor
      } else if (e instanceof MedApiError) {
        setError(e.message);
      } else {
        setError('Something went wrong. Try again.');
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.surface.bg }} contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()} hitSlop={12}>
        <Text style={styles.back}>‹ Back</Text>
      </Pressable>
      <SectionTitle>Craft</SectionTitle>
      <Hint>
        I write only from what's real: your logged reflections and facts. Where you need a real
        moment, the draft says so — it never invents one.
      </Hint>

      <View style={styles.kindRow}>
        <Pressable
          onPress={() => setKind('activity_description')}
          style={[styles.kindChip, kind === 'activity_description' && styles.kindActive]}
        >
          <Text style={[styles.kindText, kind === 'activity_description' && styles.kindTextActive]}>
            Activity description
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setKind('personal_statement')}
          style={[styles.kindChip, kind === 'personal_statement' && styles.kindActive]}
        >
          <Text style={[styles.kindText, kind === 'personal_statement' && styles.kindTextActive]}>
            Personal statement
          </Text>
        </Pressable>
      </View>

      {kind === 'activity_description' && (
        <>
          <Text style={styles.label}>Which activity?</Text>
          {activities.length === 0 ? (
            <Card>
              <Text style={styles.emptyText}>
                Log some hours with a "where" first — each place you've served becomes an activity
                I can draft.
              </Text>
            </Card>
          ) : (
            activities.map((a) => (
              <Pressable key={`${a.org}|${a.role}`} onPress={() => setSelected(a)}>
                <Card
                  style={
                    selected?.org === a.org && selected?.role === a.role
                      ? { borderColor: theme.accent, backgroundColor: theme.accentSoft }
                      : undefined
                  }
                >
                  <Text style={styles.actName}>
                    {a.role ? `${a.role} — ` : ''}
                    {a.org}
                  </Text>
                  <Text style={styles.actMeta}>
                    {a.label} · {Math.round(a.total_hours)}h logged
                  </Text>
                </Card>
              </Pressable>
            ))
          )}
        </>
      )}

      <Text style={styles.label}>A theme you want it to carry (optional)</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g. learning to sit with uncertainty"
        placeholderTextColor={theme.surface.t3}
        value={theme_}
        onChangeText={setTheme_}
      />

      <View style={{ height: 14 }} />
      <ChunkyButton
        label={busy ? 'Drafting…' : 'Craft it (1 Move)'}
        onPress={run}
        disabled={busy || (kind === 'activity_description' && !selected)}
      />
      {busy && <ActivityIndicator color={theme.accent} style={{ marginTop: 16 }} />}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {output ? (
        <Card style={{ marginTop: 16, borderColor: theme.accent }}>
          <Text style={styles.output}>{output}</Text>
        </Card>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 60 },
  back: { fontSize: 16, color: theme.accent, fontWeight: '700' },
  kindRow: { flexDirection: 'row', gap: 8, marginVertical: 14 },
  kindChip: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.surface.s2,
    borderWidth: 1,
    borderColor: theme.surface.border,
  },
  kindActive: { backgroundColor: theme.accentSoft, borderColor: theme.accent },
  kindText: { fontSize: 13, fontWeight: '700', color: theme.surface.t2 },
  kindTextActive: { color: theme.accentDark },
  label: { fontSize: 14, fontWeight: '700', color: theme.surface.t1, marginTop: 10, marginBottom: 6 },
  input: {
    backgroundColor: theme.surface.s2,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.surface.border,
    padding: 14,
    fontSize: 15,
    color: theme.surface.t1,
  },
  actName: { fontSize: 15, fontWeight: '700', color: theme.surface.t1 },
  actMeta: { fontSize: 12, color: theme.surface.t3, marginTop: 2 },
  emptyText: { fontSize: 14, color: theme.surface.t2, lineHeight: 20 },
  error: { color: theme.danger, marginTop: 12, textAlign: 'center' },
  output: { fontSize: 15, color: theme.surface.t1, lineHeight: 23 },
});
