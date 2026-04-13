import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Target,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Maximize2,
  Activity,
  Box,
  Hash,
  ExternalLink
} from 'lucide-react';
import { detectionService } from '../services/detectionService';
import { DetectionDocument, CrackInstance, Severity, Orientation } from '../types';
import { CyberButton } from '../components/CyberButton';

export const Detections: React.FC = () => {
  const navigate = useNavigate();
  const [detections, setDetections] = useState<DetectionDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    severity: '' as Severity | '',
    surfaceType: '',
  });

  useEffect(() => {
    fetchDetections();
  }, [page, filters]);

  const fetchDetections = async () => {
    try {
      setIsLoading(true);
      const response = await detectionService.listDetections({
        page,
        pageSize: 10,
        severity: filters.severity || undefined,
        surfaceType: filters.surfaceType || undefined,
      });
      setDetections(response.results);
      setTotalPages(response.total_pages);
    } catch (err) {
      console.error('[HUD_DETECTIONS_ERROR]:', err);
      setError('UPLINK_SYNC_FAILED: UNABLE_TO_RETRIEVE_DETECTION_LOGS');
    } finally {
      setIsLoading(false);
    }
  };

  const flattenCracks = () => {
    return detections.flatMap(doc =>
      doc.detections.map(crack => ({
        ...crack,
        parentFilename: doc.filename,
        parentImageId: doc.image_id,
        surfaceType: doc.surface_type,
        detectedAt: doc.detected_at,
        id: `${doc.id}-${crack.crack_index}`
      }))
    );
  };

  const flattenedCracks = flattenCracks();

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="border-b border-crack-neon/30 pb-4 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
            Detection <span className="text-crack-cyan">Telemetry</span>
          </h1>
          <p className="text-crack-cyan/60 font-mono text-xs mt-1">
            REAL-TIME STRUCTURAL ANOMALY LOGS // NEURAL_ENGINE_OUTPUT
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-crack-dark border border-crack-electric/30 p-1">
            <Filter className="w-3 h-3 text-crack-cyan/50 ml-2" />
            <select
              value={filters.severity}
              onChange={(e) => setFilters(f => ({ ...f, severity: e.target.value as Severity | '' }))}
              className="bg-transparent text-crack-cyan font-mono text-[10px] tracking-widest p-2 focus:outline-none uppercase"
            >
              <option value="">ALL_SEVERITY</option>
              <option value="low">LOW_RISK</option>
              <option value="medium">MEDIUM_RISK</option>
              <option value="high">HIGH_RISK</option>
            </select>
          </div>

          <CyberButton onClick={() => setPage(1)} className="py-2">
            <Search className="w-3 h-3" />
            RELOAD
          </CyberButton>
        </div>
      </div>

      {isLoading ? (
        <div className="h-96 flex flex-col items-center justify-center text-crack-cyan">
          <Activity className="w-12 h-12 animate-spin mb-4" />
          <p className="font-mono tracking-widest animate-pulse">QUERYING_DETECTION_MATRIX...</p>
        </div>
      ) : error ? (
        <div className="h-96 flex items-center justify-center">
          <div className="border border-red-500/50 bg-red-500/10 p-6 text-center max-w-md">
            <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-2" />
            <p className="font-mono text-red-400">{error}</p>
          </div>
        </div>
      ) : flattenedCracks.length === 0 ? (
        <div className="h-96 border border-crack-electric/30 bg-crack-deep/20 flex flex-col items-center justify-center text-center">
          <Target className="w-16 h-16 text-crack-cyan/30 mb-4" />
          <h3 className="text-xl font-orbitron text-white tracking-widest uppercase">No Anomalies Found</h3>
          <p className="text-crack-cyan/60 font-mono text-sm mt-2 max-w-sm">
            The database contains no recorded detections matching your current filter criteria.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="overflow-x-auto border border-crack-electric/30 bg-crack-deep/10">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-crack-dark border-b border-crack-electric/50">
                  <th className="p-4 text-crack-cyan/70 tracking-widest uppercase font-normal">Signal_Src</th>
                  <th className="p-4 text-crack-cyan/70 tracking-widest uppercase font-normal">Metrics</th>
                  <th className="p-4 text-crack-cyan/70 tracking-widest uppercase font-normal">Topology</th>
                  <th className="p-4 text-crack-cyan/70 tracking-widest uppercase font-normal text-center">Severity</th>
                  <th className="p-4 text-crack-cyan/70 tracking-widest uppercase font-normal text-right">Timestamp</th>
                  <th className="p-4 text-crack-cyan/70 tracking-widest uppercase font-normal text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-crack-electric/20">
                {flattenedCracks.map((crack) => (
                  <tr key={crack.id} className="group hover:bg-crack-cyan/5 transition-colors">
                    <td className="p-4">
                      <div className="space-y-1">
                        <p className="text-white font-orbitron tracking-wider">{crack.parentFilename}</p>
                        <p className="text-crack-cyan/40 text-[9px] uppercase">{crack.surfaceType} // ID:{crack.crack_index}</p>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                        <div className="flex items-center gap-1">
                          <Maximize2 className="w-3 h-3 text-crack-cyan/40" />
                          <span className="text-crack-cyan/60">AREA:</span>
                          <span className="text-white">{crack.mask_area_px.toLocaleString()}px</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Box className="w-3 h-3 text-crack-cyan/40" />
                          <span className="text-crack-cyan/60">WIDTH:</span>
                          <span className="text-white">{crack.max_width_px?.toFixed(1) ?? 'N/A'}px</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Target className="w-3 h-3 text-crack-cyan/40" />
                          <span className="text-crack-cyan/60">CONF:</span>
                          <span className="text-crack-neon">{(crack.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Hash className="w-3 h-3 text-crack-cyan/40" />
                          <span className="text-crack-cyan/60">FD:</span>
                          <span className="text-crack-neon font-bold">{crack.fractal_dimension?.toFixed(3) ?? 'PENDING'}</span>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 uppercase">
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "w-2 h-2 rounded-full",
                          crack.orientation === 'forked' ? "bg-red-500 shadow-[0_0_5px_red]" :
                            crack.orientation === 'unknown' ? "bg-gray-500" : "bg-crack-cyan shadow-[0_0_5px_cyan]"
                        )} />
                        <span className="text-white tracking-widest">{crack.orientation}</span>
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      <StatusPill severity={crack.severity as Severity} />
                    </td>
                    <td className="p-4 text-right">
                      <p className="text-crack-cyan/60">{new Date(crack.detectedAt).toLocaleDateString()}</p>
                      <p className="text-crack-cyan/40 text-[9px]">{new Date(crack.detectedAt).toLocaleTimeString()}</p>
                    </td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => navigate(`/inference/${crack.parentImageId}`)}
                        className="p-2 text-crack-cyan hover:bg-crack-cyan/20 rounded transition-colors"
                        title="VIEW_DATA_LAYER"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* PAGINATION */}
          <div className="flex items-center justify-between border border-crack-electric/30 bg-crack-dark/50 p-4">
            <span className="text-[10px] font-mono text-crack-cyan/50 tracking-widest">
              TELEMETRY_PAGE_{page}_OF_{totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 border border-crack-electric/50 text-crack-cyan hover:bg-crack-cyan/10 disabled:opacity-30 disabled:border-crack-electric/20 transition-all font-mono text-xs flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" /> PREV
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 border border-crack-electric/50 text-crack-cyan hover:bg-crack-cyan/10 disabled:opacity-30 disabled:border-crack-electric/20 transition-all font-mono text-xs flex items-center gap-2"
              >
                NEXT <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const StatusPill = ({ severity }: { severity: Severity }) => {
  const tone =
    severity === 'high'
      ? 'border-red-500/50 text-red-500 bg-red-500/10 shadow-[0_0_10px_rgba(239,68,68,0.2)]'
      : severity === 'medium'
        ? 'border-amber-500/50 text-amber-500 bg-amber-500/10'
        : 'border-crack-cyan/50 text-crack-cyan bg-crack-cyan/10';

  return (
    <span className={`px-3 py-1 text-[10px] font-mono tracking-[0.2em] border uppercase font-bold ${tone}`}>
      {severity}
    </span>
  );
};

const cn = (...classes: any[]) => classes.filter(Boolean).join(' ');

export default Detections;
