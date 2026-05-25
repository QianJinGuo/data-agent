import type { AudienceResult } from '../types';

interface AudiencePreviewProps {
  preview: AudienceResult;
}

export default function AudiencePreview({ preview }: AudiencePreviewProps) {
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 rounded-lg p-4">
        <p className="text-sm text-blue-700 font-medium">Estimated Audience</p>
        <p className="text-3xl font-bold text-blue-900">{preview.estimated_count.toLocaleString()}</p>
        <p className="text-sm text-blue-600">users</p>
      </div>
      {preview.insights && (
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Insights</p>
          <p className="text-sm text-gray-600">{preview.insights}</p>
        </div>
      )}
    </div>
  );
}