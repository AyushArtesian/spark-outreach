import { useState } from 'react';
import SectionWrapper from '../SectionWrapper';

const OBJECTS_DEPTH = [
  { emoji: '🏔️', label: 'Mountain', depth: 100, y: 15, x: 50, size: 'text-5xl' },
  { emoji: '🏠', label: 'House', depth: 60, y: 40, x: 30, size: 'text-4xl' },
  { emoji: '🌳', label: 'Tree', depth: 40, y: 50, x: 70, size: 'text-3xl' },
  { emoji: '🚗', label: 'Car', depth: 20, y: 70, x: 45, size: 'text-2xl' },
  { emoji: '🧑', label: 'Person', depth: 5, y: 75, x: 65, size: 'text-3xl' },
];

export default function DepthPerceptionSection() {
  const [showDepth, setShowDepth] = useState(false);

  return (
    <SectionWrapper id="depth" title="Depth Perception" label="AI can estimate distance in images" number={35}>
      <div className="flex flex-col items-center gap-6">
        <div className="relative w-80 h-64 rounded-xl border border-gray-700 overflow-hidden">
          {/* Background gradient - sky to ground */}
          <div className={`absolute inset-0 transition-all duration-700 ${
            showDepth
              ? 'bg-gradient-to-b from-blue-900 via-purple-900 to-red-900'
              : 'bg-gradient-to-b from-sky-800/50 via-sky-900/30 to-green-900/40'
          }`} />

          {OBJECTS_DEPTH.map((obj, i) => (
            <div
              key={i}
              className={`absolute transition-all duration-700 ${obj.size}`}
              style={{
                left: `${obj.x}%`,
                top: `${obj.y}%`,
                transform: 'translate(-50%, -50%)',
                filter: showDepth ? `blur(${obj.depth / 30}px)` : 'none',
                opacity: showDepth ? 1 - obj.depth / 150 : 1,
              }}
            >
              {obj.emoji}
            </div>
          ))}

          {/* Depth labels */}
          {showDepth && OBJECTS_DEPTH.map((obj, i) => (
            <div
              key={`label-${i}`}
              className="absolute text-xs font-mono px-1.5 py-0.5 rounded bg-black/60 transition-opacity duration-500"
              style={{
                left: `${obj.x}%`,
                top: `${obj.y + 6}%`,
                transform: 'translateX(-50%)',
                color: obj.depth > 60 ? '#60a5fa' : obj.depth > 30 ? '#a78bfa' : '#f87171',
              }}
            >
              {obj.depth}m away
            </div>
          ))}

          {/* Depth scale */}
          {showDepth && (
            <div className="absolute right-2 top-2 bottom-2 w-4 rounded-full overflow-hidden border border-gray-600">
              <div className="w-full h-full bg-gradient-to-b from-blue-500 via-purple-500 to-red-500" />
              <span className="absolute -left-6 top-0 text-xs text-blue-400">Far</span>
              <span className="absolute -left-8 bottom-0 text-xs text-red-400">Near</span>
            </div>
          )}
        </div>

        <button
          onClick={() => setShowDepth(d => !d)}
          className={`px-4 py-2 text-sm rounded-lg transition-colors text-white ${
            showDepth ? 'bg-purple-600 hover:bg-purple-500' : 'bg-blue-600 hover:bg-blue-500'
          }`}
        >
          {showDepth ? 'Show Normal View' : 'Show Depth Map'}
        </button>
      </div>
    </SectionWrapper>
  );
}
