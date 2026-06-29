/* ═══════════════════════════════════════════════════════════════════════
   HAZMOD — Interactive Web Application
   Three.js · GSAP · Leaflet · Physics Engine
   ═══════════════════════════════════════════════════════════════════════ */

// ── PHYSICS ENGINE ─────────────────────────────────────────────────────
const PG_COEFF = {
  A: { ay: 0.22, by: 0.89, az: 0.20, bz: 0.89 },
  B: { ay: 0.16, by: 0.87, az: 0.12, bz: 0.87 },
  C: { ay: 0.11, by: 0.87, az: 0.08, bz: 0.87 },
  D: { ay: 0.08, by: 0.85, az: 0.06, bz: 0.80 },
  E: { ay: 0.06, by: 0.80, az: 0.03, bz: 0.75 },
  F: { ay: 0.04, by: 0.75, az: 0.016, bz: 0.72 },
};
const SEUILS = { 'ERPG-1': 1.0, 'ERPG-2': 3.0, 'ERPG-3': 20.0 };
const K_DENSE = 5674366.0;
const EXP_Q = 0.80;
const EXP_X = 1.888;
const F_STAB_DENSE = { A: 0.35, B: 0.55, C: 0.82, D: 1.00, E: 1.25, F: 1.60 };

function sigmaPG(x, stab) {
  x = Math.max(x, 1.0);
  const c = PG_COEFF[stab] || PG_COEFF.D;
  const fac = Math.pow(1 + 0.0001 * x, -0.5);
  return {
    sy: c.ay * Math.pow(x, c.by) * fac,
    sz: Math.max(c.az * Math.pow(x, c.bz) * fac, 0.5),
  };
}

function qDebit(Q_kg, dureeMin, typeBrutal) {
  const durEff = typeBrutal ? Math.min(dureeMin, 10) : dureeMin;
  return Q_kg / Math.max(durEff, 1) / 60;
}

function concPPM(Q_kgs, u, x, y, stab, H = 0) {
  x = Math.max(x, 1);
  const { sy, sz } = sigmaPG(x, stab);
  const denom = Math.PI * u * sy * sz;
  if (denom < 1e-10) return 0;
  let C = (Q_kgs * 1000) / denom * Math.exp(-0.5 * (y / sy) ** 2);
  if (H > 0) C *= 2 * Math.exp(-0.5 * (H / sz) ** 2);
  return Math.max(C * 24.45 / 70.9, 0);
}

function rayonSeuil(Q_kg, u, stab, H, seuil, dureeMin, typeBrutal) {
  const Q_kgs = qDebit(Q_kg, dureeMin, typeBrutal);
  const H_eff = typeBrutal ? 0 : H;

  if (!typeBrutal) {
    const F = F_STAB_DENSE[stab] || 1.0;
    const R = Math.pow(K_DENSE * Math.pow(Q_kgs, EXP_Q) * F / (u * seuil), 1.0 / EXP_X);
    return Math.min(Math.max(R, 1), 30000);
  }

  const hiMax = 20000;
  let lo = 1, hi = hiMax;
  if (concPPM(Q_kgs, u, lo, 0, stab, H_eff) <= seuil) return 1;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (concPPM(Q_kgs, u, mid, 0, stab, H_eff) > seuil) lo = mid;
    else hi = mid;
  }
  const R_plume = hi;
  const durEff = Math.min(dureeMin, 10);
  if (durEff < 30) {
    const dur_s = Math.max(durEff, 1) * 60;
    const T_transit = R_plume / Math.max(u, 0.1);
    if (dur_s < T_transit) return Math.min(Math.sqrt(R_plume * u * dur_s), R_plume);
  }
  return R_plume;
}

function monteCarlo(Q_kg, u, stab, H, N, dureeMin, typeBrutal) {
  const Q_kgs = qDebit(Q_kg, dureeMin, typeBrutal);
  const H_eff = typeBrutal ? 0 : H;
  const distances = [100, 200, 300, 500, 750, 1000, 1500, 2000, 3000];
  const result = {};

  for (const d of distances) {
    const { sy, sz } = sigmaPG(d, stab);
    const samples = [];
    for (let i = 0; i < N; i++) {
      const Qv = Q_kgs * Math.exp((Math.random() + Math.random() + Math.random() - 1.5) * 0.3 * 2);
      const uv = Math.max(0.3, Math.min(15, u * Math.exp((Math.random() + Math.random() + Math.random() - 1.5) * 0.2 * 2)));
      const denom = Math.PI * uv * sy * sz;
      let c = denom > 0 ? (Qv * 1000) / denom * 24.45 / 70.9 : 0;
      if (H_eff > 0) c *= 2 * Math.exp(-0.5 * (H_eff / sz) ** 2);
      samples.push(Math.max(c, 0));
    }
    samples.sort((a, b) => a - b);
    const mean = samples.reduce((a, b) => a + b, 0) / N;
    result[d] = {
      mean,
      p50: samples[Math.floor(N * 0.5)],
      p95: samples[Math.floor(N * 0.95)],
      p_e1: samples.filter(s => s > SEUILS['ERPG-1']).length / N,
      p_e2: samples.filter(s => s > SEUILS['ERPG-2']).length / N,
      p_e3: samples.filter(s => s > SEUILS['ERPG-3']).length / N,
    };
  }
  return result;
}

