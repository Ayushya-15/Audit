import { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { getDashboard, getHeatmap, runScan, discoverDevices, trainModels } from '../api/client';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const fetchData = async () => {
    try {
      const [dashRes, heatRes] = await Promise.all([getDashboard(), getHeatmap()]);
      setStats(dashRes.data);
      setHeatmap(heatRes.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleFullScan = async () => {
    setScanning(true);
    try {
      await discoverDevices(5);
      await runScan();
      await trainModels();
      await fetchData();
    } catch (err) {
      console.error('Scan failed:', err);
    } finally {
      setScanning(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-400">Loading dashboard...</div>;

  const severityData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [stats?.critical_risks || 0, stats?.high_risks || 0, stats?.medium_risks || 0, stats?.low_risks || 0],
      backgroundColor: ['#dc2626', '#ea580c', '#ca8a04', '#16a34a'],
      borderWidth: 0,
    }],
  };

  const heatmapBarData = {
    labels: heatmap.map(h => h.hostname),
    datasets: [{
      label: 'Risk Score',
      data: heatmap.map(h => h.risk_score),
      backgroundColor: heatmap.map(h => {
        if (h.risk_score >= 0.75) return '#dc2626';
        if (h.risk_score >= 0.5) return '#ea580c';
        if (h.risk_score >= 0.25) return '#ca8a04';
        return '#16a34a';
      }),
    }],
  };

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Risk Dashboard</h2>
        <button
          onClick={handleFullScan}
          disabled={scanning}
          className="bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 px-6 py-2 rounded-lg font-medium transition-colors"
        >
          {scanning ? '⏳ Scanning...' : '🔍 Run Full Scan'}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Devices', value: stats?.total_devices || 0, color: 'cyan' },
          { label: 'Open Risks', value: stats?.open_risks || 0, color: 'red' },
          { label: 'Avg Risk Score', value: (stats?.avg_risk_score || 0).toFixed(3), color: 'yellow' },
          { label: 'Quarantined', value: stats?.quarantined_devices || 0, color: 'orange' },
        ].map((card) => (
          <div key={card.label} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <p className="text-gray-400 text-sm">{card.label}</p>
            <p className={`text-3xl font-bold text-${card.color}-400`}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Risk Severity Distribution</h3>
          <div className="max-w-xs mx-auto">
            <Doughnut data={severityData} options={{ plugins: { legend: { labels: { color: '#9ca3af' } } } }} />
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Risk Heatmap by Device</h3>
          <Bar
            data={heatmapBarData}
            options={{
              scales: {
                y: { beginAtZero: true, max: 1, ticks: { color: '#9ca3af' }, grid: { color: '#374151' } },
                x: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } },
              },
              plugins: { legend: { display: false } },
            }}
          />
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
        {stats?.recent_alerts?.length ? (
          <div className="space-y-2">
            {stats.recent_alerts.map((alert) => (
              <div key={alert.id} className={`p-3 rounded-lg border ${
                alert.severity === 'critical' ? 'border-red-700 bg-red-900/20' :
                alert.severity === 'high' ? 'border-orange-700 bg-orange-900/20' :
                'border-gray-700 bg-gray-700/20'
              }`}>
                <div className="flex justify-between">
                  <span className="font-medium">{alert.title}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    alert.severity === 'critical' ? 'bg-red-800 text-red-200' :
                    alert.severity === 'high' ? 'bg-orange-800 text-orange-200' :
                    'bg-gray-700 text-gray-300'
                  }`}>{alert.severity}</span>
                </div>
                <p className="text-sm text-gray-400 mt-1">{alert.message}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No recent alerts. Run a scan to detect risks.</p>
        )}
      </div>
    </div>
  );
}
