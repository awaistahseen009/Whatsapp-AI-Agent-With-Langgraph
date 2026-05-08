import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import { Loader2, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorVar, setErrorVar] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorVar('');

    try {
      const response = await api.post('/auth/login/', { email, password });
      const { access_token, refresh_token, user } = response.data;
      
      login(access_token, refresh_token, user);
      navigate('/');
    } catch (err: any) {
      if (err.response?.status === 403 || err.response?.status === 204) {
        setErrorVar(err.response.data.detail || 'Invalid email or password');
      } else {
        setErrorVar('System error. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-semibold tracking-tight text-anthropic-dark">
          Sign in to Riley Estate
        </h2>
        <p className="mt-2 text-center text-sm text-anthropic-light">
          Welcome back. Please enter your agent or admin credentials.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm border border-cream-200 sm:rounded-xl sm:px-10">
          <form className="space-y-6" onSubmit={handleLogin}>
            {errorVar && (
              <div className="p-3 rounded-md bg-red-50 border border-red-100 flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                <p className="text-sm font-medium text-red-800">{errorVar}</p>
              </div>
            )}
            
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-anthropic-dark">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm placeholder-anthropic-light focus:outline-none focus:ring-1 focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm transition-shadow"
                  placeholder="agent@rileyestate.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-anthropic-dark">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-cream-200 rounded-md shadow-sm placeholder-anthropic-light focus:outline-none focus:ring-1 focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm transition-shadow"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <a href="#" className="font-medium text-anthropic-gray hover:text-anthropic-dark transition-colors">
                  Forgot your password?
                </a>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-anthropic-dark hover:bg-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-anthropic-dark transition-all disabled:opacity-70"
              >
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Log In'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