// ── STATE ──────────────────────────────────────────────────────────────
const state = {
  Q_kg: 9000, dureeMin: 60, hauteur: 2, typeBrutal: true,
  u_ms: 5, dirVent: 280, stab: 'C',
  lat: 33.9716, lon: -6.8498,
  densPop: 2000, distPop: 300,
  ppeLevel: 2, earlyWarning: false, delaiEvac: 30, coordSec: 2,
  mcIter: 2000,
  r1: 0, r2: 0, r3: 0,
  gravite: 0,
  mc: null,
  simulated: false,
};

// ── THREE.JS PARTICLE SYSTEM ───────────────────────────────────────────
let scene, camera, renderer, particles;

function initThree() {
  const canvas = document.getElementById('three-canvas');
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 50;

  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const particleCount = 3000;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  const sizes = new Float32Array(particleCount);
  const velocities = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 120;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 80;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 60;
    velocities[i * 3] = (Math.random() - 0.3) * 0.02;
    velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.01;
    velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.005;

    const zone = Math.random();
    if (zone < 0.15) {
      colors[i * 3] = 0.93; colors[i * 3 + 1] = 0.27; colors[i * 3 + 2] = 0.27;
      sizes[i] = Math.random() * 1.5 + 0.5;
    } else if (zone < 0.35) {
      colors[i * 3] = 0.96; colors[i * 3 + 1] = 0.62; colors[i * 3 + 2] = 0.04;
      sizes[i] = Math.random() * 1.2 + 0.3;
    } else {
      colors[i * 3] = 0.23; colors[i * 3 + 1] = 0.51; colors[i * 3 + 2] = 0.96;
      sizes[i] = Math.random() * 0.8 + 0.2;
    }
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
  geometry._velocities = velocities;

  const material = new THREE.PointsMaterial({
    size: 0.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  particles = new THREE.Points(geometry, material);
  scene.add(particles);

  animateThree();
}

function animateThree() {
  requestAnimationFrame(animateThree);
  const positions = particles.geometry.attributes.position.array;
  const velocities = particles.geometry._velocities;
  const time = Date.now() * 0.0005;

  for (let i = 0; i < positions.length / 3; i++) {
    positions[i * 3] += velocities[i * 3] + Math.sin(time + i) * 0.003;
    positions[i * 3 + 1] += velocities[i * 3 + 1] + Math.cos(time + i * 0.7) * 0.002;
    positions[i * 3 + 2] += velocities[i * 3 + 2];

    if (positions[i * 3] > 60) positions[i * 3] = -60;
    if (positions[i * 3] < -60) positions[i * 3] = 60;
    if (Math.abs(positions[i * 3 + 1]) > 40) velocities[i * 3 + 1] *= -1;
  }

  particles.geometry.attributes.position.needsUpdate = true;
  particles.rotation.y = time * 0.05;
  particles.rotation.x = Math.sin(time * 0.3) * 0.05;
  renderer.render(scene, camera);
}

// ── LOADING ANIMATION ──────────────────────────────────────────────────
function animateLoader() {
  const steps = document.querySelectorAll('.loader-step');
  const fills = document.querySelectorAll('.step-fill');
  const gradients = ['#3B82F6', '#7C3AED', '#059669', '#DC2626', '#D97706'];

  gsap.timeline()
    .to(fills[0], { width: '100%', duration: 0.6, ease: 'power2.out', delay: 0.3 })
    .to(fills[1], { width: '100%', duration: 0.5, ease: 'power2.out' }, '-=0.1')
    .to(fills[2], { width: '100%', duration: 0.4, ease: 'power2.out' }, '-=0.1')
    .to(fills[3], { width: '100%', duration: 0.5, ease: 'power2.out' }, '-=0.1')
    .to(fills[4], { width: '100%', duration: 0.4, ease: 'power2.out' }, '-=0.1')
    .to('#loader', {
      opacity: 0,
      duration: 0.8,
      ease: 'power2.inOut',
      delay: 0.4,
      onComplete: () => {
        document.getElementById('loader').classList.add('hidden');
        initApp();
      },
    });
}

// ── APP INITIALIZATION ─────────────────────────────────────────────────
function initApp() {
  document.querySelector('.navbar').classList.add('visible');

  gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

  // Hero animations
  const heroTl = gsap.timeline({ delay: 0.2 });
  heroTl
    .from('.hero-badge-row', { opacity: 0, y: 20, duration: 0.6, ease: 'power3.out' })
    .from('.hero-title .hero-line', {
      opacity: 0, y: 40, duration: 0.8, ease: 'power3.out', stagger: 0.15,
    }, '-=0.3')
    .from('.hero-desc', { opacity: 0, y: 20, duration: 0.6, ease: 'power3.out' }, '-=0.4')
    .from('.hero-actions', { opacity: 0, y: 20, duration: 0.6, ease: 'power3.out' }, '-=0.3')
    .from('.hero-stat', {
      opacity: 0, y: 30, scale: 0.9, duration: 0.5, ease: 'back.out(1.4)', stagger: 0.1,
    }, '-=0.3');

  // Counter animations
  animateCounter('statAccidents', 81, 1.5);
  animateCounter('statHotspots', 122, 1.8);
  animateCounter('statMC', 2000, 2);
  animateCounter('statStab', 6, 1.2);

  // Scroll reveal
  document.querySelectorAll('[data-reveal]').forEach((el, i) => {
    ScrollTrigger.create({
      trigger: el,
      start: 'top 85%',
      onEnter: () => {
        gsap.to(el, {
          opacity: 1, y: 0, duration: 0.8,
          delay: i % 4 * 0.1,
          ease: 'power3.out',
          onStart: () => el.classList.add('revealed'),
        });
      },
      once: true,
    });
  });

  // Nav tabs
  setupNavTabs();
  setupInputs();
  setupMap();
}

function animateCounter(id, target, duration) {
  const el = document.getElementById(id);
  gsap.to({ val: 0 }, {
    val: target,
    duration,
    delay: 0.5,
    ease: 'power2.out',
    onUpdate: function () {
      el.textContent = Math.round(this.targets()[0].val).toLocaleString();
    },
  });
}

// ── NAV TABS ───────────────────────────────────────────────────────────
function setupNavTabs() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.section);
      if (target) {
        gsap.to(window, { scrollTo: { y: target, offsetY: 60 }, duration: 1, ease: 'power3.inOut' });
      }
    });
  });

  // Update active tab on scroll
  const sections = ['hero', 'simulation', 'map-section', 'dashboard', 'monte-carlo', 'operations'];
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    ScrollTrigger.create({
      trigger: el,
      start: 'top center',
      end: 'bottom center',
      onEnter: () => setActiveTab(id),
      onEnterBack: () => setActiveTab(id),
    });
  });

  // Hero buttons
  document.getElementById('startSimBtn')?.addEventListener('click', () => {
    gsap.to(window, { scrollTo: { y: '#simulation', offsetY: 60 }, duration: 1.2, ease: 'power3.inOut' });
  });
  document.getElementById('viewDashBtn')?.addEventListener('click', () => {
    gsap.to(window, { scrollTo: { y: '#dashboard', offsetY: 60 }, duration: 1.2, ease: 'power3.inOut' });
  });
}

