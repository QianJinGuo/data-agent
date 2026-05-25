import type { Plan } from '../types';

interface PlanSelectorProps {
  plans: Plan[];
  selectedId: string | null;
  onSelect: (planId: string) => void;
}

function PlanSelector({ plans, selectedId, onSelect }: PlanSelectorProps) {
  if (plans.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No plans available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {plans.map((plan) => (
        <label
          key={plan.id}
          className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition-colors ${
            selectedId === plan.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 bg-white hover:border-gray-300'
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
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">{plan.name}</h4>
              {plan.recommended && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                  Recommended
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              <span>Reach: {plan.estimated_reach.toLocaleString()}</span>
              <span>Budget: {plan.budget}</span>
            </div>
          </div>
        </label>
      ))}
    </div>
  );
}

export default PlanSelector;