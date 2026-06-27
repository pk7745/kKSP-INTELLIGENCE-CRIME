import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts';

const CRIME_COLORS = {
  Theft: '#6366f1',
  Murder: '#ef4444',
  Robbery: '#f97316',
  Assault: '#f59e0b',
  'Cyber Crime': '#8b5cf6',
  'Drug Offence': '#10b981',
};

const DISTRICTS = [
  { id: 'BEU', name: 'Bengaluru Urban' },
  { id: 'MYS', name: 'Mysuru' },
  { id: 'MNG', name: 'Mangaluru' },
  { id: 'HUB', name: 'Hubballi-Dharwad' },
  { id: 'BLG', name: 'Belagavi' },
  { id: 'KLB', name: 'Kalaburagi' },
  { id: 'DWD', name: 'Davanagere' },
  { id: 'SHV', name: 'Shivamogga' },
  { id: 'TUM', name: 'Tumakuru' },
  { id: 'BER', name: 'Bengaluru Rural' },
];

function RiskCalendar({ predictions, district }) {
  const distPreds = predictions.filter(p => p.DistrictID === district);
  const dates = [...new Set(distPreds.map(p => p.PredictionDate))].sort().slice(0, 7);
  const crimeTypes = [...new Set(distPreds.map(p => p.CrimeType))];

  if (dates.length === 0) {
    return <div className="text-gray-500 text-sm text-center py-4">No prediction data</div>;
  }

  const maxScore = Math.max(...distPreds.map(p => p.RiskScore || 0), 0.01);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="text-left text-gray-400 font-normal py-1 pr-3">Crime Type</th>
            {dates.map(d => (
              <th key={d} className="text-center text-gray-400 font-normal py-1 px-1 min-w-16">
                {new Date(d).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {crimeTypes.map(ct => (
            <tr key={ct}>
              <td className="py-1 pr-3 text-gray-300 whitespace-nowrap">{ct}</td>
              {dates.map(d => {
                const pred = distPreds.find(p => p.PredictionDate === d && p.CrimeType === ct);
                const score = pred?.RiskScore || 0;
                const intensity = score / maxScore;
                const bg = score >= 0.7 ? `rgba(239,68,68,${0.3 + intensity * 0.7})` :
                           score >= 0.4 ? `rgba(249,115,22,${0.3 + intensity * 0.7})` :
                           `rgba(34,197,94,${0.2 + intensity * 0.5})`;
                return (
                  <td key={d} className="py-1 px-1">
                    <div
                      className="h-8 rounded flex items-center justify-center text-white font-bold"
                      style={{ backgroundColor: bg }}
                      title={`${ct} on ${d}: ${pred?.PredictedCount || 0} predicted, risk ${Math.round(score * 100)}%`}
                    >
                      {pred?.PredictedCount || 0}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SHAPFactors({ factors }) {
  let parsed = factors;
  if (typeof factors === 'string') {
    try { parsed = JSON.parse(factors); } catch { return null; }
  }
  if (!Array.isArray(parsed) || parsed.length === 0) return null;

  return (
    <div className="mt-2">
      <p className="text-xs text-gray-400 mb-2">Key Risk Factors:</p>
      {parsed.map((f, i) => (
        <div key={i} className="flex items-center gap-2 mb-1.5">
          <span className="text-xs text-gray-300 w-40 flex-shrink-0">{f.factor}</span>
          <div className="flex-1 bg-gray-700 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full bg-indigo-500"
              style={{ width: `${Math.abs(f.value) * 100}%` }}
            />
          </div>
          <span className={`text-xs w-10 text-right ${f.value > 0 ? 'text-red-400' : 'text-green-400'}`}>
            {f.value > 0 ? '+' : ''}{(f.value * 100).toFixed(0)}%
          </span>
        </div>
      ))}
    </div>
  );
}

export default function PredictionPanel() {
  const [predictions, setPredictions] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('BEU');
  const [loading, setLoading] = useState(true);
  const [patrolMsg, setPatrolMsg] = useState(null);
  const [loadingPatrol, setLoadingPatrol] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/predictions');
        const data = await res.json();
        setPredictions(data.predictions || []);
      } catch (err) {
        console.error('Prediction load error:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const districtPreds = predictions.filter(p => p.DistrictID === selectedDistrict);

  const lineData = (() => {
    const dateMap = {};
    districtPreds.forEach(p => {
      if (!dateMap[p.PredictionDate]) dateMap[p.PredictionDate] = { date: p.PredictionDate };
      dateMap[p.PredictionDate][p.CrimeType] = p.PredictedCount;
    });
    return Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date)).map(d => ({
      ...d,
      date: new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    }));
  })();

  const crimeTypes = [...new Set(districtPreds.map(p => p.CrimeType))];

  const topPred = districtPreds.reduce((max, p) => (!max || p.RiskScore > max.RiskScore) ? p : max, null);

  const handlePatrolReco = async () => {
    setLoadingPatrol(true);
    setPatrolMsg(null);
    try {
      const distName = DISTRICTS.find(d => d.id === selectedDistrict)?.name || selectedDistrict;
      const res = await fetch('/api/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `Where should I deploy patrol tonight in ${distName}? What are the predicted high-risk areas?`,
          session_id: `patrol-${selectedDistrict}-${Date.now()}`,
          district_filter: selectedDistrict,
        }),
      });
      const data = await res.json();
      setPatrolMsg(data.response || 'No recommendation available.');
    } catch (err) {
      setPatrolMsg('Failed to get patrol recommendation. Please try again.');
    } finally {
      setLoadingPatrol(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-400">Loading predictions...</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white">7-Day Crime Predictions</h2>
        <div className="flex items-center gap-3">
          <select
            value={selectedDistrict}
            onChange={e => setSelectedDistrict(e.target.value)}
            className="bg-gray-800 text-white text-sm border border-gray-600 rounded px-3 py-1.5"
          >
            {DISTRICTS.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <button
            onClick={handlePatrolReco}
            disabled={loadingPatrol}
            className="bg-indigo-700 hover:bg-indigo-600 disabled:bg-indigo-900 text-white text-sm px-3 py-1.5 rounded transition-colors whitespace-nowrap"
          >
            {loadingPatrol ? '...' : '🚔 Patrol Reco'}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {patrolMsg && (
          <div className="bg-indigo-900 border border-indigo-600 rounded-lg p-4">
            <p className="text-xs font-bold text-indigo-300 mb-2">KAVERI Patrol Recommendation</p>
            <p className="text-sm text-white">{patrolMsg}</p>
          </div>
        )}

        {topPred && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-400">{Math.round((topPred.RiskScore || 0) * 100)}%</div>
              <div className="text-xs text-gray-400 mt-1">Peak Risk Score</div>
              <div className="text-xs text-gray-500">{topPred.CrimeType}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-400">{topPred.PredictedCount}</div>
              <div className="text-xs text-gray-400 mt-1">Peak Predicted Count</div>
              <div className="text-xs text-gray-500">{topPred.PredictionDate}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-400">{crimeTypes.length}</div>
              <div className="text-xs text-gray-400 mt-1">Crime Types Tracked</div>
              <div className="text-xs text-gray-500">XGBoost Model</div>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">7-Day Predicted Crime Counts</h3>
          {lineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={lineData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }} />
                <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11 }} />
                {crimeTypes.map(ct => (
                  <Line
                    key={ct}
                    type="monotone"
                    dataKey={ct}
                    stroke={CRIME_COLORS[ct] || '#6b7280'}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500">No prediction data for this district</div>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Risk Calendar (Next 7 Days)</h3>
          <RiskCalendar predictions={predictions} district={selectedDistrict} />
        </div>

        {topPred?.SHAPFactors && (
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">AI Explainability — Risk Factors</h3>
            <SHAPFactors factors={topPred.SHAPFactors} />
          </div>
        )}
      </div>
    </div>
  );
}
