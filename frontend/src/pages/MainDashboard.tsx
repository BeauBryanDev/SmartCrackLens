import React, { useState, useEffect } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, 
  BarChart, Bar, 
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { Activity, Image as ImageIcon, AlertTriangle, Zap, Loader2 } from 'lucide-react';
import { analyticService } from '../services/analyticService';
import { detectionService } from '../services/detectionService';
import { DashboardResponse, FractalChartData } from '../types';
import { useAuth } from '../hooks/useAuth';
import { FractalAnalysisChart } from '@/components/FractalAnalysisChart';


// --- THEME COLORS ---
const COLORS = {
  cyan: '#00B4D8',
  electric: '#0077B6',
  neon: '#90E0EF',
  danger: '#EF4444',
  warning: '#F59E0B',
  dark: '#03045E'
};

const SEVERITY_COLORS = [COLORS.cyan,  COLORS.warning, COLORS.danger, COLORS.electric];

export const MainDashboard: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<FractalChartData[]>([]);

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        setIsLoading(true);
        // Fetch 30-day dashboard data via the established service
        const dashboardPayload = await analyticService.getDashboard(30);
        setData(dashboardPayload);
      } catch (err) {
        console.error('[HUD_TELEMETRY_ERROR]: Failed to fetch dashboard data.', err);
        setError('UPLINK_FAILED: UNABLE TO RETRIEVE TELEMETRY.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTelemetry();
  }, []);

  useEffect(() => {
    detectionService
      .getFractalData()
      .then((fractalData) => setChartData(fractalData))
      .catch((err) => {
        console.error('[HUD_FRACTAL_ERROR]: Failed to fetch fractal chart data.', err);
        setChartData([]);
      });
  }, []);

  // --- LOADING STATE ---
  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-crack-cyan">
        <Loader2 className="w-12 h-12 animate-spin mb-4" />
        <p className="font-mono tracking-widest animate-pulse">ESTABLISHING_TELEMETRY_LINK...</p>
      </div>
    );
  }

  // --- ERROR STATE ---
  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="border border-red-500/50 bg-red-500/10 p-6 text-center">
          <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-2" />
          <p className="font-mono text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  // Safely fallback to empty data structures if the user has no history
  const hasData = !!data && data.summary.total_images_analyzed > 0;
  const highSeverityCount =
    data?.severity.data.find((entry) => entry.name === 'high')?.value ?? 0;

  return (
    
    <div className="space-y-6 pb-8 animate-in fade-in duration-700">
      
      {/* HEADER SECTION */}
      <div className="flex items-center justify-between border-b border-crack-neon/30 pb-4">
        <div>
          <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
            Global <span className="text-crack-cyan">Telemetry</span>
          </h1>
          <p className="text-crack-cyan/60 font-mono text-xs mt-1">
            OPERATOR: {user?.username} | ENGINE: YOLOv8_ONNX
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-crack-cyan opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-crack-neon"></span>
          </span>
          <span className="text-crack-cyan font-mono text-xs tracking-widest">LIVE</span>
        </div>
      </div>

      {/* TOP SUMMARY CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard icon={ImageIcon} title="SCANNED_IMAGES" value={data?.summary.total_images_analyzed || 0} />
        <SummaryCard icon={Activity} title="DETECTED_CRACKS" value={data?.summary.total_cracks_detected || 0} />
        <SummaryCard icon={AlertTriangle} title="HIGH_SEVERITY" value={highSeverityCount} color="text-red-500" />
        <SummaryCard icon={Zap} title="AVG_LATENCY" value={`${data?.summary.average_inference_ms || 0}ms`} />
      </div>

      {!hasData ? (
        /* EMPTY STATE FOR NEW USERS */
        <div className="w-full py-20 border border-crack-electric/30 bg-crack-deep/20 flex flex-col items-center justify-center text-center">
          <Activity className="w-16 h-16 text-crack-cyan/30 mb-4" />
          <h3 className="text-xl font-orbitron text-white tracking-widest">NO_DATA_FOUND</h3>
          <p className="text-crack-cyan/60 font-mono text-sm mt-2 max-w-md">
            The neural engine requires image input to generate telemetry. Upload structural scans to initialize the analytics matrix.
          </p>
        </div>
      ) : (
        /* MAIN CHARTS GRID */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* TIMELINE (Span 2 columns) */}
          <div className="lg:col-span-2 border border-crack-electric/30 bg-crack-deep/20 p-4 relative group">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
            <h3 className="text-xs font-mono text-crack-cyan tracking-widest mb-4"> INFERENCE_TIMELINE_30D</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.timeline.data}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.cyan} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={COLORS.cyan} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#00B4D8" opacity={0.1} />
                  <XAxis dataKey="date" stroke={COLORS.cyan} fontSize={10} tickMargin={10} />
                  <YAxis stroke={COLORS.cyan} fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: '#03045E', borderColor: '#00B4D8', color: '#fff', fontFamily: 'monospace' }} />
                  <Area type="monotone" dataKey="total_cracks" stroke={COLORS.neon} fillOpacity={1} fill="url(#colorCount)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* SEVERITY PIE CHART */}
          <div className="border border-crack-electric/30 bg-crack-deep/20 p-4 relative group">
            <h3 className="text-xs font-mono text-crack-cyan tracking-widest mb-4">SEVERITY_DISTRIBUTION</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.severity.data}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {data.severity.data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[index % SEVERITY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#03045E', borderColor: '#00B4D8', color: '#fff', fontFamily: 'monospace' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* SURFACE TYPES BAR CHART */}
          <div className="border border-crack-electric/30 bg-crack-deep/20 p-4 relative group">
            <h3 className="text-xs font-mono text-crack-cyan tracking-widest mb-4">SURFACE_ANOMALIES</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.surface.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#00B4D8" opacity={0.1} />
                  <XAxis dataKey="surface" stroke={COLORS.cyan} fontSize={10} />
                  <YAxis stroke={COLORS.cyan} fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: '#03045E', borderColor: '#00B4D8', fontFamily: 'monospace' }} cursor={{fill: 'rgba(0, 180, 216, 0.1)'}}/>
                  <Bar dataKey="cracks" fill={COLORS.electric} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="lg:col-span-3 flex flex-col xl:flex-row gap-6">
            {/* ORIENTATION RADAR CHART */}
            <div className="flex-1 border border-crack-electric/30 bg-crack-deep/20 p-4 relative group flex flex-col">
              <h3 className="text-xs font-mono text-crack-cyan tracking-widest mb-4">SPATIAL_ORIENTATION</h3>
              <div className="h-64 w-full flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data.orientation.data}>
                    <PolarGrid stroke={COLORS.cyan} opacity={0.3} />
                    <PolarAngleAxis dataKey="orientation" tick={{ fill: COLORS.cyan, fontSize: 10, fontFamily: 'monospace' }} />
                    <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={{ fill: COLORS.cyan, fontSize: 10 }} />
                    <Radar name="Cracks" dataKey="count" stroke={COLORS.neon} fill={COLORS.electric} fillOpacity={0.5} />
                    <Tooltip contentStyle={{ backgroundColor: '#03045E', borderColor: '#00B4D8', fontFamily: 'monospace' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <FractalAnalysisChart data={chartData} />
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

// --- HELPER COMPONENT FOR SUMMARY CARDS ---
const SummaryCard = ({ icon: Icon, title, value, color = "text-crack-neon" }: any) => (
  <div className="border border-crack-electric/50 bg-crack-deep/40 p-4 flex items-center gap-4 relative overflow-hidden group hover:border-crack-cyan transition-colors">
    <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
    <div className="p-3 bg-crack-dark border border-crack-electric rounded-sm shadow-[inset_0_0_10px_rgba(0,119,182,0.3)]">
      <Icon className={`w-6 h-6 ${color}`} />
    </div>
    <div>
      <p className="text-[10px] font-mono text-crack-cyan/70 tracking-widest">{title}</p>
      <p className={`text-2xl font-orbitron font-bold tracking-wider ${color}`}>
        {value}
      </p>
    </div>
  </div>
);

export default MainDashboard;
