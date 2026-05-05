import { useState, useEffect } from 'react';
import { Loader2, Key, Wrench, AlertTriangle } from 'lucide-react';
import api from '../api/axios';

interface TokenLog {
  log_id: string;
  client_phone: string | null;
  node_name: string;
  model_name: string;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  created_at: string;
}

interface ToolLog {
  log_id: string;
  client_phone: string | null;
  tool_name: string;
  success: boolean;
  error_message: string | null;
  execution_time_ms: number;
  created_at: string;
}

interface ErrorLog {
  error_id: string;
  client_phone: string | null;
  node_name: string;
  error_type: string;
  error_message: string;
  created_at: string;
}

export default function SystemLogsPage() {
  const [activeTab, setActiveTab] = useState<'tokens' | 'tools' | 'errors'>('tokens');
  
  const [tokenLogs, setTokenLogs] = useState<TokenLog[]>([]);
  const [toolLogs, setToolLogs] = useState<ToolLog[]>([]);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, [activeTab]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      if (activeTab === 'tokens') {
        const res = await api.get('/logs/tokens');
        setTokenLogs(res.data);
      } else if (activeTab === 'tools') {
        const res = await api.get('/logs/tools');
        setToolLogs(res.data);
      } else if (activeTab === 'errors') {
        const res = await api.get('/logs/errors');
        setErrorLogs(res.data);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderTabs = () => (
    <div className="border-b border-cream-200 mb-6">
      <nav className="-mb-px flex space-x-8">
        <button
          onClick={() => setActiveTab('tokens')}
          className={`${
            activeTab === 'tokens'
              ? 'border-anthropic-dark text-anthropic-dark font-medium'
              : 'border-transparent text-anthropic-gray hover:text-anthropic-dark hover:border-cream-300'
          } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center`}
        >
          <Key className="mr-2 h-4 w-4" />
          Token Usage
        </button>
        <button
          onClick={() => setActiveTab('tools')}
          className={`${
            activeTab === 'tools'
              ? 'border-anthropic-dark text-anthropic-dark font-medium'
              : 'border-transparent text-anthropic-gray hover:text-anthropic-dark hover:border-cream-300'
          } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center`}
        >
          <Wrench className="mr-2 h-4 w-4" />
          Tool Executions
        </button>
        <button
          onClick={() => setActiveTab('errors')}
          className={`${
            activeTab === 'errors'
              ? 'border-anthropic-dark text-anthropic-dark font-medium'
              : 'border-transparent text-anthropic-gray hover:text-anthropic-dark hover:border-cream-300'
          } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center`}
        >
          <AlertTriangle className="mr-2 h-4 w-4" />
          System Errors
        </button>
      </nav>
    </div>
  );

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">System Logs</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Monitor API token usage, tool executions, and system failures.
          </p>
        </div>
      </div>

      {renderTabs()}

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="bg-white border border-cream-200 rounded-lg overflow-hidden shadow-sm">
          <div className="overflow-x-auto custom-scrollbar">
            <table className="min-w-full divide-y divide-cream-200">
              <thead className="bg-cream-50">
                {activeTab === 'tokens' && (
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Time</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Node / Model</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Client</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">IO Tokens</th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-anthropic-gray uppercase tracking-wider">Cost ($)</th>
                  </tr>
                )}
                {activeTab === 'tools' && (
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Time</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Tool Name</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Status</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Duration</th>
                  </tr>
                )}
                {activeTab === 'errors' && (
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Time</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Node</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Type</th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Message</th>
                  </tr>
                )}
              </thead>
              <tbody className="bg-white divide-y divide-cream-200">
                {activeTab === 'tokens' && tokenLogs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-cream-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">
                      <span className="font-semibold">{log.node_name}</span> <br/>
                      <span className="text-xs">{log.model_name}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">{log.client_phone || 'System'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">In: {log.tokens_in} / Out: {log.tokens_out}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark text-right font-medium">${Number(log.cost_usd).toFixed(4)}</td>
                  </tr>
                ))}

                {activeTab === 'tools' && toolLogs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-cream-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-anthropic-dark">{log.tool_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full uppercase tracking-wide ${log.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {log.success ? 'Success' : 'Failed'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">{log.execution_time_ms}ms</td>
                  </tr>
                ))}

                {activeTab === 'errors' && errorLogs.map((log) => (
                  <tr key={log.error_id} className="hover:bg-cream-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">{log.node_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full uppercase bg-red-100 text-red-800 tracking-wide">
                        {log.error_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-anthropic-dark max-w-xs truncate" title={log.error_message}>
                      {log.error_message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {(activeTab === 'tokens' && tokenLogs.length === 0) || 
             (activeTab === 'tools' && toolLogs.length === 0) || 
             (activeTab === 'errors' && errorLogs.length === 0) ? (
              <div className="text-center py-12">
                <p className="text-sm text-anthropic-gray">No logs recorded currently.</p>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
