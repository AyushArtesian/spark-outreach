import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const AUGMENTATIONS = [
  { name: 'Original', transform: '', delay: 0 },
  { name: 'Flipped', transform: 'scaleX(-1)', delay: 200 },
  { name: 'Rotated 15°', transform: 'rotate(15deg)', delay: 400 },
  { name: 'Rotated -15°', transform: 'rotate(-15deg)', delay: 600 },
  { name: 'Zoomed In', transform: 'scale(1.3)', delay: 800 },
  { name: 'Zoomed Out', transform: 'scale(0.7)', delay: 1000 },
  { name: 'Skewed', transform: 'skewX(10deg)', delay: 1200 },
  { name: 'Darkened', transform: 'brightness(0.5)', delay: 1400 },
  { name: 'Brightened', transform: 'brightness(1.5)', delay: 1600 },
];

function CatIcon({ aug, visible }: { aug: typeof AUGMENTATIONS[0]; visible: boolean }) {
  const isFilter = aug.name === 'Darkened' || aug.name === 'Brightened';
  return (
    <div className={`flex flex-col items-center gap-2 transition-all duration-500 ${visible ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}`}>
      <div
        className="w-20 h-20 bg-gray-800 rounded-lg flex items-center justify-center overflow-hidden border border-gray-700"
        style={isFilter ? { filter: aug.transform } : {}}
      >
        <svg
          viewBox="0 0 60 60"
          className="w-14 h-14"
          style={!isFilter ? { transform: aug.transform } : {}}
        >
          {/* Cat face */}
          <ellipse cx="30" cy="35" rx="18" ry="16" fill="#f59e0b" />
          <polygon points="14,25 12,8 24,20" fill="#f59e0b" />
          <polygon points="46,25 48,8 36,20" fill="#f59e0b" />
          <polygon points="14,25 12,8 24,20" fill="#d97706" opacity="0.3" />
          <polygon points="46,25 48,8 36,20" fill="#d97706" opacity="0.3" />
          <ellipse cx="23" cy="32" rx="3" ry="3.5" fill="#1e293b" />
          <ellipse cx="37" cy="32" rx="3" ry="3.5" fill="#1e293b" />
          <ellipse cx="24" cy="31" rx="1" ry="1.2" fill="white" />
          <ellipse cx="38" cy="31" rx="1" ry="1.2" fill="white" />
          <ellipse cx="30" cy="38" rx="2.5" ry="2" fill="#f472b6" />
          <line x1="12" y1="35" x2="22" y2="36" stroke="#d97706" strokeWidth="0.7" />
          <line x1="12" y1="38" x2="22" y2="38" stroke="#d97706" strokeWidth="0.7" />
          <line x1="38" y1="36" x2="48" y2="35" stroke="#d97706" strokeWidth="0.7" />
          <line x1="38" y1="38" x2="48" y2="38" stroke="#d97706" strokeWidth="0.7" />
        </svg>
      </div>
      <span className="text-xs text-gray-400">{aug.name}</span>
    </div>
  );
}

export default function DataAugmentationSection() {
  const [visibleCount, setVisibleCount] = useState(0);

  const animate = () => {
    setVisibleCount(0);
  };

  useEffect(() => {
    if (visibleCount < AUGMENTATIONS.length) {
      const timer = setTimeout(() => setVisibleCount(v => v + 1), 250);
      return () => clearTimeout(timer);
    }
  }, [visibleCount]);

  return (
    <SectionWrapper id="data-augmentation" title="Data Augmentation" label="AI is trained using many variations of same image" number={30}>
      <div className="flex flex-col items-center gap-6">
        <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
          {AUGMENTATIONS.map((aug, i) => (
            <CatIcon key={aug.name} aug={aug} visible={i < visibleCount} />
          ))}
        </div>
        <p className="text-gray-500 text-xs text-center max-w-md">
          By creating many versions of the same image, AI models learn to recognize objects regardless of orientation, lighting, or zoom level.
        </p>
        <button
          onClick={animate}
          className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white text-sm rounded-lg transition-colors"
        >
          Replay Augmentation
        </button>
      </div>
    </SectionWrapper>
  );
}
