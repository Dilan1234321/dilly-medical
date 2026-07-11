/**
 * On-device speech-to-text for reflection capture (expo-speech-recognition).
 * Ported from career Dilly — lazy-require so simulators without the native
 * module degrade to typing without crashing.
 */
let _mod: any = null;
try {
  _mod = require('expo-speech-recognition');
} catch {
  /* not linked until native rebuild */
}
const M: any = _mod?.ExpoSpeechRecognitionModule || null;

let _subs: any[] = [];
let _listening = false;
let _pendingStart: ReturnType<typeof setTimeout> | null = null;
let _starting = false;

export function sttAvailable(): boolean {
  return !!(M && typeof M.start === 'function');
}

export async function sttRequestPermission(): Promise<boolean> {
  if (!M?.requestPermissionsAsync) return false;
  try {
    const r = await M.requestPermissionsAsync();
    return !!(r?.granted ?? r?.status === 'granted');
  } catch {
    return false;
  }
}

export interface SttHandlers {
  onPartial?: (text: string) => void;
  onFinal?: (text: string) => void;
  onEnd?: () => void;
  onError?: (err: string) => void;
}

function _clearSubs() {
  for (const s of _subs) {
    try {
      s?.remove?.();
    } catch {
      /* ignore */
    }
  }
  _subs = [];
}

export function sttStart(h: SttHandlers): boolean {
  if (!sttAvailable() || _starting) return false;
  try {
    if (_listening) M?.stop?.();
  } catch {
    /* ignore */
  }
  _listening = false;
  _clearSubs();
  if (_pendingStart) {
    clearTimeout(_pendingStart);
    _pendingStart = null;
  }
  _starting = true;

  _pendingStart = setTimeout(() => {
    _pendingStart = null;
    try {
      const add = (ev: string, cb: (e: any) => void) => {
        try {
          const s = M.addListener(ev, cb);
          if (s) _subs.push(s);
        } catch {
          /* ignore */
        }
      };
      add('result', (e: any) => {
        const t = e?.results?.[0]?.transcript ?? '';
        if (e?.isFinal) h.onFinal?.(String(t));
        else h.onPartial?.(String(t));
      });
      add('end', () => {
        _listening = false;
        _starting = false;
        h.onEnd?.();
      });
      add('error', (e: any) => {
        _listening = false;
        _starting = false;
        h.onError?.(String(e?.error || e?.message || 'speech-error'));
      });
      M.start({
        lang: 'en-US',
        interimResults: true,
        continuous: false,
        requiresOnDeviceRecognition: false,
        addsPunctuation: true,
        iosTaskHint: 'dictation',
        contextualStrings: [
          'clinical', 'shadowing', 'scribe', 'EMT', 'CNA', 'volunteer',
          'patient', 'hospital', 'MCAT', 'AMCAS', 'secondary', 'MMI',
        ],
      });
      _listening = true;
    } catch (e) {
      _listening = false;
      h.onError?.(String(e));
    } finally {
      _starting = false;
    }
  }, 160);
  return true;
}

export function sttStop(): void {
  if (_pendingStart) {
    clearTimeout(_pendingStart);
    _pendingStart = null;
  }
  _starting = false;
  try {
    if (_listening) M?.stop?.();
  } catch {
    /* ignore */
  }
  _listening = false;
  _clearSubs();
}

export function sttIsListening(): boolean {
  return _listening;
}
