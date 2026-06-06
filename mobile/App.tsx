import { StatusBar } from 'expo-status-bar';
import * as Haptics from 'expo-haptics';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { findBoroughForLocation, getDepartmentForCategory, BoroughHit, SortedCategory } from './src/lib/geolocate';
import {
  submitPhotoForClassification, mapIssueType, severityToBadge, bandTone,
  VLMReport, VLM_BASE_URL,
} from './src/lib/api';
import { ReactNode, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';

// ── Palette (GOV.UK green system + neutral ink) ─────────────────────────
const p = {
  bg: '#ECEEF1',
  card: '#FFFFFF',
  cardDim: '#F8F9FB',
  ink: '#0E0E10',
  inkDim: '#4B5563',
  inkFaint: '#9CA3AF',
  border: '#E5E7EB',
  borderSoft: '#EFF1F4',
  green: '#00703C',
  greenSoft: '#E8F1EC',
  greenChipBg: '#D5E9DB',
  red: '#C00000',
  amber: '#D97706',
  amberSoft: '#FDEBC8',
  blue: '#1D4ED8',
  blueSoft: '#DBEAFE',
};

// ── Real scraped Lambeth data (extracted from data/fixmystreet_reports.csv) ─
type Report = {
  id: string;
  label: string;
  icon: IconKey;
  department: string;
  street: string;
  status: 'open' | 'in_progress' | 'routed' | 'fixed';
  ago: string;
  fixed_ago?: string;
  step: number;
  total: number;
};

const YOUR_REPORTS: Report[] = [
  { id: '9530378', label: 'Pothole', icon: 'pothole', department: 'Highways',
    street: 'Holmewood Road', status: 'in_progress', ago: 'Reported 2 days ago',
    step: 3, total: 4 },
  { id: '9530320', label: 'Fly-tipping', icon: 'flytipping', department: 'Waste',
    street: 'Brixton Hill', status: 'routed', ago: 'Reported 5 hrs ago',
    step: 1, total: 4 },
  { id: '9405901', label: 'Streetlight out', icon: 'streetlight', department: 'Lighting',
    street: 'Effra Road', status: 'fixed', ago: 'Fixed last week', fixed_ago: 'last week',
    step: 4, total: 4 },
];

const FIXED_NEAR_YOU: Array<Pick<Report, 'id' | 'label' | 'street' | 'icon'> & { ago: string }> = [
  { id: '9458319', label: 'Fly-tip cleared',    icon: 'flytipping',  street: 'Durning Road',     ago: 'last week' },
  { id: '9447689', label: 'Fly-tip cleared',    icon: 'flytipping',  street: 'Bloomhall Road',   ago: 'last week' },
  { id: '9484029', label: 'Fly-tip cleared',    icon: 'flytipping',  street: 'Alexandra Drive',  ago: 'last week' },
  { id: '9487368', label: 'Tree cleared',       icon: 'tree',        street: 'Burgoyne Road',    ago: '2 weeks ago' },
  { id: '9477436', label: 'Street cleaning',    icon: 'other',       street: 'Lancaster Avenue', ago: '2 weeks ago' },
  { id: '9405901', label: 'Streetlight fixed',  icon: 'streetlight', street: 'Effra Road',       ago: 'last week' },
];

const COMMUNITY_STATS = { open: 98, fixed: 186, total: 284 };

// ── Screen state machine ────────────────────────────────────────────────
type Screen = 'welcome' | 'camera' | 'classify' | 'sent' | 'dashboard' | 'settings';
type Tab = 'report' | 'dashboard';

// ── Icons (Views only — zero asset deps) ────────────────────────────────
// Aligned to the SortedCategory taxonomy used by the geolocate + api modules.
type IconKey = SortedCategory;

function CategoryIcon({ kind, size = 26, color = p.green }: { kind: IconKey; size?: number; color?: string }) {
  const s = size;
  switch (kind) {
    case 'pothole':
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          {/* road bump */}
          <View style={{ position: 'absolute', bottom: s * 0.25, width: s * 0.78, height: 2, backgroundColor: color }} />
          <View style={{ position: 'absolute', bottom: s * 0.25, width: s * 0.42, height: s * 0.32,
                         borderTopLeftRadius: s * 0.32, borderTopRightRadius: s * 0.32,
                         borderWidth: 2, borderBottomWidth: 0, borderColor: color }} />
          {/* the "hole" — two short dashes */}
          <View style={{ position: 'absolute', bottom: s * 0.18, left: s * 0.1, width: s * 0.18, height: 2, backgroundColor: color }} />
          <View style={{ position: 'absolute', bottom: s * 0.18, right: s * 0.1, width: s * 0.18, height: 2, backgroundColor: color }} />
        </View>
      );
    case 'flytipping':
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          {/* bag silhouette */}
          <View style={{ width: s * 0.72, height: s * 0.56, borderRadius: s * 0.12,
                         borderWidth: 2, borderColor: color, marginTop: s * 0.18 }} />
          {/* knot */}
          <View style={{ position: 'absolute', top: s * 0.08, width: s * 0.28, height: s * 0.16,
                         borderRadius: s * 0.08, borderWidth: 2, borderColor: color }} />
        </View>
      );
    case 'streetlight':
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          <View style={{ width: 2, height: s * 0.78, backgroundColor: color }} />
          <View style={{ position: 'absolute', top: s * 0.08, width: s * 0.36, height: s * 0.2,
                         borderTopLeftRadius: s * 0.1, borderTopRightRadius: s * 0.1,
                         borderWidth: 2, borderColor: color }} />
        </View>
      );
    case 'tree':
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          <View style={{ width: 2, height: s * 0.32, backgroundColor: color, marginTop: s * 0.45 }} />
          <View style={{ position: 'absolute', top: s * 0.05, width: s * 0.6, height: s * 0.5,
                         borderRadius: s * 0.3, borderWidth: 2, borderColor: color }} />
        </View>
      );
    case 'graffiti':
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          <View style={{ width: s * 0.78, height: s * 0.6, borderRadius: 4, borderWidth: 2, borderColor: color }} />
          <View style={{ position: 'absolute', width: s * 0.35, height: 2, backgroundColor: color, transform: [{ rotate: '-20deg' }] }} />
          <View style={{ position: 'absolute', width: s * 0.28, height: 2, backgroundColor: color, top: s * 0.42, transform: [{ rotate: '15deg' }] }} />
        </View>
      );
    case 'drain':
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          <View style={{ width: s * 0.8, height: s * 0.6, borderRadius: 4, borderWidth: 2, borderColor: color }} />
          {[0, 1, 2].map(i => (
            <View key={i} style={{ position: 'absolute', top: s * (0.28 + i * 0.13), width: s * 0.6, height: 2, backgroundColor: color }} />
          ))}
        </View>
      );
    default:
      return (
        <View style={{ width: s, height: s, alignItems: 'center', justifyContent: 'center' }}>
          <View style={{ width: s * 0.6, height: s * 0.6, borderRadius: s * 0.3, borderWidth: 2, borderColor: color }} />
          <View style={{ position: 'absolute', width: 2, height: s * 0.36, backgroundColor: color, transform: [{ rotate: '45deg' }] }} />
        </View>
      );
  }
}

