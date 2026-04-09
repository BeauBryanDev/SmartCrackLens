/* * Public Landing Page
 * Describes the SmartCrackLens mission, the dangers of structural damage,
 * and the AI technology stack powering the application.
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, Cpu, Activity, ChevronRight } from 'lucide-react';
import { CyberButton } from '../components/CyberButton';

// Assumes images are placed in src/assets/
// If you use Vite, you can import them like this:
import crackImg01 from  '../assets/seg_crack_01.jpg';
import crackImg02 from '../assets/seg_crack_02.jpg';
import crackImg03 from  '../assets/seg_crack_03.jpg';
import crackImg04  from  '../assets/seg_cracked4.jpg';

export const Home: React.FC = () => {
  return (
    <div className="w-full pb-16">
      
      {/* HERO SECTION */}
      <section className="relative py-20 flex flex-col items-center text-center border-b border-crack-neon/20">
        <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
        
        <Activity className="w-16 h-16 text-crack-cyan mb-6 animate-pulse shadow-neon-border rounded-full p-2" />
        
        <h1 className="text-4xl md:text-6xl font-orbitron font-bold text-white tracking-[0.2em] uppercase mb-4 drop-shadow-[0_0_15px_rgba(0,119,182,0.8)]">
          SMART<span className="text-crack-cyan">CRACK</span>LENS
        </h1>
        
        <p className="max-w-2xl text-crack-cyan/80 font-mono text-sm md:text-base leading-relaxed mb-10">
          ADVANCED COMPUTER VISION PROTOCOL FOR STRUCTURAL HEALTH MONITORING. 
          DETECT, ANALYZE, AND PREVENT CATASTROPHIC FAILURES IN REAL-TIME.
        </p>

        <div className="flex flex-col sm:flex-row gap-6">
          <Link to="/login">
            <CyberButton variant="ghost" className="w-full sm:w-auto text-lg px-8">
              SYSTEM_LOGIN
            </CyberButton>
          </Link>
          <Link to="/register">
            <CyberButton variant="primary" className="w-full sm:w-auto text-lg px-8">
              INITIALIZE_ACCESS
            </CyberButton>
          </Link>
        </div>
      </section>

      {/* MISSION CONTENT SECTION */}
      <section className="max-w-5xl mx-auto mt-16 px-4 font-mono text-crack-cyan/80 space-y-16">
        
        {/* TEXT BLOCK 1: The Problem */}
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <ShieldAlert className="w-6 h-6 text-red-500" />
            <h2 className="text-2xl font-orbitron text-white tracking-widest uppercase">The Structural Threat</h2>
          </div>
          
          <p className="leading-relaxed text-justify">
            In industrial and urban environments, the early detection of concrete cracks is not merely a maintenance task—it is a critical safety imperative. Micro-fractures often serve as the initial symptom of deep structural fatigue, compromising the integrity of load-bearing walls, bridges, and dam infrastructures. Ignoring these early warning signs inevitably leads to accelerated degradation, exorbitant repair costs, and catastrophic collapses.
          </p>
          
          <p className="leading-relaxed text-justify">
            Concrete deterioration is driven by a multitude of unavoidable factors. Environmental thermal expansion, continuous mechanical stress from heavy machinery, ground settlement, and moisture infiltration all conspire to break down structural bonds. Once water penetrates a hairline crack, it oxidizes the internal steel rebar, expanding it and causing the concrete to spall and shatter from the inside out.
          </p>

          <div className="my-10 border border-crack-electric/50 p-2 bg-crack-deep/30 relative group">
            <div className="absolute inset-0 bg-crack-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            {/* IMAGE 1 */}
            <img 
              src={crackImg01} 
              alt="Industrial Crack Detection Example 1" 
              className="w-full h-auto object-cover grayscale hover:grayscale-0 transition-all duration-700 border border-crack-neon/30"
            />
            <div className="absolute bottom-4 left-4 bg-crack-dark/90 px-3 py-1 border border-crack-cyan text-xs">
              SCAN_RESULT_01: SEVERE_FRACTURE_DETECTED
            </div>
          </div>

          <p className="leading-relaxed text-justify">
            Traditional human inspection methods are painfully slow, subjective, and prone to error, especially in hard-to-reach industrial sectors. The modern engineering landscape demands an automated, objective, and highly scalable solution to monitor these anomalies before they breach critical safety thresholds.
          </p>
        </div>
        <p className="leading-relaxed text-justify"> 
        Cracks in concrete structures represent significant safety risks, as they often signal underlying structural distress or compromised load-bearing capacity. While some fissures are superficial, others act as "entry points" for moisture, chlorides, and aggressive chemicals that penetrate deep into the material, leading to the corrosion of internal steel reinforcement. This process, known as carbonation, results in rust expansion that creates internal pressure, further fracturing the concrete and ultimately reducing the structure's service life and overall stability
        </p>
        <p className="leading-relaxed text-justify">
        The timely detection of these defects is critical because small, manageable cracks can quickly evolve into complex systems of destruction if left untreated. Proactive monitoring allows engineers to implement cost-effective repairs and preventive measures before significant damage occurs, avoiding the need for expensive total replacements or the risk of catastrophic failure. In critical infrastructure like bridges or power plants, early identification through automated systems ensures public safety and maintains the continuous operational integrity of the facility.
        </p>
        <div className="my-10 border border-crack-electric/50 p-2 bg-crack-deep/30 relative group">
            <div className="absolute inset-0 bg-crack-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            {/* IMAGE 1 */}
            <img 
              src={crackImg04} 
              alt="Industrial Crack Detection Example 1" 
              className="w-full h-auto object-cover grayscale hover:grayscale-0 transition-all duration-700 border border-crack-neon/30"
            />
            <div className="absolute bottom-4 left-4 bg-crack-dark/90 px-3 py-1 border border-crack-cyan text-xs">
               SCAN_RESULT_01: SEVERE_FRACTURE_DETECTED
            </div>
          </div>
        <p className="leading-relaxed text-justify">
        From a geometric perspective, cracks exhibit a distinct fractal nature characterized by irregularity, roughness, and self-similarity across different scales. This fractal dimension serves as a quantitative index for damage assessment, as the complexity of the crack pattern is directly related to the energy dissipated during the fracture process and the overall degradation level of the concrete. Because these patterns cannot be fully captured by traditional Euclidean geometry, analyzing their fractal characteristics is essential for developing precise computer vision models that can accurately categorize the severity of structural damage.
        </p>
        {/* TEXT BLOCK 2: The Technology */}
        <div className="space-y-6 pt-8 border-t border-crack-neon/20">
          <div className="flex items-center gap-3 mb-6">
            <Cpu className="w-6 h-6 text-crack-electric" />
            <h2 className="text-2xl font-orbitron text-white tracking-widest uppercase">The Neural Architecture</h2>
          </div>
          
          <p className="leading-relaxed text-justify">
            SmartCrackLens was engineered to solve this problem  using state-of-the-art Deep Learning. The core intelligence relies on a custom-trained YOLOv8-nano-seg model. Trained on high-performance GPUs within Google Colab, this model has learned to precisely segment crack topologies down to the pixel level, distinguishing structural anomalies from natural concrete textures, shadows, and debris.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-10">
            {/* IMAGE 2 */}
            <div className="border border-crack-electric/50 p-2 bg-crack-deep/30 relative group">
              <img 
                src={crackImg02} 
                alt="AI Segmentation Mask Example" 
                className="w-full h-48 object-cover grayscale hover:grayscale-0 transition-all duration-700"
              />
              <div className="absolute top-4 left-4 bg-crack-dark/90 px-2 py-1 border border-crack-cyan text-[10px]">
                 INFERENCE_MASK_01
              </div>
            </div>
            {/* IMAGE 3 */}
            <div className="border border-crack-electric/50 p-2 bg-crack-deep/30 relative group">
              <img 
                src={crackImg03} 
                alt="Model Confidence Heatmap" 
                className="w-full h-48 object-cover grayscale hover:grayscale-0 transition-all duration-700"
              />
              <div className="absolute top-4 left-4 bg-crack-dark/90 px-2 py-1 border border-crack-cyan text-[10px]">
                 INFERENCE_MASK_02
              </div>
            </div>
          </div>

          <p className="leading-relaxed text-justify">
            To achieve maximum inference speed without compromising accuracy, the trained weights were exported to ONNX format. The backend infrastructure is powered by a high-concurrency FastAPI server, utilizing ONNXRuntime for hardware-accelerated predictions and OpenCV2 for rapid image tensor preprocessing. This ensures that massive images are analyzed in milliseconds.
          </p>
          
          <p className="leading-relaxed text-justify">
            Finally, all telemetry, inference metadata, and user contexts are persisted in a robust MongoDB database. This NoSQL architecture allows the system to seamlessly scale, linking geometric crack data to specific industrial locations, and providing the foundation for the predictive analytics rendered in this Command Center to detect cracks in wall and concreate surfaces.
          </p>
        </div>

      </section>
    </div>
  );
};

export default Home;