import type { Plan } from '../types';

interface PlanSelectorProps {
  plans: Plan[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function PlanSelector({ plans, selectedId, onSelect }: PlanSelectorProps) {
  if (plans.length === 0) {
    return <p className="text-gray-500 text-sm">No plans available</p>;
  }
  return (
    <div className="space-y-3">
      {plans.map((plan) => (
        <label
          key={plan.id}
          className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition-colors ${
            selectedId === plan.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300'
          }`}
        >
          <input
            type="radio"
            name="plan"
            value={plan.id}
            checked={selectedId === plan.id}
            onChange={() => onSelect(plan.id)}
            className="mt-1 mr-3"
          />
          <div className="flex-1">
            <p className="font-medium text-gray-900">{plan.name}</p>
            <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
            <div className="flex gap-4 mt-2">
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {plan.dimension}
              </span>
              <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                {plan.estimated_effect}
              </span>
            </div>
          </div>
        </label>
      ))}
    </div>
  );
}