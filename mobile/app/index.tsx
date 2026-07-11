import { Redirect } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { getToken, med } from '../lib/api';
import { theme } from '../lib/theme';

export default function Index() {
  const [dest, setDest] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (!token) {
        setDest('/onboarding');
        return;
      }
      try {
        await med.get('/auth/me');
        setDest('/(app)');
      } catch {
        setDest('/onboarding');
      }
    })();
  }, []);

  if (!dest) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.surface.bg }}>
        <ActivityIndicator color={theme.accent} />
      </View>
    );
  }
  return <Redirect href={dest as any} />;
}
