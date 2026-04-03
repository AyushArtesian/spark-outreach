import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const FACES = [
  { x: 25, y: 15, w: 20, h: 25 },
  { x: 60, y: 20, w: 18, h: 23 },
];

export default function FaceDetectionSection() {
  const [detected, setDetected] = useState<number[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanLine, setScanLine] = useState(0);

  const startScan = () => {
    setDetected([]);
    setScanning(true);
    setScanLine(0);
  };

  useEffect(() => {
    if (!scanning) return;
    const timer = setInterval(() => {
      setScanLine(prev => {
        const next = prev + 2;
        if (next > 100) {
          setScanning(false);
          return 0;
        }
        FACES.forEach((face, idx) => {
          if (next >= face.y + face.h / 2) {
            setDetected(d => d.includes(idx) ? d : [...d, idx]);
          }
        });
        return next;
      });
    }, 30);
    return () => clearInterval(timer);
  }, [scanning]);

  useEffect(() => { startScan(); }, []);

  return (
    <SectionWrapper id="face-detection" title="Face Detection" label="AI detects faces using patterns" number={24}>
      <div className="flex flex-col items-center gap-6">
        <div className="relative w-80 h-56 bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
          {/* Simulated scene with people */}
          <div className="absolute inset-0 bg-gradient-to-b from-blue-900/40 to-gray-900/60" />
          {/* Person silhouettes */}
          <div className="absolute" style={{ left: '25%', top: '15%', width: '20%', height: '50%' }}>
            <div className="w-full aspect-square rounded-full bg-gradient-to-b from-amber-200 to-amber-300 mx-auto" style={{ width: '60%' }} />
            <div className="w-full h-1/2 bg-gradient-to-b from-blue-400 to-blue-500 rounded-t-lg mt-1" />
          </div>
          <div className="absolute" style={{ left: '60%', top: '20%', width: '18%', height: '45%' }}>
            <div className="w-full aspect-square rounded-full bg-gradient-to-b from-amber-100 to-amber-200 mx-auto" style={{ width: '55%' }} />
            <div className="w-full h-1/2 bg-gradient-to-b from-red-400 to-red-500 rounded-t-lg mt-1" />
          </div>

          {/* Scan line */}
          {scanning && (
            <div
              className="absolute left-0 right-0 h-0.5 bg-green-400 shadow-lg shadow-green-400/50 transition-none"
              style={{ top: `${scanLine}%` }}
            />
          )}

          {/* Detection boxes */}
          {FACES.map((face, idx) => (
            detected.includes(idx) && (
              <div
                key={idx}
                className="absolute border-2 border-green-400 rounded animate-pulse"
                style={{
                  left: `${face.x}%`,
                  top: `${face.y}%`,
                  width: `${face.w}%`,
                  height: `${face.h}%`,
                }}
              >
                <span className="absolute -top-5 left-0 text-green-400 text-xs font-mono bg-gray-900/80 px-1 rounded">
                  Face {idx + 1}
                </span>
              </div>
            )
          ))}
        </div>
        <button
          onClick={startScan}
          disabled={scanning}
          className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-700 text-white text-sm rounded-lg transition-colors"
        >
          {scanning ? 'Scanning...' : 'Detect Faces'}
        </button>
      </div>
    </SectionWrapper>
  );
}
