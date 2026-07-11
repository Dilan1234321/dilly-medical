/**
 * MMI interview practice — voice-friendly answers, AI feedback per station.
 */
import { router } from 'expo-router';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Card, ChunkyButton, Hint, SectionTitle } from '../../components/UI';
import { med } from '../../lib/api';
import { sttAvailable, sttRequestPermission, sttStart, sttStop } from '../../lib/speechToText';
import { theme } from '../../lib/theme';

interface Station {
  id: string;
  type: string;
  prompt: string;
  probe?: string;
}

export default function Interview() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [idx, setIdx] = useState(0);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);

  const start = async () => {
    setBusy(true);
    try {
      const r = await med.post<{ session_id: number; stations: Station[] }>('/interview/session', { count: 3 });
      setSessionId(r.session_id);
      setStations(r.stations);
      setIdx(0);
      setAnswer('');
      setFeedback(null);
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (!sessionId) return;
    setBusy(true);
    try {
      const res = await med.fetch('/interview/feedback', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, station_index: idx, answer }),
      });
      if (res.ok) {
        const fb = await res.json();
        setFeedback(fb.feedback);
      }
    } finally {
      setBusy(false);
    }
  };

  const toggleMic = async () => {
    if (listening) {
      sttStop();
      setListening(false);
      return;
    }
    const ok = await sttRequestPermission();
    if (!ok) return;
    const started = sttStart({
      onPartial: (t) => setAnswer(t),
      onFinal: (t) => setAnswer((a) => (a ? `${a} ${t}` : t).trim()),
      onEnd: () => setListening(false),
      onError: () => setListening(false),
    });
    setListening(!!started);
  };

  const station = stations[idx];

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.surface.bg }} contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()} hitSlop={12}>
        <Text style={styles.back}>‹ Back</Text>
      </Pressable>
      <SectionTitle>Interview practice</SectionTitle>
      <Hint>MMI-style stations with honest feedback. Answer out loud or type — feedback spends one Move.</Hint>

      {!sessionId && (
        <ChunkyButton label={busy ? 'Setting up…' : 'Start a 3-station round'} onPress={start} disabled={busy} />
      )}

      {station && (
        <Card>
          <Text style={styles.type}>{station.type}</Text>
          <Text style={styles.prompt}>{station.prompt}</Text>
          {station.probe ? <Text style={styles.probe}>{station.probe}</Text> : null}
          <TextInput
            style={[styles.input, { minHeight: 120 }]}
            multiline
            placeholder="Answer out loud or type here…"
            placeholderTextColor={theme.surface.t3}
            value={answer}
            onChangeText={setAnswer}
          />
          {sttAvailable() && (
            <Pressable onPress={toggleMic} style={[styles.mic, listening && styles.micOn]}>
              <Text style={styles.micText}>{listening ? '● Listening… tap to stop' : '🎤 Answer by voice'}</Text>
            </Pressable>
          )}
          <View style={{ height: 10 }} />
          <ChunkyButton label={busy ? 'Reading your answer…' : 'Get feedback (1 Move)'} onPress={submit} disabled={busy || answer.length < 10} />
          {feedback && (
            <View style={styles.fb}>
              <Text style={styles.rating}>Rating: {feedback.rating}</Text>
              {(feedback.strengths || []).map((s: string, i: number) => (
                <Text key={`s${i}`} style={styles.line}>+ {s}</Text>
              ))}
              {(feedback.improvements || []).map((s: string, i: number) => (
                <Text key={`i${i}`} style={styles.line}>→ {s}</Text>
              ))}
            </View>
          )}
          {feedback && idx < stations.length - 1 && (
            <>
              <View style={{ height: 10 }} />
              <ChunkyButton
                label="Next station"
                variant="ghost"
                onPress={() => {
                  setIdx(idx + 1);
                  setAnswer('');
                  setFeedback(null);
                }}
              />
            </>
          )}
        </Card>
      )}
      {busy && <ActivityIndicator color={theme.accent} style={{ marginTop: 16 }} />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, paddingBottom: 60 },
  back: { fontSize: 16, color: theme.accent, fontWeight: '700' },
  type: { fontSize: 12, fontWeight: '800', color: theme.accent, textTransform: 'uppercase' },
  prompt: { fontSize: 16, fontWeight: '700', color: theme.surface.t1, marginTop: 8, lineHeight: 23 },
  probe: { fontSize: 14, color: theme.surface.t2, marginTop: 8, fontStyle: 'italic' },
  input: {
    marginTop: 12,
    backgroundColor: theme.surface.s2,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.surface.border,
    padding: 14,
    fontSize: 15,
    color: theme.surface.t1,
  },
  mic: {
    marginTop: 10,
    padding: 12,
    borderRadius: 12,
    backgroundColor: theme.surface.s2,
    alignItems: 'center',
  },
  micOn: { backgroundColor: theme.accentSoft, borderWidth: 1, borderColor: theme.accent },
  micText: { fontWeight: '700', color: theme.accentDark },
  fb: { marginTop: 14, paddingTop: 12, borderTopWidth: 1, borderTopColor: theme.surface.border },
  rating: { fontWeight: '800', color: theme.surface.t1, marginBottom: 6 },
  line: { fontSize: 14, color: theme.surface.t2, marginBottom: 4, lineHeight: 20 },
});
