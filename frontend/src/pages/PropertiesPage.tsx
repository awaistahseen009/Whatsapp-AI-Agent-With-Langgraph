import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Plus, Home, Search, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
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
  bedrooms?: number;
  bathrooms?: number;
  square_footage?: number;
}

const ITEMS_PER_PAGE = 12;

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Pagination & Filters
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterPropertyType, setFilterPropertyType] = useState('all');
  const [filterCity, setFilterCity] = useState('all');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [bedroomFilter, setBedroomFilter] = useState('all');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const { user } = useAuth();

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const response = await api.get('/properties/?limit=1000');
      setProperties(response.data);
    } catch (error) {
      console.error('Failed to fetch properties:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique cities for filter dropdown
  const uniqueCities = useMemo(() => {
    const cities = [...new Set(properties.map(p => p.location_city).filter(Boolean))];
    return cities.sort();
  }, [properties]);

  // Get unique property types for filter dropdown
  const uniquePropertyTypes = useMemo(() => {
    const types = [...new Set(properties.map(p => p.property_type).filter(Boolean))];
    return types.sort();
  }, [properties]);

  const filteredProperties = useMemo(() => {
    return properties.filter(p => {
       const matchesSearch = p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                             p.location_city.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             p.location_area.toLowerCase().includes(searchQuery.toLowerCase());
       
       const matchesType = filterType === 'all' ? true : p.listing_type.toLowerCase() === filterType.toLowerCase();
       const matchesPropertyType = filterPropertyType === 'all' ? true : p.property_type.toLowerCase() === filterPropertyType.toLowerCase();
       const matchesCity = filterCity === 'all' ? true : p.location_city === filterCity;
       
       const matchesPrice = 
         (priceRange.min === '' || p.price >= parseInt(priceRange.min)) &&
         (priceRange.max === '' || p.price <= parseInt(priceRange.max));
       
       const matchesBedrooms = bedroomFilter === 'all' ? true : 
         (bedroomFilter === '4+' ? (p.bedrooms || 0) >= 4 : (p.bedrooms || 0) === parseInt(bedroomFilter));
       
       return matchesSearch && matchesType && matchesPropertyType && matchesCity && matchesPrice && matchesBedrooms;
    });
  }, [properties, searchQuery, filterType, filterPropertyType, filterCity, priceRange, bedroomFilter]);

  const totalPages = Math.ceil(filteredProperties.length / ITEMS_PER_PAGE);
  
  const paginatedProperties = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredProperties.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredProperties, currentPage]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(price);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center sm:justify-between mb-8 pb-5 border-b border-cream-200">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-anthropic-dark flex items-center gap-2">
            Properties Catalog 
            <span className="bg-cream-100 text-xs font-bold text-anthropic-gray px-2 py-1 rounded-full">{properties.length}</span>
          </h1>
          <p className="mt-1 text-sm text-anthropic-gray">
            Your real estate listings available for AI query injection.
          </p>
        </div>
        {user?.role === 'owner' && (
          <Link 
            to="/properties/new"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-anthropic-dark hover:bg-anthropic-gray focus:outline-none transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Property
          </Link>
        )}
      </div>

      <div className="mb-6 space-y-4">
        <div className="flex gap-4">
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-anthropic-light" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-cream-200 rounded-md leading-5 bg-white placeholder-anthropic-light focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
              placeholder="Search properties, cities, or areas..."
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1); }}
            />
          </div>
          <div className="relative">
             <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
               <Filter className="h-4 w-4 text-anthropic-light" />
             </div>
             <select
               value={filterType}
               onChange={e => { setFilterType(e.target.value); setCurrentPage(1); }}
               className="block w-full pl-10 pr-8 py-2 border border-cream-200 rounded-md leading-5 bg-white text-anthropic-dark focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm appearance-none"
             >
               <option value="all">All Listings</option>
               <option value="sale">For Sale</option>
               <option value="rent">For Rent</option>
             </select>
          </div>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="inline-flex items-center px-4 py-2 border border-cream-200 rounded-md shadow-sm text-sm font-medium text-anthropic-dark bg-white hover:bg-cream-100 focus:outline-none transition-colors"
          >
            <Filter className="h-4 w-4 mr-2" />
            Advanced Filters
          </button>
        </div>

        {showAdvancedFilters && (
          <div className="bg-cream-50 p-4 rounded-lg border border-cream-200 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-anthropic-gray mb-1">Property Type</label>
                <select
                  value={filterPropertyType}
                  onChange={e => { setFilterPropertyType(e.target.value); setCurrentPage(1); }}
                  className="block w-full px-3 py-2 border border-cream-200 rounded-md leading-5 bg-white text-anthropic-dark focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
                >
                  <option value="all">All Types</option>
                  {uniquePropertyTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-anthropic-gray mb-1">City</label>
                <select
                  value={filterCity}
                  onChange={e => { setFilterCity(e.target.value); setCurrentPage(1); }}
                  className="block w-full px-3 py-2 border border-cream-200 rounded-md leading-5 bg-white text-anthropic-dark focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
                >
                  <option value="all">All Cities</option>
                  {uniqueCities.map(city => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-anthropic-gray mb-1">Bedrooms</label>
                <select
                  value={bedroomFilter}
                  onChange={e => { setBedroomFilter(e.target.value); setCurrentPage(1); }}
                  className="block w-full px-3 py-2 border border-cream-200 rounded-md leading-5 bg-white text-anthropic-dark focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
                >
                  <option value="all">Any</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4+">4+</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="block text-xs font-medium text-anthropic-gray">Price Range</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={priceRange.min}
                    onChange={e => { setPriceRange(prev => ({ ...prev, min: e.target.value })); setCurrentPage(1); }}
                    className="block w-full px-3 py-2 border border-cream-200 rounded-md leading-5 bg-white text-anthropic-dark focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={priceRange.max}
                    onChange={e => { setPriceRange(prev => ({ ...prev, max: e.target.value })); setCurrentPage(1); }}
                    className="block w-full px-3 py-2 border border-cream-200 rounded-md leading-5 bg-white text-anthropic-dark focus:outline-none focus:bg-white focus:ring-1 focus:ring-anthropic-dark sm:text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-anthropic-light" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {paginatedProperties.map((property) => (
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
                <div className="flex items-center text-sm text-anthropic-gray mt-1 mb-2">
                  <Home className="h-3 w-3 mr-1" />
                  {property.location_area}, {property.location_city}
                </div>
                
                <div className="flex items-center gap-4 text-xs text-anthropic-gray mb-4">
                  {property.bedrooms && (
                    <span>{property.bedrooms} bed{property.bedrooms !== 1 ? 's' : ''}</span>
                  )}
                  {property.bathrooms && (
                    <span>{property.bathrooms} bath{property.bathrooms !== 1 ? 's' : ''}</span>
                  )}
                  {property.square_footage && (
                    <span>{property.square_footage.toLocaleString()} sqft</span>
                  )}
                </div>

                <div className="mt-auto pt-4 border-t border-cream-100 flex items-center justify-between">
                  <div>
                    <span className="text-lg font-bold text-anthropic-dark">{formatPrice(property.price)}</span>
                    <div className="text-xs text-anthropic-gray capitalize">{property.listing_type}</div>
                  </div>
                  <Link 
                    to={`/properties/${property.property_id}/edit`}
                    className="inline-flex items-center px-3 py-1.5 border border-cream-200 shadow-sm text-xs font-medium rounded-md text-anthropic-dark bg-white hover:bg-cream-100 focus:outline-none transition-colors"
                  >
                    Edit &rarr;
                  </Link>
                </div>
              </div>
            ))}

            {paginatedProperties.length === 0 && (
              <div className="col-span-full py-16 border-2 border-dashed border-cream-200 rounded-lg text-center">
                <p className="text-sm font-medium text-anthropic-dark mt-2">No properties match your filter</p>
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-between border-t border-cream-200 pt-5">
              <div className="flex flex-1 justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center rounded-md border border-cream-200 bg-white px-4 py-2 text-sm font-medium text-anthropic-gray hover:bg-cream-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="relative ml-3 inline-flex items-center rounded-md border border-cream-200 bg-white px-4 py-2 text-sm font-medium text-anthropic-gray hover:bg-cream-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-anthropic-gray">
                    Showing <span className="font-medium text-anthropic-dark">{(currentPage - 1) * ITEMS_PER_PAGE + 1}</span> to{' '}
                    <span className="font-medium text-anthropic-dark">
                      {Math.min(currentPage * ITEMS_PER_PAGE, filteredProperties.length)}
                    </span>{' '}
                    of <span className="font-medium text-anthropic-dark">{filteredProperties.length}</span> results
                  </p>
                </div>
                <div>
                  <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center rounded-l-md px-2 py-2 text-anthropic-gray ring-1 ring-inset ring-cream-200 hover:bg-cream-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                    >
                      <span className="sr-only">Previous</span>
                      <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                    </button>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center rounded-r-md px-2 py-2 text-anthropic-gray ring-1 ring-inset ring-cream-200 hover:bg-cream-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                    >
                      <span className="sr-only">Next</span>
                      <ChevronRight className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
