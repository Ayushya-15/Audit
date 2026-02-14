import { useState } from 'react';
import { downloadReport } from '../api/client';

export default function ReportGenerator() {
  const [generating, setGenerating] = useState(false);

  const handleDownload = async () => {
    setGenerating(true);
    try {
      const res = await downloadReport();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'riskshield_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Report generation failed:', err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">📄 Report Generation</h2>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 max-w-2xl">
        <h3 className="text-lg font-semibold mb-4">ISO 31000 Compliance Report</h3>
        <p className="text-gray-400 mb-6">
          Generate a comprehensive PDF report including:
        </p>
        <ul className="text-gray-400 space-y-2 mb-6 list-disc list-inside">
          <li>Executive summary with risk heatmaps and scores</li>
          <li>Detailed findings per device with ML confidence scores</li>
          <li>Treatment plans with automated recommendations</li>
          <li>ISO 31000 compliance audit trail</li>
        </ul>
        <button
          onClick={handleDownload}
          disabled={generating}
          className="bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 px-6 py-3 rounded-lg font-medium transition-colors"
        >
          {generating ? '⏳ Generating...' : '📥 Download PDF Report'}
        </button>
      </div>
    </div>
  );
}
