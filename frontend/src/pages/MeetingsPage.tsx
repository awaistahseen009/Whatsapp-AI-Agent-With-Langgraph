import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Video, MapPin } from 'lucide-react';
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

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      const response = await api.get('/meetings');
      setMeetings(response.data);
    } catch (error) {
      console.error('Failed to fetch meetings:', error);
    } finally {
      setLoading(false);
    }
  };

  const cancelMeeting = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this meeting?')) return;
    try {
      await api.delete(`/meetings/${id}`);
      setMeetings(prev => prev.map(m => m.meeting_id === id ? { ...m, status: 'cancelled' } : m));
    } catch (error) {
      console.error('Failed to cancel meeting:', error);
      alert('Only admin/owner can cancel meetings.');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Meetings Schedule</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Upcoming property tours and virtual consultations booked by AI.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="bg-white border border-cream-200 rounded-lg overflow-hidden shadow-sm">
          <ul className="divide-y divide-cream-200">
            {meetings.map((meeting) => (
              <li key={meeting.meeting_id} className="p-6 hover:bg-cream-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex gap-4 items-center">
                    <div className="bg-cream-100 p-3 rounded-full flex-shrink-0 h-10 w-10 flex justify-center items-center">
                      {meeting.meeting_format === 'virtual' ? <Video className="h-5 w-5 text-accent-blue" /> : <MapPin className="h-5 w-5 text-anthropic-dark" />}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-anthropic-dark capitalize">
                        {meeting.meeting_type.replace('_', ' ')}
                      </h3>
                      <div className="flex flex-col sm:flex-row sm:items-center text-sm text-anthropic-gray gap-2 sm:gap-4 mt-0.5">
                        <span className="font-medium text-anthropic-dark">{meeting.client_phone}</span>
                        <span className="hidden sm:inline">•</span>
                        <span>{new Date(meeting.start_time).toLocaleString()} ({meeting.duration_minutes} min)</span>
                      </div>
                      
                      {meeting.status !== 'scheduled' && (
                         <div className="mt-2 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 uppercase tracking-wider">
                           {meeting.status}
                         </div>
                      )}
                    </div>
                  </div>
                  
                  <Link 
                    to={`/meetings/${meeting.meeting_id}/edit`}
                    className="inline-flex items-center px-4 py-2 border border-cream-200 shadow-sm text-sm font-medium rounded-md text-anthropic-dark bg-white hover:bg-cream-100 focus:outline-none transition-colors"
                  >
                    View Details &rarr;
                  </Link>
                </div>
              </li>
            ))}
            
            {meetings.length === 0 && (
               <li className="p-12 text-center text-anthropic-gray text-sm">
                 No upcoming meetings.
               </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