function CheckIcon({ size = 16, color = p.green }: { size?: number; color?: string }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: size * 0.5, height: 2, backgroundColor: color, transform: [{ rotate: '45deg' }, { translateX: -1 }, { translateY: 2 }] }} />
      <View style={{ position: 'absolute', width: size * 0.85, height: 2, backgroundColor: color, transform: [{ rotate: '-45deg' }, { translateX: 4 }, { translateY: -1 }] }} />
    </View>
  );
}

function ChevronRight({ size = 14, color = p.inkFaint }: { size?: number; color?: string }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: size * 0.55, height: size * 0.55, borderRightWidth: 2, borderTopWidth: 2,
                     borderColor: color, transform: [{ rotate: '45deg' }] }} />
    </View>
  );
}

function ChevronLeft({ size = 14, color = p.blue }: { size?: number; color?: string }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: size * 0.55, height: size * 0.55, borderLeftWidth: 2, borderTopWidth: 2,
                     borderColor: color, transform: [{ rotate: '-45deg' }] }} />
    </View>
  );
}

function CameraTabIcon({ active }: { active: boolean }) {
  const c = active ? p.green : p.inkFaint;
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: 22, height: 16, borderRadius: 4, borderWidth: 1.6, borderColor: c }} />
      <View style={{ position: 'absolute', top: 2, width: 10, height: 5,
                     borderTopLeftRadius: 3, borderTopRightRadius: 3,
                     borderWidth: 1.6, borderBottomWidth: 0, borderColor: c }} />
      <View style={{ position: 'absolute', width: 7, height: 7, borderRadius: 3.5,
                     borderWidth: 1.6, borderColor: c, top: 8 }} />
    </View>
  );
}

function DashboardTabIcon({ active }: { active: boolean }) {
  const c = active ? p.green : p.inkFaint;
  return (
    <View style={{ width: 22, height: 22, flexDirection: 'row', flexWrap: 'wrap', gap: 3 }}>
      {[0, 1, 2, 3].map(i => (
        <View key={i} style={{ width: 9.5, height: 9.5, borderRadius: 2, backgroundColor: c }} />
      ))}
    </View>
  );
}

function HamburgerIcon() {
  return (
    <View style={{ width: 24, height: 18, justifyContent: 'space-between' }}>
      {[0, 1, 2].map(i => (
        <View key={i} style={{ width: 22, height: 2, backgroundColor: '#fff', borderRadius: 1 }} />
      ))}
    </View>
  );
}

function LibraryIcon({ size = 22 }: { size?: number }) {
  // Two stacked photo frames with a tiny mountain glyph in the front one
  return (
    <View style={{ width: size, height: size }}>
      {/* back card (slightly offset) */}
      <View style={{ position: 'absolute', top: 0, left: 4, right: -2, bottom: 4,
                     borderRadius: 3, borderWidth: 1.5, borderColor: 'rgba(255,255,255,0.55)' }} />
      {/* front card */}
      <View style={{ position: 'absolute', top: 4, left: 0, right: 2, bottom: 0,
                     borderRadius: 3, borderWidth: 1.5, borderColor: '#fff',
                     backgroundColor: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
        {/* sun */}
        <View style={{ position: 'absolute', top: 2, right: 2, width: 3, height: 3, borderRadius: 1.5,
                       backgroundColor: '#fff' }} />
        {/* mountain */}
        <View style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 0,
                       borderLeftWidth: 6, borderRightWidth: 6, borderBottomWidth: 6,
                       borderLeftColor: 'transparent', borderRightColor: 'transparent', borderBottomColor: '#fff' }} />
      </View>
    </View>
  );
}

