import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

interface MovingObject {
  id: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  size: number;
  color: string;
}

export default function MotionDetectionSection() {
  const [objects, setObjects] = useState<MovingObject[]>([
    { id: 0, x: 20, y: 30, dx: 0.8, dy: 0.3, size: 12, color: '#3b82f6' },
    { id: 1, x: 70, y: 60, dx: -0.5, dy: 0.6, size: 10, color: '#ef4444' },
    { id: 2, x: 50, y: 20, dx: 0.3, dy: -0.4, size: 8, color: '#22c55e' },
  ]);
  const [showMotion, setShowMotion] = useState(true);
  const [trails, setTrails] = useState<{ x: number; y: number; id: number }[]>([]);

  useEffect(() => {
    const timer = setInterval(() => {
      setObjects(prev => prev.map(obj => {
        let nx = obj.x + obj.dx;
        let ny = obj.y + obj.dy;
        let ndx = obj.dx;
        let ndy = obj.dy;
        if (nx < 5 || nx > 95) ndx = -ndx;
        if (ny < 5 || ny > 95) ndy = -ndy;
        nx = Math.max(5, Math.min(95, nx));
        ny = Math.max(5, Math.min(95, ny));
        return { ...obj, x: nx, y: ny, dx: ndx, dy: ndy };
      }));
      setTrails(prev => {
        const newTrails = objects.map(o => ({ x: o.x, y: o.y, id: o.id }));
        return [...prev.slice(-30), ...newTrails];
      });
    }, 50);
    return () => clearInterval(timer);
  }, [objects]);

  return (
    <SectionWrapper id="motion-detection" title="Motion Detection" label="AI detects movement in videos" number={27}>
      <div className="flex flex-col items-center gap-4">
        <div className="relative w-80 h-56 bg-gray-900 rounded-xl overflow-hidden border border-gray-700">
          {/* Grid overlay */}
          <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            {Array.from({ length: 10 }, (_, i) => (
              <g key={i}>
                <line x1={i * 10} y1="0" x2={i * 10} y2="100" stroke="#374151" strokeWidth="0.3" />
                <line x1="0" y1={i * 10} x2="100" y2={i * 10} stroke="#374151" strokeWidth="0.3" />
              </g>
            ))}
          </svg>

          <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            {/* Motion trails */}
            {showMotion && trails.map((t, i) => (
              <circle
                key={i}
                cx={t.x} cy={t.y}
                r="1"
                fill={objects.find(o => o.id === t.id)?.color || '#fff'}
                opacity={0.15}
              />
            ))}

            {/* Moving objects */}
            {objects.map(obj => (
              <g key={obj.id}>
                <circle cx={obj.x} cy={obj.y} r={obj.size / 2} fill={obj.color} opacity={0.8} />
                {showMotion && (
                  <>
                    <rect
                      x={obj.x - obj.size / 2 - 2}
                      y={obj.y - obj.size / 2 - 2}
                      width={obj.size + 4}
                      height={obj.size + 4}
                      fill="none"
                      stroke="#fbbf24"
                      strokeWidth="0.5"
                      strokeDasharray="2,1"
                      className="animate-pulse"
                    />
                    <line
                      x1={obj.x} y1={obj.y}
                      x2={obj.x + obj.dx * 15} y2={obj.y + obj.dy * 15}
                      stroke="#fbbf24" strokeWidth="0.5"
                      markerEnd="url(#arrowhead)"
                    />
                  </>
                )}
              </g>
            ))}
            <defs>
              <marker id="arrowhead" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto">
                <polygon points="0 0, 6 2, 0 4" fill="#fbbf24" />
              </marker>
            </defs>
          </svg>

          {/* Label */}
          <div className="absolute top-2 left-2 text-xs font-mono text-green-400 bg-gray-900/80 px-2 py-0.5 rounded">
            {showMotion ? 'MOTION ON' : 'MOTION OFF'}
          </div>
        </div>

        <button
          onClick={() => setShowMotion(m => !m)}
          className={`px-4 py-2 text-sm rounded-lg transition-colors text-white ${
            showMotion ? 'bg-yellow-600 hover:bg-yellow-500' : 'bg-gray-600 hover:bg-gray-500'
          }`}
        >
          {showMotion ? 'Hide Motion Overlay' : 'Show Motion Overlay'}
        </button>
      </div>
    </SectionWrapper>
  );
}
