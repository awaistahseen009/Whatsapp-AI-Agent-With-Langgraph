import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Users, 
  MessageSquare, 
  Calendar, 
  AlertTriangle,
  Activity,
  LogOut,
  Menu,
  X,
  User,
  FileText
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import SecuritySetupModal from '../components/SecuritySetupModal';

import { Shield } from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', icon: Activity, path: '/' },
  { name: 'Clients', icon: Users, path: '/clients' },
  { name: 'Chat Sessions', icon: MessageSquare, path: '/sessions' },
  { name: 'Properties', icon: Building2, path: '/properties' },
  { name: 'Meetings', icon: Calendar, path: '/meetings' },
  { name: 'Escalations', icon: AlertTriangle, path: '/escalations' },
  { name: 'Agents', icon: Shield, path: '/agents', ownerOnly: true },
  { name: 'System Logs', icon: FileText, path: '/system-logs', ownerOnly: true },
  { name: 'Profile', icon: User, path: '/profile' },
];

export default function DashboardLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-cream-50 flex">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-40 lg:hidden" 
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-cream-100 border-r border-cream-200 
        transform transition-transform duration-200 ease-in-out
        lg:relative lg:translate-x-0
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-full flex flex-col pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-6">
            <h1 className="text-xl font-semibold tracking-tighter text-anthropic-dark">Riley Estate</h1>
          </div>
          
          <nav className="mt-8 flex-1 px-4 space-y-1">
            {NAV_ITEMS.filter(item => !item.ownerOnly || user?.role === 'owner').map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) => `
                  group flex items-center px-2 py-2.5 text-sm font-medium rounded-md transition-colors
                  ${isActive 
                    ? 'bg-white text-anthropic-dark shadow-sm border border-cream-200' 
                    : 'text-anthropic-gray hover:bg-cream-200 hover:text-anthropic-dark'
                  }
                `}
                end={item.path === '/'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <item.icon className="mr-3 flex-shrink-0 h-4 w-4" aria-hidden="true" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Bottom user section */}
          <div className="flex-shrink-0 border-t border-cream-200 p-4">
            <div className="flex items-center">
              <div className="ml-3 w-full">
                <p className="text-sm font-medium text-anthropic-dark truncate">{user?.email}</p>
                <p className="text-xs font-medium text-anthropic-light uppercase mt-0.5">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="mt-4 w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-anthropic-dark bg-white border border-cream-200 hover:bg-cream-50 rounded-md transition-colors"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <div className="lg:hidden border-b border-cream-200 bg-white flex items-center justify-between p-4 flex-shrink-0">
          <h1 className="text-lg font-semibold tracking-tighter text-anthropic-dark">Riley Estate</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="text-anthropic-gray hover:text-anthropic-dark p-2"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        <main className="flex-1 relative overflow-y-auto focus:outline-none custom-scrollbar">
          <Outlet />
        </main>
      </div>

      <SecuritySetupModal />
    </div>
  );
}
