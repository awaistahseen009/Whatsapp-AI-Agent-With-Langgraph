import { Activity, Users, Home, TrendingUp } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function DashboardOverview() {
  const { user } = useAuth();
  
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8 pb-5 border-b border-cream-200">
        <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Overview</h1>
        <p className="mt-1 text-sm text-anthropic-gray">
          Welcome back to your Riley Estate dashboard, {user?.role.toUpperCase()}.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {[
          { name: 'Active Clients', stat: '142', icon: Users, change: '+12%', color: 'text-anthropic-dark' },
          { name: 'Properties Managed', stat: '45', icon: Home, change: '+4.5%', color: 'text-anthropic-dark' },
          { name: 'Average Response Time', stat: '1.2s', icon: Activity, change: '-0.3s', color: 'text-green-600' },
          { name: 'Conversion Rate', stat: '24.5%', icon: TrendingUp, change: '+2.1%', color: 'text-anthropic-dark' },
        ].map((item) => (
          <div key={item.name} className="bg-white overflow-hidden shadow-sm border border-cream-200 rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <item.icon className="h-6 w-6 text-anthropic-light" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-anthropic-gray truncate">{item.name}</dt>
                    <dd>
                      <div className="text-lg font-medium text-anthropic-dark">{item.stat}</div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-cream-50 px-5 py-3">
              <div className="text-sm">
                <span className={`font-medium ${item.color}`}>
                  {item.change}
                </span>
                <span className="text-anthropic-light ml-2">from last month</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Pending Tasks area placeholder */}
      <h2 className="text-lg font-medium tracking-tight text-anthropic-dark mt-10 mb-4">Recent Escalations</h2>
      <div className="bg-white border border-cream-200 rounded-lg shadow-sm">
        <div className="p-6 text-center text-anthropic-gray text-sm">
          No escalations require your attention today. Good job!
        </div>
      </div>
    </div>
  );
}
