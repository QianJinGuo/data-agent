import { useState, useEffect } from 'react';
import type { ConversationMessage, QueryResponse } from '../types';
import { queryNL2SQL } from '../api/client';
import ChatInput from '../components/ChatInput';
import ConversationList from '../components/ConversationList';
import QueryResult from '../components/QueryResult';

const STORAGE_KEY = 'data-agent-conversations';

function NL2SQLPage() {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<ConversationMessage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setMessages(parsed);
        }
      } catch (e) {
        console.error('Failed to parse stored conversations', e);
      }
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    }
  }, [messages]);

  const handleSend = async (question: string) => {
    setError(null);
    setLoading(true);

    const newMessage: ConversationMessage = {
      id: `msg-${Date.now()}`,
      question,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setSelectedMessage(newMessage);

    try {
      let conversationId: string | undefined;
      const lastWithResponse = messages.filter((m) => m.response).pop();
      if (lastWithResponse?.response?.conversation_id) {
        conversationId = lastWithResponse.response.conversation_id;
      }

      const response: QueryResponse = await queryNL2SQL(question, conversationId);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === newMessage.id
            ? { ...msg, response }
            : msg
        )
      );
      setSelectedMessage((prev) =>
        prev?.id === newMessage.id
          ? { ...prev, response }
          : prev
      );
    } catch (err) {
      const errorResponse: QueryResponse = {
        sql: '',
        answer: `Error: Failed to connect to server. Make sure the backend is running at http://localhost:8000`,
      };
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === newMessage.id
            ? { ...msg, response: errorResponse }
            : msg
        )
      );
      setError('Failed to fetch response');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Data Agent - NL2SQL</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white rounded-xl shadow-sm p-4 h-[600px] overflow-y-auto">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">History</h2>
          <ConversationList
            messages={messages}
            selectedId={selectedMessage?.id}
            onSelect={setSelectedMessage}
          />
        </div>

        <div className="lg:col-span-2 flex flex-col h-[600px]">
          <div className="flex-1 bg-white rounded-xl shadow-sm p-4 overflow-y-auto mb-4">
            {selectedMessage ? (
              <div>
                <div className="mb-4 pb-4 border-b border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Question</p>
                  <p className="text-gray-900 font-medium">{selectedMessage.question}</p>
                </div>
                {selectedMessage.response ? (
                  <QueryResult response={selectedMessage.response} />
                ) : (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>Select a conversation or ask a new question</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <ChatInput
              onSend={handleSend}
              loading={loading}
              disabled={loading}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default NL2SQLPage;