function GearIcon({ size = 20, color = p.inkDim }: { size?: number; color?: string }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: size * 0.7, height: size * 0.7, borderRadius: size * 0.35,
                     borderWidth: 2, borderColor: color }} />
      <View style={{ position: 'absolute', width: size * 0.3, height: size * 0.3,
                     borderRadius: size * 0.15, borderWidth: 2, borderColor: color, backgroundColor: '#fff' }} />
    </View>
  );
}

// ── Shared bits ──────────────────────────────────────────────────────────
function Wordmark({ light = false }: { light?: boolean }) {
  const inkColor = light ? '#fff' : p.ink;
  const dimColor = light ? 'rgba(255,255,255,0.55)' : p.inkDim;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
      <View style={{ width: 28, height: 28, borderRadius: 6, backgroundColor: inkColor,
                     alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: light ? p.ink : '#fff', fontSize: 14, fontWeight: '900', letterSpacing: -0.5 }}>S</Text>
      </View>
      <Text style={{ color: inkColor, fontSize: 18, fontWeight: '700', letterSpacing: -0.3 }}>
        See it <Text style={{ color: p.red }}>—</Text> Sorted.
      </Text>
    </View>
  );
}

function Pill({ label, kind }: { label: string; kind: 'progress' | 'routed' | 'fixed' | 'beta' }) {
  const styles = {
    progress: { bg: p.amberSoft, fg: p.amber },
    routed:   { bg: p.blueSoft,  fg: p.blue },
    fixed:    { bg: p.greenChipBg, fg: p.green },
    beta:     { bg: p.blue, fg: '#fff' },
  }[kind];
  return (
    <View style={{ paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, backgroundColor: styles.bg }}>
      <Text style={{ color: styles.fg, fontSize: 11, fontWeight: '800', letterSpacing: 0.4 }}>{label}</Text>
    </View>
  );
}

function ProgressBar({ step, total }: { step: number; total: number }) {
  return (
    <View style={{ flexDirection: 'row', gap: 4, marginTop: 6 }}>
      {Array.from({ length: total }).map((_, i) => (
        <View key={i} style={{ flex: 1, height: 4, borderRadius: 2,
                               backgroundColor: i < step ? p.green : p.border }} />
      ))}
    </View>
  );
}

// ── Welcome screen ──────────────────────────────────────────────────────
function WelcomeScreen({ onStart }: { onStart: () => void }) {
  const bullets = [
    'Potholes, fly-tipping, broken streetlights and more',
    'No forms, no reference numbers to keep',
    'Track every report on this phone',
  ];
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 8 }}>
        <Wordmark />
      </View>
      <View style={{ marginTop: 16, marginHorizontal: 16, backgroundColor: p.card, borderRadius: 18,
                     padding: 22, flex: 1 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <Pill label="BETA" kind="beta" />
          <Text style={{ color: p.inkDim, fontSize: 13, flex: 1 }}>A faster way to report street problems to your council.</Text>
        </View>
        <Text style={{ color: p.ink, fontSize: 38, fontWeight: '900', letterSpacing: -1.2, lineHeight: 42 }}>
          Report a{'\n'}street problem
        </Text>
        <Text style={{ color: p.inkDim, fontSize: 15, lineHeight: 22, marginTop: 14 }}>
          Take one photo. We work out what it is, route it to the right council, and track it until it's fixed.
        </Text>

        <View style={{ marginTop: 22, gap: 14 }}>
          {bullets.map(b => (
            <View key={b} style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 10 }}>
              <View style={{ width: 22, height: 22, borderRadius: 11, backgroundColor: p.greenChipBg,
                             alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>
                <CheckIcon size={14} color={p.green} />
              </View>
              <Text style={{ flex: 1, color: p.ink, fontSize: 15, lineHeight: 22 }}>{b}</Text>
            </View>
          ))}
        </View>

        <View style={{ flex: 1 }} />

        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onStart(); }}
          style={({ pressed }) => [{
            backgroundColor: p.green, borderRadius: 12, paddingVertical: 16, paddingHorizontal: 22,
            flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
            opacity: pressed ? 0.9 : 1,
          }]}
        >
          <Text style={{ color: '#fff', fontSize: 17, fontWeight: '700' }}>Start now</Text>
          <Text style={{ color: '#fff', fontSize: 20, fontWeight: '700' }}>→</Text>
        </Pressable>
        <Text style={{ color: p.inkFaint, fontSize: 12, marginTop: 12, textAlign: 'center', lineHeight: 18 }}>
          Continuing as a guest — your reports are kept on this phone.{'\n'}
          Google sign-in for cross-device sync is coming soon.
        </Text>
      </View>
    </View>
  );
}

