import { useState } from 'react';
import { Shield, Key, Save, Loader2, User as UserIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';

export default function ProfilePage() {
  const { user } = useAuth();
  
  // Password State
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loadingPwd, setLoadingPwd] = useState(false);
  
  // Security State
  const [securityQuestion, setSecurityQuestion] = useState('');
  const [securityAnswer, setSecurityAnswer] = useState('');
  const [loadingSec, setLoadingSec] = useState(false);

  const [message, setMessage] = useState<{type: 'success'|'error', text: string} | null>(null);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    
    setLoadingPwd(true);
    try {
      await api.put('/auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      setMessage({ type: 'success', text: 'Password successfully updated.' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to update password.' });
    } finally {
      setLoadingPwd(false);
    }
  };

  const handleSecuritySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!securityQuestion || !securityAnswer) {
      return;
    }
    
    setLoadingSec(true);
    try {
      await api.post('/auth/set-question/', {
        question: securityQuestion,
        answer: securityAnswer
      });
      setMessage({ type: 'success', text: 'Security question successfully updated.' });
      setSecurityQuestion('');
      setSecurityAnswer('');
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to update security question.' });
    } finally {
      setLoadingSec(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8 pb-5 border-b border-cream-200">
        <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Your Profile</h1>
        <p className="mt-1 text-sm text-anthropic-gray">
          Manage your account settings and security preferences.
        </p>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-md border ${message.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          <p className="text-sm font-medium">{message.text}</p>
        </div>
      )}

      <div className="space-y-6">
        
        {/* Profile Card */}
        <div className="bg-white border border-cream-200 rounded-lg shadow-sm">
          <div className="px-6 py-5 border-b border-cream-200 flex items-center gap-4 bg-cream-50">
            <div className="bg-white p-3 rounded-full shadow-sm border border-cream-200">
               <UserIcon className="h-6 w-6 text-anthropic-dark" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-anthropic-dark">Account Details</h2>
              <p className="text-sm text-anthropic-gray">{user?.email}</p>
            </div>
          </div>
          <div className="p-6">
             <div className="grid grid-cols-2 gap-4">
               <div>
                  <p className="text-xs text-anthropic-light uppercase tracking-wide font-semibold mb-1">Email prefix</p>
                  <p className="text-sm font-medium text-anthropic-dark">{user?.email?.split('@')[0]}</p>
               </div>
               <div>
                  <p className="text-xs text-anthropic-light uppercase tracking-wide font-semibold mb-1">Role</p>
                  <p className="text-sm font-medium text-anthropic-dark capitalize bg-cream-100 inline-block px-2 py-0.5 rounded">{user?.role}</p>
               </div>
               <div className="col-span-2">
                  <p className="text-xs text-anthropic-light uppercase tracking-wide font-semibold mb-1">Email</p>
                  <p className="text-sm font-medium text-anthropic-dark">{user?.email}</p>
               </div>
             </div>
          </div>
        </div>

        {/* Change Password */}
        <div className="bg-white border border-cream-200 rounded-lg shadow-sm">
           <div className="px-6 py-4 border-b border-cream-200 flex items-center gap-3 bg-cream-50">
             <Key className="h-5 w-5 text-anthropic-dark" />
             <h2 className="text-lg font-semibold text-anthropic-dark">Change Password</h2>
           </div>
           <form onSubmit={handlePasswordSubmit} className="p-6 space-y-4 max-w-md">
             <div>
               <label className="block text-sm font-medium text-anthropic-dark mb-1">Current Password</label>
               <input
                 type="password"
                 required
                 value={oldPassword}
                 onChange={e => setOldPassword(e.target.value)}
                 className="w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark sm:text-sm"
               />
             </div>
             <div>
               <label className="block text-sm font-medium text-anthropic-dark mb-1">New Password</label>
               <input
                 type="password"
                 required
                 value={newPassword}
                 onChange={e => setNewPassword(e.target.value)}
                 className="w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark sm:text-sm"
               />
             </div>
             <div>
               <label className="block text-sm font-medium text-anthropic-dark mb-1">Confirm New Password</label>
               <input
                 type="password"
                 required
                 value={confirmPassword}
                 onChange={e => setConfirmPassword(e.target.value)}
                 className="w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark sm:text-sm"
               />
             </div>
             <button
               type="submit"
               disabled={loadingPwd}
               className="mt-2 inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-anthropic-dark hover:bg-black focus:outline-none transition-colors disabled:opacity-50"
             >
               {loadingPwd ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
               Update Password
             </button>
           </form>
        </div>

        {/* Security Question */}
        <div className="bg-white border border-cream-200 rounded-lg shadow-sm">
           <div className="px-6 py-4 border-b border-cream-200 flex items-center gap-3 bg-cream-50">
             <Shield className="h-5 w-5 text-anthropic-dark" />
             <h2 className="text-lg font-semibold text-anthropic-dark">Security Recovery</h2>
           </div>
           <form onSubmit={handleSecuritySubmit} className="p-6 space-y-4 max-w-md">
             <p className="text-sm text-anthropic-gray mb-4">
               Set a security question so you can recover your account if you forget your password.
             </p>
             <div>
               <label className="block text-sm font-medium text-anthropic-dark mb-1">Question</label>
               <input
                 type="text"
                 required
                 placeholder="E.g., What was the name of your first pet?"
                 value={securityQuestion}
                 onChange={e => setSecurityQuestion(e.target.value)}
                 className="w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark sm:text-sm"
               />
             </div>
             <div>
               <label className="block text-sm font-medium text-anthropic-dark mb-1">Answer</label>
               <input
                 type="password"
                 required
                 placeholder="Your secret answer"
                 value={securityAnswer}
                 onChange={e => setSecurityAnswer(e.target.value)}
                 className="w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark sm:text-sm"
               />
             </div>
             <button
               type="submit"
               disabled={loadingSec}
               className="mt-2 inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-anthropic-dark hover:bg-black focus:outline-none transition-colors disabled:opacity-50"
             >
               {loadingSec ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Shield className="h-4 w-4 mr-2" />}
               Save Security Setup
             </button>
           </form>
        </div>

      </div>
    </div>
  );
}
