import { useState, useEffect } from 'react';
import { Shield, Loader2, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';

export default function SecuritySetupModal() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [securityQuestion, setSecurityQuestion] = useState('');
  const [securityAnswer, setSecurityAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showAnswer, setShowAnswer] = useState(false);

  useEffect(() => {
    const checkSecurityStatus = async () => {
       try {
         if (user && !sessionStorage.getItem('security_skipped') && !sessionStorage.getItem('security_setup_done')) {
            const response = await api.get('/auth/has-security-question/');
            if (!response.data.has_security_question) {
               setIsOpen(true);
            } else {
               sessionStorage.setItem('security_setup_done', 'true');
            }
         }
       } catch (e) {
         // ignore
       }
    };
    // small timeout to ensure token is loaded
    setTimeout(checkSecurityStatus, 500);
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!securityQuestion || !securityAnswer) {
      setError('Both fields are required.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      await api.post('/auth/set-question/', {
        question: securityQuestion,
        answer: securityAnswer
      });
      setIsOpen(false);
      sessionStorage.setItem('security_setup_done', 'true');
      sessionStorage.removeItem('security_skipped');
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to setup security question. You can try later in your Profile.');
    } finally {
      setLoading(false);
    }
  };

  const skipForNow = () => {
    sessionStorage.setItem('security_skipped', 'true');
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-anthropic-dark bg-opacity-75 transition-opacity backdrop-blur-sm" aria-hidden="true"></div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6 opacity-100 scale-100 translate-y-0">
          <div>
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-cream-100">
              <Shield className="h-6 w-6 text-anthropic-dark" aria-hidden="true" />
            </div>
            <div className="mt-3 text-center sm:mt-5">
              <h3 className="text-lg leading-6 font-semibold text-anthropic-dark" id="modal-title">
                Secure Your Account
              </h3>
              <div className="mt-2">
                <p className="text-sm text-anthropic-gray">
                  It looks like you haven't set up a security question yet. This is critical for recovering your account if you lose your password.
                </p>
              </div>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="mt-5 sm:mt-6 space-y-4">
            {error && (
              <div className="p-3 bg-red-50 text-red-800 text-sm rounded-md flex items-center gap-2 border border-red-100">
                <AlertTriangle className="h-4 w-4" />
                {error}
              </div>
            )}
            
            <div className="text-left">
              <label className="block text-sm font-medium text-anthropic-dark mb-1">Security Question</label>
              <input
                type="text"
                required
                placeholder="E.g., What was the name of your first pet?"
                value={securityQuestion}
                onChange={e => setSecurityQuestion(e.target.value)}
                className="w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark"
              />
            </div>
            
            <div className="text-left relative">
              <label className="block text-sm font-medium text-anthropic-dark mb-1">Secret Answer</label>
              <div className="relative">
                <input
                  type={showAnswer ? "text" : "password"}
                  required
                  placeholder="Make it memorable"
                  value={securityAnswer}
                  onChange={e => setSecurityAnswer(e.target.value)}
                  className="w-full px-3 py-2 pr-10 border border-cream-200 rounded-md shadow-sm focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark"
                />
                <button
                  type="button"
                  onClick={() => setShowAnswer(!showAnswer)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-anthropic-gray hover:text-anthropic-dark"
                >
                  {showAnswer ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-anthropic-dark text-base font-medium text-white hover:bg-black focus:outline-none sm:col-start-2 sm:text-sm transition-colors disabled:opacity-50 items-center"
              >
                {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                Save & Continue
              </button>
              <button
                type="button"
                onClick={skipForNow}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-cream-200 shadow-sm px-4 py-2 bg-white text-base font-medium text-anthropic-dark hover:bg-cream-50 focus:outline-none sm:mt-0 sm:col-start-1 sm:text-sm transition-colors"
              >
                Skip for now
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
