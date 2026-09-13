// Games Catalog
const gamesCatalog = [
  {
    name: 'Genshin Impact',
    spec: 'HIGH GPU · 5.2 GB RAM',
    color: '#6257ff',
    badge: 'DEMANDING',
    app_ram_gb: 5.2,
    app_storage_gb: 28.0,
    app_gpu_intensity: 0.94,
    app_cpu_intensity: 0.88,
    target_fps: 60,
    gain: 8,
  },
  {
    name: 'Call of Duty: Mobile',
    spec: 'HIGH GPU · 3.8 GB RAM',
    color: '#ff783d',
    badge: 'COMPETITIVE',
    app_ram_gb: 3.8,
    app_storage_gb: 14.0,
    app_gpu_intensity: 0.72,
    app_cpu_intensity: 0.65,
    target_fps: 120,
    gain: 4,
  },
  {
    name: 'Honkai: Star Rail',
    spec: 'HIGH GPU · 4.6 GB RAM',
    color: '#ed60b2',
    badge: 'DEMANDING',
    app_ram_gb: 4.6,
    app_storage_gb: 22.0,
    app_gpu_intensity: 0.86,
    app_cpu_intensity: 0.78,
    target_fps: 60,
    gain: 6,
  },
  {
    name: 'PUBG Mobile',
    spec: 'MEDIUM GPU · 3.1 GB RAM',
    color: '#ffca52',
    badge: 'COMPETITIVE',
    app_ram_gb: 3.1,
    app_storage_gb: 12.0,
    app_gpu_intensity: 0.60,
    app_cpu_intensity: 0.58,
    target_fps: 90,
    gain: 3,
  },
  {
    name: 'Wuthering Waves',
    spec: 'VERY HIGH GPU · 5.8 GB RAM',
    color: '#6ce1da',
    badge: 'EXTREME',
    app_ram_gb: 5.8,
    app_storage_gb: 26.0,
    app_gpu_intensity: 0.98,
    app_cpu_intensity: 0.92,
    target_fps: 60,
    gain: 10,
  },
  {
    name: 'Asphalt Legends',
    spec: 'MEDIUM GPU · 2.4 GB RAM',
    color: '#7e97ff',
    badge: 'ARCADE',
    app_ram_gb: 2.4,
    app_storage_gb: 6.5,
    app_gpu_intensity: 0.52,
    app_cpu_intensity: 0.45,
    target_fps: 90,
    gain: 2,
  }
];

const getGamesCatalog = () => {
  return gamesCatalog;
};

const getDeviceInfo = () => {
  return {
    device: "iQOO 13 5G",
    chipset: "Snapdragon 8 Elite",
    ram_gb: 12,
    storage_gb: 256
  };
};

