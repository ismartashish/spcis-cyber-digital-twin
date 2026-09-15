/**
 * API client for SPCIS Cyber Immune System
 */

const BASE_URL = '';

async function fetchJson(url, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${url}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`API error ${res.status}: ${errText || res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`Request to ${url} failed:`, err);
    throw err;
  }
}

export const api = {
  getStatus: () => fetchJson('/api/status'),
  getTopology: () => fetchJson('/api/topology'),
  getState: () => fetchJson('/api/simulation/state'),
  resetSimulation: (seed = null, policyMode = 'ppo') =>
    fetchJson('/api/simulation/reset', {
      method: 'POST',
      body: JSON.stringify({ seed, policy_mode: policyMode }),
    }),
  stepSimulation: () =>
    fetchJson('/api/simulation/step', {
      method: 'POST',
    }),
  autoStepSimulation: (steps = 5) =>
    fetchJson('/api/simulation/auto', {
      method: 'POST',
      body: JSON.stringify({ steps }),
    }),
  runBenchmark: (episodes = 5, redPolicy = 'heuristic', maxSteps = 40) =>
    fetchJson('/api/arena/benchmark', {
      method: 'POST',
      body: JSON.stringify({ episodes, red_policy: redPolicy, max_steps: maxSteps }),
    }),
  getLatestReport: () => fetchJson('/api/report/latest'),
};
