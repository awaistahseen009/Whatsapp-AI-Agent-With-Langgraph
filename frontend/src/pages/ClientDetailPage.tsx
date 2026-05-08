import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, User, Phone, MapPin, Mail, DollarSign, Clock, CheckCircle, Home, Briefcase } from 'lucide-react';
import api from '../api/axios';

interface Client {
  phone_num: string;
  name: string;
  email: string | null;
  city: string;
  timezone: string;
  status: string;
  intent: string | null;
  budget_min: number | null;
  budget_max: number | null;
  preferred_locations?: string[];
  property_type_pref?: string[];
  loan_preapproved?: boolean;
  onboarding_complete?: boolean;
  created_at?: string;
  last_active_at?: string;
}

const formatTimezone = (timezone: string) => {
  // Convert timezone to a more readable format
  const timezoneMap: { [key: string]: string } = {
    'America/New_York': 'Eastern Time (ET)',
    'America/Chicago': 'Central Time (CT)',
    'America/Denver': 'Mountain Time (MT)',
    'America/Los_Angeles': 'Pacific Time (PT)',
    'Europe/London': 'Greenwich Mean Time (GMT)',
    'Europe/Paris': 'Central European Time (CET)',
    'Asia/Tokyo': 'Japan Standard Time (JST)',
    'Asia/Shanghai': 'China Standard Time (CST)',
    'Australia/Sydney': 'Australian Eastern Time (AET)'
  };
  
  return timezoneMap[timezone] || timezone;
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchClient();
  }, [id]);

  const fetchClient = async () => {
    try {
      // Endpoint depends on if there's a GET /clients/:id or if we fetch all.
      // Easiest is to fetch all and filter if no specific GET exists.
      const response = await api.get('/clients/');
      const found = response.data.find((c: Client) => c.phone_num.replace('+', '') === id);
      if (found) {
        setClient(found);
      } else {
        navigate('/clients');
      }
    } catch (error) {
      console.error('Failed to fetch client:', error);
      navigate('/clients');
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

  if (!client) return null;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <Link to="/clients" className="inline-flex items-center text-sm font-medium text-anthropic-gray hover:text-anthropic-dark mb-6 transition-colors">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Clients
      </Link>

      <div className="bg-white border border-cream-200 rounded-lg shadow-sm overflow-hidden">
        <div className="bg-cream-50 px-6 py-5 border-b border-cream-200 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-white p-3 rounded-full border border-cream-200 shadow-sm">
              <User className="h-6 w-6 text-anthropic-dark" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-anthropic-dark">{client.name}</h2>
              <p className="text-sm text-anthropic-gray">Client Profile</p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
            {client.status}
          </span>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Contact Information</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-anthropic-gray" />
                  <span className="text-sm font-medium text-anthropic-dark">{client.phone_num}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-anthropic-gray" />
                  <span className="text-sm text-anthropic-dark">{client.email || 'No email provided'}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Location</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <MapPin className="h-4 w-4 text-anthropic-gray" />
                  <span className="text-sm text-anthropic-dark">{client.city}</span>
                </div>
                <div className="flex items-center gap-3 ml-7">
                  <Clock className="h-3 w-3 text-anthropic-gray" />
                  <span className="text-xs text-anthropic-gray">{formatTimezone(client.timezone)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
             <div>
              <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">AI Discovery Status</h3>
              <div className="bg-cream-50 p-4 rounded-md border border-cream-100">
                <p className="text-xs text-anthropic-gray mb-1">Detected Intent:</p>
                <p className="text-sm font-semibold text-anthropic-dark capitalize">{client.intent || 'Needs further profiling'}</p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Budget Range</h3>
              <div className="flex items-center gap-3">
                <div className="bg-green-50 p-2 rounded text-green-700">
                  <DollarSign className="h-5 w-5" />
                </div>
                <div>
                  {client.budget_min && client.budget_max ? (
                    <span className="text-sm font-semibold text-anthropic-dark">
                       ${client.budget_min.toLocaleString()} – ${client.budget_max.toLocaleString()}
                    </span>
                  ) : (
                    <span className="text-sm text-anthropic-gray italic">No budget discussed yet</span>
                  )}
                </div>
              </div>
            </div>

            {client.preferred_locations && client.preferred_locations.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Preferred Locations</h3>
                <div className="flex flex-wrap gap-2">
                  {client.preferred_locations.map((location, index) => (
                    <span key={index} className="inline-flex items-center px-2 py-1 bg-cream-100 text-anthropic-dark text-xs rounded-full">
                      <MapPin className="h-3 w-3 mr-1" />
                      {location}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {client.property_type_pref && client.property_type_pref.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Property Types</h3>
                <div className="flex flex-wrap gap-2">
                  {client.property_type_pref.map((propertyType, index) => (
                    <span key={index} className="inline-flex items-center px-2 py-1 bg-blue-50 text-accent-blue text-xs rounded-full">
                      <Home className="h-3 w-3 mr-1" />
                      {propertyType}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Financial Status</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  {client.loan_preapproved ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <Briefcase className="h-4 w-4 text-anthropic-gray" />
                  )}
                  <span className="text-sm text-anthropic-dark">
                    {client.loan_preapproved ? 'Loan Pre-approved' : 'Loan Status Unknown'}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                    client.onboarding_complete 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {client.onboarding_complete ? 'Onboarding Complete' : 'Onboarding In Progress'}
                  </span>
                </div>
              </div>
            </div>

            {(client.created_at || client.last_active_at) && (
              <div>
                <h3 className="text-sm font-medium text-anthropic-light uppercase tracking-wider mb-3">Activity Timeline</h3>
                <div className="space-y-2 text-xs">
                  {client.created_at && (
                    <div className="flex justify-between">
                      <span className="text-anthropic-gray">First Contact:</span>
                      <span className="text-anthropic-dark">{formatDate(client.created_at)}</span>
                    </div>
                  )}
                  {client.last_active_at && (
                    <div className="flex justify-between">
                      <span className="text-anthropic-gray">Last Active:</span>
                      <span className="text-anthropic-dark">{formatDate(client.last_active_at)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
