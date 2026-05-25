import { useState } from 'react';
import type { AudiencePreviewResponse, Plan, Task } from '../types';
import { createCampaign, getPlans, applyPlan } from '../api/client';
import AudiencePreview from './AudiencePreview';
import PlanSelector from './PlanSelector';
import StrategyConfig from './StrategyConfig';
import TaskList from './TaskList';

const CHANNEL_OPTIONS = ['sms', 'webhook', 'email'];

interface CampaignBuilderProps {
  onComplete?: (tasks: Task[]) => void;
}

function CampaignBuilder({ onComplete }: CampaignBuilderProps) {
  const [step, setStep] = useState(1);
  const [objective, setObjective] = useState('');
  const [audienceDescription, setAudienceDescription] = useState('');
  const [channels, setChannels] = useState<string[]>(['email']);
  const [audiencePreview, setAudiencePreview] = useState<AudiencePreviewResponse | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStep1Next = async () => {
    if (!objective.trim() || !audienceDescription.trim()) {
      setError('Please fill in both objective and audience description');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const preview = await createCampaign(objective, audienceDescription, undefined, channels);
      setAudiencePreview(preview);
      const plansResponse = await getPlans(objective, audienceDescription, channels);
      setPlans(plansResponse.proposed_plans || []);
      if (plansResponse.proposed_plans?.length === 1) {
        setSelectedPlanId(plansResponse.proposed_plans[0].id);
      }
      setStep(2);
    } catch (err) {
      setError('Failed to fetch audience preview. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStep3Next = () => {
    if (!selectedPlanId) {
      setError('Please select a plan');
      return;
    }
    setError(null);
    setStep(4);
  };

  const handleStep4Submit = async (config: { timing: string; channels: string[]; content: string }) => {
    if (!selectedPlanId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await applyPlan(selectedPlanId, config.channels, config.content);
      setTasks(result.tasks || []);
      setStep(5);
      if (onComplete) {
        onComplete(result.tasks || []);
      }
    } catch (err) {
      setError('Failed to generate tasks. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleChannel = (channel: string) => {
    if (channels.includes(channel)) {
      setChannels(channels.filter((c) => c !== channel));
    } else {
      setChannels([...channels, channel]);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        {[1, 2, 3, 4, 5].map((s) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center font-medium text-sm ${
                step >= s
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {s}
            </div>
            {s < 5 && (
              <div
                className={`w-16 h-1 mx-2 ${
                  step > s ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {!loading && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">Campaign Objective</h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Objective
                </label>
                <textarea
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  placeholder="e.g., Increase customer retention by 20%"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Audience Description
                </label>
                <textarea
                  value={audienceDescription}
                  onChange={(e) => setAudienceDescription(e.target.value)}
                  placeholder="e.g., Customers who made a purchase in the last 90 days and have not opened any email in the last 30 days"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Channels
                </label>
                <div className="flex gap-4">
                  {CHANNEL_OPTIONS.map((channel) => (
                    <label key={channel} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={channels.includes(channel)}
                        onChange={() => toggleChannel(channel)}
                        className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm capitalize">{channel}</span>
                    </label>
                  ))}
                </div>
              </div>
              <button
                onClick={handleStep1Next}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Next: Preview Audience
              </button>
            </div>
          )}

          {step === 2 && audiencePreview && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">Audience Preview</h2>
              <AudiencePreview preview={audiencePreview} />
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  Next: Select Plan
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">Select a Plan</h2>
              <PlanSelector
                plans={plans}
                selectedId={selectedPlanId}
                onSelect={setSelectedPlanId}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleStep3Next}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  Next: Configure Strategy
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">Configure Strategy</h2>
              <StrategyConfig
                channels={channels}
                onSubmit={handleStep4Submit}
              />
              <button
                onClick={() => setStep(3)}
                className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors mt-4"
              >
                Back
              </button>
            </div>
          )}

          {step === 5 && tasks.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">Generated Tasks</h2>
              <p className="text-sm text-gray-500">
                {tasks.length} tasks have been created for your campaign
              </p>
              <TaskList tasks={tasks} />
              <button
                onClick={() => {
                  setStep(1);
                  setObjective('');
                  setAudienceDescription('');
                  setChannels(['email']);
                  setAudiencePreview(null);
                  setPlans([]);
                  setSelectedPlanId(null);
                  setTasks([]);
                }}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Start New Campaign
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CampaignBuilder;