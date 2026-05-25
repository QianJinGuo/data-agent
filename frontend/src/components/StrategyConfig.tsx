import { useState } from 'react';

interface StrategyConfigProps {
  channels: string[];
  onSubmit: (config: { timing: string; channels: string[]; content: string }) => void;
}

const CHANNEL_OPTIONS = ['sms', 'webhook', 'email'];

function StrategyConfig({ channels, onSubmit }: StrategyConfigProps) {
  const [timing, setTiming] = useState('');
  const [selectedChannels, setSelectedChannels] = useState<string[]>(channels);
  const [content, setContent] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ timing, channels: selectedChannels, content });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Timing
        </label>
        <input
          type="text"
          value={timing}
          onChange={(e) => setTiming(e.target.value)}
          placeholder="e.g., Immediately, 2 days from now, Every Monday at 9am"
          className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                checked={selectedChannels.includes(channel)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedChannels([...selectedChannels, channel]);
                  } else {
                    setSelectedChannels(selectedChannels.filter((c) => c !== channel));
                  }
                }}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm capitalize">{channel}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Message Content
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Enter your campaign message content..."
          rows={4}
          className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        Generate Tasks
      </button>
    </form>
  );
}

export default StrategyConfig;