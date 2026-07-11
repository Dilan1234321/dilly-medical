/**
 * You — profile (the numbers), facts (your story), plan items, plan
 * management, and sign out. Facts are the source of truth for every read.
 */
import { router } from 'expo-router';
import React, { useCallback, useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  Pressable,
  View,
} from 'react-native';
import { useFocusEffect } from 'expo-router';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { clearToken, med } from '../../lib/api';
import { theme } from '../../lib/theme';

interface Me {
  email: string;
  name: string;
  plan: string;
  edu_verified: number;
  target_cycle_year: number | null;
  state: string;
  gpa: number | null;
  mcat: number | null;
}

interface Fact {
  id: number;
  category: string;
  text: string;
}

interface PlanItem {
  id: number;
  text: string;
  source: string;
  done: number;
}

const FACT_CATEGORIES = [
  'clinical', 'shadowing', 'research', 'service', 'leadership', 'course', 'award', 'life', 'letter',
];

export default function You() {
  const [me, setMe] = useState<Me | null>(null);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [plan, setPlan] = useState<PlanItem[]>([]);
  const [gpa, setGpa] = useState('');
  const [mcat, setMcat] = useState('');
  const [factText, setFactText] = useState('');
  const [factCategory, setFactCategory] = useState('clinical');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [m, f, p] = await Promise.all([
        med.get<Me>('/auth/me'),
        med.get<{ facts: Fact[] }>('/facts'),
        med.get<{ items: PlanItem[] }>('/plan-items'),
      ]);
      setMe(m);
      setFacts(f.facts);
      setPlan(p.items);
      setGpa(m.gpa != null ? String(m.gpa) : '');
      setMcat(m.mcat != null ? String(m.mcat) : '');
    } catch {
      // keep last state
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const saveNumbers = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {};
      if (gpa) body.gpa = parseFloat(gpa);
      if (mcat) body.mcat = parseInt(mcat, 10);
      await med.patch('/profile', body);
      await load();
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  const addFact = async () => {
    if (factText.trim().length < 3) return;
    try {
      await med.post('/facts', { category: factCategory, text: factText.trim() });
      setFactText('');
      await load();
    } catch {
      // ignore
    }
  };

  const togglePlan = async (id: number) => {
    try {
      await med.patch(`/plan-items/${id}`);
      await load();
    } catch {
      // ignore
    }
  };

  const signOut = async () => {
    await clearToken();
    router.replace('/onboarding');
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.surface.bg }} contentContainerStyle={styles.container}>
      <SectionTitle>You</SectionTitle>
      {me && (
        <Card>
          <Text style={styles.email}>{me.email}</Text>
          <Text style={styles.meta}>
            Plan: {me.plan}
            {me.edu_verified ? ' · .edu verified' : ''}
            {me.target_cycle_year ? ` · aiming for the ${me.target_cycle_year} cycle` : ''}
            {me.state ? ` · ${me.state}` : ''}
          </Text>
        </Card>
      )}

      <SectionTitle>Your numbers</SectionTitle>
      <Card>
        <Text style={styles.label}>GPA</Text>
        <TextInput
          style={styles.input}
          placeholder="3.70"
          placeholderTextColor={theme.surface.t3}
          keyboardType="decimal-pad"
          value={gpa}
          onChangeText={setGpa}
        />
        <Text style={styles.label}>MCAT (leave blank if not taken)</Text>
        <TextInput
          style={styles.input}
          placeholder="512"
          placeholderTextColor={theme.surface.t3}
          keyboardType="number-pad"
          value={mcat}
          onChangeText={setMcat}
        />
        <View style={{ height: 10 }} />
        <ChunkyButton label={saving ? 'Saving…' : 'Save'} onPress={saveNumbers} disabled={saving} />
      </Card>

      <SectionTitle>Your story</SectionTitle>
      <Card>
        <Text style={styles.label}>Add a fact about you</Text>
        <View style={styles.chips}>
          {FACT_CATEGORIES.map((c) => (
            <Pressable
              key={c}
              onPress={() => setFactCategory(c)}
              style={[styles.chip, factCategory === c && styles.chipActive]}
            >
              <Text style={[styles.chipText, factCategory === c && styles.chipTextActive]}>{c}</Text>
            </Pressable>
          ))}
        </View>
        <TextInput
          style={[styles.input, { minHeight: 60 }]}
          placeholder="e.g. Second author on a poster at the undergrad research symposium"
          placeholderTextColor={theme.surface.t3}
          multiline
          value={factText}
          onChangeText={setFactText}
        />
        <View style={{ height: 10 }} />
        <ChunkyButton label="Add it" variant="ghost" onPress={addFact} />
        <Hint>Every read cites these. The more real material I have, the sharper I get.</Hint>
      </Card>

      {facts.map((f) => (
        <Card key={f.id}>
          <Text style={styles.factCat}>{f.category}</Text>
          <Text style={styles.factText}>{f.text}</Text>
        </Card>
      ))}

      <SectionTitle>Your plan</SectionTitle>
      {plan.length === 0 ? (
        <Card>
          <Text style={styles.metaBody}>
            Reads and picks land here when you tap "Add to plan." One list, honest and short.
          </Text>
        </Card>
      ) : (
        plan.map((p) => (
          <Pressable key={p.id} onPress={() => togglePlan(p.id)}>
            <Card style={p.done ? { opacity: 0.5 } : undefined}>
              <Text style={[styles.planText, p.done ? styles.planDone : undefined]}>
                {p.done ? '✓ ' : '○ '}
                {p.text}
              </Text>
            </Card>
          </Pressable>
        ))
      )}

      <SectionTitle>Tools</SectionTitle>
      <ChunkyButton label="Craft an essay or description" onPress={() => router.push('/(app)/craft' as any)} />
      <View style={{ height: 8 }} />
      <ChunkyButton label="See opportunities picked for you" variant="ghost" onPress={() => router.push('/(app)/opportunities' as any)} />
      <View style={{ height: 24 }} />
      <ChunkyButton label="Sign out" variant="danger" onPress={signOut} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 60 },
  email: { fontSize: 16, fontWeight: '800', color: theme.surface.t1 },
  meta: { fontSize: 13, color: theme.surface.t3, marginTop: 4 },
  metaBody: { fontSize: 14, color: theme.surface.t2, lineHeight: 20 },
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
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 8 },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.surface.s2,
    borderWidth: 1,
    borderColor: theme.surface.border,
  },
  chipActive: { backgroundColor: theme.accentSoft, borderColor: theme.accent },
  chipText: { fontSize: 12, color: theme.surface.t2, fontWeight: '600' },
  chipTextActive: { color: theme.accentDark },
  factCat: { fontSize: 11, fontWeight: '800', color: theme.accent, textTransform: 'uppercase' },
  factText: { fontSize: 14, color: theme.surface.t1, marginTop: 4, lineHeight: 20 },
  planText: { fontSize: 14, color: theme.surface.t1, lineHeight: 20 },
  planDone: { textDecorationLine: 'line-through', color: theme.surface.t3 },
});
