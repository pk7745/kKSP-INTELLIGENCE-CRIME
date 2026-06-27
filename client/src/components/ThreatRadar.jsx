import { useState, useEffect } from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

const RISK_COLORS = { HIGH: '#ef4444', MEDIUM: '#f97316', LOW: '#22c55e' };
const TREND_ICONS = { up: '↑', down: '↓', stable: '→' };

function RiskBadge({ score }) {
  const level = score >= 0.7 ? 'HIGH' : score >= 0.4 ? 'MEDIUM' : 'LOW';
  const color = RISK_COLORS[level];
  return (
    <span style={{ color }} className="font-bold text-xs">
      {level} ({Math.round(score * 100)}%)
    </span>
  );
}

export default function ThreatRadar() {
  const [hotspots, setHotspots] = useState([]);
  const [scrbStats, setScrbStats] = useState([]);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [hsRes, statsRes, ovRes] = await Promise.all([
          fetch('/api/hotspots'),
          fetch('/api/stats/scrb'),
          fetch('/api/stats/overview'),
        ]);
        const hs = await hsRes.json();
        const stats = await statsRes.json();
        const ov = await ovRes.json();
        setHotspots(hs.hotspots || []);
        setScrbStats(stats.stats || []);
        setOverview(ov);
      } catch (err) {
        console.error('ThreatRadar load error:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const radarData = hotspots.slice(0, 10).map(h => ({
    district: h.DistrictName?.split(' ')[0] || h.DistrictID,
    score: Math.round((h.Score || 0)),
    count: h.CrimeCount || 0,
  }));

  const barData2024 = scrbStats
    .filter(s => s.Year === 2024 && s.DistrictID !== 'KA')
    .reduce((acc, s) => {
      const existing = acc.find(a => a.district === s.DistrictName);
      if (existing) {
        existing[s.CrimeType] = (existing[s.CrimeType] || 0) + s.Count;
      } else {
        acc.push({ district: s.DistrictName?.split(' ')[0] || s.DistrictID, [s.CrimeType]: s.Count });
      }
      return acc;
    }, [])
    .slice(0, 8);

  const districtTable = hotspots.map(h => {
    const score = h.Score || 0;
    const level = score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW';
    const trend = Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable';
    return { ...h, level, trend };
  }).sort((a, b) => (b.Score || 0) - (a.Score || 0));

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-400">Loading analytics...</div>;
  }

  return (
    <div className="h-full overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-4">Threat Intelligence Radar</h2>

      {overview && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total FIRs', value: overview.totalFIRs?.toLocaleString() || '—', color: 'text-blue-400' },
            { label: 'Open Cases', value: overview.openCases?.toLocaleString() || '—', color: 'text-yellow-400' },
            { label: 'Active Alerts', value: overview.activeAlerts?.toLocaleString() || '—', color: 'text-red-400' },
            { label: 'Districts', value: overview.districts?.toLocaleString() || '38', color: 'text-green-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-gray-800 rounded-lg p-4 text-center">
              <div className={`text-2xl font-bold ${color}`}>{value}</div>
              <div className="text-xs text-gray-400 mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">District Risk Radar</h3>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="district" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <PolarRadiusAxis tick={{ fill: '#6b7280', fontSize: 10 }} domain={[0, 100]} />
                <Radar name="Risk Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">No hotspot data</div>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Crime by District (2024)</h3>
          {barData2024.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData2024} margin={{ top: 0, right: 10, left: -20, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="district" tick={{ fill: '#9ca3af', fontSize: 10 }} angle={-35} textAnchor="end" />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }} />
                <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11 }} />
                <Bar dataKey="Theft" fill="#6366f1" stackId="a" />
                <Bar dataKey="Cyber Crime" fill="#8b5cf6" stackId="a" />
                <Bar dataKey="Murder" fill="#ef4444" stackId="a" />
                <Bar dataKey="Robbery" fill="#f97316" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">No stats data</div>
          )}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <h3 className="text-sm font-semibold text-gray-300 px-4 py-3 border-b border-gray-700">
          District Risk Assessment
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-750">
                <th className="text-left px-4 py-2 text-gray-400 font-medium">District</th>
                <th className="text-right px-4 py-2 text-gray-400 font-medium">Risk Score</th>
                <th className="text-left px-4 py-2 text-gray-400 font-medium">Dominant Crime</th>
                <th className="text-right px-4 py-2 text-gray-400 font-medium">Crime Count</th>
                <th className="text-center px-4 py-2 text-gray-400 font-medium">Trend</th>
                <th className="text-center px-4 py-2 text-gray-400 font-medium">Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {districtTable.map((d, i) => (
                <tr key={d.DistrictID || i} className="border-t border-gray-700 hover:bg-gray-750">
                  <td className="px-4 py-2 text-white font-medium">{d.DistrictName || d.DistrictID}</td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-20 bg-gray-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${d.level === 'HIGH' ? 'bg-red-500' : d.level === 'MEDIUM' ? 'bg-orange-500' : 'bg-green-500'}`}
                          style={{ width: `${d.Score || 0}%` }}
                        />
                      </div>
                      <span className="text-gray-300 text-xs w-8 text-right">{Math.round(d.Score || 0)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-gray-300">{d.DominantCrimeType || '—'}</td>
                  <td className="px-4 py-2 text-right text-gray-300">{(d.CrimeCount || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-center">
                    <span className={d.trend === 'up' ? 'text-red-400' : d.trend === 'down' ? 'text-green-400' : 'text-gray-400'}>
                      {TREND_ICONS[d.trend]}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-center">
                    <RiskBadge score={(d.Score || 0) / 100} />
                  </td>
                </tr>
              ))}
              {districtTable.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">No district data</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