function setActiveTab(id) {
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.section === id);
  });
}

// ── INPUT BINDINGS ─────────────────────────────────────────────────────
function setupInputs() {
  const bind = (id, key, outputId, fmt) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      state[key] = parseFloat(el.value);
      if (outputId) document.getElementById(outputId).textContent = fmt(el.value);
      onParamChange();
    });
  };

  bind('inputQ', 'Q_kg', 'outputQ', v => Number(v).toLocaleString() + ' kg');
  bind('inputDuration', 'dureeMin', 'outputDuration', v => v + ' min');
  bind('inputHeight', 'hauteur', 'outputHeight', v => v + ' m');
  bind('inputWind', 'u_ms', 'outputWind', v => parseFloat(v).toFixed(1) + ' m/s');
  bind('inputDir', 'dirVent', 'outputDir', v => v + '°');
  bind('inputDens', 'densPop', 'outputDens', v => Number(v).toLocaleString());
  bind('inputEvac', 'delaiEvac', 'outputEvac', v => v + ' min');
  bind('inputCoord', 'coordSec', 'outputCoord', v => v);

  // Wind compass
  const dirInput = document.getElementById('inputDir');
  if (dirInput) {
    dirInput.addEventListener('input', () => {
      const needle = document.getElementById('compassNeedle');
      if (needle) needle.style.transform = `translate(-50%, -100%) rotate(${dirInput.value}deg)`;
    });
  }

  // Toggle groups
  document.querySelectorAll('.toggle-group').forEach(group => {
    group.querySelectorAll('.toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        gsap.from(btn, { scale: 0.9, duration: 0.2, ease: 'back.out(2)' });

        if (group.id === 'releaseType') state.typeBrutal = btn.dataset.value === 'brutal';
        if (group.id === 'ppeLevel') state.ppeLevel = parseInt(btn.dataset.value);
        if (group.id === 'mcIter') state.mcIter = parseInt(btn.dataset.value);
        onParamChange();
      });
    });
  });

  // Stability
  document.querySelectorAll('.stab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.stab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.stab = btn.dataset.stab;
      gsap.from(btn, { scale: 0.85, duration: 0.25, ease: 'back.out(2)' });
      onParamChange();
    });
  });

  // Switch
  document.getElementById('earlyWarning')?.addEventListener('change', (e) => {
    state.earlyWarning = e.target.checked;
    onParamChange();
  });

  // Coords
  document.getElementById('inputLat')?.addEventListener('change', (e) => {
    state.lat = parseFloat(e.target.value);
    onParamChange();
  });
  document.getElementById('inputLon')?.addEventListener('change', (e) => {
    state.lon = parseFloat(e.target.value);
    onParamChange();
  });

  // Launch button
  document.getElementById('launchBtn')?.addEventListener('click', runSimulation);
}

