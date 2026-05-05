import { useState, useEffect } from 'react';
import { Loader2, MessageSquare } from 'lucide-react';
import api from '../api/axios';

interface ChatSession {
  session_id: string;
  client_phone: string;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  escalated: boolean;
}

import { Link } from 'react-router-dom';

export default function ChatSessionsPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await api.get('/chat/sessions');
      setSessions(response.data);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Chat Sessions</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Overview of AI conversations with clients.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {sessions.map((session) => (
            <div key={session.session_id} className="bg-white border border-cream-200 rounded-lg shadow-sm hover:shadow-md transition-shadow flex flex-col p-5 relative overflow-hidden">
               {session.escalated && (
                 <div className="absolute top-0 right-0 bg-red-500 text-white text-[10px] uppercase font-bold px-2 py-1 rounded-bl-md">
                   Escalated
                 </div>
               )}
              <div className="flex items-center gap-3 mb-4 mt-2">
                <div className="bg-cream-100 p-2 rounded-full">
                  <MessageSquare className="h-5 w-5 text-anthropic-dark" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-anthropic-dark">{session.client_phone}</h3>
                </div>
              </div>
              <div className="text-xs text-anthropic-gray space-y-1">
                <p>Started: {session.started_at ? `${new Date(session.started_at).toLocaleDateString()} ${new Date(session.started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}` : 'N/A'}</p>
                <p>Last interaction: {session.ended_at ? new Date(session.ended_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : (session.started_at ? new Date(session.started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Ongoing')}</p>
                <p>Total messages: {session.message_count}</p>
              </div>
              
              <div className="mt-4 pt-4 border-t border-cream-100 flex items-center justify-between">
                <Link 
                  to={`/sessions/${session.session_id}`}
                  className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-cream-200 shadow-sm text-sm font-medium rounded-md text-anthropic-dark bg-white hover:bg-cream-100 focus:outline-none transition-colors w-full justify-center"
                >
                  View Full Transcript &rarr;
                </Link>
              </div>
            </div>
          ))}

          {sessions.length === 0 && (
            <div className="col-span-full text-center py-12 border-2 border-dashed border-cream-200 rounded-lg">
              <p className="text-sm text-anthropic-gray">No chat sessions found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
