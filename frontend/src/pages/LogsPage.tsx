import { useState, useEffect } from 'react';
import { Loader2, Activity, Wrench, AlertTriangle, Search, Filter, TrendingUp } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

interface TokenLog {
  log_id: string;
  client_phone: string | null;
  session_id: string;
  node_name: string;
  model_name: string;
  tokens_in: number;
  tokens_out: number;
  latency_ms: number;
  cost_usd: number;
  created_at: string;
}

interface ToolLog {
  log_id: string;
  client_phone: string | null;
  session_id: string;
  tool_name: string;
  success: boolean;
  error_message: string | null;
  execution_time_ms: number;
  created_at: string;
}

interface ErrorLog {
  error_id: string;
  client_phone: string | null;
  thread_id: string;
  node_name: string;
  incoming_message: string;
  error_type: string;
  error_message: string;
  traceback: string;
  retry_count: number;
  retry_status: string;
  created_at: string;
}

export default function LogsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'tokens' | 'tools' | 'errors'>('tokens');
  const [tokenLogs, setTokenLogs] = useState<TokenLog[]>([]);
  const [toolLogs, setToolLogs] = useState<ToolLog[]>([]);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterClient, setFilterClient] = useState('');

  useEffect(() => {
    if (user?.role === 'owner') {
      fetchLogs();
    }
  }, [activeTab, user]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let endpoint = '/logs';
      switch (activeTab) {
        case 'tokens':
          endpoint += '/tokens';
          break;
        case 'tools':
          endpoint += '/tools';
          break;
        case 'errors':
          endpoint += '/errors';
          break;
      }
      
      const response = await api.get(endpoint);
      const data = response.data || [];
      
      if (activeTab === 'tokens') {
        setTokenLogs(data);
      } else if (activeTab === 'tools') {
        setToolLogs(data);
      } else {
        setErrorLogs(data);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const filteredTokenLogs = tokenLogs.filter(log => 
    (!searchQuery || log.node_name.toLowerCase().includes(searchQuery.toLowerCase()) || log.model_name.toLowerCase().includes(searchQuery.toLowerCase())) &&
    (!filterClient || log.client_phone === filterClient)
  );

  const filteredToolLogs = toolLogs.filter(log => 
    (!searchQuery || log.tool_name.toLowerCase().includes(searchQuery.toLowerCase())) &&
    (!filterClient || log.client_phone === filterClient)
  );

  const filteredErrorLogs = errorLogs.filter(log => 
    (!searchQuery || log.error_type.toLowerCase().includes(searchQuery.toLowerCase()) || log.node_name.toLowerCase().includes(searchQuery.toLowerCase())) &&
    (!filterClient || log.client_phone === filterClient)
  );

  const getTokenStats = () => {
    const totalTokens = filteredTokenLogs.reduce((sum, log) => sum + log.tokens_in + log.tokens_out, 0);
    const totalCost = filteredTokenLogs.reduce((sum, log) => sum + log.cost_usd, 0);
    const avgLatency = filteredTokenLogs.length > 0 
      ? filteredTokenLogs.reduce((sum, log) => sum + log.latency_ms, 0) / filteredTokenLogs.length 
      : 0;
    return { totalTokens, totalCost, avgLatency };
  };

  const getToolStats = () => {
    const total = filteredToolLogs.length;
    const successful = filteredToolLogs.filter(log => log.success).length;
    const successRate = total > 0 ? (successful / total) * 100 : 0;
    return { total, successful, successRate };
  };

  if (user?.role !== 'owner') {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-red-800 font-medium">Access Denied</h3>
          <p className="text-red-600 mt-1">Only owners can view system logs.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8 pb-5 border-b border-cream-200">
        <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">System Logs</h1>
        <p className="mt-1 text-sm text-anthropic-gray">
          Monitor AI agent performance, token usage, and system errors.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-cream-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('tokens')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tokens'
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-anthropic-gray hover:text-anthropic-dark'
            }`}
          >
            <Activity className="h-4 w-4 inline mr-2" />
            Token Logs
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tools'
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-anthropic-gray hover:text-anthropic-dark'
            }`}
          >
            <Wrench className="h-4 w-4 inline mr-2" />
            Tool Executions
          </button>
          <button
            onClick={() => setActiveTab('errors')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'errors'
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-anthropic-gray hover:text-anthropic-dark'
            }`}
          >
            <AlertTriangle className="h-4 w-4 inline mr-2" />
            Error Logs
          </button>
        </nav>
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-anthropic-light" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-cream-200 rounded-md leading-5 bg-white placeholder-anthropic-light focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
            placeholder={`Search ${activeTab}...`}
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Filter className="h-4 w-4 text-anthropic-light" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-cream-200 rounded-md leading-5 bg-white placeholder-anthropic-light focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
            placeholder="Filter by client phone..."
            value={filterClient}
            onChange={e => setFilterClient(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <>
          {/* Token Logs */}
          {activeTab === 'tokens' && (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white border border-cream-200 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-blue-100 p-3 rounded-lg">
                      <Activity className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-anthropic-gray">Total Tokens</p>
                      <p className="text-2xl font-semibold text-anthropic-dark">{getTokenStats().totalTokens.toLocaleString()}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white border border-cream-200 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-green-100 p-3 rounded-lg">
                      <TrendingUp className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-anthropic-gray">Total Cost</p>
                      <p className="text-2xl font-semibold text-anthropic-dark">{formatCurrency(getTokenStats().totalCost)}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white border border-cream-200 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-purple-100 p-3 rounded-lg">
                      <Activity className="h-6 w-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-anthropic-gray">Avg Latency</p>
                      <p className="text-2xl font-semibold text-anthropic-dark">{(getTokenStats().avgLatency / 1000).toFixed(2)}s</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Token Logs Table */}
              <div className="bg-white border border-cream-200 rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-cream-200">
                    <thead className="bg-cream-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Client</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Node</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Model</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Tokens (In/Out)</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Latency</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Cost</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-cream-200">
                      {filteredTokenLogs.map((log) => (
                        <tr key={log.log_id} className="hover:bg-cream-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">
                            {formatTimestamp(log.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.client_phone || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.node_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.model_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.tokens_in} / {log.tokens_out}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {(log.latency_ms / 1000).toFixed(2)}s
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {formatCurrency(log.cost_usd)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {filteredTokenLogs.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-sm text-anthropic-gray">No token logs found.</p>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Tool Logs */}
          {activeTab === 'tools' && (
            <>
              {/* Tool Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white border border-cream-200 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-blue-100 p-3 rounded-lg">
                      <Wrench className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-anthropic-gray">Total Executions</p>
                      <p className="text-2xl font-semibold text-anthropic-dark">{getToolStats().total}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white border border-cream-200 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-green-100 p-3 rounded-lg">
                      <TrendingUp className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-anthropic-gray">Successful</p>
                      <p className="text-2xl font-semibold text-anthropic-dark">{getToolStats().successful}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white border border-cream-200 rounded-lg p-6 shadow-sm">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-purple-100 p-3 rounded-lg">
                      <Activity className="h-6 w-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-anthropic-gray">Success Rate</p>
                      <p className="text-2xl font-semibold text-anthropic-dark">{getToolStats().successRate.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tool Logs Table */}
              <div className="bg-white border border-cream-200 rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-cream-200">
                    <thead className="bg-cream-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Client</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Tool</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Execution Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Error</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-cream-200">
                      {filteredToolLogs.map((log) => (
                        <tr key={log.log_id} className="hover:bg-cream-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">
                            {formatTimestamp(log.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.client_phone || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.tool_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              log.success 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {log.success ? 'Success' : 'Failed'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                            {log.execution_time_ms}ms
                          </td>
                          <td className="px-6 py-4 text-sm text-anthropic-gray max-w-xs truncate">
                            {log.error_message || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {filteredToolLogs.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-sm text-anthropic-gray">No tool logs found.</p>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Error Logs */}
          {activeTab === 'errors' && (
            <div className="bg-white border border-cream-200 rounded-lg shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-cream-200">
                  <thead className="bg-cream-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Client</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Node</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Error Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Message</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Retries</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-anthropic-gray uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-cream-200">
                    {filteredErrorLogs.map((log) => (
                      <tr key={log.error_id} className="hover:bg-cream-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-gray">
                          {formatTimestamp(log.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                          {log.client_phone || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                          {log.node_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                          {log.error_type}
                        </td>
                        <td className="px-6 py-4 text-sm text-anthropic-gray max-w-xs truncate" title={log.error_message}>
                          {log.error_message}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-anthropic-dark">
                          {log.retry_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            log.retry_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            log.retry_status === 'retried' ? 'bg-blue-100 text-blue-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {log.retry_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {filteredErrorLogs.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-sm text-anthropic-gray">No error logs found.</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
