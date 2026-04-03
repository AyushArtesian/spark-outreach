import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const OBJECTS = [
  { label: 'Car', x: 5, y: 55, w: 25, h: 22, color: '#3b82f6', conf: 96 },
  { label: 'Person', x: 35, y: 25, w: 12, h: 35, color: '#22c55e', conf: 91 },
  { label: 'Tree', x: 72, y: 15, w: 20, h: 45, color: '#a855f7', conf: 88 },
  { label: 'Dog', x: 52, y: 62, w: 15, h: 15, color: '#f59e0b', conf: 85 },
  { label: 'Bird', x: 60, y: 5, w: 8, h: 8, color: '#ef4444', conf: 72 },
];

export default function MultiObjectSection() {
  const [detected, setDetected] = useState(0);
  const [isDetecting, setIsDetecting] = useState(false);

  const startDetection = () => {
    setDetected(0);
    setIsDetecting(true);
  };

  useEffect(() => {
    if (!isDetecting) return;
    if (detected < OBJECTS.length) {
      const timer = setTimeout(() => setDetected(d => d + 1), 500);
      return () => clearTimeout(timer);
    } else {
      setIsDetecting(false);
    }
  }, [detected, isDetecting]);

  useEffect(() => { startDetection(); }, []);

  return (
    <SectionWrapper id="multi-object" title="Multi-Object Scenes" label="AI can detect many objects at once" number={34}>
      <div className="flex flex-col items-center gap-6">
        <div className="relative w-80 h-56 bg-gradient-to-b from-sky-900/50 to-green-900/30 rounded-xl border border-gray-700 overflow-hidden">
          {/* Scene elements */}
          <div className="absolute bottom-0 left-0 right-0 h-2/5 bg-gradient-to-t from-green-800/60 to-transparent" />

          {/* Car */}
          <div className="absolute text-3xl" style={{ left: '10%', bottom: '18%' }}>🚗</div>
          {/* Person */}
          <div className="absolute text-3xl" style={{ left: '37%', top: '25%' }}>🧑</div>
          {/* Tree */}
          <div className="absolute text-4xl" style={{ right: '12%', top: '15%' }}>🌳</div>
          {/* Dog */}
          <div className="absolute text-2xl" style={{ left: '54%', bottom: '15%' }}>🐕</div>
          {/* Bird */}
          <div className="absolute text-lg" style={{ left: '60%', top: '5%' }}>🐦</div>

          {/* Detection boxes */}
          {OBJECTS.map((obj, i) => (
            i < detected && (
              <div
                key={i}
                className="absolute transition-all duration-300"
                style={{
                  left: `${obj.x}%`,
                  top: `${obj.y}%`,
                  width: `${obj.w}%`,
                  height: `${obj.h}%`,
                  border: `2px solid ${obj.color}`,
                  borderRadius: '4px',
                  animation: 'fadeIn 0.3s ease-out',
                }}
              >
                <span
                  className="absolute -top-5 left-0 text-xs font-mono px-1 rounded"
                  style={{ backgroundColor: obj.color, color: 'white' }}
                >
                  {obj.label} {obj.conf}%
                </span>
              </div>
            )
          ))}

          <div className="absolute top-2 right-2 text-xs font-mono text-white bg-gray-900/80 px-2 py-1 rounded">
            Objects: {detected}/{OBJECTS.length}
          </div>
        </div>

        <button
          onClick={startDetection}
          disabled={isDetecting}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white text-sm rounded-lg transition-colors"
        >
          {isDetecting ? 'Detecting...' : 'Detect Objects'}
        </button>
      </div>
    </SectionWrapper>
  );
}
