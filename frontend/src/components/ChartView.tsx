import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { ChartDataPoint } from '../types';

interface ChartViewProps {
  data?: ChartDataPoint[];
  columns?: string[];
  chartType?: string;
  title?: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

function ChartView({ data, columns, chartType, title }: ChartViewProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data available for visualization
      </div>
    );
  }

  const renderTable = () => (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns?.map((col) => (
              <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.slice(0, 50).map((row, idx) => (
            <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {columns?.map((col) => (
                <td key={col} className="px-4 py-2 text-sm text-gray-900">
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 50 && (
        <p className="text-sm text-gray-500 text-center py-2">Showing 50 of {data.length} rows</p>
      )}
    </div>
  );

  const getChartData = () => {
    if (!columns || columns.length < 2) return null;
    const xKey = columns[0];
    const yKeys = columns.slice(1);
    return { xKey, yKeys };
  };

  const chartData = getChartData();

  if (chartType === 'line' && chartData) {
    return (
      <div className="bg-white rounded-lg p-4">
        {title && <h3 className="text-lg font-medium mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={chartData.xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {chartData.yKeys.map((key, idx) => (
              <Line key={key} type="monotone" dataKey={key} stroke={COLORS[idx % COLORS.length]} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === 'column_parallel' && chartData) {
    return (
      <div className="bg-white rounded-lg p-4">
        {title && <h3 className="text-lg font-medium mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={chartData.xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            {chartData.yKeys.map((key, idx) => (
              <Bar key={key} dataKey={key} fill={COLORS[idx % COLORS.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === 'pie' && chartData) {
    const yKey = chartData.yKeys[0];
    return (
      <div className="bg-white rounded-lg p-4">
        {title && <h3 className="text-lg font-medium mb-4">{title}</h3>}
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              dataKey={yKey}
              nameKey={chartData.xKey}
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={(entry) => `${entry[chartData.xKey]}: ${entry[yKey]}`}
            >
              {data.map((_, idx) => (
                <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === 'measure_card' && data.length > 0) {
    const keys = Object.keys(data[0]).filter(k => k !== columns?.[0]);
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {keys.map((key) => (
          <div key={key} className="bg-white rounded-lg p-6 text-center shadow">
            <p className="text-sm text-gray-500 mb-1">{key}</p>
            <p className="text-3xl font-bold text-blue-600">
              {typeof data[0][key] === 'number' ? data[0][key].toLocaleString() : data[0][key]}
            </p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-4">
      {title && <h3 className="text-lg font-medium mb-4">{title}</h3>}
      {renderTable()}
    </div>
  );
}

export default ChartView;