// ── Camera screen + classification drawer ───────────────────────────────
function CameraScreen({
  onClassified,
  onTab,
}: {
  onClassified: () => void;
  onTab: (t: Tab) => void;
}) {
  const [phase, setPhase] = useState<'viewfinder' | 'analysing' | 'classified'>('viewfinder');
  const [flash, setFlash] = useState<'off' | 'on'>('off');
  const [hit, setHit] = useState<BoroughHit | null>(null);
  const [vlm, setVlm] = useState<VLMReport | null>(null);
  const drawer = useRef(new Animated.Value(0)).current;
  const ringPulse = useRef(new Animated.Value(0)).current;
  const cameraRef = useRef<CameraView | null>(null);
  const [permission, requestPermission] = useCameraPermissions();

  useEffect(() => {
    if (permission && !permission.granted && permission.canAskAgain) {
      requestPermission();
    }
  }, [permission, requestPermission]);

  // Get GPS once, then derive borough locally. Returns null if denied.
  async function getCoordsAndBorough(): Promise<{ lat: number; lon: number; hit: BoroughHit | null } | null> {
    try {
      const perm = await Location.requestForegroundPermissionsAsync();
      if (perm.status !== 'granted') return null;
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const lat = loc.coords.latitude;
      const lon = loc.coords.longitude;
      return { lat, lon, hit: findBoroughForLocation(lat, lon) };
    } catch {
      return null;
    }
  }

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(ringPulse, { toValue: 1, duration: 1100, easing: Easing.out(Easing.quad), useNativeDriver: true }),
        Animated.timing(ringPulse, { toValue: 0, duration: 1100, easing: Easing.in(Easing.quad), useNativeDriver: true }),
      ]),
    ).start();
  }, [ringPulse]);

  const runClassification = async (impact: Haptics.ImpactFeedbackStyle, photoUri?: string) => {
    Haptics.impactAsync(impact);
    setPhase('analysing');
    // 1) GPS first (~100ms) — sequential so the VLM call can use the coords.
    const where = await getCoordsAndBorough();
    setHit(where?.hit ?? null);
    // 2) VLM with grounding hints, parallel with a min 800ms dramatic pause.
    const [vlmReport] = await Promise.all([
      photoUri
        ? submitPhotoForClassification(photoUri, {
            latitude: where?.lat,
            longitude: where?.lon,
            borough: where?.hit?.borough.name,
          })
        : Promise.resolve(null),
      new Promise(r => setTimeout(r, 800)),
    ]);
    setVlm(vlmReport);
    setPhase('classified');
    Animated.spring(drawer, { toValue: 1, useNativeDriver: true, bounciness: 6 }).start();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };
  const onCapture = async () => {
    let uri: string | undefined;
    try {
      const photo = await cameraRef.current?.takePictureAsync({ quality: 0.6, skipProcessing: true });
      uri = photo?.uri;
    } catch { /* keep going with mock */ }
    runClassification(Haptics.ImpactFeedbackStyle.Heavy, uri);
  };
  const onPickLibrary = async () => {
    Haptics.selectionAsync();
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      exif: true,
    });
    if (result.canceled) return;
    runClassification(Haptics.ImpactFeedbackStyle.Light, result.assets[0]?.uri);
  };
  const onRetake = () => {
    Haptics.selectionAsync();
    Animated.timing(drawer, { toValue: 0, duration: 200, useNativeDriver: true }).start(() => {
      setPhase('viewfinder');
    });
  };
  const onSend = () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    Animated.timing(drawer, { toValue: 0, duration: 200, useNativeDriver: true }).start(() => {
      setPhase('viewfinder');
      onClassified();
    });
  };

  const drawerTranslateY = drawer.interpolate({ inputRange: [0, 1], outputRange: [400, 0] });
  const pulseScale = ringPulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.08] });
  const pulseOpacity = ringPulse.interpolate({ inputRange: [0, 1], outputRange: [0.5, 0.05] });

  const hasCamera = permission?.granted ?? false;

  return (
    <View style={{ flex: 1, backgroundColor: '#0c0c0e' }}>
      {/* Live camera background */}
      {hasCamera && (
        <CameraView
          ref={cameraRef}
          style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
          facing="back"
          flash={flash}
        />
      )}
      {/* Subtle vignette so the overlay reads */}
      {hasCamera && (
        <View pointerEvents="none" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 140,
                                            backgroundColor: 'rgba(0,0,0,0.35)' }} />
      )}
      {hasCamera && (
        <View pointerEvents="none" style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 260,
                                            backgroundColor: 'rgba(0,0,0,0.55)' }} />
      )}

      {/* Top controls */}
      <View style={{ position: 'absolute', top: 18, left: 18, right: 18, flexDirection: 'row',
                     justifyContent: 'space-between', alignItems: 'center', zIndex: 5 }}>
        <Pressable hitSlop={10} onPress={() => Haptics.selectionAsync()}>
          <HamburgerIcon />
        </Pressable>
        <Pressable hitSlop={10} onPress={() => {
          Haptics.selectionAsync();
          setFlash(f => f === 'off' ? 'on' : 'off');
        }}>
          <Text style={{ color: flash === 'on' ? '#FFD166' : '#fff', fontSize: 20 }}>⚡</Text>
        </Pressable>
      </View>

      {/* Viewfinder content area */}
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        {phase === 'viewfinder' && (
          <>
            <View style={styles.viewfinder}>
              <View style={[styles.corner, { top: 0, left: 0, borderTopWidth: 3, borderLeftWidth: 3 }]} />
              <View style={[styles.corner, { top: 0, right: 0, borderTopWidth: 3, borderRightWidth: 3 }]} />
              <View style={[styles.corner, { bottom: 0, left: 0, borderBottomWidth: 3, borderLeftWidth: 3 }]} />
              <View style={[styles.corner, { bottom: 0, right: 0, borderBottomWidth: 3, borderRightWidth: 3 }]} />
            </View>
            <Text style={{ color: '#fff', fontSize: 14, fontWeight: '600', marginTop: 28 }}>
              Point at the problem — we'll detect it
            </Text>
          </>
        )}
        {phase === 'analysing' && (
          <>
            <Text style={{ color: '#fff', fontSize: 17, fontWeight: '700' }}>Analysing…</Text>
            <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, marginTop: 6 }}>
              Detecting category and severity
            </Text>
          </>
        )}
      </View>

      {/* Shutter row: library | shutter | spacer */}
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around',
                     paddingBottom: 100, paddingHorizontal: 36 }}>
        {/* Library — pick from photos */}
        <Pressable onPress={onPickLibrary} disabled={phase !== 'viewfinder'}
                   style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1, alignItems: 'center', gap: 6 }]}>
          <View style={{ width: 50, height: 50, borderRadius: 10, borderWidth: 1.5,
                         borderColor: 'rgba(255,255,255,0.7)', alignItems: 'center', justifyContent: 'center',
                         backgroundColor: 'rgba(255,255,255,0.06)' }}>
            <LibraryIcon />
          </View>
          <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 10, fontWeight: '700', letterSpacing: 0.4 }}>
            LIBRARY
          </Text>
        </Pressable>

        {/* Shutter */}
        <Pressable onPress={onCapture} disabled={phase !== 'viewfinder'}>
          <View style={{ width: 86, height: 86, alignItems: 'center', justifyContent: 'center' }}>
            <Animated.View style={{ position: 'absolute', width: 86, height: 86, borderRadius: 43,
                                   borderWidth: 2, borderColor: '#fff',
                                   transform: [{ scale: pulseScale }], opacity: pulseOpacity }} />
            <View style={{ width: 76, height: 76, borderRadius: 38, borderWidth: 3, borderColor: '#fff',
                           padding: 4 }}>
              <View style={{ flex: 1, borderRadius: 30, backgroundColor: phase === 'viewfinder' ? '#fff' : '#ddd' }} />
            </View>
          </View>
        </Pressable>

        {/* Spacer to keep shutter centered */}
        <View style={{ width: 50 }} />
      </View>

      {/* Classification bottom sheet */}
      <Animated.View style={{ position: 'absolute', left: 0, right: 0, bottom: 0,
                              backgroundColor: p.card, borderTopLeftRadius: 22, borderTopRightRadius: 22,
                              paddingHorizontal: 22, paddingTop: 14, paddingBottom: 110,
                              transform: [{ translateY: drawerTranslateY }] }}>
        <View style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: p.border,
                       alignSelf: 'center', marginBottom: 18 }} />
        {(() => {
          // Prefer real VLM; fall back to a mock pothole when offline.
          const vlmA = vlm?.analysis;
          const cat = vlmA ? mapIssueType(vlmA.issue_type) : { icon: 'pothole' as SortedCategory, label: 'Pothole' };
          const sev = severityToBadge(vlmA?.severity ?? 4);
          const sevColor = sev.tone === 'high' ? p.red : sev.tone === 'medium' ? p.amber : p.green;
          const isLive = !!vlmA;
          // Backend borough beats GPS when available (it's enriched with the
          // VLM's location hint + density lookup).
          const backendBorough = vlm?.enrichment?.borough;
          const dept = hit ? getDepartmentForCategory(hit.borough, cat.icon) : 'Highways';
          const boroughLabel = backendBorough ?? hit?.borough.short_name;
          const locationLine = vlmA
            ? `${boroughLabel ?? vlmA.location} · ${Math.round((vlmA.confidence ?? 0) * 100)}% confident`
            : hit
              ? `${hit.borough.short_name} · ${hit.source === 'polygon' ? 'GPS confirmed' : `~${hit.distance_km.toFixed(1)} km from centroid`}`
              : 'Location not available · using fallback';
          // Priority band styling
          const band = vlm?.priority_band;
          const bandT = band ? bandTone(band) : null;
          const bandBg = bandT === 'high' ? '#FDE7E7' : bandT === 'medium' ? p.amberSoft : p.greenChipBg;
          const bandFg = bandT === 'high' ? p.red : bandT === 'medium' ? p.amber : p.green;
          return (
            <>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
                <View style={{ width: 50, height: 50, borderRadius: 12, backgroundColor: p.greenChipBg,
                               alignItems: 'center', justifyContent: 'center' }}>
                  <CategoryIcon kind={cat.icon} size={26} color={p.green} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: p.ink, fontSize: 19, fontWeight: '800' }}>
                    {cat.label} <Text style={{ color: sevColor }}>· {sev.label}</Text>
                  </Text>
                  <Text style={{ color: p.inkDim, fontSize: 13, marginTop: 2 }}>{locationLine}</Text>
                </View>
                {/* Tiny source indicator */}
                <View style={{ paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999,
                               backgroundColor: isLive ? p.greenChipBg : p.borderSoft }}>
                  <Text style={{ color: isLive ? p.green : p.inkFaint, fontSize: 10, fontWeight: '800',
                                 letterSpacing: 0.6 }}>
                    {isLive ? 'NEMOTRON' : 'OFFLINE'}
                  </Text>
                </View>
              </View>
              {vlmA?.description && (
                <Text style={{ color: p.inkDim, fontSize: 13, lineHeight: 18, marginTop: 12 }}>
                  "{vlmA.description}"
                </Text>
              )}
              <View style={{ marginTop: 16, padding: 14, backgroundColor: p.cardDim, borderRadius: 10,
                             borderLeftWidth: 3, borderLeftColor: p.green }}>
                <Text style={{ color: p.ink, fontSize: 14, lineHeight: 20 }}>
                  {hit || backendBorough ? (
                    <>
                      Send to <Text style={{ fontWeight: '800' }}>
                        {boroughLabel} — {dept}
                      </Text>. We'll track it and tell you when it's fixed.
                    </>
                  ) : (
                    <>
                      Allow location in <Text style={{ fontWeight: '800' }}>Settings</Text> so we can route this
                      to the right council. Submitting blind goes to Lambeth Highways by default.
                    </>
                  )}
                </Text>
                {band && (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 10 }}>
                    <View style={{ paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, backgroundColor: bandBg }}>
                      <Text style={{ color: bandFg, fontSize: 10, fontWeight: '800', letterSpacing: 0.6 }}>
                        PRIORITY {band}
                      </Text>
                    </View>
                    {vlm?.priority_score != null && (
                      <Text style={{ color: p.inkFaint, fontSize: 11, fontWeight: '700' }}>
                        score {vlm.priority_score.toFixed(1)}
                      </Text>
                    )}
                  </View>
                )}
              </View>
            </>
          );
        })()}
        <Pressable onPress={onSend} style={({ pressed }) => [{ backgroundColor: p.green, borderRadius: 12,
                   paddingVertical: 16, marginTop: 14, alignItems: 'center', opacity: pressed ? 0.9 : 1 }]}>
          <Text style={{ color: '#fff', fontSize: 16, fontWeight: '800' }}>Send report</Text>
        </Pressable>
        <Pressable onPress={onRetake} style={({ pressed }) => [{ backgroundColor: p.cardDim, borderRadius: 12,
                   paddingVertical: 16, marginTop: 8, alignItems: 'center', opacity: pressed ? 0.9 : 1,
                   borderWidth: 1, borderColor: p.border }]}>
          <Text style={{ color: p.ink, fontSize: 16, fontWeight: '700' }}>Retake</Text>
        </Pressable>
      </Animated.View>

      {/* Bottom tab bar — same as dashboard */}
      <BottomTabBar active="report" onTab={onTab} dark />
    </View>
  );
}

