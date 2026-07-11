import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { PaywallModal } from '../components/PaywallModal';
import { theme } from '../lib/theme';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: theme.surface.bg },
        }}
      />
      <PaywallModal />
    </>
  );
}
