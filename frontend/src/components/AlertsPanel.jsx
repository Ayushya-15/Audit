import { useState, useEffect } from 'react';
import { getAlerts, acknowledgeAlert } from '../api/client';

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const res = await getAlerts();
      setAlerts(res.data);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, []);

  const handleAcknowledge = async (id) => {
    await acknowledgeAlert(id);
    await fetchAlerts();
  };

  const severityStyle = (sev) => {
    switch (sev) {
      case 'critical': return 'border-red-700 bg-red-900/20';
      case 'high': return 'border-orange-700 bg-orange-900/20';
      case 'medium': return 'border-yellow-700 bg-yellow-900/20';
      default: return 'border-gray-700 bg-gray-700/20';
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🔔 Alerts</h2>
      {loading ? (
        <p className="text-gray-400">Loading alerts...</p>
      ) : alerts.length === 0 ? (
        <p className="text-gray-500">No alerts. Run a scan to generate alerts.</p>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className={`p-4 rounded-lg border ${severityStyle(alert.severity)}`}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{alert.title}</h3>
                  <p className="text-sm text-gray-400 mt-1">{alert.message}</p>
                  <p className="text-xs text-gray-500 mt-2">{new Date(alert.created_at).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    alert.severity === 'critical' ? 'bg-red-800 text-red-200' :
                    alert.severity === 'high' ? 'bg-orange-800 text-orange-200' :
                    'bg-gray-700 text-gray-300'
                  }`}>{alert.severity}</span>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded"
                    >
                      Acknowledge
                    </button>
                  )}
                  {alert.acknowledged && (
                    <span className="text-xs text-green-400">✓ Acknowledged</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