function onParamChange() {
  // Update debit
  const debit = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const debitEl = document.getElementById('debitValue');
  if (debitEl) debitEl.textContent = debit.toFixed(2) + ' kg/s';
}

// ── SIMULATION ─────────────────────────────────────────────────────────
function runSimulation() {
  const btn = document.getElementById('launchBtn');
  const text = btn.querySelector('.launch-text');
  text.textContent = 'SIMULATING...';
  gsap.to(btn, { scale: 0.96, duration: 0.1, yoyo: true, repeat: 1 });

  // Compute radii
  state.r1 = rayonSeuil(state.Q_kg, state.u_ms, state.stab, state.hauteur, SEUILS['ERPG-1'], state.dureeMin, state.typeBrutal);
  state.r2 = rayonSeuil(state.Q_kg, state.u_ms, state.stab, state.hauteur, SEUILS['ERPG-2'], state.dureeMin, state.typeBrutal);
  state.r3 = rayonSeuil(state.Q_kg, state.u_ms, state.stab, state.hauteur, SEUILS['ERPG-3'], state.dureeMin, state.typeBrutal);

  // Monte Carlo
  state.mc = monteCarlo(state.Q_kg, state.u_ms, state.stab, state.hauteur, Math.min(state.mcIter, 2000), state.dureeMin, state.typeBrutal);

  // Gravity
  state.gravite = computeGravity();
  state.simulated = true;

  setTimeout(() => {
    text.textContent = 'LAUNCH SIMULATION';
    updateUI();
    updateMap();
    gsap.to(window, { scrollTo: { y: '#map-section', offsetY: 60 }, duration: 1.2, ease: 'power3.inOut' });
  }, 600);
}

function computeGravity() {
  const Q_kgs = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const d = Math.max(state.distPop, 20);
  const { sy, sz } = sigmaPG(d, state.stab);
  const denom = Math.PI * state.u_ms * sy * sz;
  const C_pop = denom > 1e-10 ? Math.min(Math.max((Q_kgs * 1000) / denom * 24.45 / 70.9, 1e-4), 500) : 1e-4;

  const expo = Math.max(Math.log10(C_pop + 0.01) / Math.log10(500.01), 0);
  const q_score = Math.max(0, Math.min(1, (Math.log10(state.Q_kg) - 1) / (Math.log10(60000) - 1)));
  const dur_sc = Math.min(state.dureeMin / 120, 1);
  let raw = expo * 5.5 + q_score * 2.5 + dur_sc * 1.0;

  const brutM = state.typeBrutal ? 1.3 : 1.0;
  const stabM = { A: 0.7, B: 0.85, C: 0.95, D: 1.0, E: 1.1, F: 1.2 }[state.stab] || 1.0;
  const densM = 0.8 + 0.4 * Math.min(Math.log10(Math.max(state.densPop, 1)) / Math.log10(15001), 1);
  const alerteM = state.earlyWarning ? 0.78 : 1.0;

  return Math.min(10, Math.max(0, raw * brutM * stabM * densM * alerteM));
}