const analyzePerformance = (telemetry) => {
  const {
    ram_gb = 12.0,
    ram_used_percent = 47.0,
    temperature_c = 39.0,
    battery_percent = 78.0,
    app_name = "Custom Game",
    app_ram_gb = 5.0,
    app_gpu_intensity = 0.85,
    app_cpu_intensity = 0.80,
    target_fps = 60,
    is_optimized = false
  } = telemetry;

  // Find the game if it exists in the catalog to use its specific settings
  let game = gamesCatalog.find(g => g.name.toLowerCase() === app_name.toLowerCase()) || {
    name: app_name,
    app_ram_gb,
    app_gpu_intensity,
    app_cpu_intensity,
    target_fps,
    gain: 5
  };

  const effectiveTemp = is_optimized ? Math.max(35.5, temperature_c - 1.6) : temperature_c;
  const effectiveRamPct = is_optimized ? ram_used_percent * 0.72 : ram_used_percent;
  const availRam = ram_gb * (1.0 - effectiveRamPct / 100.0);
  const ramMargin = availRam - game.app_ram_gb;

  let score = 96.0;
  if (ramMargin < 0) {
    score -= Math.abs(ramMargin) * 14.0;
  } else if (ramMargin < 1.2) {
    score -= (1.2 - ramMargin) * 7.5;
  }

  if (effectiveTemp > 41.5) {
    score -= (effectiveTemp - 41.5) * 8.0 + 10.0;
  } else if (effectiveTemp > 38.0) {
    score -= (effectiveTemp - 38.0) * 3.8;
  }

  if (battery_percent < 20) {
    score -= (20 - battery_percent) * 0.7;
  }

  const workloadPenalty = (game.app_gpu_intensity * 0.6 + game.app_cpu_intensity * 0.4) * 12.0;
  score -= workloadPenalty;

  if (is_optimized) {
    score += game.gain;
  }

  const finalScore = Math.min(99, Math.max(18, Math.round(score)));
  const fpsRatio = finalScore / 100.0;
  const tFps = game.target_fps || 60;
  const predFps = Math.round(Math.min(tFps, tFps * (0.58 + 0.42 * fpsRatio)));

  let fpsMin = Math.max(30, predFps - (tFps >= 90 ? 12 : 7));
  let fpsMax = Math.min(tFps, predFps + 2);
  if (is_optimized) {
    fpsMin += Math.round(game.gain * 0.7);
    fpsMax = Math.min(tFps, fpsMax + Math.round(game.gain * 0.4));
  }

  const thermalRisk = effectiveTemp >= 41.5 ? 'HIGH' : effectiveTemp >= 37.5 ? 'MEDIUM' : 'LOW';
  const batteryImpact = game.app_gpu_intensity >= 0.85 ? 'HIGH' : game.app_gpu_intensity >= 0.6 ? 'MEDIUM' : 'LOW';
  const ramPressure = availRam < game.app_ram_gb ? 'HIGH' : availRam < game.app_ram_gb + 1.2 ? 'MEDIUM' : 'LOW';

  let verdict = 'OPTIMAL';
  let title = 'Locked in for the win.';
  let copy = 'Your device has excellent headroom for a responsive, high-frame-rate session.';

  if (finalScore < 70) {
    verdict = 'LIMITED HEADROOM';
    title = 'High thermal stress predicted.';
    copy = 'Extended play will cause thermal throttling. We recommend optimizing before starting.';
  } else if (finalScore < 88) {
    verdict = is_optimized ? 'OPTIMIZED FOR PLAY' : 'PLAYABLE WITH CARE';
    title = is_optimized ? 'Clear the runway. You’re set.' : 'Strong start. Watch the heat.';
    copy = is_optimized
      ? `Game Mode is active and background load is reduced. Stability increased by +${game.gain} pts.`
      : 'You have enough power for a smooth session, but prolonged play may create thermal pressure.';
  }

  // Generate dynamic recommendations based on issues found
  let recommendations = [];
  if (thermalRisk === 'HIGH' || thermalRisk === 'MEDIUM') {
    recommendations.push("Reduce background activity and allow the device to cool before extended gameplay.");
  }
  if (ramPressure === 'HIGH' || ramPressure === 'MEDIUM') {
    recommendations.push("Close unnecessary background applications to free up memory.");
  }
  if (batteryImpact === 'HIGH') {
    recommendations.push("Consider reducing graphics quality for sustained frame-rate stability and less battery drain.");
  }
  if (battery_percent < 20) {
    recommendations.push("Enable a balanced performance profile to extend remaining battery life.");
  }
  if (recommendations.length === 0) {
    recommendations.push("No immediate action needed. Device is operating within optimal parameters.");
  }

  const explanation = is_optimized
    ? `KATSU has created additional headroom for ${game.name}. Background tasks are cleared and Monster Mode cooling is active, maintaining stable frame pacing for the next hour.`
    : `Your iQOO 13 can run ${game.name} ${finalScore >= 85 ? 'exceptionally well' : 'comfortably'} right now. Current device temperature (${effectiveTemp.toFixed(1)}°C) and memory margin indicate ${thermalRisk === 'HIGH' ? 'potential throttling after 25–30 minutes' : 'stable pacing with low thermal resistance'}.`;

  return {
    performanceScore: finalScore,
    verdict: verdict,
    verdictTitle: title,
    verdictCopy: copy,
    estimatedFrameRate: `${fpsMin}–${fpsMax} FPS`,
    fpsMin: fpsMin,
    fpsMax: fpsMax,
    thermalRisk: thermalRisk,
    batteryImpact: batteryImpact,
    ramPressure: ramPressure,
    explanation: explanation,
    recommendations: recommendations,
    modelConfidence: 94,
    gain: game.gain
  };
};

module.exports = {
  getGamesCatalog,
  getDeviceInfo,
  analyzePerformance
};
