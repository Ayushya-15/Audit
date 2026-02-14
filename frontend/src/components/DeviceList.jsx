import { useState, useEffect } from 'react';
import { getDevices, discoverDevices } from '../api/client';

export default function DeviceList() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDevices = async () => {
    try {
      const res = await getDevices();
      setDevices(res.data);
    } catch (err) {
      console.error('Failed to fetch devices:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDevices(); }, []);

  const handleDiscover = async () => {
    setLoading(true);
    await discoverDevices(5);
    await fetchDevices();
  };

  const statusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'quarantined': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Network Devices</h2>
        <button onClick={handleDiscover} className="bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded-lg text-sm">
          🔍 Discover Devices
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : (
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-750">
              <tr className="border-b border-gray-700">
                <th className="text-left p-3 text-gray-400">Hostname</th>
                <th className="text-left p-3 text-gray-400">IP Address</th>
                <th className="text-left p-3 text-gray-400">MAC Address</th>
                <th className="text-left p-3 text-gray-400">OS</th>
                <th className="text-left p-3 text-gray-400">Status</th>
                <th className="text-left p-3 text-gray-400">Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device) => (
                <tr key={device.id} className="border-b border-gray-700 hover:bg-gray-750">
                  <td className="p-3 font-medium">{device.hostname}</td>
                  <td className="p-3 font-mono text-cyan-300">{device.ip_address}</td>
                  <td className="p-3 font-mono text-gray-400">{device.mac_address || 'N/A'}</td>
                  <td className="p-3">{device.os_type || 'Unknown'}</td>
                  <td className={`p-3 font-medium ${statusColor(device.status)}`}>
                    {device.status === 'active' ? '🟢' : device.status === 'quarantined' ? '🔴' : '⚪'} {device.status}
                  </td>
                  <td className="p-3 text-gray-400">{new Date(device.last_seen).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {devices.length === 0 && (
            <p className="text-center py-8 text-gray-500">No devices found. Click &quot;Discover Devices&quot; to scan the network.</p>
          )}
        </div>
      )}
    </div>
  );
}
