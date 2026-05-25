import type { QueryResponse } from '../types';
import ChartView from './ChartView';

interface QueryResultProps {
  response: QueryResponse;
}

function QueryResult({ response }: QueryResultProps) {
  return (
    <div className="space-y-4">
      {response.MOCK_MODE && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 text-sm text-yellow-800">
          Running in mock mode - results may not reflect actual data
        </div>
      )}

      {response.intent && (
        <div className="inline-block bg-blue-100 text-blue-800 text-xs font-medium px-3 py-1 rounded-full">
          Intent: {response.intent}
        </div>
      )}

      {response.sql && (
        <div className="bg-gray-900 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Generated SQL</h4>
          <pre className="text-sm text-green-400 overflow-x-auto">
            <code>{response.sql}</code>
          </pre>
        </div>
      )}

      {response.answer && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Answer</h4>
          <p className="text-gray-900">{response.answer}</p>
        </div>
      )}

      {response.attribution && response.attribution.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-purple-800 mb-2">Attribution</h4>
          <div className="space-y-2">
            {response.attribution.map((attr, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-purple-700">{attr.field}:</span>
                <span className="font-medium text-purple-900">{attr.value}</span>
                <span className="text-purple-500">({(attr.confidence * 100).toFixed(0)}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {response.anomaly && response.anomaly.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-red-800 mb-2">Anomalies Detected</h4>
          <div className="space-y-2">
            {response.anomaly.map((anom, idx) => (
              <div key={idx} className="text-sm">
                <span className="font-medium text-red-700">{anom.field}</span>
                <span className="text-red-500 ml-2">Expected: {anom.expected}</span>
                <span className="text-red-500 ml-2">Actual: {anom.actual}</span>
                <span className="ml-2 text-xs bg-red-200 text-red-800 px-2 py-0.5 rounded">
                  {anom.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {response.data && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Visualization</h4>
          <ChartView
            data={response.data}
            columns={response.columns}
            chartType={response.chart_type}
          />
        </div>
      )}
    </div>
  );
}

export default QueryResult;