import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, UserPlus } from 'lucide-react';
import api from '../api/axios';

export default function AgentEditPage() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirm_password: '',
    role: 'agent'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirm_password) {
        setError("Passwords do not match");
        return;
    }
    
    setSaving(true);
    setError(null);
    try {
      await api.post('/auth/signup/', formData);
      navigate('/agents');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create agent');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto h-full text-left">
      <div className="mb-6">
        <Link to="/agents" className="inline-flex items-center text-sm font-medium text-anthropic-gray hover:text-anthropic-dark transition-colors">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Agents
        </Link>
      </div>

      <div className="bg-white border border-cream-200 shadow-sm rounded-lg overflow-hidden">
         <div className="px-8 py-6 border-b border-cream-200 text-left">
           <h2 className="text-xl font-semibold text-anthropic-dark">
             Add New Agent Account
           </h2>
           <p className="text-sm text-anthropic-light mt-1">This will create a new user profile that can access the dashboard internal tooling.</p>
         </div>

         {error && (
            <div className="p-4 bg-red-50 border-b border-red-100 text-red-600 text-sm">
               {error}
            </div>
         )}
         
         <form onSubmit={handleSubmit} className="p-8 space-y-6">
            <div className="grid grid-cols-1 gap-6">
               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Full Name</label>
                  <input required name="name" value={formData.name} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Email Address</label>
                  <input required type="email" name="email" value={formData.email} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Set Role</label>
                  <select name="role" value={formData.role} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2 bg-white">
                     <option value="agent">Agent (Limited Rights)</option>
                     <option value="owner">Owner (Admin Rights)</option>
                  </select>
               </div>

               <div className="border-t border-cream-200 mt-2 pt-6">
                   <h3 className="text-sm font-semibold text-anthropic-dark mb-4">Security</h3>
                   <div className="space-y-4">
                       <div>
                          <label className="block text-sm font-medium text-anthropic-dark mb-2">Temporary Password</label>
                          <input required type="password" name="password" minLength={8} value={formData.password} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
                       </div>
                       <div>
                          <label className="block text-sm font-medium text-anthropic-dark mb-2">Confirm Password</label>
                          <input required type="password" minLength={8} name="confirm_password" value={formData.confirm_password} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
                       </div>
                   </div>
               </div>
            </div>

            <div className="pt-6 border-t border-cream-200 flex justify-end gap-3 mt-8">
               <button type="button" onClick={() => navigate('/agents')} className="px-4 py-2 border border-cream-300 shadow-sm text-sm font-medium rounded-md text-anthropic-dark bg-white hover:bg-cream-50 focus:outline-none transition-colors">
                 Cancel
               </button>
               <button type="submit" disabled={saving} className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-anthropic-dark hover:bg-anthropic-gray focus:outline-none transition-colors disabled:opacity-50">
                 {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <UserPlus className="h-4 w-4 mr-2" />}
                 Create Account
               </button>
            </div>
         </form>
      </div>
    </div>
  );
}
