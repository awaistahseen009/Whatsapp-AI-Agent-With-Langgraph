import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Calendar, MapPin, Video, Trash2, XCircle } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

interface Meeting {
  meeting_id: string;
  client_phone: string;
  meeting_type: string;
  meeting_format: string;
  start_time: string;
  duration_minutes: number;
  status: string;
  zoom_join_url: string | null;
}

export default function MeetingEditPage() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  const [meetingData, setMeetingData] = useState<{meeting: Meeting, summary?: string, transcripts?: any[]} | null>(null);

  useEffect(() => {
    fetchMeeting();
  }, [id]);

  const fetchMeeting = async () => {
    try {
      const response = await api.get(`/meetings/${id}/details`);
      if (response.data) {
        setMeetingData({
          meeting: response.data,
          summary: response.data.generated_summary,
          transcripts: response.data.transcripts
        });
        setMeeting(response.data);
      } else {
        navigate('/meetings');
      }
    } catch (error) {
      console.error('Failed to fetch meeting details:', error);
      navigate('/meetings');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!meeting) return;
    try {
      await api.put(`/meetings/${meeting.meeting_id}`, { status: newStatus });
      setMeeting({ ...meeting, status: newStatus });
    } catch (error) {
      console.error('Failed to change meeting status:', error);
    }
  };

  const cancelMeeting = async () => {
    if (!meeting || !window.confirm('Are you sure you want to cancel this meeting?')) return;
    try {
      await api.delete(`/meetings/${meeting.meeting_id}`);
      navigate('/meetings');
    } catch (error) {
      console.error('Failed to cancel meeting:', error);
      alert('Only admin/owner can cancel meetings.');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-24">
        <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
      </div>
    );
  }

  if (!meeting) return null;

  return (
    <div className="p-8 max-w-3xl mx-auto flex flex-col h-full">
      <Link to="/meetings" className="inline-flex items-center text-sm font-medium text-anthropic-gray hover:text-anthropic-dark transition-colors mb-6">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Meetings
      </Link>
      
      <div className="bg-white border text-left border-cream-200 rounded-lg shadow-sm p-8 relative overflow-hidden flex-1">
        
        <div className="flex justify-between items-start mb-8">
          <div className="flex items-center gap-4">
            <div className="bg-cream-100 p-4 rounded-full">
              {meeting.meeting_format === 'virtual' ? (
                <Video className="h-6 w-6 text-accent-blue" />
              ) : (
                <MapPin className="h-6 w-6 text-anthropic-dark" />
              )}
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-anthropic-dark capitalize tracking-tight">
                 {meeting.meeting_type.replace('_', ' ')}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${meeting.status === 'scheduled' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {meeting.status}
                </span>
                <span className="text-sm font-medium text-anthropic-gray">with {meeting.client_phone}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-cream-50 p-6 rounded-lg border border-cream-200 mb-8">
           <div>
             <h3 className="text-xs font-semibold text-anthropic-light uppercase tracking-wider mb-2">Schedule Time</h3>
             <div className="flex items-center text-anthropic-dark">
                <Calendar className="h-4 w-4 mr-2 text-anthropic-gray" />
                <span className="font-medium text-sm">{new Date(meeting.start_time).toLocaleString()}</span>
             </div>
           </div>
           
           <div>
             <h3 className="text-xs font-semibold text-anthropic-light uppercase tracking-wider mb-2">Duration & Format</h3>
             <div className="flex items-center text-anthropic-dark gap-4">
               <span className="font-medium text-sm">{meeting.duration_minutes} minutes</span>
               <span className="text-anthropic-light text-xs">•</span>
               <span className="font-medium text-sm capitalize flex items-center">
                 {meeting.meeting_format === 'virtual' ? <Video className="h-4 w-4 mr-1 text-accent-blue" /> : <MapPin className="h-4 w-4 mr-1 text-anthropic-gray" />}
                 {meeting.meeting_format}
               </span>
             </div>
           </div>
        </div>

        {meeting.meeting_format === 'virtual' && meeting.zoom_join_url && (
            <div className="mb-8">
              <h3 className="text-xs font-semibold text-anthropic-light uppercase tracking-wider mb-2">Zoom Access</h3>
              <div className="bg-white border border-cream-200 rounded p-4 flex justify-between items-center shadow-sm">
                <span className="text-sm text-anthropic-dark font-mono truncate max-w-md">
                  {meeting.zoom_join_url}
                </span>
                <a 
                   href={meeting.zoom_join_url} 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   className="flex-shrink-0 ml-4 px-4 py-2 bg-accent-blue text-white text-sm font-medium rounded hover:bg-blue-600 transition-colors"
                >
                  Join Meeting &rarr;
                </a>
              </div>
            </div>
        )}

        {meetingData?.summary && (
            <div className="mb-8">
              <h3 className="text-xs font-semibold text-anthropic-light uppercase tracking-wider mb-2 flex items-center">
                 <Loader2 className="h-3 w-3 mr-1" />
                 AI Context Summary
              </h3>
              <div className="bg-cream-50 italic text-sm text-anthropic-dark border border-cream-200 rounded p-5 shadow-sm leading-relaxed">
                {meetingData.summary}
              </div>
            </div>
        )}

        <div className="pt-6 border-t border-cream-200 flex justify-between items-center">
            <span className="text-xs text-anthropic-light">Meeting ID: {meeting.meeting_id}</span>
            {meeting.status === 'scheduled' && (
              <div className="flex gap-3">
                 <button
                   onClick={() => handleStatusChange('completed')}
                   className="inline-flex items-center justify-center px-4 py-2 border border-cream-200 shadow-sm text-sm font-medium rounded-md text-green-700 bg-white hover:bg-green-50 focus:outline-none transition-colors"
                 >
                   <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                   Mark Completed
                 </button>
                 <button
                   onClick={cancelMeeting}
                   className="inline-flex items-center justify-center px-4 py-2 border border-red-200 shadow-sm text-sm font-medium rounded-md text-red-600 bg-white hover:bg-red-50 focus:outline-none transition-colors"
                 >
                   <XCircle className="h-4 w-4 mr-2" />
                   Cancel Meeting
                 </button>
              </div>
            )}
        </div>

      </div>
    </div>
  );
}
