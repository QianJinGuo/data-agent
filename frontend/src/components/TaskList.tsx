import type { Task } from '../types';

interface TaskListProps {
  tasks: Task[];
}

export default function TaskList({ tasks }: TaskListProps) {
  if (tasks.length === 0) {
    return <p className="text-gray-500 text-sm">No tasks generated</p>;
  }
  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div key={task.id} className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <span className={`w-2 h-2 rounded-full ${
              task.status === 'pending' ? 'bg-yellow-500' : 'bg-green-500'
            }`} />
            <div>
              <p className="font-medium text-gray-900 capitalize">{task.channel}</p>
              <p className="text-sm text-gray-500">ID: {task.id.slice(0, 8)}...</p>
            </div>
          </div>
          <span className="text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-full capitalize">
            {task.status}
          </span>
        </div>
      ))}
    </div>
  );
}