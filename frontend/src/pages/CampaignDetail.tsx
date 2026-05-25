import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import type { Task } from '../types';
import { listTasks } from '../api/client';
import TaskList from '../components/TaskList';

function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true);
      try {
        const result = await listTasks();
        setTasks(result.tasks || []);
      } catch (err) {
        setError('Failed to load tasks');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTasks();
  }, [id]);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Campaign Details</h1>
        <Link
          to="/marketing"
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Back to Marketing
        </Link>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Tasks</h2>
          <TaskList tasks={tasks} />
        </div>
      )}
    </div>
  );
}

export default CampaignDetail;