// ── UPDATE UI ──────────────────────────────────────────────────────────
function updateUI() {
  if (!state.simulated) return;

  // Zone cards
  animateValue('zoneR3', state.r3, ' m');
  animateValue('zoneR2', state.r2, ' m');
  animateValue('zoneR1', state.r1, ' m');
  animateValue('zoneEvac', Math.max(state.r2, 200), ' m');

  // Legend
  setText('legR3', Math.round(state.r3) + ' m');
  setText('legR2', Math.round(state.r2) + ' m');
  setText('legR1', Math.round(state.r1) + ' m');
  setText('legEvac', Math.round(Math.max(state.r2, 200)) + ' m');

  // KPIs
  const SECTEUR = 1 / 6;
  const popE2 = Math.round(Math.PI * (state.r2 / 1000) ** 2 * SECTEUR * state.densPop);
  const blesses = Math.round(Math.PI * (Math.max(state.r2, 200) / 1000) ** 2 * state.densPop * 0.028 * 0.1 / 0.12);
  const arrival = state.distPop / Math.max(state.u_ms, 0.1) / 60;

  animateValue('kpiGravity', state.gravite, '/10', 1);
  animateValue('kpiPop', popE2, '');
  animateValue('kpiInjuries', blesses, '');
  animateValue('kpiArrival', arrival, ' min', 1);

  // MC at population distance
  const dRef = Object.keys(state.mc).map(Number).reduce((a, b) =>
    Math.abs(b - state.distPop) < Math.abs(a - state.distPop) ? b : a
  );
  const mcData = state.mc[dRef];
  animateValue('kpiMC', mcData.p_e2 * 100, '%', 1);

  const deaths = state.gravite >= 5 ? Math.round(blesses * 0.005 * (state.gravite - 4)) : 0;
  animateValue('kpiDeaths', deaths, '');

  // Gravity bar
  const gravFill = document.getElementById('kpiGravityFill');
  if (gravFill) {
    gravFill.style.width = (state.gravite * 10) + '%';
    gravFill.style.background = state.gravite >= 7 ? '#EF4444' : state.gravite >= 4 ? '#F59E0B' : '#10B981';
  }

  // Decision banner
  const banner = document.getElementById('decisionBanner');
  const label = document.getElementById('decisionLabel');
  const detail = document.getElementById('decisionDetail');
  const physics = document.getElementById('decisionPhysics');
  banner.className = 'decision-banner';

  if (state.distPop <= state.r3) {
    banner.classList.add('red');
    label.textContent = 'MANDATORY CONFINEMENT';
    label.style.color = '#EF4444';
    detail.textContent = `Population at ${state.distPop}m is in RED zone ERPG-3 (${Math.round(state.r3)}m). Evacuation = direct exposure to >20ppm Cl₂.`;
  } else if (state.distPop <= state.r2) {
    banner.classList.add('amber');
    label.textContent = arrival * 60 > state.delaiEvac ? 'EVACUATION POSSIBLE' : 'CONFINEMENT';
    label.style.color = '#F59E0B';
    detail.textContent = `Population at ${state.distPop}m is in ORANGE zone ERPG-2 (${Math.round(state.r2)}m).`;
  } else {
    banner.classList.add('green');
    label.textContent = 'NO IMMEDIATE ACTION';
    label.style.color = '#10B981';
    detail.textContent = `Population at ${state.distPop}m is outside ERPG zones.`;
  }

  const Q_kgs = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const cPop = concPPM(Q_kgs, state.u_ms, state.distPop, 0, state.stab);
  physics.textContent = `C estimated: ${cPop.toFixed(3)} ppm · Q=${Q_kgs.toFixed(2)} kg/s · u=${state.u_ms} m/s · Stab=${state.stab}`;

  // MC stats
  setText('mcP50', mcData.p50.toFixed(3) + ' ppm');
  setText('mcP95', mcData.p95.toFixed(3) + ' ppm');
  setText('mcPE1', (mcData.p_e1 * 100).toFixed(1) + '%');
  setText('mcPE2', (mcData.p_e2 * 100).toFixed(1) + '%');
  setText('mcPE3', (mcData.p_e3 * 100).toFixed(1) + '%');
  setText('mcMean', mcData.mean.toFixed(3) + ' ppm');

  setText('legMC', (mcData.p_e2 * 100).toFixed(0) + '%');
  setText('legG', state.gravite.toFixed(1) + '/10');

  const legMC = document.getElementById('legMC');
  const legG = document.getElementById('legG');
  if (legMC) legMC.style.background = mcData.p_e2 >= 0.7 ? '#B91C1C' : mcData.p_e2 >= 0.3 ? '#B45309' : '#15803D';
  if (legG) legG.style.background = state.gravite >= 7 ? '#DC2626' : state.gravite >= 4 ? '#D97706' : '#16A34A';

  // MC alert
  const mcAlert = document.getElementById('mcAlert');
  const mcAlertText = document.getElementById('mcAlertText');
  if (mcData.p_e2 >= 0.7) {
    mcAlert.className = 'mc-alert red';
    mcAlertText.textContent = `HIGH RISK: ${(mcData.p_e2 * 100).toFixed(0)}% probability of exceeding ERPG-2 at ${dRef}m. Immediate action required.`;
  } else if (mcData.p_e2 >= 0.3) {
    mcAlert.className = 'mc-alert amber';
    mcAlertText.textContent = `MODERATE RISK: ${(mcData.p_e2 * 100).toFixed(0)}% probability of exceeding ERPG-2 at ${dRef}m.`;
  } else {
    mcAlert.className = 'mc-alert';
    mcAlertText.textContent = `LOW RISK: ${(mcData.p_e2 * 100).toFixed(0)}% probability of exceeding ERPG-2 at ${dRef}m.`;
  }

  setText('mcIterCount', `N=${state.mcIter.toLocaleString()}`);

  drawConcChart();
  drawMCChart();
}

