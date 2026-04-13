import React from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell, Legend
} from 'recharts';
import { Activity } from 'lucide-react';
import { FractalChartData  } from '@/types';


interface Props {

  data: FractalChartData[];

}

// Cyberpunk HUD Severity Palette
const SEVERITY_COLORS: Record<string, string> = {
  high: '#EF4444',   // Red
  medium: '#F59E0B', // Amber/Orange
  low: '#00B4D8',    // Crack-Cyan
};

export const FractalAnalysisChart: React.FC<Props> = ({ data }) => {
  
  if (!data || data.length === 0) {
    return (

      <div className="w-full h-[400px] border border-crack-electric/30 bg-crack-deep/20 flex flex-col items-center justify-center">
        <Activity className="w-8 h-8 text-crack-cyan/30 mb-2 animate-pulse" />
        <span className="text-crack-cyan/50 font-mono text-xs tracking-widest">INSUFFICIENT_FRACTAL_DATA</span>
      </div>
    );
  }

  return (
    <div className="w-full h-[450px] border border-crack-electric/30 bg-crack-deep/20 p-4 relative group flex flex-col">
      {/* Background grid effect */}
      <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
      
      <div className="mb-4 relative z-10 flex items-center justify-between">
        <h3 className="text-xs font-mono text-crack-cyan tracking-widest">
           FRACTAL_COMPLEXITY_MATRIX
        </h3>
        <span className="text-[10px] font-mono text-crack-cyan/50 uppercase">
          Area vs Box-Counting Dim
        </span>
      </div>
      
      <div className="flex-1 w-full relative z-10">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
            {/* Dark Cyberpunk Grid */}
            <CartesianGrid strokeDasharray="3 3" stroke="#00B4D8" opacity={0.1} />
            
            <XAxis 
              type="number" 
              dataKey="area" 
              name="Mask Area" 
              unit="px²" 
              stroke="#00B4D8"
              fontSize={10}
              tickMargin={10}
              label={{ value: 'SURFACE AREA (px²)', position: 'bottom', fill: '#00B4D8', fontSize: 10, fontFamily: 'monospace' }}
            />
            
            <YAxis 
              type="number" 
              dataKey="fractalDim" 
              name="Fractal Dimension" 
              domain={[1.0, 2.0]}
              stroke="#00B4D8"
              fontSize={10}
              tickCount={6}
              label={{ value: 'FRACTAL DIM (FD)', angle: -90, position: 'insideLeft', fill: '#00B4D8', fontSize: 10, fontFamily: 'monospace', offset: 15 }}
            />
            
            {/* ZAxis mapping area to bubble radius (range is in pixels) */}
            <ZAxis type="number" dataKey="area" range={[40, 300]} />
            
            {/* Custom Terminal-Style Tooltip */}
            <Tooltip 
              cursor={{ strokeDasharray: '3 3', stroke: '#90E0EF', strokeWidth: 1 }} 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const info = payload[0].payload as FractalChartData;
                  const color = SEVERITY_COLORS[info.severity] || '#90E0EF';
                  
                  return (
                    <div className="bg-crack-dark/95 border border-crack-cyan p-3 shadow-[0_0_15px_rgba(0,119,182,0.4)] backdrop-blur-sm">
                      <p className="font-mono text-xs text-white border-b border-crack-neon/30 pb-1 mb-2 tracking-wider">
                        FILE: {info.filename}
                      </p>
                      <div className="font-mono text-[10px] space-y-1">
                        <p className="text-crack-cyan">AREA: <span className="text-white">{info.area} px²</span></p>
                        <p className="text-crack-cyan">FRACTAL_DIM: <span className="text-white">{info.fractalDim.toFixed(3)}</span></p>
                        <p className="flex items-center gap-2">
                          <span className="text-crack-cyan">SEVERITY:</span> 
                          <span className="uppercase font-bold tracking-widest" style={{ color }}>
                            [{info.severity}]
                          </span>
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            
            <Legend 
              verticalAlign="top" 
              height={36} 
              iconType="circle"
              wrapperStyle={{ fontSize: '10px', fontFamily: 'monospace', color: '#00B4D8' }}
              payload={[
                { value: 'HIGH_RISK', type: 'circle', color: SEVERITY_COLORS.high },
                { value: 'MODERATE_RISK', type: 'circle', color: SEVERITY_COLORS.medium },
                { value: 'LOW_RISK', type: 'circle', color: SEVERITY_COLORS.low },
              ]}
            />

            <Scatter name="Anomalies" data={data}>
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={SEVERITY_COLORS[entry.severity] || '#00B4D8'} 
                  fillOpacity={0.7}
                  stroke={SEVERITY_COLORS[entry.severity] || '#00B4D8'}
                  strokeWidth={1}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};