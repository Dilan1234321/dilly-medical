import { Tabs } from 'expo-router';
import React from 'react';
import { Text } from 'react-native';
import { theme } from '../../lib/theme';

function TabIcon({ glyph, color }: { glyph: string; color: string }) {
  return <Text style={{ fontSize: 20, color }}>{glyph}</Text>;
}

export default function AppLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.accent,
        tabBarInactiveTintColor: theme.surface.t3,
        tabBarStyle: {
          backgroundColor: theme.surface.s1,
          borderTopColor: theme.surface.border,
        },
        sceneStyle: { backgroundColor: theme.surface.bg },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: 'Home', tabBarIcon: ({ color }) => <TabIcon glyph="⌂" color={color} /> }}
      />
      <Tabs.Screen
        name="hours"
        options={{ title: 'Hours', tabBarIcon: ({ color }) => <TabIcon glyph="✚" color={color} /> }}
      />
      <Tabs.Screen
        name="schools"
        options={{ title: 'Schools', tabBarIcon: ({ color }) => <TabIcon glyph="⚑" color={color} /> }}
      />
      <Tabs.Screen
        name="you"
        options={{ title: 'You', tabBarIcon: ({ color }) => <TabIcon glyph="◉" color={color} /> }}
      />
      {/* Push-opened screens, hidden from the tab bar */}
      <Tabs.Screen name="readiness" options={{ href: null }} />
      <Tabs.Screen name="opportunities" options={{ href: null }} />
      <Tabs.Screen name="craft" options={{ href: null }} />
      <Tabs.Screen name="interview" options={{ href: null }} />
      <Tabs.Screen name="secondaries" options={{ href: null }} />
    </Tabs>
  );
}
