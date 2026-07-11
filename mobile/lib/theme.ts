/**
 * Dilly Medical theme — a sibling of career Dilly's design language:
 * Duolingo-style chunky buttons with a depth lip, warm surfaces, system
 * font with heavy hero weights. Single static theme for v0.1 (career
 * Dilly's multi-axis Customize can be ported later).
 */
export const theme = {
  surface: {
    bg: '#FBF8F3',      // warm cream
    s1: '#FFFFFF',      // card
    s2: '#F3EDE3',      // inset
    s3: '#E9E1D2',      // pressed / border-ish
    t1: '#1E1B16',      // primary text
    t2: '#5C564A',      // secondary text
    t3: '#948C7C',      // tertiary text
    border: '#E5DCCA',
  },
  accent: '#0E7C66',     // medical teal-green
  accentDark: '#0A5F4E', // the button "lip"
  accentSoft: '#DCF0EA',
  gold: '#C9A961',
  danger: '#C4453B',
  warn: '#B97F1F',
  bands: {
    strong: '#0E7C66',
    on_track: '#3E7CB1',
    building: '#B97F1F',
    getting_started: '#948C7C',
    unknown: '#948C7C',
  } as Record<string, string>,
  radius: { card: 20, button: 16, pill: 999 },
  type: {
    heroWeight: '800' as const,
    titleWeight: '700' as const,
  },
};

export const BAND_LABELS: Record<string, string> = {
  strong: 'Ahead of the field',
  on_track: 'On track',
  building: 'Building',
  getting_started: 'Your open lane',
  unknown: 'Tell me more',
};

export const DIMENSION_LABELS: Record<string, string> = {
  stats: 'Stats',
  clinical: 'Clinical',
  shadowing: 'Shadowing',
  research_and_service: 'Research & service',
  story: 'Story',
};
