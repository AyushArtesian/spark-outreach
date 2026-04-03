import { useState } from 'react';
import SectionWrapper from '../SectionWrapper';

export default function ImageTransformSection() {
  const [rotation, setRotation] = useState(0);
  const [scale, setScale] = useState(1);
  const [flipX, setFlipX] = useState(false);
  const [flipY, setFlipY] = useState(false);

  const reset = () => {
    setRotation(0);
    setScale(1);
    setFlipX(false);
    setFlipY(false);
  };

  return (
    <SectionWrapper id="image-transform" title="Image Transformation" label="AI learns to recognize objects in different views" number={28}>
      <div className="flex flex-col items-center gap-6">
        <div className="w-64 h-64 bg-gray-800 rounded-xl overflow-hidden border border-gray-700 flex items-center justify-center">
          <div
            className="w-40 h-40 transition-all duration-500 ease-out"
            style={{
              transform: `rotate(${rotation}deg) scale(${scale}) scaleX(${flipX ? -1 : 1}) scaleY(${flipY ? -1 : 1})`,
            }}
          >
            {/* Simple house drawing */}
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <polygon points="50,10 10,45 90,45" fill="#ef4444" />
              <rect x="20" y="45" width="60" height="45" fill="#3b82f6" />
              <rect x="40" y="60" width="20" height="30" fill="#92400e" />
              <rect x="28" y="52" width="12" height="12" fill="#fbbf24" />
              <rect x="60" y="52" width="12" height="12" fill="#fbbf24" />
              <circle cx="75" cy="20" r="8" fill="#fbbf24" />
            </svg>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => setRotation(r => r + 45)}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
          >
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M1 4v6h6M23 20v-6h-6" />
              <path d="M20.49 9A9 9 0 105.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" />
            </svg>
            Rotate 45°
          </button>
          <button
            onClick={() => setScale(s => s === 1 ? 1.5 : s === 1.5 ? 0.6 : 1)}
            className="flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-lg transition-colors"
          >
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <line x1="11" y1="8" x2="11" y2="14" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>
            Scale {scale === 1 ? '1x' : scale === 1.5 ? '1.5x' : '0.6x'}
          </button>
          <button
            onClick={() => setFlipX(f => !f)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors text-white ${flipX ? 'bg-green-600' : 'bg-gray-600 hover:bg-gray-500'}`}
          >
            ↔ Flip H
          </button>
          <button
            onClick={() => setFlipY(f => !f)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors text-white ${flipY ? 'bg-green-600' : 'bg-gray-600 hover:bg-gray-500'}`}
          >
            ↕ Flip V
          </button>
        </div>
        <button onClick={reset} className="text-gray-400 hover:text-white text-xs underline">Reset</button>
      </div>
    </SectionWrapper>
  );
}
