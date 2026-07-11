/**
 * Pricing — Stripe only (no Apple IAP), mirroring career Dilly.
 * Payment Links get wired here when Stripe is configured; until then the
 * paywall's upgrade buttons call the dev plan-switch endpoint so the whole
 * flow is exercisable end to end.
 */
export const PLANS = [
  {
    id: 'starter',
    label: 'Starter',
    price: 'Free',
    blurb: '5 Moves a week. Hours log always free, forever.',
  },
  {
    id: 'dilly',
    label: 'Dilly',
    price: '$8.99/mo',
    eduPrice: '$5.99/mo with .edu',
    blurb: '120 Moves a month. Every read, scout, and draft you need.',
  },
  {
    id: 'pro',
    label: 'Pro',
    price: '$14.99/mo',
    eduPrice: '$9.99/mo with .edu',
    blurb: 'Unlimited Moves. Application-year mode.',
  },
] as const;

// Stripe Payment Links — fill when created. Empty = dev plan-switch flow.
export const STRIPE_LINKS: Record<string, string> = {
  dilly: '',
  pro: '',
};
