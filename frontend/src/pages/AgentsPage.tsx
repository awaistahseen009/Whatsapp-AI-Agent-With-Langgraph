import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, UserPlus, Shield, User as UserIcon } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

interface Agent {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await api.get('/auth/agents');
      setAgents(response.data);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Agents & Users</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Manage your internal team members and administration roles.
          </p>
        </div>
        {user?.role === 'owner' && (
          <Link 
            to="/agents/new"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-anthropic-dark hover:bg-anthropic-gray focus:outline-none transition-colors mt-4 sm:mt-0"
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Add Agent
          </Link>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="bg-white border text-left border-cream-200 rounded-lg shadow-sm overflow-hidden">
           <table className="min-w-full divide-y divide-cream-200">
             <thead className="bg-cream-50">
               <tr>
                 <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-anthropic-dark uppercase tracking-wider">Name / ID</th>
                 <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-anthropic-dark uppercase tracking-wider">Email</th>
                 <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-anthropic-dark uppercase tracking-wider">Role</th>
                 <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-anthropic-dark uppercase tracking-wider">Created</th>
               </tr>
             </thead>
             <tbody className="bg-white divide-y divide-cream-200">
               {agents.map((agent) => (
                 <tr key={agent.id} className="hover:bg-cream-50 transition-colors">
                   <td className="px-6 py-4 whitespace-nowrap">
                     <div className="flex items-center">
                       <div className="flex-shrink-0 h-10 w-10 bg-cream-100 rounded-full flex items-center justify-center">
                          {agent.role === 'owner' ? <Shield className="h-5 w-5 text-accent-blue" /> : <UserIcon className="h-5 w-5 text-anthropic-dark" />}
                       </div>
                       <div className="ml-4">
                         <div className="text-sm font-medium text-anthropic-dark">{agent.name}</div>
                         <div className="text-xs text-anthropic-gray font-mono">{agent.id.substring(0, 8)}...</div>
                       </div>
                     </div>
                   </td>
                   <td className="px-6 py-4 whitespace-nowrap">
                     <div className="text-sm text-anthropic-gray">{agent.email}</div>
                   </td>
                   <td className="px-6 py-4 whitespace-nowrap">
                     <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${agent.role === 'owner' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                       {agent.role}
                     </span>
                   </td>
                   <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">
                     {new Date(agent.created_at).toLocaleDateString()}
                   </td>
                 </tr>
               ))}
             </tbody>
           </table>
           
           {agents.length === 0 && (
             <div className="text-center py-12">
               <p className="text-sm text-anthropic-gray">No agents found.</p>
             </div>
           )}
        </div>
      )}
    </div>
  );
}
