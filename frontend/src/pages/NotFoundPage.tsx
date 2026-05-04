import { Link } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-cream-50 flex flex-col justify-center items-center py-12 px-6">
      <div className="text-center max-w-md w-full">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-cream-200 mb-6 border border-cream-300 shadow-sm">
          <AlertCircle className="h-8 w-8 text-anthropic-dark" />
        </div>
        
        <h1 className="mt-4 text-4xl font-extrabold tracking-tight text-anthropic-dark sm:text-5xl">
          404
        </h1>
        <h2 className="mt-2 text-2xl font-semibold text-anthropic-dark tracking-tight">
          Page not found
        </h2>
        <p className="mt-4 text-base text-anthropic-gray font-medium leading-relaxed">
          The page you are looking for doesn't exist or has been moved. Let's get you back on track.
        </p>

        <div className="mt-10">
          <Link
            to="/"
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-anthropic-dark hover:bg-black transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-anthropic-dark"
          >
            <Home className="h-5 w-5 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
