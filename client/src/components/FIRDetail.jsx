import { useState } from 'react';

const CHARGESHEET_LABELS = {
  A: { label: 'Chargesheeted (A)', color: 'text-green-400', desc: 'Case chargesheeted — accused sent for trial' },
  B: { label: 'False Case (B)', color: 'text-yellow-400', desc: 'Case found false or no offence made out' },
  C: { label: 'Undetected (C)', color: 'text-red-400', desc: 'Case undetected — accused not identified' },
};

function Section({ title, children }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-bold text-indigo-300 mb-3 border-b border-gray-700 pb-2">{title}</h3>
      {children}
    </div>
  );
}

function LabelValue({ label, value }) {
  return (
    <div className="flex gap-2 mb-1.5">
      <span className="text-xs text-gray-400 w-36 flex-shrink-0">{label}</span>
      <span className="text-xs text-gray-200">{value || '—'}</span>
    </div>
  );
}

export default function FIRDetail({ fir, onClose }) {
  const [similarCases, setSimilarCases] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [showSimilar, setShowSimilar] = useState(false);

  if (!fir) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <div className="text-4xl mb-2">📁</div>
          <p>Select a FIR from the Crime Map to view details</p>
        </div>
      </div>
    );
  }

  const handleFindSimilar = async () => {
    setLoadingSimilar(true);
    setShowSimilar(true);
    try {
      const res = await fetch('/api/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `Find cases similar to FIR ${fir.CrimeNo}: ${fir.BriefFacts}`,
          session_id: `fir-detail-${fir.CrimeNo}`,
          intent_override: 'CRIME_DNA',
        }),
      });
      const data = await res.json();
      setSimilarCases(data.similar_cases || []);
    } catch (err) {
      console.error('Similar cases fetch error:', err);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const victims = fir.victims || [];
  const accused = fir.accused || [];
  const sections = fir.sections || [];
  const chargesheet = fir.chargesheet;
  const chargeInfo = chargesheet ? CHARGESHEET_LABELS[chargesheet.Outcome] : null;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">FIR Details</h2>
          <p className="text-xs text-indigo-400 font-mono">{fir.CrimeNo}</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        <Section title="Case Master">
          <LabelValue label="FIR Number" value={fir.CrimeNo} />
          <LabelValue label="District" value={fir.DistrictID} />
          <LabelValue label="Unit / Station" value={fir.UnitID} />
          <LabelValue label="Crime Date & Time" value={fir.CrimeDateTime} />
          <LabelValue label="Registration" value={fir.RegistrationDateTime} />
          <LabelValue label="Crime Sub-Head" value={fir.CrimeSubHeadID} />
          <LabelValue label="GPS" value={fir.Latitude && fir.Longitude ? `${fir.Latitude}, ${fir.Longitude}` : null} />
          <LabelValue label="Status" value={fir.Status} />
          <div className="mt-2">
            <span className="text-xs text-gray-400 block mb-1">Brief Facts</span>
            <p className="text-xs text-gray-200 leading-relaxed bg-gray-900 rounded p-2">{fir.BriefFacts || '—'}</p>
          </div>
        </Section>

        {victims.length > 0 && (
          <Section title={`Victims (${victims.length})`}>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400">
                    <th className="text-left pb-2">No.</th>
                    <th className="text-left pb-2">Name</th>
                    <th className="text-left pb-2">Age</th>
                    <th className="text-left pb-2">Gender</th>
                    <th className="text-left pb-2">Injury</th>
                  </tr>
                </thead>
                <tbody>
                  {victims.map((v, i) => (
                    <tr key={i} className="border-t border-gray-700">
                      <td className="py-1.5 pr-3 text-gray-400">{v.VictimNo || `V${i + 1}`}</td>
                      <td className="py-1.5 pr-3 text-white">{v.VictimName}</td>
                      <td className="py-1.5 pr-3 text-gray-300">{v.Age}</td>
                      <td className="py-1.5 pr-3 text-gray-300">{v.Gender === 'M' ? 'Male' : v.Gender === 'F' ? 'Female' : v.Gender}</td>
                      <td className="py-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          v.InjuryType === 'Fatal' ? 'bg-red-900 text-red-300' :
                          v.InjuryType === 'Grievous' ? 'bg-orange-900 text-orange-300' :
                          v.InjuryType === 'Minor' ? 'bg-yellow-900 text-yellow-300' :
                          'bg-gray-700 text-gray-400'
                        }`}>
                          {v.InjuryType || 'None'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        )}

        {accused.length > 0 && (
          <Section title={`Accused (${accused.length})`}>
            <div className="space-y-2">
              {accused.map((a, i) => (
                <div key={i} className="bg-gray-900 rounded p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-white">{a.AccusedName}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      a.ArrestStatus === 'Arrested' ? 'bg-green-900 text-green-300' :
                      a.ArrestStatus === 'Absconding' ? 'bg-red-900 text-red-300' :
                      'bg-gray-700 text-gray-400'
                    }`}>
                      {a.ArrestStatus}
                    </span>
                  </div>
                  <div className="flex gap-4 text-xs text-gray-400">
                    <span>{a.AccusedNo} | Age: {a.Age} | {a.Gender === 'M' ? 'Male' : 'Female'}</span>
                    {a.PriorCases > 0 && (
                      <span className="text-orange-400">⚠️ {a.PriorCases} prior case{a.PriorCases !== 1 ? 's' : ''}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {sections.length > 0 && (
          <Section title="IPC / BNS Sections Applied">
            <div className="flex flex-wrap gap-2">
              {sections.map((s, i) => (
                <div key={i} className="bg-indigo-900 border border-indigo-600 rounded px-2 py-1">
                  <span className="text-xs font-bold text-indigo-200">{s.ActCode} {s.SectionNo}</span>
                  <span className="text-xs text-indigo-400 ml-1">— {s.Description}</span>
                </div>
              ))}
            </div>
          </Section>
        )}

        {chargeInfo && (
          <Section title="Chargesheet Outcome">
            <div className="flex items-center gap-3">
              <span className={`text-lg font-bold ${chargeInfo.color}`}>{chargeInfo.label}</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">{chargeInfo.desc}</p>
            {chargesheet.ChargesheetDate && (
              <LabelValue label="Chargesheet Date" value={chargesheet.ChargesheetDate} />
            )}
            {chargesheet.Court && (
              <LabelValue label="Court" value={chargesheet.Court} />
            )}
          </Section>
        )}

        <div className="mt-2">
          <button
            onClick={handleFindSimilar}
            disabled={loadingSimilar}
            className="w-full bg-purple-800 hover:bg-purple-700 disabled:bg-purple-900 text-white text-sm py-2 rounded-lg transition-colors"
          >
            {loadingSimilar ? '🔍 Searching...' : '🧬 Find Similar Cases (Crime DNA)'}
          </button>
        </div>

        {showSimilar && (
          <Section title="Similar Cases (Crime DNA)">
            {loadingSimilar ? (
              <div className="text-center py-4 text-gray-400 text-sm">Analyzing case similarity...</div>
            ) : similarCases.length > 0 ? (
              <div className="space-y-2">
                {similarCases.map((c, i) => (
                  <div key={i} className="bg-gray-900 rounded p-3 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-mono text-indigo-300">{c.CrimeNo}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{c.BriefFacts?.slice(0, 80)}...</p>
                    </div>
                    <span className="text-xs font-bold text-purple-400 ml-3">
                      {Math.round((c.similarity_score || 0) * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500">No similar cases found in the embedding database.</p>
            )}
          </Section>
        )}
      </div>
    </div>
  );
}
