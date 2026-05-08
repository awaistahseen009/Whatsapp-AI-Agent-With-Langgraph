import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, MessageSquare, AlertTriangle } from 'lucide-react';
import api from '../api/axios';

interface ChatMessage {
  id: string;
  sender_type: 'human' | 'ai';
  content: string;
  timestamp: string;
}

interface TranscriptMessage {
  transcript_id: string;
  message_type: 'user' | 'assistant' | 'system';
  message_content: string;
  timestamp: string;
}

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTranscripts();
  }, [id]);

  const fetchTranscripts = async () => {
    try {
      const response = await api.get(`/chat/sessions/${id}/transcripts/`);
      setTranscripts(response.data || []);
    } catch (error) {
      console.error('Failed to fetch transcripts:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-24">
        <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto h-[calc(100vh-64px)] flex flex-col">
      <div className="mb-6 flex items-center justify-between flex-shrink-0">
        <Link to="/sessions" className="inline-flex items-center text-sm font-medium text-anthropic-gray hover:text-anthropic-dark transition-colors">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Sessions
        </Link>
        <div className="flex items-center gap-2 text-sm text-anthropic-light">
          Session ID: <span className="font-mono text-xs">{id}</span>
        </div>
      </div>

      <div className="bg-white border text-left border-cream-200 rounded-lg shadow-sm flex flex-col flex-1 overflow-hidden">
        <div className="bg-cream-50 px-6 py-4 border-b border-cream-200 flex items-center gap-3">
          <MessageSquare className="h-5 w-5 text-anthropic-dark" />
          <h2 className="text-lg font-semibold text-anthropic-dark">Full Transcript</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-cream-50/30">
          {transcripts.length === 0 ? (
            <div className="flex justify-center items-center h-full">
               <p className="text-anthropic-gray text-sm">No transcript available.</p>
            </div>
          ) : (
            transcripts.map((msg) => (
              <div key={msg.transcript_id} className={`flex w-full mt-2 space-x-3 max-w-xs ${msg.message_type === 'user' ? 'ml-auto justify-end' : ''}`}>
                
                {msg.message_type !== 'user' && (
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-cream-200 flex items-center justify-center">
                    <span className="text-xs font-bold text-anthropic-dark">AI</span>
                  </div>
                )}
                
                <div className={`${msg.message_type === 'user' ? 'min-w-fit' : ''}`}>
                  <div className={`p-3 text-sm shadow-sm ${msg.message_type === 'user' ? 'bg-anthropic-dark text-white rounded-l-lg rounded-br-lg' : 'bg-white border border-cream-200 text-anthropic-dark rounded-r-lg rounded-bl-lg'}`}>
                    {msg.message_content}
                  </div>
                  <span className={`text-[10px] text-anthropic-light mt-1 block uppercase tracking-wide font-medium ${msg.message_type === 'user' ? 'text-right' : ''}`}>
                    {msg.message_type === 'user' ? 'Human' : 'Riley Agent'} • {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>

              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
