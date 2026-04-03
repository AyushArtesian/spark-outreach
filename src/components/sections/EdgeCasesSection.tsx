import { useState } from 'react';
import SectionWrapper from '../SectionWrapper';

const EDGE_CASES = [
  {
    name: 'Optical Illusion',
    description: 'Is it a duck or a rabbit?',
    emoji: '🐰',
    prediction: 'Rabbit (52%) / Duck (48%)',
    confused: true,
  },
  {
    name: 'Camouflage',
    description: 'Hidden animal in leaves',
    emoji: '🍃',
    prediction: 'Leaves (89%) - Missed the frog!',
    confused: true,
  },
  {
    name: 'Unusual Angle',
    description: 'Car photographed from below',
    emoji: '🚗',
    prediction: 'Unknown Object (67%)',
    confused: true,
  },
  {
    name: 'Adversarial Pattern',
    description: 'Modified pixels trick AI',
    emoji: '🔲',
    prediction: 'Toaster (99%) - Actually a cat!',
    confused: true,
  },
];

export default function EdgeCasesSection() {
  const [selectedCase, setSelectedCase] = useState<number | null>(null);

  return (
    <SectionWrapper id="edge-cases" title="Edge Cases" label="AI struggles with unusual patterns" number={38}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {EDGE_CASES.map((ec, i) => (
          <div
            key={i}
            onClick={() => setSelectedCase(selectedCase === i ? null : i)}
            className={`flex flex-col items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-500 ${
              selectedCase === i
                ? 'bg-red-900/20 border-red-500/50 scale-105'
                : 'bg-gray-800/50 border-gray-700/30 hover:border-gray-600'
            }`}
          >
            <span className={`text-4xl transition-all duration-500 ${selectedCase === i ? 'animate-bounce' : ''}`}>
              {ec.emoji}
            </span>
            <span className="text-white text-sm font-semibold text-center">{ec.name}</span>
            <span className="text-gray-400 text-xs text-center">{ec.description}</span>
            {selectedCase === i && (
              <div className="mt-2 p-2 bg-red-900/30 rounded-lg border border-red-700/30 w-full">
                <span className="text-xs text-red-300 block text-center">AI says:</span>
                <span className="text-xs text-red-400 font-mono block text-center mt-1">{ec.prediction}</span>
                <div className="flex items-center justify-center gap-1 mt-2">
                  <span className="text-red-500 text-lg">⚠️</span>
                  <span className="text-red-400 text-xs">Confused!</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      <p className="text-gray-500 text-xs text-center mt-4 max-w-md mx-auto">
        Click each card to see how AI can be confused by unusual inputs. These edge cases help researchers build more robust models.
      </p>
    </SectionWrapper>
  );
}
