import { useState } from 'react';
import Dashboard from './components/Dashboard';
import DeviceList from './components/DeviceList';
import NetworkTopology from './components/NetworkTopology';
import AlertsPanel from './components/AlertsPanel';
import TreatmentWorkflow from './components/TreatmentWorkflow';
import ReportGenerator from './components/ReportGenerator';

const tabs = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'devices', label: 'Devices', icon: '🖥️' },
  { id: 'topology', label: 'Network', icon: '🌐' },
  { id: 'alerts', label: 'Alerts', icon: '🔔' },
  { id: 'treatment', label: 'Treatment', icon: '🛡️' },
  { id: 'reports', label: 'Reports', icon: '📄' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🛡️</span>
            <h1 className="text-xl font-bold text-cyan-400">RiskShield</h1>
            <span className="text-xs bg-cyan-900 text-cyan-300 px-2 py-0.5 rounded">ISO 31000</span>
          </div>
          <span className="text-sm text-gray-400">GRC Compliance Tool</span>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="p-6">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'devices' && <DeviceList />}
        {activeTab === 'topology' && <NetworkTopology />}
        {activeTab === 'alerts' && <AlertsPanel />}
        {activeTab === 'treatment' && <TreatmentWorkflow />}
        {activeTab === 'reports' && <ReportGenerator />}
      </main>
    </div>
  );
}
