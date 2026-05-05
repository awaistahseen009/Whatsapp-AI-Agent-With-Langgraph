import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Loader2, ArrowLeft, Video, MapPin, MessageSquare, FileText, Clock, User } from 'lucide-react';
import api from '../api/axios';

interface Transcript {
  transcript_id: string;
  message_content: string;
  message_type: string;
  created_at: string;
  tokens_used?: number;
  processing_time_ms?: number;
}

interface MeetingDetails {
  meeting_id: string;
  client_phone: string;
  meeting_type: string;
  meeting_format: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  status: string;
  notes?: string;
  conversation_summary?: string;
  zoom_join_url?: string;
  zoom_meeting_id?: string;
  client_timezone: string;
  conversation_session?: any;
  transcripts: Transcript[];
  generated_summary?: string;
}

export default function MeetingDetailPage() {
  const { meetingId } = useParams<{ meetingId: string }>();
  const [meeting, setMeeting] = useState<MeetingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (meetingId) {
      fetchMeetingDetails();
    }
  }, [meetingId]);

  const fetchMeetingDetails = async () => {
    try {
      const response = await api.get(`/meetings/${meetingId}/details`);
      setMeeting(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch meeting details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-red-800 font-medium">Error</h3>
          <p className="text-red-600 mt-1">{error || 'Meeting not found'}</p>
          <Link 
            to="/meetings" 
            className="inline-flex items-center mt-4 text-red-600 hover:text-red-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Meetings
          </Link>
        </div>
      </div>
    );
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <User className="h-4 w-4 text-anthropic-dark" />;
      case 'assistant':
        return <MessageSquare className="h-4 w-4 text-accent-blue" />;
      default:
        return <FileText className="h-4 w-4 text-anthropic-gray" />;
    }
  };

  const getMeetingIcon = () => {
    return meeting.meeting_format === 'virtual' ? 
      <Video className="h-6 w-6 text-accent-blue" /> : 
      <MapPin className="h-6 w-6 text-anthropic-dark" />;
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link 
          to="/meetings" 
          className="inline-flex items-center text-anthropic-gray hover:text-anthropic-dark mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Meetings
        </Link>
        
        <div className="flex items-start gap-6">
          <div className="bg-cream-100 p-4 rounded-full flex-shrink-0">
            {getMeetingIcon()}
          </div>
          
          <div className="flex-1">
            <h1 className="text-2xl font-medium text-anthropic-dark capitalize">
              {meeting.meeting_type.replace('_', ' ')}
            </h1>
            
            <div className="mt-2 space-y-1">
              <div className="flex items-center gap-2 text-anthropic-gray">
                <User className="h-4 w-4" />
                <span className="font-medium text-anthropic-dark">{meeting.client_phone}</span>
              </div>
              
              <div className="flex items-center gap-2 text-anthropic-gray">
                <Clock className="h-4 w-4" />
                <span>{formatTimestamp(meeting.start_time)} ({meeting.duration_minutes} minutes)</span>
              </div>
              
              <div className="flex items-center gap-2 text-anthropic-gray">
                <span className="text-sm">Timezone: {meeting.client_timezone}</span>
              </div>
              
              {meeting.zoom_join_url && (
                <div className="mt-2">
                  <a 
                    href={meeting.zoom_join_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-1 bg-accent-blue text-white text-sm rounded hover:bg-blue-600 transition-colors"
                  >
                    <Video className="h-4 w-4 mr-2" />
                    Join Zoom Meeting
                  </a>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex-shrink-0">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              meeting.status === 'scheduled' ? 'bg-green-100 text-green-800' :
              meeting.status === 'completed' ? 'bg-blue-100 text-blue-800' :
              'bg-red-100 text-red-800'
            }`}>
              {meeting.status.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Meeting Notes */}
      {meeting.notes && (
        <div className="bg-white border border-cream-200 rounded-lg p-6 mb-6 shadow-sm">
          <h2 className="text-lg font-medium text-anthropic-dark mb-3">Meeting Notes</h2>
          <p className="text-anthropic-gray whitespace-pre-wrap">{meeting.notes}</p>
        </div>
      )}

      {/* Conversation Summary */}
      {(meeting.conversation_summary || meeting.generated_summary) && (
        <div className="bg-white border border-cream-200 rounded-lg p-6 mb-6 shadow-sm">
          <h2 className="text-lg font-medium text-anthropic-dark mb-3 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-anthropic-light" />
            Conversation Summary
          </h2>
          <div className="bg-cream-50 rounded-lg p-4">
            <p className="text-anthropic-gray leading-relaxed">
              {meeting.conversation_summary || meeting.generated_summary}
            </p>
          </div>
          {meeting.generated_summary && !meeting.conversation_summary && (
            <p className="text-xs text-anthropic-light mt-2 italic">
              *Summary automatically generated from conversation transcripts
            </p>
          )}
        </div>
      )}

      {/* Conversation Transcripts */}
      {meeting.transcripts && meeting.transcripts.length > 0 && (
        <div className="bg-white border border-cream-200 rounded-lg shadow-sm">
          <div className="p-6 border-b border-cream-200">
            <h2 className="text-lg font-medium text-anthropic-dark flex items-center">
              <MessageSquare className="h-5 w-5 mr-2 text-anthropic-light" />
              Conversation Transcripts ({meeting.transcripts.length} messages)
            </h2>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {meeting.transcripts.map((transcript) => (
              <div 
                key={transcript.transcript_id} 
                className={`p-4 border-b border-cream-100 ${
                  transcript.message_type === 'user' ? 'bg-cream-50' : 'bg-white'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-1">
                    {getMessageIcon(transcript.message_type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-anthropic-dark capitalize">
                        {transcript.message_type}
                      </span>
                      <span className="text-xs text-anthropic-light">
                        {formatTimestamp(transcript.created_at)}
                      </span>
                    </div>
                    
                    <p className="text-anthropic-gray whitespace-pre-wrap break-words">
                      {transcript.message_content}
                    </p>
                    
                    {(transcript.tokens_used || transcript.processing_time_ms) && (
                      <div className="mt-2 flex items-center gap-4 text-xs text-anthropic-light">
                        {transcript.tokens_used && (
                          <span>Tokens: {transcript.tokens_used}</span>
                        )}
                        {transcript.processing_time_ms && (
                          <span>Processing: {transcript.processing_time_ms}ms</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Transcripts Message */}
      {(!meeting.transcripts || meeting.transcripts.length === 0) && (
        <div className="bg-white border border-cream-200 rounded-lg p-12 text-center shadow-sm">
          <MessageSquare className="h-12 w-12 text-anthropic-light mx-auto mb-4" />
          <h3 className="text-lg font-medium text-anthropic-dark mb-2">No Transcripts Available</h3>
          <p className="text-anthropic-gray">
            Conversation transcripts for this meeting are not available.
          </p>
        </div>
      )}
    </div>
  );
}
