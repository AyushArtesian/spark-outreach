import { useState } from 'react';
import SectionWrapper from '../SectionWrapper';

const TRAINING_IMAGES = [
  { label: 'Cat A', emoji: '🐱', known: true },
  { label: 'Cat B', emoji: '🐈', known: true },
  { label: 'Cat C', emoji: '😺', known: true },
];

const TEST_IMAGES = [
  { label: 'New Cat', emoji: '🐈‍⬛', expected: 'Cat', known: false },
  { label: 'Dog', emoji: '🐕', expected: 'Not Cat', known: false },
  { label: 'New Cat 2', emoji: '😸', expected: 'Cat', known: false },
];

export default function OverfittingSection() {
  const [tested, setTested] = useState<Record<number, boolean>>({});
  const [mode, setMode] = useState<'training' | 'testing'>('training');

  const testImage = (idx: number) => {
    setTested(prev => ({ ...prev, [idx]: true }));
  };

  return (
    <SectionWrapper id="overfitting" title="Overfitting" label="AI can memorize instead of learning" number={31}>
      <div className="flex flex-col items-center gap-6">
        <div className="flex gap-4 mb-2">
          <button
            onClick={() => { setMode('training'); setTested({}); }}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${mode === 'training' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400'}`}
          >
            Training Data
          </button>
          <button
            onClick={() => { setMode('testing'); setTested({}); }}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${mode === 'testing' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400'}`}
          >
            New Data (Test)
          </button>
        </div>

        {mode === 'training' ? (
          <div className="grid grid-cols-3 gap-4">
            {TRAINING_IMAGES.map((img, i) => (
              <div key={i} className="flex flex-col items-center gap-2 p-4 rounded-xl bg-green-900/20 border border-green-700/30">
                <span className="text-5xl">{img.emoji}</span>
                <span className="text-white text-sm font-medium">{img.label}</span>
                <div className="flex items-center gap-1 text-green-400 text-xs">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  100% correct
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {TEST_IMAGES.map((img, i) => {
              const isTested = tested[i];
              const isWrong = i === 0 || i === 2;
              return (
                <div
                  key={i}
                  onClick={() => testImage(i)}
                  className={`flex flex-col items-center gap-2 p-4 rounded-xl border cursor-pointer transition-all duration-500 ${
                    isTested
                      ? isWrong
                        ? 'bg-red-900/20 border-red-700/30 animate-pulse'
                        : 'bg-green-900/20 border-green-700/30'
                      : 'bg-gray-800/50 border-gray-700/30 hover:border-gray-600'
                  }`}
                >
                  <span className="text-5xl">{img.emoji}</span>
                  <span className="text-white text-sm font-medium">{img.label}</span>
                  {isTested ? (
                    <div className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      isWrong ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                    }`}>
                      {isWrong ? 'WRONG - "Not Cat"' : 'Correct'}
                    </div>
                  ) : (
                    <span className="text-gray-500 text-xs">Click to test</span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <p className="text-gray-500 text-xs text-center max-w-sm">
          {mode === 'training'
            ? 'The model memorized these exact images perfectly.'
            : 'But it fails on new images it has never seen before!'}
        </p>
      </div>
    </SectionWrapper>
  );
}
