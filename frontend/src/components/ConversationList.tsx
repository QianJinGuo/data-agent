import type { ConversationMessage } from '../types';

interface ConversationListProps {
  messages: ConversationMessage[];
  selectedId?: string;
  onSelect: (message: ConversationMessage) => void;
}

function ConversationList({ messages, selectedId, onSelect }: ConversationListProps) {
  if (messages.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-sm">No conversations yet. Ask a question to get started!</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {messages.map((msg) => (
        <button
          key={msg.id}
          onClick={() => onSelect(msg)}
          className={`w-full text-left p-3 rounded-lg transition-colors ${
            selectedId === msg.id
              ? 'bg-blue-100 border border-blue-300'
              : 'bg-white border border-gray-200 hover:bg-gray-50'
          }`}
        >
          <p className="text-sm font-medium text-gray-900 truncate">{msg.question}</p>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(msg.timestamp).toLocaleTimeString()}
          </p>
        </button>
      ))}
    </div>
  );
}

export default ConversationList;