/**
 * Secondary essays — school-specific + generic prompts, Craft from real facts.
 */
import { router } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { theme } from '../../lib/theme';

interface Prompt {
  id: string;
  label: string;
  text: string;
  char_limit: number;
}

export default function Secondaries() {
  const [generic, setGeneric] = useState<Prompt[]>([]);
  const [schoolPrompts, setSchoolPrompts] = useState<Prompt[]>([]);
  const [selected, setSelected] = useState<Prompt | null>(null);
  const [output, setOutput] = useState('');
  const [busy, setBusy] = useState(false);
  const [schoolId, setSchoolId] = useState('');

  useEffect(() => {
    med.get<{ generic: Prompt[] }>('/secondaries/prompts').then((r) => setGeneric(r.generic)).catch(() => {});
  }, []);

  const loadSchool = async (id: string) => {
    setSchoolId(id);
    try {
      const r = await med.get<{ school: Prompt[] }>(`/secondaries/prompts?school_id=${id}`);
      setSchoolPrompts(r.school);
    } catch {
      setSchoolPrompts([]);
    }
  };

  const craft = async () => {
    if (!selected) return;
    setBusy(true);
    setOutput('');
    try {
      const res = await med.fetch('/secondaries/craft', {
        method: 'POST',
        body: JSON.stringify({
          school_id: schoolId,
          prompt_id: selected.id,
          prompt_text: selected.text,
          char_limit: selected.char_limit,
        }),
      });
      if (res.ok) {
        const r = await res.json();
        setOutput(r.output);
      }
    } finally {
      setBusy(false);
    }
  };

  const prompts = [...schoolPrompts, ...generic];

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.surface.bg }} contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()} hitSlop={12}>
        <Text style={styles.back}>‹ Back</Text>
      </Pressable>
      <SectionTitle>Secondary essays</SectionTitle>
      <Hint>Pick a prompt. Craft builds from your logged reflections and facts only — never invented stories.</Hint>

      <Card>
        <Text style={styles.label}>Load prompts for a saved school (optional)</Text>
        <View style={styles.row}>
          {['usf', 'fsu', 'harvard', 'ucsf', 'tulane'].map((id) => (
            <Pressable key={id} onPress={() => loadSchool(id)} style={[styles.chip, schoolId === id && styles.chipOn]}>
              <Text style={[styles.chipText, schoolId === id && styles.chipTextOn]}>{id.toUpperCase()}</Text>
            </Pressable>
          ))}
        </View>
      </Card>

      {prompts.map((p) => (
        <Pressable key={p.id} onPress={() => setSelected(p)}>
          <Card style={selected?.id === p.id ? { borderColor: theme.accent } : undefined}>
            <Text style={styles.pLabel}>{p.label}</Text>
            <Text style={styles.pText} numberOfLines={3}>{p.text}</Text>
            <Text style={styles.limit}>{p.char_limit} chars</Text>
          </Card>
        </Pressable>
      ))}

      {selected && (
        <>
          <ChunkyButton label={busy ? 'Drafting…' : 'Craft draft (1 Move)'} onPress={craft} disabled={busy} />
          {busy && <ActivityIndicator color={theme.accent} style={{ marginTop: 12 }} />}
          {output ? (
            <Card style={{ marginTop: 12 }}>
              <Text style={styles.output}>{output}</Text>
              <Text style={styles.count}>{output.length} / {selected.char_limit} characters</Text>
            </Card>
          ) : null}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 60 },
  back: { fontSize: 16, color: theme.accent, fontWeight: '700' },
  label: { fontSize: 13, fontWeight: '700', color: theme.surface.t2, marginBottom: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, backgroundColor: theme.surface.s2, borderWidth: 1, borderColor: theme.surface.border },
  chipOn: { backgroundColor: theme.accentSoft, borderColor: theme.accent },
  chipText: { fontSize: 11, fontWeight: '700', color: theme.surface.t2 },
  chipTextOn: { color: theme.accentDark },
  pLabel: { fontSize: 15, fontWeight: '800', color: theme.surface.t1 },
  pText: { fontSize: 13, color: theme.surface.t2, marginTop: 4, lineHeight: 19 },
  limit: { fontSize: 11, color: theme.surface.t3, marginTop: 6 },
  output: { fontSize: 15, color: theme.surface.t1, lineHeight: 23 },
  count: { fontSize: 12, color: theme.surface.t3, marginTop: 8 },
});
