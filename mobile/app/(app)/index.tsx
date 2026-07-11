/**
 * Home — the 'where you stand' surface.
 * Header: DillyFace | Moves counter | (settings lives in You).
 * Scroll: readiness teaser -> weekly brief -> open lane -> plan items.
 */
import { router, useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { BandPill, Card, ChunkyButton, DillyFace, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { DIMENSION_LABELS, theme } from '../../lib/theme';

interface Brief {
  phase: { label: string; move: string; months_to_submission: number | null };
  hours_this_week: number;
  open_lane: string | null;
  this_week: string;
  open_plan_items: number;
  moves: { plan: string; limit: number; used: number; remaining: number };
}

interface LatestRead {
  read: {
    dimensions: { dimension: string; band: string; headline: string; move: string }[];
    your_open_lane: string;
    this_week: string;
  } | null;
}

export default function Home() {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [latest, setLatest] = useState<LatestRead | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, l] = await Promise.all([
        med.get<Brief>('/brief'),
        med.get<LatestRead>('/readiness/latest'),
      ]);
      setBrief(b);
      setLatest(l);
    } catch {
      // keep last known state; Home should never hard-fail
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const movesLabel = brief
    ? brief.moves.limit < 0
      ? 'Unlimited Moves'
      : `${brief.moves.remaining} Move${brief.moves.remaining === 1 ? '' : 's'} left`
    : '';

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: theme.surface.bg }}
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={async () => {
            setRefreshing(true);
            await load();
            setRefreshing(false);
          }}
        />
      }
    >
      <View style={styles.header}>
        <DillyFace size={44} />
        <View style={styles.movesPill}>
          <Text style={styles.movesText}>{movesLabel}</Text>
        </View>
      </View>

      <SectionTitle>Where you stand</SectionTitle>
      {latest?.read ? (
        <Card>
          {latest.read.dimensions.map((d) => (
            <View key={d.dimension} style={styles.dimRow}>
              <Text style={styles.dimLabel}>{DIMENSION_LABELS[d.dimension] || d.dimension}</Text>
              <BandPill band={d.band} />
            </View>
          ))}
          <View style={{ height: 10 }} />
          <ChunkyButton label="Run a fresh Readiness Read" onPress={() => router.push('/(app)/readiness' as any)} />
          <Hint>A fresh read spends one Move and updates everything above.</Hint>
        </Card>
      ) : (
        <Card>
          <Text style={styles.invite}>
            Let's find out. Your first Readiness Read looks at your stats, hours, and story against
            real matriculant numbers — and tells you your open lane.
          </Text>
          <View style={{ height: 12 }} />
          <ChunkyButton label="Read me" onPress={() => router.push('/(app)/readiness' as any)} />
        </Card>
      )}

      {brief && (
        <>
          <SectionTitle>This week</SectionTitle>
          <Card>
            <Text style={styles.phase}>
              {brief.phase.label}
              {brief.phase.months_to_submission !== null && brief.phase.months_to_submission > 0
                ? ` — ${brief.phase.months_to_submission} months to submission`
                : ''}
            </Text>
            <Text style={styles.move}>{brief.this_week}</Text>
            <Hint>
              {brief.hours_this_week > 0
                ? `You logged ${brief.hours_this_week} hours this week. Keep the rhythm.`
                : 'Nothing logged yet this week — even one shift counts.'}
            </Hint>
          </Card>
        </>
      )}

      {brief?.open_lane && (
        <Pressable onPress={() => router.push('/(app)/opportunities' as any)}>
          <Card style={{ borderColor: theme.accent }}>
            <Text style={styles.laneTitle}>
              Your open lane: {DIMENSION_LABELS[brief.open_lane] || brief.open_lane}
            </Text>
            <Text style={styles.laneBody}>
              I found opportunities picked for exactly this gap. Tap to see why each one fits you.
            </Text>
          </Card>
        </Pressable>
      )}

      <SectionTitle>Practice</SectionTitle>
      <Card>
        <ChunkyButton label="MMI interview practice" onPress={() => router.push('/(app)/interview' as any)} />
        <View style={{ height: 8 }} />
        <ChunkyButton label="Secondary essay Craft" variant="ghost" onPress={() => router.push('/(app)/secondaries' as any)} />
        <View style={{ height: 8 }} />
        <ChunkyButton label="Personal statement / W&A Craft" variant="ghost" onPress={() => router.push('/(app)/craft' as any)} />
      </Card>

      {brief && brief.open_plan_items > 0 && (
        <Card>
          <Text style={styles.planCount}>
            {brief.open_plan_items} thing{brief.open_plan_items === 1 ? '' : 's'} on your plan
          </Text>
          <Hint>Your plan lives in the You tab — check things off as you do them.</Hint>
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 40 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  movesPill: {
    backgroundColor: theme.accentSoft,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: theme.radius.pill,
  },
  movesText: { color: theme.accentDark, fontWeight: '800', fontSize: 13 },
  dimRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 7,
  },
  dimLabel: { fontSize: 15, fontWeight: '700', color: theme.surface.t1 },
  invite: { fontSize: 15, color: theme.surface.t2, lineHeight: 22 },
  phase: { fontSize: 13, fontWeight: '800', color: theme.accent, textTransform: 'uppercase' },
  move: { fontSize: 15, color: theme.surface.t1, marginTop: 6, lineHeight: 22 },
  laneTitle: { fontSize: 16, fontWeight: '800', color: theme.accentDark },
  laneBody: { fontSize: 14, color: theme.surface.t2, marginTop: 4, lineHeight: 20 },
  planCount: { fontSize: 15, fontWeight: '700', color: theme.surface.t1 },
});
