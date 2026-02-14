import { useState, useEffect } from 'react';
import { getRisks, executeTreatment, getAuditLog } from '../api/client';

export default function TreatmentWorkflow() {
  const [risks, setRisks] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionResults, setActionResults] = useState({});

  const fetchData = async () => {
    try {
      const [risksRes, auditRes] = await Promise.all([
        getRisks({ status: 'open' }),
        getAuditLog(),
      ]);
      setRisks(risksRes.data);
      setAuditLog(auditRes.data);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAction = async (riskId, action) => {
    try {
      const res = await executeTreatment({ risk_id: riskId, action });
      setActionResults(prev => ({ ...prev, [riskId]: res.data }));
      await fetchData();
    } catch (err) {
      console.error('Treatment failed:', err);
    }
  };

  const severityBadge = (sev) => {
    const colors = {
      critical: 'bg-red-800 text-red-200',
      high: 'bg-orange-800 text-orange-200',
      medium: 'bg-yellow-800 text-yellow-200',
      low: 'bg-green-800 text-green-200',
    };
    return colors[sev] || 'bg-gray-700 text-gray-300';
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🛡️ Risk Treatment Workflow</h2>

      {/* Open Risks */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Open Risks</h3>
        {loading ? (
          <p className="text-gray-400">Loading...</p>
        ) : risks.length === 0 ? (
          <p className="text-gray-500">No open risks. Run a scan to detect risks.</p>
        ) : (
          risks.map((risk) => (
            <div key={risk.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold">{risk.title}</h4>
                  <p className="text-sm text-gray-400">{risk.description}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${severityBadge(risk.severity)}`}>
                  {risk.severity}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-sm mb-3">
                <div><span className="text-gray-500">Likelihood:</span> {risk.likelihood}</div>
                <div><span className="text-gray-500">Impact:</span> {risk.impact}</div>
                <div><span className="text-gray-500">Score:</span> {risk.risk_score}</div>
              </div>
              {risk.treatment_plan && (
                <div className="bg-gray-900 rounded p-3 text-sm mb-3">
                  <p className="text-gray-500 text-xs mb-1">Recommended Treatment:</p>
                  <pre className="whitespace-pre-wrap text-gray-300">{risk.treatment_plan}</pre>
                </div>
              )}
              <div className="flex gap-2">
                <button onClick={() => handleAction(risk.id, 'quarantine')} className="bg-red-700 hover:bg-red-600 px-3 py-1 rounded text-xs">
                  🔒 Quarantine
                </button>
                <button onClick={() => handleAction(risk.id, 'firewall_rule')} className="bg-orange-700 hover:bg-orange-600 px-3 py-1 rounded text-xs">
                  🧱 Firewall Rule
                </button>
                <button onClick={() => handleAction(risk.id, 'patch')} className="bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-xs">
                  🔧 Patch
                </button>
                <button onClick={() => handleAction(risk.id, 'accept')} className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-xs">
                  ✓ Accept
                </button>
                <button onClick={() => handleAction(risk.id, 'escalate')} className="bg-purple-700 hover:bg-purple-600 px-3 py-1 rounded text-xs">
                  ⬆ Escalate
                </button>
              </div>
              {actionResults[risk.id] && (
                <div className={`mt-2 text-sm p-2 rounded ${actionResults[risk.id].success ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'}`}>
                  {actionResults[risk.id].message}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Audit Log */}
      <div>
        <h3 className="text-lg font-semibold mb-3">ISO 31000 Audit Trail</h3>
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-3 text-gray-400">Timestamp</th>
                <th className="text-left p-3 text-gray-400">Action</th>
                <th className="text-left p-3 text-gray-400">ISO Phase</th>
                <th className="text-left p-3 text-gray-400">Details</th>
              </tr>
            </thead>
            <tbody>
              {auditLog.slice(0, 20).map((entry) => (
                <tr key={entry.id} className="border-b border-gray-700">
                  <td className="p-3 text-gray-400">{new Date(entry.timestamp).toLocaleString()}</td>
                  <td className="p-3">{entry.action}</td>
                  <td className="p-3"><span className="bg-cyan-900 text-cyan-300 text-xs px-2 py-0.5 rounded">{entry.iso_phase || 'N/A'}</span></td>
                  <td className="p-3 text-gray-400">{entry.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {auditLog.length === 0 && (
            <p className="text-center py-6 text-gray-500">No audit entries yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
