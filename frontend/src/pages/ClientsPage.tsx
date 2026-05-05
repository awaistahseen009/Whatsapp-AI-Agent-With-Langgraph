import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Loader2 } from 'lucide-react';
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
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusStyle = (status: string) => {
    switch(status.toLowerCase()) {
      case 'new': return 'bg-blue-100 text-blue-800';
      case 'serious': return 'bg-yellow-100 text-yellow-800';
      case 'converted': return 'bg-green-100 text-green-800';
      case 'lost': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Clients</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Manage leads generated via the WhatsApp AI.
          </p>
        </div>
      </div>

      <div className="mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-anthropic-light" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-cream-200 rounded-md leading-5 bg-white placeholder-anthropic-light focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
            placeholder="Search clients..."
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="bg-white border border-cream-200 rounded-lg overflow-hidden shadow-sm">
          <div className="overflow-x-auto custom-scrollbar">
            <table className="min-w-full divide-y divide-cream-200">
              <thead className="bg-cream-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Client</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Contact</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Location</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Status</th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">View Details</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-cream-200">
                {clients.map((client) => (
                  <tr key={client.phone_num} className="hover:bg-cream-50 transition-colors group">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-anthropic-dark">{client.name}</div>
                          <div className="text-sm text-anthropic-light">Intent: {client.intent || 'Unknown'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-anthropic-dark">{client.phone_num}</div>
                      <div className="text-sm text-anthropic-light">{client.email || 'No email provided'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-anthropic-dark">{client.city}</div>
                      <div className="text-sm text-anthropic-light">{client.timezone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full uppercase tracking-wide ${getStatusStyle(client.status)}`}>
                        {client.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link 
                        to={`/clients/${client.phone_num.replace('+', '')}`} 
                        className="inline-flex items-center px-3 py-1.5 border border-cream-200 shadow-sm text-xs font-medium rounded-md text-anthropic-dark bg-white hover:bg-cream-100 focus:outline-none transition-colors"
                      >
                        Details &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {clients.length === 0 && (
              <div className="text-center py-12">
                <p className="text-sm text-anthropic-gray">No clients discovered yet.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
