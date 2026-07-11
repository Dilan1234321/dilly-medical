/**
 * Global paywall pub/sub — the career-Dilly pattern: non-React code
 * (the API client's 402 interceptor) can open the paywall; the host
 * modal in the root layout subscribes.
 */
import { useEffect, useState } from 'react';

export interface PaywallContext {
  surface?: string;   // which feature hit the wall (backend `feature`)
  promise?: string;   // backend `message` — what upgrading unlocks
}

type Listener = (ctx: PaywallContext | null) => void;

let _current: PaywallContext | null = null;
const _listeners = new Set<Listener>();

export function openPaywall(ctx?: PaywallContext) {
  _current = ctx ?? {};
  _listeners.forEach((l) => l(_current));
}

export function closePaywall() {
  _current = null;
  _listeners.forEach((l) => l(null));
}

export function usePaywall(): PaywallContext | null {
  const [ctx, setCtx] = useState<PaywallContext | null>(_current);
  useEffect(() => {
    const l: Listener = (c) => setCtx(c);
    _listeners.add(l);
    return () => {
      _listeners.delete(l);
    };
  }, []);
  return ctx;
}
