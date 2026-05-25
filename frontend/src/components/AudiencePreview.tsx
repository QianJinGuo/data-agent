import type { AudiencePreviewResponse } from '../types';

interface AudiencePreviewProps {
  preview: AudiencePreviewResponse;
}

function AudiencePreview({ preview }: AudiencePreviewProps) {
  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Audience Preview</h3>

      <div className="mb-4">
        <p className="text-sm text-gray-500">Estimated Reach</p>
        <p className="text-3xl font-bold text-blue-600">{preview.estimated_count.toLocaleString()}</p>
      </div>

      {preview.insights && preview.insights.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-2">Key Insights</p>
          <div className="space-y-2">
            {preview.insights.map((insight, idx) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <span className="text-sm text-gray-700">{insight.label}</span>
                <span className="text-sm font-medium text-gray-900">
                  {typeof insight.value === 'number' ? insight.value.toLocaleString() : insight.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {preview.rules && preview.rules.length > 0 && (
        <div>
          <p className="text-sm text-gray-500 mb-2">Segmentation Rules</p>
          <ul className="space-y-1">
            {preview.rules.map((rule, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start">
                <span className="mr-2 text-blue-500">•</span>
                {rule}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default AudiencePreview;