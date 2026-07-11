/**
 * Dilly Medical API client.
 *
 * Same contract as career Dilly's `dilly.ts`:
 *  - `med.fetch(path, init)` returns a raw Response and auto-opens the
 *    global paywall on 402 (with cooldown so bursts open one modal).
 *  - `med.get/post/patch/del` return parsed JSON and throw MedApiError
 *    (with .status/.code) on non-2xx.
 *
 * Token storage: AsyncStorage for v0.1 (SecureStore hardening later —
 * same migration career Dilly did).
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { openPaywall } from '../hooks/usePaywall';

export const API_BASE =
  process.env.EXPO_PUBLIC_MED_API_BASE || 'http://localhost:8100';

const TOKEN_KEY = 'dilly_med_token_v1';

export async function getToken(): Promise<string | null> {
  try {
    return await AsyncStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export async function setToken(token: string): Promise<void> {
  try {
    await AsyncStorage.setItem(TOKEN_KEY, token);
  } catch {
    // ignore
  }
}

export async function clearToken(): Promise<void> {
  try {
    await AsyncStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

export class MedApiError extends Error {
  status: number;
  code?: string;
  detail?: unknown;
  constructor(status: number, message: string, code?: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

let _lastPaywallAt = 0;
const PAYWALL_COOLDOWN_MS = 5000;

async function rawFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = await getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init?.headers as Record<string, string>) || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (res.status === 402) {
    const now = Date.now();
    if (now - _lastPaywallAt > PAYWALL_COOLDOWN_MS) {
      _lastPaywallAt = now;
      let ctx: { surface?: string; promise?: string } | undefined;
      try {
        const body = await res.clone().json();
        ctx = {
          surface: body?.detail?.feature || body?.feature,
          promise: body?.detail?.message || body?.message,
        };
      } catch {
        // non-JSON body -> default paywall copy
      }
      openPaywall(ctx);
    }
  }
  return res;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await rawFetch(path, init);
  if (!res.ok) {
    let code: string | undefined;
    let detail: unknown;
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body;
      code = (detail as any)?.code;
      message = (detail as any)?.message || message;
    } catch {
      // keep defaults
    }
    throw new MedApiError(res.status, message, code, detail);
  }
  return (await res.json()) as T;
}

export const med = {
  fetch: rawFetch,
  get: <T>(path: string) => json<T>(path),
  post: <T>(path: string, body?: unknown) =>
    json<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    json<T>(path, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  del: <T>(path: string) => json<T>(path, { method: 'DELETE' }),
};