function animateValue(id, target, suffix = '', decimals = 0) {
  const el = document.getElementById(id);
  if (!el) return;
  gsap.to({ val: 0 }, {
    val: target,
    duration: 1.2,
    ease: 'power2.out',
    onUpdate: function () {
      const v = this.targets()[0].val;
      el.textContent = (decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString()) + suffix;
    },
  });
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ── CHARTS (Canvas 2D) ────────────────────────────────────────────────
function drawConcChart() {
  const canvas = document.getElementById('concChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.parentElement.clientWidth - 32;
  const H = 300;
  canvas.width = W * 2;
  canvas.height = H * 2;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(2, 2);

  const Q_kgs = qDebit(state.Q_kg, state.dureeMin, state.typeBrutal);
  const maxDist = Math.max(state.r1 * 1.2, 500);
  const pad = { t: 20, r: 20, b: 40, l: 60 };
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;

  const points = [];
  for (let i = 0; i <= 200; i++) {
    const x = 10 + (maxDist - 10) * i / 200;
    const c = concPPM(Q_kgs, state.u_ms, x, 0, state.stab, state.typeBrutal ? 0 : state.hauteur);
    points.push({ x, c: Math.max(c, 0.001) });
  }

  const maxC = Math.max(...points.map(p => p.c), 25);
  const logMax = Math.log10(maxC);
  const logMin = Math.log10(0.001);

  ctx.clearRect(0, 0, W, H);

  // Background zones
  const zones = [
    { min: 20, max: maxC, color: 'rgba(239,68,68,0.06)' },
    { min: 3, max: 20, color: 'rgba(245,158,11,0.06)' },
    { min: 1, max: 3, color: 'rgba(16,185,129,0.06)' },
  ];
  zones.forEach(z => {
    const y1 = pad.t + (1 - (Math.log10(z.max) - logMin) / (logMax - logMin)) * ph;
    const y2 = pad.t + (1 - (Math.log10(z.min) - logMin) / (logMax - logMin)) * ph;
    ctx.fillStyle = z.color;
    ctx.fillRect(pad.l, Math.max(y1, pad.t), pw, Math.min(y2, H - pad.b) - Math.max(y1, pad.t));
  });

  // Grid
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 0.5;
  [0.01, 0.1, 1, 3, 10, 20, 100].forEach(v => {
    if (v > maxC) return;
    const y = pad.t + (1 - (Math.log10(v) - logMin) / (logMax - logMin)) * ph;
    if (y < pad.t || y > H - pad.b) return;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText(v >= 1 ? v : v.toFixed(2), pad.l - 6, y + 3);
  });

  // Threshold lines
  [{ v: 1, c: '#10B981', l: 'ERPG-1' }, { v: 3, c: '#F59E0B', l: 'ERPG-2' }, { v: 20, c: '#EF4444', l: 'ERPG-3' }].forEach(({ v, c, l }) => {
    const y = pad.t + (1 - (Math.log10(v) - logMin) / (logMax - logMin)) * ph;
    if (y < pad.t || y > H - pad.b) return;
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = c;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = c;
    ctx.font = '8px JetBrains Mono';
    ctx.textAlign = 'left';
    ctx.fillText(l, W - pad.r - 40, y - 4);
  });

  // Curve
  ctx.beginPath();
  points.forEach((p, i) => {
    const px = pad.l + (p.x / maxDist) * pw;
    const py = pad.t + (1 - (Math.log10(p.c) - logMin) / (logMax - logMin)) * ph;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.strokeStyle = '#3B82F6';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Fill under
  const lastP = points[points.length - 1];
  ctx.lineTo(pad.l + (lastP.x / maxDist) * pw, H - pad.b);
  ctx.lineTo(pad.l, H - pad.b);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
  grad.addColorStop(0, 'rgba(59,130,246,0.15)');
  grad.addColorStop(1, 'rgba(59,130,246,0)');
  ctx.fillStyle = grad;
  ctx.fill();

  // Axes labels
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = '10px Inter';
  ctx.textAlign = 'center';
  ctx.fillText('Distance (m)', W / 2, H - 6);

  // X ticks
  const xTicks = [100, 500, 1000, 2000, 5000, 10000].filter(v => v <= maxDist);
  xTicks.forEach(v => {
    const px = pad.l + (v / maxDist) * pw;
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText(v >= 1000 ? (v / 1000) + 'k' : v, px, H - pad.b + 14);
  });
}

function drawMCChart() {
  if (!state.mc) return;
  const canvas = document.getElementById('mcChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.parentElement.clientWidth - 32;
  const H = 350;
  canvas.width = W * 2;
  canvas.height = H * 2;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(2, 2);

  const pad = { t: 20, r: 20, b: 40, l: 60 };
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;
  const distances = Object.keys(state.mc).map(Number).sort((a, b) => a - b);

  ctx.clearRect(0, 0, W, H);

  // Grid
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 0.5;
  [0, 20, 40, 60, 80, 100].forEach(v => {
    const y = pad.t + (1 - v / 100) * ph;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText(v + '%', pad.l - 6, y + 3);
  });

  const maxD = distances[distances.length - 1];
  const xScale = d => pad.l + (d / maxD) * pw;
  const yScale = v => pad.t + (1 - v) * ph;

  // Draw lines for each ERPG
  const series = [
    { key: 'p_e3', color: '#EF4444', label: 'P(C>ERPG-3)' },
    { key: 'p_e2', color: '#F59E0B', label: 'P(C>ERPG-2)' },
    { key: 'p_e1', color: '#10B981', label: 'P(C>ERPG-1)' },
  ];

  series.forEach(({ key, color }) => {
    // Fill
    ctx.beginPath();
    distances.forEach((d, i) => {
      const px = xScale(d);
      const py = yScale(state.mc[d][key]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.lineTo(xScale(maxD), yScale(0));
    ctx.lineTo(xScale(distances[0]), yScale(0));
    ctx.closePath();
    ctx.fillStyle = color.replace(')', ',0.08)').replace('rgb', 'rgba');
    ctx.fill();

    // Line
    ctx.beginPath();
    distances.forEach((d, i) => {
      const px = xScale(d);
      const py = yScale(state.mc[d][key]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Dots
    distances.forEach(d => {
      const px = xScale(d);
      const py = yScale(state.mc[d][key]);
      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });
  });

  // Legend
  series.forEach(({ color, label }, i) => {
    const lx = W - pad.r - 130;
    const ly = pad.t + 15 + i * 16;
    ctx.fillStyle = color;
    ctx.fillRect(lx, ly - 4, 10, 10);
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'left';
    ctx.fillText(label, lx + 14, ly + 5);
  });

  // X labels
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = '10px Inter';
  ctx.textAlign = 'center';
  ctx.fillText('Distance (m)', W / 2, H - 6);
  distances.forEach(d => {
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText(d >= 1000 ? (d / 1000) + 'k' : d, xScale(d), H - pad.b + 14);
  });
}

// ── LEAFLET MAP ────────────────────────────────────────────────────────
let map, zoneLayers = [];

function setupMap() {
  map = L.map('map', {
    center: [state.lat, state.lon],
    zoom: 13,
    zoomControl: false,
  });

  L.control.zoom({ position: 'topright' }).addTo(map);

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'ESRI World Imagery',
    maxZoom: 18,
  }).addTo(map);

  // Map tile controls
  document.querySelectorAll('.map-ctrl').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.map-ctrl').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Source marker with pulse
  const pulseIcon = L.divIcon({
    className: '',
    html: `<div style="position:relative;width:28px;height:28px;">
      <div style="position:absolute;inset:0;border-radius:50%;background:rgba(239,68,68,0.3);animation:mapPulse 2s ease-in-out infinite;"></div>
      <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;background:#EF4444;border:2px solid #fff;box-shadow:0 0 12px rgba(239,68,68,0.5);"></div>
    </div>
    <style>@keyframes mapPulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.8);opacity:0.3}}</style>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
  L.marker([state.lat, state.lon], { icon: pulseIcon }).addTo(map);

  setText('mapCoord', `${state.lat.toFixed(4)}°N, ${Math.abs(state.lon).toFixed(4)}°W`);
}

function updateMap() {
  if (!map || !state.simulated) return;

  // Clear old zones
  zoneLayers.forEach(l => map.removeLayer(l));
  zoneLayers = [];

  const propDir = (state.dirVent + 180) % 360;

  const zones = [
    { r: state.r1, fill: '#86EFAC', border: '#16A34A', opacity: 0.3, label: 'ERPG-1' },
    { r: state.r2, fill: '#FDB168', border: '#D97706', opacity: 0.35, label: 'ERPG-2' },
    { r: state.r3, fill: '#FC8181', border: '#C53030', opacity: 0.4, label: 'ERPG-3' },
  ];

  zones.forEach(z => {
    const pts = conePolygon(state.lat, state.lon, z.r, state.dirVent);
    const poly = L.polygon(pts, {
      color: z.border,
      weight: 3,
      fillColor: z.fill,
      fillOpacity: z.opacity,
    }).addTo(map);
    poly.bindTooltip(`${z.label}: ${Math.round(z.r)}m`, { sticky: true });
    zoneLayers.push(poly);
  });

  // Evacuation perimeter
  const evac = Math.max(state.r2, 200);
  const evacPts = conePolygon(state.lat, state.lon, evac, state.dirVent, 42);
  const evacPoly = L.polygon(evacPts, {
    color: '#F59E0B',
    weight: 2,
    dashArray: '10 5',
    fillColor: '#FEF3C7',
    fillOpacity: 0.05,
  }).addTo(map);
  zoneLayers.push(evacPoly);

  // Wind arrow
  const tipLatLon = geoPoint(state.lat, state.lon, Math.max(state.r2 * 0.3, 300), propDir);
  const arrow = L.polyline([[state.lat, state.lon], tipLatLon], {
    color: '#3B82F6',
    weight: 3,
    opacity: 0.8,
  }).addTo(map);
  zoneLayers.push(arrow);

  // Fit bounds
  const allPts = conePolygon(state.lat, state.lon, state.r1, state.dirVent, 40);
  const bounds = L.latLngBounds(allPts);
  map.fitBounds(bounds.pad(0.15));
}

function geoPoint(lat, lon, dist, bearing) {
  const R = 6371000;
  const latR = lat * Math.PI / 180;
  const bearR = bearing * Math.PI / 180;
  const dR = dist / R;
  const newLat = Math.asin(Math.sin(latR) * Math.cos(dR) + Math.cos(latR) * Math.sin(dR) * Math.cos(bearR));
  const newLon = lon * Math.PI / 180 + Math.atan2(
    Math.sin(bearR) * Math.sin(dR) * Math.cos(latR),
    Math.cos(dR) - Math.sin(latR) * Math.sin(newLat)
  );
  return [newLat * 180 / Math.PI, newLon * 180 / Math.PI];
}

function conePolygon(lat, lon, radius, windFrom, halfAngle = 36) {
  const propDir = (windFrom + 180) % 360;
  const pts = [];
  const nArc = 80;

  for (let i = 0; i <= nArc; i++) {
    const t = -1 + 2 * i / nArc;
    const bearing = (propDir + t * halfAngle + 360) % 360;
    const rMod = radius * Math.exp(-0.5 * (t * 1.8) ** 2);
    pts.push(geoPoint(lat, lon, Math.max(rMod, radius * 0.04), bearing));
  }

  const backR = radius * 0.06;
  const backDir = (propDir + 180) % 360;
  for (let i = 0; i <= 16; i++) {
    const angle = (backDir - 90 + 180 * i / 16 + 360) % 360;
    pts.push(geoPoint(lat, lon, backR, angle));
  }

  pts.push(pts[0]);
  return pts;
}

// ── WINDOW RESIZE ──────────────────────────────────────────────────────
window.addEventListener('resize', () => {
  if (renderer) {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
  if (state.simulated) {
    drawConcChart();
    drawMCChart();
  }
});

// ── INIT ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initThree();
  animateLoader();
});
