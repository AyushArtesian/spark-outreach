import { useState, useEffect, useRef } from 'react';
import SectionWrapper from '../SectionWrapper';

interface DetectedObj {
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  color: string;
  conf: number;
}

export default function RealTimeVisionSection() {
  const [isRunning, setIsRunning] = useState(true);
  const [fps, setFps] = useState(30);
  const [objects, setObjects] = useState<DetectedObj[]>([]);
  const frameRef = useRef(0);

  useEffect(() => {
    if (!isRunning) return;
    const timer = setInterval(() => {
      frameRef.current += 1;
      const f = frameRef.current;
      const newObjects: DetectedObj[] = [
        {
          x: 10 + Math.sin(f * 0.03) * 15,
          y: 40 + Math.cos(f * 0.02) * 10,
          w: 22, h: 18,
          label: 'Car',
          color: '#3b82f6',
          conf: 90 + Math.floor(Math.random() * 8),
        },
        {
          x: 55 + Math.sin(f * 0.05) * 8,
          y: 30 + Math.cos(f * 0.04) * 5,
          w: 10, h: 28,
          label: 'Person',
          color: '#22c55e',
          conf: 85 + Math.floor(Math.random() * 10),
        },
        {
          x: 75 + Math.cos(f * 0.02) * 5,
          y: 50 + Math.sin(f * 0.03) * 8,
          w: 12, h: 10,
          label: 'Dog',
          color: '#f59e0b',
          conf: 78 + Math.floor(Math.random() * 12),
        },
      ];
      setObjects(newObjects);
      setFps(28 + Math.floor(Math.random() * 5));
    }, 100);
    return () => clearInterval(timer);
  }, [isRunning]);

  return (
    <SectionWrapper id="realtime" title="Real-Time Vision" label="AI works in real-time for videos" number={37}>
      <div className="flex flex-col items-center gap-6">
        <div className="relative w-80 h-56 bg-gray-900 rounded-xl overflow-hidden border border-gray-700">
          {/* Simulated camera feed */}
          <div className="absolute inset-0 bg-gradient-to-b from-sky-900/30 to-green-900/20" />
          <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-green-800/40 to-transparent" />

          {/* Objects with bounding boxes */}
          {isRunning && objects.map((obj, i) => (
            <div
              key={i}
              className="absolute transition-all duration-100"
              style={{
                left: `${obj.x}%`,
                top: `${obj.y}%`,
                width: `${obj.w}%`,
                height: `${obj.h}%`,
              }}
            >
              <div className="w-full h-full border-2 rounded" style={{ borderColor: obj.color }} />
              <span
                className="absolute -top-4 left-0 text-xs font-mono px-1 rounded whitespace-nowrap"
                style={{ backgroundColor: obj.color, color: 'white', fontSize: '10px' }}
              >
                {obj.label} {obj.conf}%
              </span>
            </div>
          ))}

          {/* HUD overlay */}
          <div className="absolute top-2 left-2 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-xs font-mono text-white/80">{isRunning ? 'LIVE' : 'PAUSED'}</span>
          </div>
          <div className="absolute top-2 right-2 text-xs font-mono text-green-400 bg-gray-900/80 px-2 py-0.5 rounded">
            {isRunning ? `${fps} FPS` : '-- FPS'}
          </div>
          <div className="absolute bottom-2 left-2 text-xs font-mono text-white/60 bg-gray-900/80 px-2 py-0.5 rounded">
            Objects: {isRunning ? objects.length : 0}
          </div>
        </div>

        <button
          onClick={() => setIsRunning(r => !r)}
          className={`px-4 py-2 text-sm rounded-lg transition-colors text-white ${
            isRunning ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500'
          }`}
        >
          {isRunning ? 'Pause Feed' : 'Resume Feed'}
        </button>
      </div>
    </SectionWrapper>
  );
}
