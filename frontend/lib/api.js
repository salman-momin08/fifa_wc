const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

const mockDB = {
  nodes: {
    "Gate A": { coords: "45.4215, -75.6972", features: "wheelchair ramp, elevator, restroom, first-aid station" },
    "Gate B": { coords: "45.4218, -75.6968", features: "wheelchair ramp, restroom" },
    "Gate C": { coords: "45.4222, -75.6980", features: "escalator, restroom" },
    "Transit Plaza": { coords: "45.4200, -75.6950", features: "wheelchair ramp, bus transfer bay" },
    "Concourse West": { coords: "45.4210, -75.7000", features: "wheelchair ramp, elevator, water refill point" }
  }
};

export async function fetchTransitStatus(offlineMode) {
  if (offlineMode) {
    return [
      { route: 'Metro Line Red', status: 'normal', delay_minutes: 0 },
      { route: 'Shuttle Route 101', status: 'delayed', delay_minutes: 15 },
      { route: 'West Parking Express', status: 'normal', delay_minutes: 0 }
    ];
  }
  try {
    const res = await fetch(`${API_BASE}/transport/status`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Backend offline, utilizing transit fallback.");
  }
  return [
    { route: 'Metro Line Red (Offline)', status: 'normal', delay_minutes: 0 },
    { route: 'Shuttle Route 101 (Offline)', status: 'delayed', delay_minutes: 15 }
  ];
}

export async function fetchSensorsStatus(offlineMode) {
  if (offlineMode) {
    return [
      { zone: 'Gate A', density_percentage: 85, advisory: 'High density entry lines.' },
      { zone: 'Gate B', density_percentage: 45, advisory: 'Flowing smoothly.' },
      { zone: 'Transit Plaza', density_percentage: 70, advisory: 'Steady queueing.' }
    ];
  }
  try {
    const res = await fetch(`${API_BASE}/crowd/status`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Backend offline, utilizing sensors fallback.");
  }
  return [
    { zone: 'Gate A (Offline)', density_percentage: 80, advisory: 'High flow warning.' }
  ];
}

export async function fetchIncidents(offlineMode) {
  if (offlineMode) {
    return [
      { id: 101, title: 'Scanner Issue Gate A', description: 'Scanner 3 not booting.', gate: 'Gate A', severity: 'medium', status: 'draft', suggested_action: 'Deploy manual scan crew.', is_approved: false },
      { id: 102, title: 'Bus delay', description: 'Route 101 delay.', gate: 'Transit Plaza', severity: 'low', status: 'active', suggested_action: 'Broadcast warning to fans.', is_approved: true }
    ];
  }
  try {
    const res = await fetch(`${API_BASE}/decision/list`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Backend offline, utilizing incidents fallback.");
  }
  return [
    { id: 999, title: 'Network Warning (Offline)', description: 'FastAPI Operations Command center is currently offline.', gate: 'Stadium', severity: 'low', status: 'active', suggested_action: 'Perform manual reports.', is_approved: true }
  ];
}

export async function fetchSustainabilityNudge(gate, lang, offlineMode) {
  if (offlineMode) {
    const details = mockDB.nodes[gate] || { features: "General recycling bins." };
    return `[Offline Safe Mode] Sustainability tip: Water refilling and ${details.features} are fully active at ${gate}. Bring your reusable flask!`;
  }
  try {
    const res = await fetch(`${API_BASE}/sustainability/nudge?gate=${encodeURIComponent(gate)}&lang=${lang}`);
    if (res.ok) {
      const data = await res.json();
      return data.nudge;
    }
  } catch (e) {
    console.warn("Backend offline, utilizing sustainability nudge fallback.");
  }
  return `Help us reduce plastic waste! Find water refilling points inside ${gate}.`;
}

export async function queryAssistantAPI(queryText, lang, offlineMode) {
  if (offlineMode) {
    let reply = "I am operating in Offline Guide Mode. ";
    const queryLower = queryText.toLowerCase();
    
    let foundStart = null;
    let foundEnd = null;
    Object.keys(mockDB.nodes).forEach(k => {
      if (queryLower.includes(k.toLowerCase())) {
        if (!foundStart) foundStart = k;
        else foundEnd = k;
      }
    });

    if (foundStart && foundEnd) {
      reply += `To route from ${foundStart} to ${foundEnd}: Use Outer Concourse ring. Estimated transit: 5 minutes. Accessibility features: ${mockDB.nodes[foundEnd].features}.`;
    } else if (foundStart) {
      reply += `${foundStart} verified coordinates: LatLng ${mockDB.nodes[foundStart].coords}. Nearby features: ${mockDB.nodes[foundStart].features}.`;
    } else {
      reply += "Please ask for directions between coordinates like 'Transit Plaza' and 'Gate B'. Offline tables are ready.";
    }
    return reply;
  }

  try {
    const res = await fetch(`${API_BASE}/assistant/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText, lang })
    });
    if (res.ok) {
      const data = await res.json();
      return data.response;
    }
  } catch (e) {
    console.warn("Backend offline, assistant query fallback.");
  }
  return 'Offline backup: Proceed to Concourse West to access main restrooms.';
}

export async function submitIncidentReport(payload) {
  const res = await fetch(`${API_BASE}/decision/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (res.ok) return await res.json();
  throw new Error("Failed to report incident");
}

export async function submitSensorUpdate(payload) {
  const res = await fetch(`${API_BASE}/crowd/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (res.ok) return await res.json();
  throw new Error("Failed to update sensor");
}

export async function approveIncidentBroadcast(id, customAction) {
  const res = await fetch(`${API_BASE}/decision/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: id, custom_action: customAction })
  });
  if (res.ok) return await res.json();
  throw new Error("Failed to approve incident");
}

export async function fetchLiveMatch(offlineMode) {
  if (offlineMode) {
    return {
      home_team: "CANADA", home_flag: "🇨🇦", home_score: 2,
      away_team: "USA", away_flag: "🇺🇸", away_score: 1,
      match_minute: "76th Minute", is_live: true,
      possession_home: 52, possession_away: 48,
      shots_home: 12, shots_away: 9,
      pass_accuracy_home: 85, pass_accuracy_away: 81,
      attendance: "68,243", stadium_capacity_pct: 92.4
    };
  }
  try {
    const res = await fetch(`${API_BASE}/match/live`);
    if (res.ok) return await res.json();
  } catch {
    // Offline fallback
  }
  return {
    home_team: "CANADA", home_flag: "🇨🇦", home_score: 2,
    away_team: "USA", away_flag: "🇺🇸", away_score: 1,
    match_minute: "76th Minute", is_live: true,
    possession_home: 52, possession_away: 48,
    shots_home: 12, shots_away: 9,
    pass_accuracy_home: 85, pass_accuracy_away: 81,
    attendance: "68,243", stadium_capacity_pct: 92.4
  };
}

export async function fetchMatchFixtures(offlineMode) {
  if (offlineMode) {
    return [
      { id: 1, date_label: "Tomorrow - 18:00 Local", teams: "🇲🇽 Mexico vs 🇦🇷 Argentina", stage: "Matchday 2 - Group Stage" },
      { id: 2, date_label: "July 16 - 20:00 Local", teams: "🇫🇷 France vs 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England", stage: "Matchday 3 - Group Stage" },
      { id: 3, date_label: "July 18 - 17:00 Local", teams: "🇧🇷 Brazil vs 🇪🇸 Spain", stage: "Round of 32" }
    ];
  }
  try {
    const res = await fetch(`${API_BASE}/match/fixtures`);
    if (res.ok) return await res.json();
  } catch {
    // Offline fallback
  }
  return [
    { id: 1, date_label: "Tomorrow - 18:00 Local", teams: "🇲🇽 Mexico vs 🇦🇷 Argentina", stage: "Matchday 2 - Group Stage" },
    { id: 2, date_label: "July 16 - 20:00 Local", teams: "🇫🇷 France vs 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England", stage: "Matchday 3 - Group Stage" },
    { id: 3, date_label: "July 18 - 17:00 Local", teams: "🇧🇷 Brazil vs 🇪🇸 Spain", stage: "Round of 32" }
  ];
}

