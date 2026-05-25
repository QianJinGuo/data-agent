import type { Task } from '../types';

interface TaskListProps {
  tasks: Task[];
}

function TaskList({ tasks }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No tasks generated yet
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="bg-white rounded-lg p-4 border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {task.channel.toUpperCase()}
              </span>
              <span className={`text-xs px-2 py-1 rounded ${getStatusColor(task.status)}`}>
                {task.status}
              </span>
            </div>
            {task.scheduled_at && (
              <span className="text-xs text-gray-500">
                {new Date(task.scheduled_at).toLocaleString()}
              </span>
            )}
          </div>

          <p className="text-sm font-medium text-gray-900 mb-1">{task.type}</p>
          <p className="text-sm text-gray-600 mb-2">Target: {task.target}</p>
          <p className="text-sm text-gray-700">{task.content}</p>
        </div>
      ))}
    </div>
  );
}

export default TaskList;