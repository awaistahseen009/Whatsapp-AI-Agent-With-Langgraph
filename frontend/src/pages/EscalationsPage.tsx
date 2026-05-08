import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, AlertTriangle, CheckCircle } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

interface Escalation {
  escalation_id: string;
  client_phone: string;
  triggered_at: string;
  reason: string;
  conversation_summary: string;
  last_client_message: string;
  status: string;
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchEscalations();
  }, []);

  const fetchEscalations = async () => {
    try {
      const response = await api.get('/escalations/');
      setEscalations(response.data);
    } catch (error) {
      console.error('Failed to fetch escalations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (id: string, newStatus: 'resolved' | 'dismissed') => {
    try {
      await api.put(`/escalations/${id}/resolve/`, { status: newStatus, resolution_notes: 'Handled via dashboard' });
      // Remove from UI
      setEscalations((prev) => prev.filter(e => e.escalation_id !== id));
    } catch (error) {
      console.error('Failed to resolve escalation:', error);
      alert("Only an admin/owner can resolve escalations");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Action Hub: Escalations</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            These clients hit a dead end with the AI and require human intervention.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="space-y-6">
          {escalations.filter(e => e.status.toLowerCase() === 'pending').map((escalation) => (
            <div key={escalation.escalation_id} className="bg-white border text-left border-red-200 rounded-lg shadow-sm p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-red-400"></div>
              
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-red-50 p-2 rounded-full">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-anthropic-dark">Client Assistance Required</h3>
                    <p className="text-sm font-medium text-anthropic-gray">{escalation.client_phone}</p>
                  </div>
                </div>
                <div className="text-xs text-anthropic-light">
                  {new Date(escalation.triggered_at).toLocaleString()}
                </div>
              </div>

              <div className="mt-2 bg-cream-50 p-4 border border-cream-200 rounded-md">
                <p className="text-sm font-semibold text-anthropic-dark mb-1">AI Reason for handover:</p>
                <p className="text-sm text-anthropic-gray mb-4">{escalation.reason}</p>

                <p className="text-sm font-semibold text-anthropic-dark mb-1">Last message from client:</p>
                <p className="text-sm text-anthropic-dark bg-white border border-cream-200 inline-block px-3 py-2 rounded">
                  "{escalation.last_client_message}"
                </p>
              </div>

               <div className="mt-5 flex gap-3">
                 <Link
                   to={`/escalations/${escalation.escalation_id}/edit`}
                   className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-anthropic-dark hover:bg-black w-full focus:outline-none transition-colors"
                 >
                   Resolve Escalation &rarr;
                 </Link>
              </div>
            </div>
          ))}

          {escalations.filter(e => e.status.toLowerCase() === 'pending').length === 0 && (
            <div className="text-center py-16 border-2 border-dashed border-cream-200 rounded-lg">
              <CheckCircle className="mx-auto h-12 w-12 text-green-400" />
              <h3 className="mt-2 text-sm font-medium text-anthropic-dark">All Caught Up</h3>
              <p className="mt-1 text-sm text-anthropic-gray">There are no pending escalations.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
