import { useState } from 'react';
import SectionWrapper from '../SectionWrapper';

const OBJECTS = [
  { emoji: '🚗', label: 'Red Car', variants: ['🚙', '🏎️', '🚕'] },
  { emoji: '🐶', label: 'Dog', variants: ['🐕', '🦮', '🐩'] },
  { emoji: '🌳', label: 'Tree', variants: ['🌲', '🌴', '🎄'] },
];

export default function GeneralizationSection() {
  const [selectedObj, setSelectedObj] = useState(0);
  const [predictions, setPredictions] = useState<Record<number, boolean>>({});

  const predict = (varIdx: number) => {
    setPredictions(prev => ({ ...prev, [varIdx]: true }));
  };

  const obj = OBJECTS[selectedObj];

  return (
    <SectionWrapper id="generalization" title="Generalization" label="Good AI works on new unseen data" number={32}>
      <div className="flex flex-col items-center gap-6">
        <div className="flex gap-3">
          {OBJECTS.map((o, i) => (
            <button
              key={i}
              onClick={() => { setSelectedObj(i); setPredictions({}); }}
              className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                i === selectedObj ? 'bg-green-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {o.emoji} {o.label}
            </button>
          ))}
        </div>

        <div className="flex flex-col items-center gap-4">
          <div className="text-gray-400 text-sm">Trained on:</div>
          <div className="text-6xl p-4 bg-gray-800 rounded-xl border border-gray-700">{obj.emoji}</div>

          <div className="text-gray-400 text-sm mt-4">Can it recognize these new variations?</div>
          <div className="flex gap-4">
            {obj.variants.map((v, i) => (
              <div
                key={i}
                onClick={() => predict(i)}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border cursor-pointer transition-all duration-500 ${
                  predictions[i]
                    ? 'bg-green-900/20 border-green-500/50 scale-105'
                    : 'bg-gray-800/50 border-gray-700/30 hover:border-gray-600 hover:scale-102'
                }`}
              >
                <span className="text-5xl">{v}</span>
                {predictions[i] ? (
                  <span className="text-green-400 text-xs font-semibold">
                    Correctly identified as {obj.label}
                  </span>
                ) : (
                  <span className="text-gray-500 text-xs">Click to predict</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <p className="text-gray-500 text-xs text-center max-w-sm">
          A well-trained model generalizes — it correctly identifies new variations it has never seen before.
        </p>
      </div>
    </SectionWrapper>
  );
}
