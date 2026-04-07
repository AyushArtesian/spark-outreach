import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const FEATURE_TYPES = [
  { name: 'Edges', color: 'from-blue-500 to-cyan-500', pattern: 'edges' },
  { name: 'Textures', color: 'from-green-500 to-emerald-500', pattern: 'textures' },
  { name: 'Shapes', color: 'from-purple-500 to-pink-500', pattern: 'shapes' },
  { name: 'Colors', color: 'from-orange-500 to-red-500', pattern: 'colors' },
];

function FeatureGrid({ pattern, visible }: { pattern: string; visible: boolean }) {
  const getPattern = (r: number, c: number) => {
    switch (pattern) {
      case 'edges':
        return (r === 0 || c === 0 || r === 4 || c === 4) ? 0.9 : 0.1;
      case 'textures':
        return (r + c) % 2 === 0 ? 0.8 : 0.2;
      case 'shapes':
        return Math.abs(r - 2) + Math.abs(c - 2) <= 2 ? 0.9 : 0.15;
      case 'colors':
        return (r * 5 + c) / 25;
      default:
        return 0.5;
    }
  };

  return (
    <div className={`inline-grid gap-0.5 transition-all duration-700 ${visible ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}`}>
      {Array.from({ length: 5 }, (_, r) => (
        <div key={r} className="flex gap-0.5">
          {Array.from({ length: 5 }, (_, c) => {
            const intensity = getPattern(r, c);
            return (
              <div
                key={c}
                className="w-8 h-8 rounded"
                style={{ backgroundColor: `rgba(255,255,255,${intensity})` }}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

export default function FeatureMapsSection() {
  const [visibleLayers, setVisibleLayers] = useState(0);

  useEffect(() => {
    if (visibleLayers < FEATURE_TYPES.length) {
      const timer = setTimeout(() => setVisibleLayers(v => v + 1), 600);
      return () => clearTimeout(timer);
    }
  }, [visibleLayers]);

  return (
    <SectionWrapper id="feature-maps" title="Feature Maps" label="Different filters detect different patterns" number={22}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {FEATURE_TYPES.map((ft, i) => (
          <div key={ft.name} className="flex flex-col items-center gap-3">
            <FeatureGrid pattern={ft.pattern} visible={i < visibleLayers} />
            <div className={`text-sm font-semibold bg-gradient-to-r ${ft.color} bg-clip-text text-transparent transition-opacity duration-500 ${i < visibleLayers ? 'opacity-100' : 'opacity-0'}`}>
              {ft.name}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-600 to-transparent" />
        <span className="text-gray-400 text-xs">Stacked feature maps build understanding</span>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-600 to-transparent" />
      </div>
      <button
        onClick={() => setVisibleLayers(0)}
        className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-lg transition-colors"
      >
        Replay Animation
      </button>
    </SectionWrapper>
  );
}
