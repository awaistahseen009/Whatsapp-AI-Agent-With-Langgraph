import { useState, useEffect } from 'react';
import { Loader2, Plus, Home } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

interface Property {
  property_id: string;
  title: string;
  property_type: string;
  listing_type: string;
  location_area: string;
  location_city: string;
  price: number;
  available: boolean;
}

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const response = await api.get('/properties');
      setProperties(response.data);
    } catch (error) {
      console.error('Failed to fetch properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(price);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark">Properties Catalog</h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Your real estate listings available for AI query injection.
          </p>
        </div>
        {user?.role === 'owner' && (
          <div className="mt-4 sm:mt-0">
            <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-anthropic-dark hover:bg-black focus:outline-none transition-colors">
              <Plus className="-ml-1 mr-2 h-4 w-4" aria-hidden="true" />
              Add Property
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {properties.map((property) => (
             <div key={property.property_id} className="bg-white border border-cream-200 rounded-lg shadow-sm hover:shadow-md transition-shadow flex flex-col p-5 relative overflow-hidden">
               <div className="flex justify-between items-start mb-3">
                  <div className="bg-cream-100 px-2 py-1 rounded text-xs font-medium text-anthropic-dark capitalize">
                    {property.property_type} • {property.listing_type}
                  </div>
                  <span className={`px-2 inline-flex text-[10px] leading-5 font-semibold rounded-full uppercase tracking-wide ${property.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {property.available ? 'Available' : 'Sold'}
                  </span>
               </div>
               <h3 className="text-lg font-semibold text-anthropic-dark truncate" title={property.title}>{property.title}</h3>
               <div className="flex items-center text-sm text-anthropic-gray mt-1 mb-4">
                 <Home className="h-3 w-3 mr-1" />
                 {property.location_area}, {property.location_city}
               </div>

               <div className="mt-auto pt-4 border-t border-cream-100 flex items-center justify-between">
                 <span className="text-md font-bold text-anthropic-dark">{formatPrice(property.price)}</span>
                 <button className="text-accent-blue text-sm font-medium hover:underline focus:outline-none">
                   Edit &rarr;
                 </button>
               </div>
             </div>
          ))}

          {properties.length === 0 && (
             <div className="col-span-full py-16 border-2 border-dashed border-cream-200 rounded-lg text-center">
               <p className="text-sm font-medium text-anthropic-dark mt-2">No properties here</p>
               <p className="text-sm text-anthropic-gray">Start adding properties to let the AI agent market them.</p>
             </div>
          )}
        </div>
      )}
    </div>
  );
}