// ── Dashboard screen ────────────────────────────────────────────────────
function DashboardScreen({ onTab, justSent, onSettings }: { onTab: (t: Tab) => void; justSent: boolean; onSettings: () => void }) {
  const stats = { open: 2, fixed: 1, total: 3 };
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 8, paddingBottom: 14 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <Wordmark />
          <Pressable hitSlop={10} onPress={() => { Haptics.selectionAsync(); onSettings(); }}>
            <GearIcon />
          </Pressable>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 14 }}>
          <Pill label="BETA" kind="beta" />
          <Text style={{ color: p.inkDim, fontSize: 13 }}>Guest — reports saved on this phone.</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 110 }}
                  showsVerticalScrollIndicator={false}>
        <Text style={{ color: p.ink, fontSize: 28, fontWeight: '900', letterSpacing: -0.8, paddingHorizontal: 4 }}>
          Your reports
        </Text>
        <Text style={{ color: p.inkDim, fontSize: 14, marginTop: 4, paddingHorizontal: 4 }}>
          Everything you've sent, tracked to fixed.
        </Text>

        {justSent && (
          <View style={{ marginTop: 14, padding: 12, borderRadius: 10, backgroundColor: p.greenChipBg,
                         flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <View style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: p.green,
                           alignItems: 'center', justifyContent: 'center' }}>
              <CheckIcon size={12} color="#fff" />
            </View>
            <Text style={{ color: p.green, fontSize: 13, fontWeight: '700' }}>
              Report sent — routed to Lambeth Highways.
            </Text>
          </View>
        )}

        {/* Stats row */}
        <View style={{ flexDirection: 'row', gap: 10, marginTop: 14 }}>
          <StatCard value={stats.open} label="Open" color={p.red} />
          <StatCard value={stats.fixed} label="Fixed" color={p.green} />
          <StatCard value={stats.total} label="Total" color={p.ink} />
        </View>

        {/* Your reports list */}
        <View style={{ backgroundColor: p.card, borderRadius: 14, marginTop: 16,
                       borderWidth: 1, borderColor: p.borderSoft }}>
          {YOUR_REPORTS.map((r, i) => (
            <View key={r.id} style={{
              padding: 14, gap: 8,
              borderTopWidth: i === 0 ? 0 : 1, borderTopColor: p.borderSoft,
            }}>
              <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
                <View style={{ width: 44, height: 44, borderRadius: 10, backgroundColor: p.cardDim,
                               alignItems: 'center', justifyContent: 'center' }}>
                  <CategoryIcon kind={r.icon} color={p.green} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: p.ink, fontSize: 15, fontWeight: '800' }}>
                    {r.label} <Text style={{ color: p.inkDim, fontWeight: '500' }}>· {r.street}</Text>
                  </Text>
                  <Text style={{ color: p.inkFaint, fontSize: 12, marginTop: 2 }}>{r.ago}</Text>
                </View>
                <Pill
                  label={statusLabel(r.status)}
                  kind={r.status === 'fixed' ? 'fixed' : r.status === 'routed' ? 'routed' : 'progress'}
                />
              </View>
              <ProgressBar step={r.step} total={r.total} />
            </View>
          ))}
        </View>

        {/* Fixed near you */}
        <Text style={{ color: p.inkFaint, fontSize: 11, fontWeight: '800', letterSpacing: 1,
                       marginTop: 26, marginBottom: 10, paddingHorizontal: 4 }}>
          FIXED NEAR YOU
        </Text>
        <View style={{ backgroundColor: p.card, borderRadius: 14,
                       borderWidth: 1, borderColor: p.borderSoft }}>
          {FIXED_NEAR_YOU.map((r, i) => (
            <View key={r.id} style={{
              flexDirection: 'row', alignItems: 'center', gap: 10,
              paddingVertical: 12, paddingHorizontal: 14,
              borderTopWidth: i === 0 ? 0 : 1, borderTopColor: p.borderSoft,
            }}>
              <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: p.green }} />
              <Text style={{ flex: 1, color: p.ink, fontSize: 14 }}>
                <Text style={{ fontWeight: '700' }}>{r.label}</Text>
                <Text style={{ color: p.inkDim }}> · {r.street}</Text>
              </Text>
              <Text style={{ color: p.inkFaint, fontSize: 12 }}>{r.ago}</Text>
            </View>
          ))}
        </View>

        <Text style={{ color: p.inkFaint, fontSize: 12, textAlign: 'center', marginTop: 18, lineHeight: 18 }}>
          {COMMUNITY_STATS.fixed.toLocaleString()} reports fixed in Lambeth this year ·{'\n'}
          {COMMUNITY_STATS.open} currently open
        </Text>
      </ScrollView>

      <BottomTabBar active="dashboard" onTab={onTab} />
    </View>
  );
}

