import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import api from '../api/axios';

interface PropertyData {
  title: string;
  property_type: string;
  listing_type: string;
  location_area: string;
  location_city: string;
  address: string;
  price: number | string;
  available: boolean;
  bedrooms?: number | string;
  bathrooms?: number | string;
  size_sqft: number | string;
}

export default function PropertyEditPage() {
  const { id } = useParams<{ id: string }>();
  const isNew = !id || id === 'new';
  const navigate = useNavigate();

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<PropertyData>({
    title: '',
    property_type: 'apartment',
    listing_type: 'sale',
    location_area: '',
    location_city: '',
    address: '',
    price: '',
    available: true,
    bedrooms: '',
    bathrooms: '',
    size_sqft: ''
  });

  useEffect(() => {
    if (!isNew) {
      fetchProperty();
    }
  }, [id, isNew]);

  const fetchProperty = async () => {
    try {
      const res = await api.get(`/properties/${id}/`);
      if (res.data) {
        setFormData(res.data);
      }
    } catch (err: any) {
      console.error(err);
      setError('Failed to load property');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target as any;
    let finalValue: any = value;
    
    if (type === 'checkbox') {
      finalValue = (e.target as HTMLInputElement).checked;
    } else if (type === 'number') {
      finalValue = value === '' ? '' : Number(value);
    }
    
    setFormData(prev => ({ ...prev, [name]: finalValue }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      // Provide fallback defaults for validation bounds
      const payload = {
        ...formData,
        price: Number(formData.price) || 0,
        size_sqft: Number(formData.size_sqft) || 1, // field gt=0
        bedrooms: formData.bedrooms === '' ? null : Number(formData.bedrooms),
        bathrooms: formData.bathrooms === '' ? null : Number(formData.bathrooms),
      };

      if (isNew) {
         await api.post('/properties/', payload);
      } else {
         await api.put(`/properties/${id}/`, payload);
      }
      navigate('/properties');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save property');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
     return <div className="flex justify-center p-24"><Loader2 className="h-8 w-8 animate-spin text-anthropic-light" /></div>;
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <Link to="/properties" className="inline-flex items-center text-sm font-medium text-anthropic-gray hover:text-anthropic-dark transition-colors">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Properties
        </Link>
      </div>

      <div className="bg-white border border-cream-200 shadow-sm rounded-lg overflow-hidden">
         <div className="px-8 py-6 border-b border-cream-200">
           <h2 className="text-xl font-semibold text-anthropic-dark">
             {isNew ? 'Add New Property' : 'Edit Property'}
           </h2>
         </div>

         {error && (
            <div className="p-4 bg-red-50 border-b border-red-100 text-red-600 text-sm">
               {typeof error === 'object' ? JSON.stringify(error) : error}
            </div>
         )}
         
         <form onSubmit={handleSubmit} className="p-8 space-y-6 text-left">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <div className="col-span-full">
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Title</label>
                  <input required name="title" value={formData.title} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Property Type</label>
                  <select name="property_type" value={formData.property_type} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2 bg-white">
                     <option value="apartment">Apartment</option>
                     <option value="house">House</option>
                     <option value="villa">Villa</option>
                     <option value="commercial">Commercial</option>
                     <option value="plot">Plot</option>
                  </select>
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Listing Type</label>
                  <select name="listing_type" value={formData.listing_type} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2 bg-white">
                     <option value="sale">Sale / Buy</option>
                     <option value="rent">Rent</option>
                     <option value="invest">Invest</option>
                  </select>
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">City</label>
                  <select required name="location_city" value={formData.location_city} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2 bg-white">
                     <option value="" disabled>Select a city...</option>
                     <option value="New York">New York</option>
                     <option value="Los Angeles">Los Angeles</option>
                     <option value="Chicago">Chicago</option>
                     <option value="Houston">Houston</option>
                     <option value="Phoenix">Phoenix</option>
                     <option value="Philadelphia">Philadelphia</option>
                     <option value="San Antonio">San Antonio</option>
                     <option value="San Diego">San Diego</option>
                     <option value="Dallas">Dallas</option>
                     <option value="Austin">Austin</option>
                     <option value="San Francisco">San Francisco</option>
                     <option value="Seattle">Seattle</option>
                     <option value="Denver">Denver</option>
                     <option value="Washington DC">Washington DC</option>
                     <option value="Boston">Boston</option>
                     <option value="Miami">Miami</option>
                     <option value="Atlanta">Atlanta</option>
                     <option value="Dubai">Dubai</option>
                     <option value="London">London</option>
                     <option value="Toronto">Toronto</option>
                  </select>
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Area / Neighborhood</label>
                  <input required name="location_area" value={formData.location_area} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
               </div>
               
               <div className="col-span-full">
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Full Street Address</label>
                  <input required name="address" value={formData.address} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
               </div>

               <div>
                  <label className="block text-sm font-medium text-anthropic-dark mb-2">Price ($)</label>
                  <input required type="number" min="0" name="price" value={formData.price} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
               </div>

               <div className="flex items-center mt-6">
                  <input type="checkbox" name="available" id="available" checked={formData.available} onChange={handleChange} className="h-4 w-4 text-anthropic-dark focus:ring-anthropic-dark border-cream-300 rounded" />
                  <label htmlFor="available" className="ml-2 block text-sm text-anthropic-dark">Available on Market</label>
               </div>

               <div className="col-span-full border-t border-cream-200 mt-4 pt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                     <label className="block text-sm font-medium text-anthropic-dark mb-2">Bedrooms</label>
                     <input type="number" min="0" name="bedrooms" value={formData.bedrooms} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
                  </div>
                  <div>
                     <label className="block text-sm font-medium text-anthropic-dark mb-2">Bathrooms</label>
                     <input type="number" min="0" name="bathrooms" value={formData.bathrooms} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
                  </div>
                  <div>
                     <label className="block text-sm font-medium text-anthropic-dark mb-2">Size (Sq Ft)</label>
                     <input required type="number" min="1" name="size_sqft" value={formData.size_sqft} onChange={handleChange} className="w-full border-cream-300 rounded-md focus:ring-anthropic-dark focus:border-anthropic-dark sm:text-sm text-anthropic-dark border p-2" />
                  </div>
               </div>
            </div>

            <div className="pt-6 border-t border-cream-200 flex justify-end gap-3">
               <button type="button" onClick={() => navigate('/properties')} className="px-4 py-2 border border-cream-300 shadow-sm text-sm font-medium rounded-md text-anthropic-dark bg-white hover:bg-cream-50 focus:outline-none transition-colors">
                 Cancel
               </button>
               <button type="submit" disabled={saving} className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-anthropic-dark hover:bg-anthropic-gray focus:outline-none transition-colors disabled:opacity-50">
                 {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                 Save Property
               </button>
            </div>
         </form>
      </div>
    </div>
  );
}
