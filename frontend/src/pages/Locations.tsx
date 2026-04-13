import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Plus,
  Trash2,
  Edit3,
  Loader2,
  Globe,
  Navigation,
  FileText,
  AlertCircle
} from 'lucide-react';
import { locationService } from '../services/locationService';
import { Location, LocationCreate } from '../types';
import { CyberButton } from '../components/CyberButton';

export const Locations: React.FC = () => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<LocationCreate>({
    name: '',
    city: '',
    country: '',
    address: '',
    description: ''
  });

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      setIsLoading(true);
      const response = await locationService.listLocations(1, 100);
      setLocations(response.results);
    } catch (err) {
      console.error('[HUD_LOCATIONS_ERROR]:', err);
      setError('UPLINK_SYNC_FAILED: UNABLE_TO_RETRIEVE_SPATIAL_DATA');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      const newLoc = await locationService.createLocation(formData);
      setLocations(prev => [newLoc, ...prev]);
      setShowForm(false);
      setFormData({ name: '', city: '', country: '', address: '', description: '' });
    } catch (err) {
      console.error('[HUD_LOCATION_CREATE_ERROR]:', err);
      alert('FAILED_TO_REGISTER_NEW_COORDINATES');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('CONFIRM_LOCATION_PURGE: THIS_ACTION_IS_IRREVERSIBLE')) return;
    try {
      await locationService.deleteLocation(id);
      setLocations(prev => prev.filter(l => l.id !== id));
    } catch (err) {
      console.error('[HUD_LOCATION_DELETE_ERROR]:', err);
      alert('COORDINATE_PURGE_REJECTED_BY_SERVER');
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="border-b border-crack-neon/30 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
            Spatial <span className="text-crack-cyan">Coordinates</span>
          </h1>
          <p className="text-crack-cyan/60 font-mono text-xs mt-1">
            ROUTING_NODES_AND_INSPECTION_SITES_REGISTRY
          </p>
        </div>

        <CyberButton onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4" />
          {showForm ? 'CLOSE_TERMINAL' : 'REGISTER_NEW_NODE'}
        </CyberButton>
      </div>

      {showForm && (
        <div className="border border-crack-electric/50 bg-crack-deep/30 p-6 relative animate-in slide-in-from-top-4 duration-300">
          <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
          <h2 className="text-sm font-mono text-crack-cyan tracking-widest mb-6 flex items-center gap-2">
            <Navigation className="w-4 h-4" /> SEQUENCE_INPUT
          </h2>

          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative z-10">
            <div className="space-y-2">
              <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase">Site_Designation</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={e => setFormData(d => ({ ...d, name: e.target.value }))}
                className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:border-crack-neon outline-none"
                placeholder="E.G. SECTOR_7_BRIDGE"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase">Urban_Zone (City)</label>
              <input
                type="text"
                required
                value={formData.city}
                onChange={e => setFormData(d => ({ ...d, city: e.target.value }))}
                className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:border-crack-neon outline-none"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase">Jurisdiction (Country)</label>
              <input
                type="text"
                required
                value={formData.country}
                onChange={e => setFormData(d => ({ ...d, country: e.target.value }))}
                className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:border-crack-neon outline-none"
              />
            </div>
            <div className="md:col-span-2 space-y-2">
              <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase">Exact_Coordinates (Address)</label>
              <input
                type="text"
                required
                value={formData.address}
                onChange={e => setFormData(d => ({ ...d, address: e.target.value }))}
                className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:border-crack-neon outline-none"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase">Observation_Log (Description)</label>
              <input
                type="text"
                value={formData.description}
                onChange={e => setFormData(d => ({ ...d, description: e.target.value }))}
                className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:border-crack-neon outline-none"
              />
            </div>

            <div className="lg:col-span-3 flex justify-end">
              <CyberButton type="submit" isLoading={isSubmitting}>
                INITIALIZE_REGISTRATION
              </CyberButton>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="h-64 flex flex-col items-center justify-center text-crack-cyan">
          <Loader2 className="w-10 h-10 animate-spin mb-3" />
          <p className="font-mono text-xs tracking-[0.2em]">SYNCING_GLOBAL_SITES...</p>
        </div>
      ) : error ? (
        <div className="p-8 border border-red-500/30 bg-red-500/5 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="font-mono text-red-400">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {locations.map((loc) => (
            <div
              key={loc.id}
              className="group relative border border-crack-electric/30 bg-crack-dark/60 p-5 hover:border-crack-cyan transition-all duration-300"
            >
              <div className="absolute top-0 right-0 p-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => handleDelete(loc.id)}
                  className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-start gap-4 mb-4">
                <div className="p-3 bg-crack-electric/20 border border-crack-electric/50">
                  <MapPin className="w-6 h-6 text-crack-cyan" />
                </div>
                <div>
                  <h3 className="text-white font-orbitron tracking-wider uppercase text-sm">{loc.name}</h3>
                  <div className="flex items-center gap-1 text-crack-cyan/60 font-mono text-[10px] mt-1">
                    <Globe className="w-3 h-3" />
                    <span>{loc.city}, {loc.country}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3 bg-black/20 p-3 border border-crack-electric/10">
                <div className="space-y-1">
                  <p className="text-[9px] font-mono text-crack-cyan/40 uppercase tracking-widest">Address_Vector</p>
                  <p className="text-white/80 font-mono text-xs line-clamp-1">{loc.address}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] font-mono text-crack-cyan/40 uppercase tracking-widest">Observation_Trace</p>
                  <p className="text-white/60 font-mono text-xs italic line-clamp-2">
                    {loc.description || 'NO_DATA_LOGGED_FOR_THIS_SITE'}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-crack-electric/10 flex justify-between items-center text-[9px] font-mono text-crack-cyan/30 uppercase tracking-tighter">
                <span>Node_ID: {loc.id.split('-')[0]}...</span>
                <span>Active_Since: {new Date(loc.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}

          {locations.length === 0 && !showForm && (
            <div className="col-span-full py-20 border border-dashed border-crack-electric/30 flex flex-col items-center justify-center opacity-50">
              <FileText className="w-12 h-12 text-crack-cyan mb-4" />
              <p className="font-mono text-sm tracking-widest">MAP_REGISTRY_EMPTY</p>
              <p className="font-mono text-[10px] mt-2">ADD A NEW LOCATION TO START ROUTING IMAGES</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Locations;
