/**
 * Opportunities — gap-matched, each with 'why I picked this' chips.
 * Browsing is free. 'Add to plan' feeds the You tab.
 */
import { router } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { DIMENSION_LABELS, theme } from '../../lib/theme';

interface Opportunity {
  id: string;
  title: string;
  org_hint: string;
  fills: string[];
  paid: boolean;
  commitment: string;
  why_base: string;
  how: string;
  why_chips: string[];
}

export default function Opportunities() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [openLane, setOpenLane] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [added, setAdded] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    try {
      const r = await med.get<{ opportunities: Opportunity[]; open_lane: string }>('/opportunities');
      setOpps(r.opportunities);
      setOpenLane(r.open_lane);
    } catch {
      // keep last state
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const addToPlan = async (o: Opportunity) => {
    try {
      await med.post('/plan-items', { text: `Start: ${o.title} — ${o.how}`, source: 'opportunity' });
      setAdded((a) => ({ ...a, [o.id]: true }));
    } catch {
      // ignore
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.surface.bg }}>
      <FlatList
        contentContainerStyle={styles.container}
        data={opps}
        keyExtractor={(o) => o.id}
        ListHeaderComponent={
          <>
            <Pressable onPress={() => router.back()} hitSlop={12}>
              <Text style={styles.back}>‹ Back</Text>
            </Pressable>
            <SectionTitle>Picked for you</SectionTitle>
            {openLane ? (
              <Hint>
                Ranked around your open lane right now: {DIMENSION_LABELS[openLane] || openLane}.
                Every pick says why it's on your list.
              </Hint>
            ) : null}
            <View style={{ height: 8 }} />
          </>
        }
        renderItem={({ item }) => {
          const isOpen = expanded === item.id;
          return (
            <Card>
              <Pressable onPress={() => setExpanded(isOpen ? null : item.id)}>
                <View style={styles.rowTop}>
                  <Text style={styles.title}>{item.title}</Text>
                  {item.paid && <Text style={styles.paid}>paid</Text>}
                </View>
                <View style={styles.chips}>
                  {item.why_chips.map((c, i) => (
                    <View key={i} style={styles.chip}>
                      <Text style={styles.chipText}>{c}</Text>
                    </View>
                  ))}
                </View>
                <Text style={styles.why}>{item.why_base}</Text>
              </Pressable>
              {isOpen && (
                <View style={styles.expand}>
                  <Text style={styles.detailLabel}>Where to look</Text>
                  <Text style={styles.detail}>{item.org_hint}</Text>
                  <Text style={styles.detailLabel}>Commitment</Text>
                  <Text style={styles.detail}>{item.commitment}</Text>
                  <Text style={styles.detailLabel}>How to start</Text>
                  <Text style={styles.detail}>{item.how}</Text>
                  <View style={{ height: 10 }} />
                  <ChunkyButton
                    label={added[item.id] ? 'On your plan ✓' : 'Add to plan'}
                    onPress={() => addToPlan(item)}
                    disabled={!!added[item.id]}
                  />
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
  back: { fontSize: 16, color: theme.accent, fontWeight: '700' },
  rowTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 16, fontWeight: '800', color: theme.surface.t1, flex: 1 },
  paid: {
    fontSize: 11,
    fontWeight: '800',
    color: theme.gold,
    borderWidth: 1,
    borderColor: theme.gold,
    borderRadius: theme.radius.pill,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  chip: {
    backgroundColor: theme.accentSoft,
    borderRadius: theme.radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  chipText: { fontSize: 11, fontWeight: '700', color: theme.accentDark },
  why: { fontSize: 13, color: theme.surface.t2, marginTop: 8, lineHeight: 19 },
  expand: { marginTop: 12, borderTopWidth: 1, borderTopColor: theme.surface.border, paddingTop: 8 },
  detailLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: theme.surface.t3,
    textTransform: 'uppercase',
    marginTop: 8,
  },
  detail: { fontSize: 13, color: theme.surface.t1, marginTop: 2, lineHeight: 19 },
});
