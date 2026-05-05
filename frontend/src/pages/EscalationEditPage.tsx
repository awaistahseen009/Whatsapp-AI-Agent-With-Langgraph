import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
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

export default function EscalationEditPage() {
  const { id } = useParams<{ id: string }>();
  const [escalation, setEscalation] = useState<Escalation | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchEscalation();
  }, [id]);

  const fetchEscalation = async () => {
    try {
      const response = await api.get('/escalations');
      const found = response.data.find((e: Escalation) => e.escalation_id === id);
      if (found) {
        setEscalation(found);
      } else {
        navigate('/escalations');
      }
    } catch (error) {
      console.error('Failed to fetch escalation:', error);
      navigate('/escalations');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (newStatus: 'resolved' | 'dismissed') => {
    if (!escalation) return;
    try {
      await api.put(`/escalations/${escalation.escalation_id}/resolve`, { status: newStatus, resolution_notes: 'Handled via dashboard edit page' });
      navigate('/escalations');
    } catch (error) {
      console.error('Failed to resolve escalation:', error);
      alert("Only an admin/owner can resolve escalations");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-24">
        <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
      </div>
    );
  }

  if (!escalation) return null;

  return (
    <div className="p-8 max-w-4xl mx-auto flex flex-col h-full">
      <Link to="/escalations" className="inline-flex items-center text-sm font-medium text-anthropic-gray hover:text-anthropic-dark transition-colors mb-6">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Escalations
      </Link>
      
      <div className="bg-white border text-left border-red-200 rounded-lg shadow-sm p-8 relative overflow-hidden flex-1">
        <div className="absolute top-0 left-0 w-2 h-full bg-red-400"></div>
        
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-4">
            <div className="bg-red-50 p-3 rounded-full">
              <AlertTriangle className="h-7 w-7 text-red-500" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-anthropic-dark">Escalation Handover</h2>
              <p className="text-sm font-medium text-anthropic-gray mt-1">Client: {escalation.client_phone}</p>
            </div>
          </div>
          <div className="text-sm text-anthropic-light bg-cream-50 px-3 py-1 rounded-md border border-cream-200">
            Triggered: {new Date(escalation.triggered_at).toLocaleString()}
          </div>
        </div>

        <div className="space-y-6">
          <div>
             <h3 className="text-sm font-semibold text-anthropic-dark mb-2">AI Reason for handover:</h3>
             <div className="bg-red-50 text-red-900 p-4 rounded-md border border-red-100">
               {escalation.reason}
             </div>
          </div>

          <div>
             <h3 className="text-sm font-semibold text-anthropic-dark mb-2">Conversation Context:</h3>
             <div className="bg-cream-50 p-4 rounded-md border border-cream-200 text-anthropic-dark italic leading-relaxed">
               "{escalation.conversation_summary}"
             </div>
          </div>

          <div>
             <h3 className="text-sm font-semibold text-anthropic-dark mb-2">Last Client Message:</h3>
             <div className="bg-white p-4 rounded-md border border-cream-200 text-anthropic-dark overflow-x-auto font-mono text-sm shadow-inner">
               "{escalation.last_client_message}"
             </div>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-cream-200 flex items-center justify-between">
          <button
            onClick={() => window.open(`https://wa.me/${escalation.client_phone.replace(/\+/g, '')}`, '_blank')}
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-anthropic-dark hover:bg-black focus:outline-none transition-colors"
          >
            Contact Client on WhatsApp &rarr;
          </button>
          
          <div className="flex gap-3">
              <button
                onClick={() => handleResolve('resolved')}
                className="inline-flex items-center justify-center px-6 py-3 border border-cream-200 text-sm font-medium rounded-md text-green-700 bg-white hover:bg-green-50 transition-colors shadow-sm"
              >
                <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
                Mark Resolved
              </button>
              <button
                onClick={() => handleResolve('dismissed')}
                className="inline-flex items-center justify-center px-6 py-3 border border-cream-200 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 transition-colors shadow-sm"
              >
                <XCircle className="h-5 w-5 mr-2" />
                Dismiss
              </button>
          </div>
        </div>
      </div>
    </div>
  );
}
