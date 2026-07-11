/**
 * Schools — browse the dataset (free), save to my list, Scout a school
 * (spends a Move). The scout result renders inline in an expandable card.
 *
 * iOS modal-on-modal rule from career Dilly is respected: the scout
 * result is inline expansion, not a stacked Modal.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { theme } from '../../lib/theme';

interface School {
  id: string;
  name: string;
  type: string;
  state: string;
  city: string;
  median_gpa: number;
  median_mcat: number;
  mission_tags: string[];
  in_state: boolean;
  saved: boolean;
}

interface ScoutRead {
  verdict: string;
  why: string[];
  gaps: string[];
  move: string;
  narrative?: string;
}

const VERDICT_COPY: Record<string, { label: string; color: string }> = {
  likely: { label: 'Likely', color: theme.bands.strong },
  target: { label: 'Target', color: theme.bands.on_track },
  reach: { label: 'Reach', color: theme.bands.building },
  far_reach: { label: 'Far reach', color: theme.danger },
  incomplete: { label: 'Tell me more', color: theme.surface.t3 },
};

export default function Schools() {
  const [schools, setSchools] = useState<School[]>([]);
  const [dataNote, setDataNote] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [scouts, setScouts] = useState<Record<string, ScoutRead>>({});
  const [scouting, setScouting] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await med.get<{ schools: School[]; data_note: string }>('/schools');
      setSchools(r.schools);
      setDataNote(r.data_note);
      const mine = await med.get<{ list: { school: { id: string }; scout: ScoutRead | null }[] }>(
        '/schools/my-list'
      );
      const cached: Record<string, ScoutRead> = {};
      mine.list.forEach((row) => {
        if (row.scout) cached[row.school.id] = row.scout;
      });
      setScouts(cached);
    } catch {
      // keep last state
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const runScout = async (id: string) => {
    setScouting(id);
    try {
      const res = await med.fetch(`/schools/${id}/scout`, { method: 'POST' });
      if (res.ok) {
        const read = (await res.json()) as ScoutRead;
        setScouts((s) => ({ ...s, [id]: read }));
      }
      // 402 handled globally by the paywall interceptor
    } catch {
      // network error; leave as-is
    } finally {
      setScouting(null);
    }
  };

  const toggleSave = async (school: School) => {
    try {
      if (school.saved) {
        await med.del(`/schools/${school.id}/save`);
      } else {
        await med.post(`/schools/${school.id}/save`);
      }
      setSchools((list) =>
        list.map((s) => (s.id === school.id ? { ...s, saved: !s.saved } : s))
      );
    } catch {
      // ignore
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.surface.bg }}>
      <FlatList
        contentContainerStyle={styles.container}
        data={schools}
        keyExtractor={(s) => s.id}
        ListHeaderComponent={
          <>
            <SectionTitle>Schools</SectionTitle>
            <Hint>{dataNote}</Hint>
            <View style={{ height: 8 }} />
          </>
        }
        renderItem={({ item }) => {
          const scout = scouts[item.id];
          const isOpen = expanded === item.id;
          return (
            <Card>
              <Pressable onPress={() => setExpanded(isOpen ? null : item.id)}>
                <View style={styles.rowTop}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.name}>{item.name}</Text>
                    <Text style={styles.meta}>
                      {item.type} · {item.city}, {item.state}
                      {item.in_state ? ' · your state' : ''}
                    </Text>
                  </View>
                  <Pressable onPress={() => toggleSave(item)} hitSlop={10}>
                    <Text style={{ fontSize: 22, color: item.saved ? theme.gold : theme.surface.t3 }}>
                      {item.saved ? '★' : '☆'}
                    </Text>
                  </Pressable>
                </View>
                <Text style={styles.medians}>
                  medians ~{item.median_gpa.toFixed(2)} GPA · ~{item.median_mcat} MCAT
                </Text>
                {scout && (
                  <View style={styles.verdictRow}>
                    <View
                      style={[
                        styles.verdictPill,
                        { borderColor: VERDICT_COPY[scout.verdict]?.color || theme.surface.t3 },
                      ]}
                    >
                      <Text
                        style={{
                          color: VERDICT_COPY[scout.verdict]?.color || theme.surface.t3,
                          fontWeight: '800',
                          fontSize: 12,
                        }}
                      >
                        {VERDICT_COPY[scout.verdict]?.label || scout.verdict}
                      </Text>
                    </View>
                  </View>
                )}
              </Pressable>

              {isOpen && (
                <View style={styles.expand}>
                  {scout ? (
                    <>
                      {scout.narrative ? <Text style={styles.narrative}>{scout.narrative}</Text> : null}
                      {scout.why.map((w, i) => (
                        <Text key={i} style={styles.why}>
                          · {w}
                        </Text>
                      ))}
                      <Text style={styles.move}>{scout.move}</Text>
                      <View style={{ height: 10 }} />
                      <ChunkyButton
                        label={scouting === item.id ? 'Reading…' : 'Scout again (1 Move)'}
                        onPress={() => runScout(item.id)}
                        disabled={scouting !== null}
                      />
                    </>
                  ) : scouting === item.id ? (
                    <ActivityIndicator color={theme.accent} style={{ marginVertical: 12 }} />
                  ) : (
                    <>
                      <Text style={styles.why}>
                        Scout reads how YOU fit this school — stats, mission, residency — and names
                        your one move to close the gap.
                      </Text>
                      <View style={{ height: 10 }} />
                      <ChunkyButton
                        label="Scout this school (1 Move)"
                        onPress={() => runScout(item.id)}
                        disabled={scouting !== null}
                      />
                    </>
                  )}
                </View>
              )}
            </Card>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 40 },
  rowTop: { flexDirection: 'row', alignItems: 'flex-start' },
  name: { fontSize: 16, fontWeight: '800', color: theme.surface.t1 },
  meta: { fontSize: 12, color: theme.surface.t3, marginTop: 2 },
  medians: { fontSize: 13, color: theme.surface.t2, marginTop: 6 },
  verdictRow: { flexDirection: 'row', marginTop: 8 },
  verdictPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radius.pill,
    borderWidth: 1.5,
  },
  expand: { marginTop: 12, borderTopWidth: 1, borderTopColor: theme.surface.border, paddingTop: 12 },
  narrative: { fontSize: 14, color: theme.surface.t1, lineHeight: 21, marginBottom: 8 },
  why: { fontSize: 13, color: theme.surface.t2, lineHeight: 20, marginBottom: 4 },
  move: { fontSize: 14, color: theme.accentDark, fontWeight: '700', marginTop: 8, lineHeight: 20 },
});
