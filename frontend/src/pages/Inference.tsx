import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Cpu,
  ChevronLeft,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
  Clock,
  Layers,
  Scan,
  Maximize
} from 'lucide-react';
import { imageService } from '../services/imageService';
import { detectionService } from '../services/detectionService';
import { inferenceService } from '../services/inferenceService';
import { ImageDoc, DetectionDocument, CrackInstance } from '../types';
import { CyberButton } from '../components/CyberButton';

export const Inference: React.FC = () => {
  const { imageId } = useParams<{ imageId: string }>();
  const navigate = useNavigate();

  const [image, setImage] = useState<ImageDoc | null>(null);
  const [detection, setDetection] = useState<DetectionDocument | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (imageId) {
      loadData(imageId);
    }
  }, [imageId]);

  const loadData = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const [imgData, detData] = await Promise.all([
        imageService.getImageById(id),
        detectionService.getDetectionByImageId(id)
      ]);
      setImage(imgData);
      setDetection(detData);
    } catch (err) {
      console.error('[HUD_INFERENCE_LOAD_ERROR]:', err);
      setError('UPLINK_SYNC_FAILED: UNABLE_TO_RETRIEVE_PIPELINE_DATA');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReanalyze = async () => {
    if (!imageId) return;
    try {
      setIsReanalyzing(true);
      const result = await inferenceService.reanalyzeImage(imageId);
      setImage(result.image);
      setDetection(result.detection);
    } catch (err) {
      console.error('[HUD_REANALYZE_ERROR]:', err);
      alert('REANALYSIS_SEQUENCE_FAILED');
    } finally {
      setIsReanalyzing(false);
    }
  };

  if (!imageId) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-6">
        <div className="p-6 border border-crack-electric/30 bg-crack-deep/20 max-w-lg">
          <Cpu className="w-16 h-16 text-crack-cyan/30 mx-auto mb-4" />
          <h2 className="text-xl font-orbitron text-white tracking-widest uppercase mb-2">Inference Hub Idle</h2>
          <p className="text-crack-cyan/60 font-mono text-sm leading-relaxed mb-6">
            The neural engine is operational but no signal has been targeted. Select an image from the registry to initialize deep inspection.
          </p>
          <Link to="/images">
            <CyberButton>
              <ExternalLink className="w-4 h-4" />
              OPEN_IMAGE_REGISTRY
            </CyberButton>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12">
      <div className="flex items-center justify-between border-b border-crack-neon/30 pb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 border border-crack-electric/50 text-crack-cyan hover:bg-crack-cyan/10 transition-all"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
              Deep <span className="text-crack-cyan">Inspection</span>
            </h1>
            <p className="text-crack-cyan/60 font-mono text-[10px] tracking-[0.2em] mt-1">
              {image?.original_filename || 'SCANNING_SIGNAL...'} // {imageId}
            </p>
          </div>
        </div>

        <CyberButton
          onClick={handleReanalyze}
          isLoading={isReanalyzing || isLoading}
          disabled={!image || image.inference_status === 'processing'}
        >
          <RefreshCw className={cn("w-4 h-4", isReanalyzing && "animate-spin")} />
          RE_TRIGGER_INFERENCE
        </CyberButton>
      </div>

      {isLoading ? (
        <div className="h-96 flex flex-col items-center justify-center text-crack-cyan">
          <RefreshCw className="w-12 h-12 animate-spin mb-4" />
          <p className="font-mono tracking-widest animate-pulse">EXTRACTING_GEOMETRIC_METADATA...</p>
        </div>
      ) : error ? (
        <div className="h-96 flex items-center justify-center border border-red-500/30 bg-red-500/5">
          <p className="text-red-400 font-mono italic">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Visualizer */}
          <div className="lg:col-span-8 space-y-6">
            <div className="border border-crack-electric/50 bg-black/40 p-4 relative overflow-hidden group">
              <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
              <div className="flex items-center justify-between mb-3 px-2">
                <span className="text-xs font-mono text-crack-cyan/70 tracking-widest flex items-center gap-2">
                  <Scan className="w-3 h-3" /> ANNOTATED_NEURAL_LAYER
                </span>
                <span className="text-[10px] font-mono text-crack-cyan/40">
                  RESOLUTION: {image?.width_px}x{image?.height_px}
                </span>
              </div>
              <div className="relative aspect-video flex items-center justify-center bg-crack-dark rounded-sm border border-crack-electric/20 overflow-hidden">
                {image?.output_url ? (
                  <img
                    src={image.output_url}
                    alt="Inference Output"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="text-crack-cyan/30 flex flex-col items-center gap-3">
                    <ShieldAlert className="w-12 h-12" />
                    <p className="font-mono text-xs tracking-widest uppercase">No Annotation Data</p>
                  </div>
                )}
              </div>
            </div>

            {/* Detections Gallery/List */}
            <div className="border border-crack-electric/30 bg-crack-deep/20 p-6">
              <h3 className="text-sm font-mono text-crack-cyan tracking-widest mb-6 flex items-center gap-2 uppercase">
                <Layers className="w-4 h-4" /> Isolated_Fragments_Registry
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {detection?.detections.map((crack) => (
                  <DetectionMiniCard key={crack.crack_index} crack={crack} />
                ))}
                {!detection?.detections.length && (
                  <div className="col-span-full py-12 text-center border border-dashed border-crack-electric/20 text-crack-cyan/40 font-mono text-xs uppercase tracking-widest">
                    Zero anomolies identified in this scan signal
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar Telemetry */}
          <div className="lg:col-span-4 space-y-6">
            <div className="border border-crack-electric/50 bg-crack-dark/80 p-6 space-y-6">
              <h3 className="text-xs font-mono text-crack-cyan tracking-widest uppercase border-b border-crack-electric/30 pb-3">
                Pipeline_Performance
              </h3>

              <div className="space-y-4">
                <TelemetryItem
                  icon={Clock}
                  label="Inference_Latency"
                  value={`${image?.inference_ms || 0}ms`}
                  sub="CPU_OPTIMIZED_ONNX"
                />
                <TelemetryItem
                  icon={Scan}
                  label="Anomaly_Density"
                  value={image?.total_cracks_detected || 0}
                  sub="DETECTED_INSTANCES"
                />
                <TelemetryItem
                  icon={ShieldAlert}
                  label="Network_Confidence"
                  value={detection?.detections.length ? `${Math.max(...detection.detections.map(d => d.confidence * 100)).toFixed(1)}%` : '0%'}
                  sub="MAX_DETECTION_SCORE"
                />
              </div>

              <div className="pt-4 space-y-3">
                <h3 className="text-xs font-mono text-crack-cyan/60 tracking-widest uppercase">System_Action_Rail</h3>
                <div className="grid grid-cols-1 gap-2">
                  <a href={image?.raw_url} target="_blank" rel="noreferrer" className="w-full">
                    <CyberButton variant="ghost" className="w-full justify-start text-xs h-10">
                      <ExternalLink className="w-3 h-3" /> VIEW_RAW_BUFFER
                    </CyberButton>
                  </a>
                  <CyberButton variant="ghost" className="w-full justify-start text-xs h-10 opacity-50 cursor-not-allowed">
                    <Maximize className="w-3 h-3" /> FULL_SCREEN_HUD
                  </CyberButton>
                </div>
              </div>
            </div>

            <div className="border border-crack-electric/30 bg-crack-cyan/5 p-6 backdrop-blur-sm">
              <h4 className="text-[10px] font-mono text-crack-cyan tracking-widest uppercase mb-4 opacity-70">
                Surface_Context
              </h4>
              <div className="p-4 bg-crack-dark border border-crack-cyan/30 relative">
                <p className="text-xl font-orbitron text-white tracking-widest uppercase truncate">
                  {detection?.surface_type || 'UNKNOWN'}
                </p>
                <div className="mt-2 h-1 w-full bg-crack-cyan/10">
                  <div className="h-full bg-crack-cyan w-3/4 animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const DetectionMiniCard = ({ crack }: { crack: CrackInstance }) => (
  <div className="border border-crack-electric/30 bg-black/20 p-4 transition-colors hover:border-crack-cyan/60">
    <div className="flex justify-between items-start mb-3">
      <span className="text-[10px] font-mono text-crack-cyan tracking-widest border border-crack-cyan/30 px-2 py-0.5">
        FRAGMENT #{crack.crack_index}
      </span>
      <span className={cn(
        "text-[9px] font-mono font-bold uppercase",
        crack.severity === 'high' ? 'text-red-500' : crack.severity === 'medium' ? 'text-amber-500' : 'text-crack-cyan'
      )}>
        {crack.severity}_SEVERITY
      </span>
    </div>

    <div className="grid grid-cols-2 gap-y-2 text-[10px] font-mono">
      <div className="text-crack-cyan/50 uppercase">Area</div>
      <div className="text-white text-right">{crack.mask_area_px?.toLocaleString()} px²</div>

      <div className="text-crack-cyan/50 uppercase">Max Width</div>
      <div className="text-white text-right">{crack.max_width_px?.toFixed(2)} px</div>

      <div className="text-crack-cyan/50 uppercase">Fractal Dim</div>
      <div className="text-crack-neon text-right font-bold">{crack.fractal_dimension?.toFixed(4)}</div>

      <div className="text-crack-cyan/50 uppercase">Topology</div>
      <div className="text-white text-right uppercase tracking-tighter">{crack.orientation}</div>
    </div>
  </div>
);

const TelemetryItem = ({ icon: Icon, label, value, sub }: any) => (
  <div className="flex items-start gap-4 p-3 bg-black/30 border-l border-crack-neon/40 hover:bg-black/50 transition-colors">
    <div className="p-2 bg-crack-electric/10">
      <Icon className="w-4 h-4 text-crack-neon" />
    </div>
    <div className="min-w-0">
      <p className="text-[9px] font-mono text-crack-cyan/50 tracking-widest uppercase">{label}</p>
      <p className="text-lg font-orbitron text-white truncate">{value}</p>
      <p className="text-[8px] font-mono text-crack-cyan/30 uppercase mt-0.5">{sub}</p>
    </div>
  </div>
);

const cn = (...classes: any[]) => classes.filter(Boolean).join(' ');

export default Inference;
