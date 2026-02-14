import { useState, useEffect } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { getDevices, getHeatmap } from '../api/client';

export default function NetworkTopology() {
  const [elements, setElements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [devRes, heatRes] = await Promise.all([getDevices(), getHeatmap()]);
        const devices = devRes.data;
        const heatmap = heatRes.data;

        const riskMap = {};
        heatmap.forEach(h => { riskMap[h.device_id] = h; });

        const els = [];
        // Gateway node
        els.push({ data: { id: 'gateway', label: 'Gateway\n192.168.1.1' }, classes: 'gateway' });

        devices.forEach(device => {
          const risk = riskMap[device.id];
          const severity = risk?.severity || 'low';
          els.push({
            data: {
              id: `device-${device.id}`,
              label: `${device.hostname}\n${device.ip_address}`,
              severity,
            },
            classes: severity,
          });
          els.push({
            data: {
              source: 'gateway',
              target: `device-${device.id}`,
            },
          });
        });

        setElements(els);
      } catch (err) {
        console.error('Failed to load topology:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const stylesheet = [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'font-size': '10px',
        color: '#9ca3af',
        'background-color': '#16a34a',
        width: 40,
        height: 40,
        'text-wrap': 'wrap',
      },
    },
    { selector: '.gateway', style: { 'background-color': '#06b6d4', width: 50, height: 50, shape: 'diamond' } },
    { selector: '.low', style: { 'background-color': '#16a34a' } },
    { selector: '.medium', style: { 'background-color': '#ca8a04' } },
    { selector: '.high', style: { 'background-color': '#ea580c' } },
    { selector: '.critical', style: { 'background-color': '#dc2626' } },
    {
      selector: 'edge',
      style: { 'line-color': '#4b5563', width: 2, 'curve-style': 'bezier' },
    },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Network Topology</h2>
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        {loading ? (
          <p className="text-gray-400 text-center py-20">Loading topology...</p>
        ) : elements.length === 0 ? (
          <p className="text-gray-500 text-center py-20">No devices found. Discover devices first.</p>
        ) : (
          <CytoscapeComponent
            elements={elements}
            stylesheet={stylesheet}
            style={{ width: '100%', height: '500px' }}
            layout={{ name: 'circle', padding: 50 }}
          />
        )}
        <div className="flex gap-4 mt-4 text-sm">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-cyan-500 inline-block"></span> Gateway</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500 inline-block"></span> Low Risk</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500 inline-block"></span> Medium</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-orange-500 inline-block"></span> High</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> Critical</span>
        </div>
      </div>
    </div>
  );
}
