import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const PREDICTIONS = [
  { label: 'Cat', confidence: 92, emoji: '🐱' },
  { label: 'Dog', confidence: 5, emoji: '🐶' },
  { label: 'Rabbit', confidence: 2, emoji: '🐰' },
  { label: 'Fox', confidence: 1, emoji: '🦊' },
];

export default function ConfidenceScoreSection() {
  const [animatedValues, setAnimatedValues] = useState<number[]>(PREDICTIONS.map(() => 0));
  const [isAnimating, setIsAnimating] = useState(false);

  const animate = () => {
    setAnimatedValues(PREDICTIONS.map(() => 0));
    setIsAnimating(true);
  };

  useEffect(() => {
    if (!isAnimating) return;
    const duration = 1500;
    const startTime = Date.now();

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - progress, 3);

      setAnimatedValues(PREDICTIONS.map(p => Math.round(p.confidence * eased)));

      if (progress >= 1) {
        clearInterval(timer);
        setIsAnimating(false);
      }
    }, 16);
    return () => clearInterval(timer);
  }, [isAnimating]);

  useEffect(() => { animate(); }, []);

  return (
    <SectionWrapper id="confidence" title="Confidence Score" label="AI gives confidence, not certainty" number={33}>
      <div className="flex flex-col items-center gap-6">
        <div className="text-6xl mb-2">🐱</div>
        <div className="text-gray-400 text-sm mb-4">What does AI think this is?</div>

        <div className="w-full max-w-md space-y-3">
          {PREDICTIONS.map((pred, i) => (
            <div key={pred.label} className="flex items-center gap-3">
              <span className="text-xl w-8">{pred.emoji}</span>
              <span className="text-white text-sm w-16">{pred.label}</span>
              <div className="flex-1 h-8 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full flex items-center justify-end pr-3 transition-all duration-100"
                  style={{
                    width: `${Math.max(4, animatedValues[i])}%`,
                    background: i === 0
                      ? 'linear-gradient(90deg, #3b82f6, #22d3ee)'
                      : 'linear-gradient(90deg, #374151, #4b5563)',
                  }}
                >
                  <span className={`text-xs font-mono font-bold ${i === 0 ? 'text-white' : 'text-gray-400'}`}>
                    {animatedValues[i]}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-blue-900/20 border border-blue-700/30 rounded-lg p-3 max-w-md">
          <p className="text-blue-300 text-xs text-center">
            AI outputs probabilities, not absolute answers. A 92% confidence means the model is fairly sure, but there is still an 8% chance it could be wrong.
          </p>
        </div>

        <button
          onClick={animate}
          disabled={isAnimating}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 text-white text-sm rounded-lg transition-colors"
        >
          Replay Animation
        </button>
      </div>
    </SectionWrapper>
  );
}