function StatCard({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <View style={{ flex: 1, backgroundColor: p.card, borderRadius: 12, paddingVertical: 14,
                   paddingHorizontal: 14, borderWidth: 1, borderColor: p.borderSoft }}>
      <Text style={{ color, fontSize: 28, fontWeight: '900', letterSpacing: -1 }}>{value}</Text>
      <Text style={{ color: p.inkDim, fontSize: 13, marginTop: 2 }}>{label}</Text>
    </View>
  );
}

function statusLabel(s: Report['status']) {
  return ({ open: 'OPEN', in_progress: 'IN PROGRESS', routed: 'ROUTED', fixed: 'FIXED' } as const)[s];
}

// ── Settings screen ─────────────────────────────────────────────────────
function SettingsScreen({ onBack }: { onBack: () => void }) {
  const [voice, setVoice] = useState(false);
  const [notify, setNotify] = useState(true);
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
                     paddingHorizontal: 18, paddingTop: 8, paddingBottom: 14 }}>
        <Pressable onPress={() => { Haptics.selectionAsync(); onBack(); }}
                   hitSlop={10}
                   style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
          <ChevronLeft size={16} color={p.blue} />
          <Text style={{ color: p.blue, fontSize: 16, fontWeight: '600' }}>Back</Text>
        </Pressable>
        <Text style={{ color: p.ink, fontSize: 16, fontWeight: '700' }}>Settings</Text>
        <View style={{ width: 50 }} />
      </View>
      <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 60 }}>
        <SectionHeader>REPORTING</SectionHeader>
        <Group>
          <Row icon={<MicGlyph />}
               title="Report by voice"
               subtitle="Describe a problem out loud instead of a photo"
               right={<Switch value={voice} onValueChange={v => { Haptics.selectionAsync(); setVoice(v); }}
                              trackColor={{ true: p.green, false: '#D1D5DB' }} thumbColor="#fff" />} />
          <Row icon={<PinGlyph />}
               title="Change area"
               subtitle="Routes reports to the right council"
               right={<View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                 <Text style={{ color: p.inkDim, fontSize: 14 }}>Brixton SW9</Text>
                 <ChevronRight />
               </View>} />
        </Group>

        <SectionHeader>NOTIFICATIONS</SectionHeader>
        <Group>
          <Row icon={<BellGlyph />}
               title="Status updates"
               subtitle="Get a nudge when your council updates a report"
               right={<Switch value={notify} onValueChange={v => { Haptics.selectionAsync(); setNotify(v); }}
                              trackColor={{ true: p.green, false: '#D1D5DB' }} thumbColor="#fff" />} />
        </Group>

        <SectionHeader>ACCOUNT</SectionHeader>
        <Group>
          <Row icon={<HomeGlyph />} title="Guest" subtitle="Reports are saved on this phone only" />
          <Row icon={<GlobeGlyph />} title="Sign in with Google" subtitle="Sync across devices — coming soon"
               right={<Text style={{ color: p.inkFaint, fontSize: 13 }}>Soon</Text>} />
          <Row icon={<ExitGlyph color={p.red} />} title="Exit guest mode" titleColor={p.red} />
        </Group>

        <Text style={{ color: p.inkFaint, fontSize: 12, textAlign: 'center', marginTop: 16 }}>
          See it — Sorted · v1.0 (beta) · Made for London
        </Text>
      </ScrollView>
    </View>
  );
}

