import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const LAYERS = [
  { name: 'Input', desc: 'Raw pixels', icon: '🖼️', color: 'from-gray-500 to-gray-400' },
  { name: 'Layer 1', desc: 'Edges & lines', icon: '📐', color: 'from-blue-500 to-blue-400' },
  { name: 'Layer 2', desc: 'Shapes & textures', icon: '🔷', color: 'from-purple-500 to-purple-400' },
  { name: 'Layer 3', desc: 'Parts & features', icon: '🧩', color: 'from-pink-500 to-pink-400' },
  { name: 'Output', desc: 'Full recognition', icon: '🎯', color: 'from-green-500 to-green-400' },
];

export default function LayersSection() {
  const [activeLayer, setActiveLayer] = useState(-1);
  const [isAnimating, setIsAnimating] = useState(false);

  const animate = () => {
    setIsAnimating(true);
    setActiveLayer(-1);
  };

  useEffect(() => {
    if (!isAnimating) return;
    if (activeLayer < LAYERS.length - 1) {
      const timer = setTimeout(() => setActiveLayer(a => a + 1), 700);
      return () => clearTimeout(timer);
    } else {
      setIsAnimating(false);
    }
  }, [activeLayer, isAnimating]);

  useEffect(() => {
    animate();
  }, []);

  return (
    <SectionWrapper id="layers" title="Layers in Vision Models" label="AI understands images step-by-step through layers" number={23}>
      <div className="flex flex-col md:flex-row items-center gap-2 md:gap-0">
        {LAYERS.map((layer, i) => (
          <div key={layer.name} className="flex items-center">
            <div
              className={`flex flex-col items-center p-4 rounded-xl border-2 transition-all duration-500 min-w-28 ${
                i <= activeLayer
                  ? 'border-white/30 bg-gradient-to-b ' + layer.color + ' shadow-lg shadow-white/10 scale-105'
                  : 'border-gray-700 bg-gray-800/50 scale-95 opacity-40'
              }`}
            >
              <span className="text-2xl mb-1">{layer.icon}</span>
              <span className="text-white font-semibold text-sm">{layer.name}</span>
              <span className={`text-xs mt-1 ${i <= activeLayer ? 'text-white/80' : 'text-gray-500'}`}>{layer.desc}</span>
            </div>
            {i < LAYERS.length - 1 && (
              <div className={`w-8 h-0.5 md:w-10 transition-all duration-500 ${i < activeLayer ? 'bg-gradient-to-r from-white/60 to-white/30' : 'bg-gray-700'}`} />
            )}
          </div>
        ))}
      </div>
      <button
        onClick={animate}
        disabled={isAnimating}
        className="mt-6 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white text-sm rounded-lg transition-colors"
      >
        {isAnimating ? 'Processing...' : 'Replay'}
      </button>
    </SectionWrapper>
  );
}
