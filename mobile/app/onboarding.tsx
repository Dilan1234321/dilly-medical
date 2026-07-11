/**
 * Onboarding: email -> code -> the three facts that unlock everything
 * (target cycle, state, GPA). Invitation tone, never deficit.
 */
import { router } from 'expo-router';
import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { ChunkyButton, Card, DillyFace, Hint } from '../components/UI';
import { med, setToken } from '../lib/api';
import { theme } from '../lib/theme';

type Step = 'email' | 'code' | 'basics';

export default function Onboarding() {
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [devCode, setDevCode] = useState('');
  const [cycleYear, setCycleYear] = useState('');
  const [state, setState] = useState('');
  const [gpa, setGpa] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const sendCode = async () => {
    setBusy(true);
    setError('');
    try {
      const r = await med.post<{ sent: boolean; dev_code?: string }>('/auth/send-code', { email });
      if (r.dev_code) setDevCode(r.dev_code);
      setStep('code');
    } catch (e: any) {
      setError(e?.message || 'Something went wrong. Try again.');
    } finally {
      setBusy(false);
    }
  };

  const verify = async () => {
    setBusy(true);
    setError('');
    try {
      const r = await med.post<{ token: string }>('/auth/verify-code', { email, code });
      await setToken(r.token);
      setStep('basics');
    } catch (e: any) {
      setError(e?.message || "That code didn't match. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const saveBasics = async () => {
    setBusy(true);
    setError('');
    try {
      const body: Record<string, unknown> = {};
      if (cycleYear) body.target_cycle_year = parseInt(cycleYear, 10);
      if (state) body.state = state.toUpperCase().slice(0, 2);
      if (gpa) body.gpa = parseFloat(gpa);
      if (Object.keys(body).length) await med.patch('/profile', body);
      router.replace('/(app)' as any);
    } catch (e: any) {
      setError(e?.message || 'Could not save. You can add these later in You.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.surface.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container}>
        <View style={{ alignItems: 'center', marginBottom: 20 }}>
          <DillyFace size={72} />
          <Text style={styles.hero}>Dilly Medical</Text>
          <Text style={styles.sub}>
            The honest read on your road to med school — built from what you actually do.
          </Text>
        </View>

        {step === 'email' && (
          <Card>
            <Text style={styles.label}>Your school email</Text>
            <TextInput
              style={styles.input}
              placeholder="you@school.edu"
              placeholderTextColor={theme.surface.t3}
              autoCapitalize="none"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />
            <Hint>.edu unlocks student pricing later. Any email works.</Hint>
            <View style={{ height: 12 }} />
            <ChunkyButton label="Send me a code" onPress={sendCode} disabled={busy || !email.includes('@')} />
          </Card>
        )}

        {step === 'code' && (
          <Card>
            <Text style={styles.label}>Enter the 6-digit code</Text>
            <TextInput
              style={styles.input}
              placeholder="123456"
              placeholderTextColor={theme.surface.t3}
              keyboardType="number-pad"
              maxLength={6}
              value={code}
              onChangeText={setCode}
            />
            {devCode ? <Hint>Dev mode — your code is {devCode}</Hint> : null}
            <View style={{ height: 12 }} />
            <ChunkyButton label="Verify" onPress={verify} disabled={busy || code.length !== 6} />
          </Card>
        )}

        {step === 'basics' && (
          <Card>
            <Text style={styles.label}>When do you want to start med school?</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. 2030"
              placeholderTextColor={theme.surface.t3}
              keyboardType="number-pad"
              maxLength={4}
              value={cycleYear}
              onChangeText={setCycleYear}
            />
            <Text style={styles.label}>Home state (2 letters)</Text>
            <TextInput
              style={styles.input}
              placeholder="FL"
              placeholderTextColor={theme.surface.t3}
              autoCapitalize="characters"
              maxLength={2}
              value={state}
              onChangeText={setState}
            />
            <Text style={styles.label}>Current GPA (you can update anytime)</Text>
            <TextInput
              style={styles.input}
              placeholder="3.70"
              placeholderTextColor={theme.surface.t3}
              keyboardType="decimal-pad"
              value={gpa}
              onChangeText={setGpa}
            />
            <Hint>
              Your state matters more than people think — public med schools heavily favor
              residents. This is how I read you against real numbers.
            </Hint>
            <View style={{ height: 12 }} />
            <ChunkyButton label="Let's build your road" onPress={saveBasics} disabled={busy} />
          </Card>
        )}

        {error ? <Text style={styles.error}>{error}</Text> : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, paddingTop: 80 },
  hero: { fontSize: 32, fontWeight: '800', color: theme.surface.t1, marginTop: 12 },
  sub: { fontSize: 15, color: theme.surface.t2, textAlign: 'center', marginTop: 6, lineHeight: 21 },
  label: { fontSize: 14, fontWeight: '700', color: theme.surface.t1, marginBottom: 6, marginTop: 10 },
  input: {
    backgroundColor: theme.surface.s2,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.surface.border,
    padding: 14,
    fontSize: 16,
    color: theme.surface.t1,
  },
  error: { color: theme.danger, textAlign: 'center', marginTop: 12 },
});