function SectionHeader({ children }: { children: string }) {
  return (
    <Text style={{ color: p.inkFaint, fontSize: 11, fontWeight: '700', letterSpacing: 1.2,
                   marginTop: 16, marginBottom: 8, paddingHorizontal: 4 }}>{children}</Text>
  );
}

function Group({ children }: { children: ReactNode }) {
  const arr = (Array.isArray(children) ? children : [children]).filter(Boolean);
  return (
    <View style={{ backgroundColor: p.card, borderRadius: 14,
                   borderWidth: 1, borderColor: p.borderSoft }}>
      {arr.map((c, i) => (
        <View key={i} style={{ borderTopWidth: i === 0 ? 0 : 1, borderTopColor: p.borderSoft }}>{c}</View>
      ))}
    </View>
  );
}

function Row({
  icon, title, subtitle, right, titleColor,
}: {
  icon: ReactNode; title: string; subtitle?: string;
  right?: ReactNode; titleColor?: string;
}) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12,
                   paddingVertical: 14, paddingHorizontal: 14 }}>
      <View style={{ width: 28, height: 28, alignItems: 'center', justifyContent: 'center' }}>{icon}</View>
      <View style={{ flex: 1 }}>
        <Text style={{ color: titleColor ?? p.ink, fontSize: 15, fontWeight: '700' }}>{title}</Text>
        {subtitle && <Text style={{ color: p.inkDim, fontSize: 12, marginTop: 1 }}>{subtitle}</Text>}
      </View>
      {right}
    </View>
  );
}

