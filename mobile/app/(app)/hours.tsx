/**
 * Hours — the wedge. Log a shift in under 15 seconds, capture the
 * reflection while it's fresh. Always free, never metered.
 *
 * Voice-first capture (mic) is the next iteration; the reflection prompt
 * and data model are already shaped for it.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { theme } from '../../lib/theme';

interface HoursEntry {
  id: number;
  category: string;
  hours: number;
  org: string;
  role: string;
  occurred_on: string;
  reflection: string;
}

interface HoursResponse {
  entries: HoursEntry[];
  totals: Record<string, number>;
  clinical_total: number;
  categories: string[];
  labels: Record<string, string>;
}

export default function Hours() {
  const [data, setData] = useState<HoursResponse | null>(null);
  const [showLog, setShowLog] = useState(false);

  // log form
  const [category, setCategory] = useState('clinical_volunteer');
  const [hours, setHours] = useState('');
  const [org, setOrg] = useState('');
  const [role, setRole] = useState('');
  const [reflection, setReflection] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setData(await med.get<HoursResponse>('/hours'));
    } catch {
      // keep last state
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async () => {
    setBusy(true);
    try {
      await med.post('/hours', {
        category,
        hours: parseFloat(hours),
        org,
        role,
        reflection,
      });
      setShowLog(false);
      setHours('');
      setReflection('');
      await load();
    } catch {
      // validation errors leave the sheet open for correction
    } finally {
      setBusy(false);
    }
  };

  const labels = data?.labels || {};

  return (
    <View style={{ flex: 1, backgroundColor: theme.surface.bg }}>
      <FlatList
        contentContainerStyle={styles.container}
        data={data?.entries || []}
        keyExtractor={(e) => String(e.id)}
        ListHeaderComponent={
          <>
            <SectionTitle>Your hours</SectionTitle>
            {data && (
              <Card>
                <View style={styles.totalsRow}>
                  <View style={styles.totalBlock}>
                    <Text style={styles.totalNum}>{Math.round(data.clinical_total)}</Text>
                    <Text style={styles.totalLabel}>clinical</Text>
                  </View>
                  <View style={styles.totalBlock}>
                    <Text style={styles.totalNum}>{Math.round(data.totals['shadowing'] || 0)}</Text>
                    <Text style={styles.totalLabel}>shadowing</Text>
                  </View>
                  <View style={styles.totalBlock}>
                    <Text style={styles.totalNum}>{Math.round(data.totals['research'] || 0)}</Text>
                    <Text style={styles.totalLabel}>research</Text>
                  </View>
                  <View style={styles.totalBlock}>
                    <Text style={styles.totalNum}>
                      {Math.round((data.totals['volunteering'] || 0) + (data.totals['leadership'] || 0))}
                    </Text>
                    <Text style={styles.totalLabel}>service</Text>
                  </View>
                </View>
              </Card>
            )}
            <ChunkyButton label="+ Log a shift" onPress={() => setShowLog(true)} />
            <Hint>
              Logging is always free. The reflection you capture today is the essay you won't have
              to invent in two years.
            </Hint>
            <View style={{ height: 8 }} />
          </>
        }
        renderItem={({ item }) => (
          <Card>
            <View style={styles.entryTop}>
              <Text style={styles.entryOrg}>{item.org || labels[item.category] || item.category}</Text>
              <Text style={styles.entryHours}>{item.hours}h</Text>
            </View>
            <Text style={styles.entryMeta}>
              {item.role ? `${item.role} · ` : ''}
              {labels[item.category] || item.category} · {item.occurred_on}
            </Text>
            {item.reflection ? <Text style={styles.reflection}>"{item.reflection}"</Text> : null}
          </Card>
        )}
        ListEmptyComponent={
          <Card>
            <Text style={styles.empty}>
              Let's build your record. Log your first shift — even one hour of shadowing counts,
              and I'll keep the ledger from here.
            </Text>
          </Card>
        }
      />

      <Modal visible={showLog} animationType="slide" transparent onRequestClose={() => setShowLog(false)}>
        <KeyboardAvoidingView
          style={styles.backdrop}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View style={styles.sheet}>
            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.sheetTitle}>Log a shift</Text>

              <Text style={styles.label}>What kind?</Text>
              <View style={styles.chips}>
                {(data?.categories || []).map((c) => (
                  <Pressable
                    key={c}
                    onPress={() => setCategory(c)}
                    style={[styles.chip, category === c && styles.chipActive]}
                  >
                    <Text style={[styles.chipText, category === c && styles.chipTextActive]}>
                      {labels[c] || c}
                    </Text>
                  </Pressable>
                ))}
              </View>

              <Text style={styles.label}>Hours</Text>
              <TextInput
                style={styles.input}
                placeholder="4"
                placeholderTextColor={theme.surface.t3}
                keyboardType="decimal-pad"
                value={hours}
                onChangeText={setHours}
              />

              <Text style={styles.label}>Where</Text>
              <TextInput
                style={styles.input}
                placeholder="Tampa General ER"
                placeholderTextColor={theme.surface.t3}
                value={org}
                onChangeText={setOrg}
              />

              <Text style={styles.label}>Your role</Text>
              <TextInput
                style={styles.input}
                placeholder="Volunteer / Scribe / RA"
                placeholderTextColor={theme.surface.t3}
                value={role}
                onChangeText={setRole}
              />

              <Text style={styles.label}>Anything stick with you today?</Text>
              <TextInput
                style={[styles.input, { minHeight: 80 }]}
                placeholder="Thirty seconds now = your essay later. What moment stayed?"
                placeholderTextColor={theme.surface.t3}
                multiline
                value={reflection}
                onChangeText={setReflection}
              />

              <View style={{ height: 14 }} />
              <ChunkyButton
                label="Save it"
                onPress={submit}
                disabled={busy || !hours || isNaN(parseFloat(hours))}
              />
              <View style={{ height: 8 }} />
              <ChunkyButton label="Cancel" variant="ghost" onPress={() => setShowLog(false)} />
              <View style={{ height: 20 }} />
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 40 },
  totalsRow: { flexDirection: 'row', justifyContent: 'space-between' },
  totalBlock: { alignItems: 'center', flex: 1 },
  totalNum: { fontSize: 26, fontWeight: '800', color: theme.accentDark },
  totalLabel: { fontSize: 12, color: theme.surface.t3, marginTop: 2 },
  entryTop: { flexDirection: 'row', justifyContent: 'space-between' },
  entryOrg: { fontSize: 15, fontWeight: '700', color: theme.surface.t1, flex: 1 },
  entryHours: { fontSize: 15, fontWeight: '800', color: theme.accent },
  entryMeta: { fontSize: 12, color: theme.surface.t3, marginTop: 2 },
  reflection: { fontSize: 14, color: theme.surface.t2, fontStyle: 'italic', marginTop: 8, lineHeight: 20 },
  empty: { fontSize: 15, color: theme.surface.t2, lineHeight: 22 },
  backdrop: { flex: 1, backgroundColor: 'rgba(20,17,12,0.55)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: theme.surface.bg,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 24,
    maxHeight: '90%',
  },
  sheetTitle: { fontSize: 22, fontWeight: '800', color: theme.surface.t1, marginBottom: 8 },
  label: { fontSize: 14, fontWeight: '700', color: theme.surface.t1, marginTop: 12, marginBottom: 6 },
  input: {
    backgroundColor: theme.surface.s2,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.surface.border,
    padding: 14,
    fontSize: 16,
    color: theme.surface.t1,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.surface.s2,
    borderWidth: 1,
    borderColor: theme.surface.border,
  },
  chipActive: { backgroundColor: theme.accentSoft, borderColor: theme.accent },
  chipText: { fontSize: 13, color: theme.surface.t2, fontWeight: '600' },
  chipTextActive: { color: theme.accentDark },
});
