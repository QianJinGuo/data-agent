import type { QueryResponse } from '../types';
import ChartView from './ChartView';

interface QueryResultProps {
  response: QueryResponse;
}

function QueryResult({ response }: QueryResultProps) {
  const chartType = response.chart_type || 'table';
  const tableData = response.query_result?.rows ?? [];
  const columns = response.query_result?.columns ?? [];

  return (
    <div className="space-y-4">
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

      {response.final_answer && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Answer</h4>
          <p className="text-gray-900">{response.final_answer}</p>
        </div>
      )}

      {tableData.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Visualization</h4>
          <ChartView data={tableData} columns={columns} chartType={chartType} />
        </div>
      )}
    </div>
  );
}

export default QueryResult;