// Tiny settings glyphs
function MicGlyph() {
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center' }}>
      <View style={{ width: 9, height: 14, borderRadius: 4.5, borderWidth: 1.6, borderColor: p.green }} />
      <View style={{ width: 14, height: 6, borderBottomLeftRadius: 7, borderBottomRightRadius: 7,
                     borderWidth: 1.6, borderTopWidth: 0, borderColor: p.green, marginTop: -1 }} />
    </View>
  );
}
function PinGlyph() {
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center' }}>
      <View style={{ width: 14, height: 14, borderRadius: 7, borderWidth: 1.6, borderColor: p.green }} />
      <View style={{ width: 0, height: 0, borderLeftWidth: 5, borderRightWidth: 5, borderTopWidth: 7,
                     borderLeftColor: 'transparent', borderRightColor: 'transparent',
                     borderTopColor: p.green, marginTop: -2 }} />
    </View>
  );
}
function BellGlyph() {
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: 14, height: 12, borderTopLeftRadius: 7, borderTopRightRadius: 7,
                     borderWidth: 1.6, borderColor: p.green }} />
      <View style={{ width: 18, height: 2, backgroundColor: p.green, marginTop: -1 }} />
      <View style={{ width: 4, height: 3, backgroundColor: p.green, marginTop: 0,
                     borderBottomLeftRadius: 2, borderBottomRightRadius: 2 }} />
    </View>
  );
}
function HomeGlyph() {
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center' }}>
      <View style={{ width: 0, height: 0, borderLeftWidth: 11, borderRightWidth: 11, borderBottomWidth: 9,
                     borderLeftColor: 'transparent', borderRightColor: 'transparent', borderBottomColor: p.green }} />
      <View style={{ width: 16, height: 10, borderWidth: 1.6, borderTopWidth: 0, borderColor: p.green }} />
    </View>
  );
}
function GlobeGlyph() {
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: 18, height: 18, borderRadius: 9, borderWidth: 1.6, borderColor: p.green }} />
      <View style={{ position: 'absolute', width: 18, height: 1.6, backgroundColor: p.green }} />
      <View style={{ position: 'absolute', width: 10, height: 18, borderRadius: 5,
                     borderWidth: 1.6, borderColor: p.green }} />
    </View>
  );
}
function ExitGlyph({ color = p.green }: { color?: string }) {
  return (
    <View style={{ width: 22, height: 22, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: 12, height: 16, borderWidth: 1.6, borderRightWidth: 0, borderColor: color }} />
      <View style={{ position: 'absolute', right: 0, width: 8, height: 1.6, backgroundColor: color }} />
      <View style={{ position: 'absolute', right: 0, width: 5, height: 5, borderRightWidth: 1.6,
                     borderTopWidth: 1.6, borderColor: color, transform: [{ rotate: '45deg' }] }} />
    </View>
  );
}

// ── Bottom tab bar ──────────────────────────────────────────────────────
function BottomTabBar({ active, onTab, dark = false }: { active: Tab; onTab: (t: Tab) => void; dark?: boolean }) {
  const bg = dark ? 'rgba(20,20,24,0.92)' : p.card;
  const border = dark ? 'rgba(255,255,255,0.08)' : p.borderSoft;
  return (
    <View style={{ position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: bg,
                   borderTopWidth: 1, borderTopColor: border, paddingBottom: 24, paddingTop: 10,
                   flexDirection: 'row' }}>
      <TabButton active={active === 'report'} label="Report" dark={dark}
                 onPress={() => onTab('report')}
                 icon={<CameraTabIcon active={active === 'report'} />} />
      <TabButton active={active === 'dashboard'} label="Dashboard" dark={dark}
                 onPress={() => onTab('dashboard')}
                 icon={<DashboardTabIcon active={active === 'dashboard'} />} />
    </View>
  );
}

function TabButton({ active, label, icon, onPress, dark }: {
  active: boolean; label: string; icon: ReactNode; onPress: () => void; dark: boolean;
}) {
  const color = active ? p.green : (dark ? 'rgba(255,255,255,0.6)' : p.inkFaint);
  return (
    <Pressable onPress={() => { Haptics.selectionAsync(); onPress(); }}
               style={{ flex: 1, alignItems: 'center', gap: 4 }}>
      {icon}
      <Text style={{ color, fontSize: 11, fontWeight: '700' }}>{label}</Text>
    </Pressable>
  );
}

// ── App root ────────────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState<Screen>('welcome');
  const [justSent, setJustSent] = useState(false);

  const onTab = (t: Tab) => {
    if (t === 'report') setScreen('camera');
    else { setScreen('dashboard'); }
  };

  const isDarkChrome = screen === 'camera';

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: isDarkChrome ? '#0c0c0e' : p.bg }}>
      <StatusBar style={isDarkChrome ? 'light' : 'dark'} />
      {screen === 'welcome'   && <WelcomeScreen onStart={() => setScreen('camera')} />}
      {screen === 'camera'    && <CameraScreen onClassified={() => { setJustSent(true); setScreen('dashboard'); }}
                                               onTab={onTab} />}
      {screen === 'dashboard' && <DashboardScreen onTab={onTab} justSent={justSent} onSettings={() => setScreen('settings')} />}
      {screen === 'settings'  && <SettingsScreen onBack={() => setScreen('dashboard')} />}
    </SafeAreaView>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  viewfinder: {
    width: 220,
    height: 220,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 34,
    height: 34,
    borderColor: '#fff',
  },
});
