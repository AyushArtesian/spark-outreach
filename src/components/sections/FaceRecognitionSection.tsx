import { useState } from 'react';
import SectionWrapper from '../SectionWrapper';

const FACE_PAIRS = [
  { face1: 'Person A (Photo 1)', face2: 'Person A (Photo 2)', similarity: 94, match: true },
  { face1: 'Person A', face2: 'Person B', similarity: 23, match: false },
  { face1: 'Person B (Photo 1)', face2: 'Person B (Photo 2)', similarity: 91, match: true },
];

function FaceIcon({ label, glow }: { label: string; glow: boolean }) {
  return (
    <div className={`flex flex-col items-center transition-all duration-700 ${glow ? 'scale-105' : ''}`}>
      <div className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl transition-all duration-700 ${
        glow ? 'bg-green-500/30 ring-4 ring-green-400 shadow-lg shadow-green-400/30' : 'bg-gray-700 ring-2 ring-gray-600'
      }`}>
        <svg viewBox="0 0 24 24" className="w-10 h-10" fill="none" stroke={glow ? '#4ade80' : '#9ca3af'} strokeWidth={1.5}>
          <circle cx="12" cy="8" r="4" />
          <path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" />
        </svg>
      </div>
      <span className="text-xs text-gray-400 mt-2 text-center">{label}</span>
    </div>
  );
}

export default function FaceRecognitionSection() {
  const [selectedPair, setSelectedPair] = useState(0);
  const [showResult, setShowResult] = useState(true);
  const pair = FACE_PAIRS[selectedPair];

  const handleSelect = (idx: number) => {
    setShowResult(false);
    setSelectedPair(idx);
    setTimeout(() => setShowResult(true), 300);
  };

  return (
    <SectionWrapper id="face-recognition" title="Face Recognition" label="Detection = finding face, Recognition = identifying person" number={25}>
      <div className="flex flex-col items-center gap-6">
        <div className="flex items-center gap-8">
          <FaceIcon label={pair.face1} glow={showResult && pair.match} />
          <div className="flex flex-col items-center">
            <div className={`text-3xl font-bold transition-all duration-700 ${
              showResult ? (pair.match ? 'text-green-400' : 'text-red-400') : 'text-gray-600'
            }`}>
              {showResult ? `${pair.similarity}%` : '...'}
            </div>
            <span className="text-xs text-gray-500 mt-1">similarity</span>
            {showResult && (
              <span className={`text-xs font-semibold mt-2 px-3 py-1 rounded-full ${
                pair.match ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {pair.match ? 'MATCH' : 'NO MATCH'}
              </span>
            )}
          </div>
          <FaceIcon label={pair.face2} glow={showResult && pair.match} />
        </div>

        <div className="flex gap-2">
          {FACE_PAIRS.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSelect(i)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                i === selectedPair ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {p.face1} vs {p.face2}
            </button>
          ))}
        </div>
      </div>
    </SectionWrapper>
  );
}
