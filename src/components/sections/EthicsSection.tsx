import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const ETHICS_CARDS = [
  {
    title: 'Privacy Concerns',
    icon: '🔒',
    color: 'from-red-500 to-orange-500',
    bgColor: 'bg-red-900/20 border-red-700/30',
    points: [
      'Facial recognition without consent',
      'Tracking people in public spaces',
      'Data collection from cameras',
    ],
  },
  {
    title: 'Surveillance Risks',
    icon: '📹',
    color: 'from-yellow-500 to-amber-500',
    bgColor: 'bg-yellow-900/20 border-yellow-700/30',
    points: [
      'Mass surveillance possibilities',
      'Government monitoring concerns',
      'Workplace surveillance ethics',
    ],
  },
  {
    title: 'Bias & Fairness',
    icon: '⚖️',
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-900/20 border-purple-700/30',
    points: [
      'Racial and gender bias in models',
      'Unequal accuracy across groups',
      'Biased training data effects',
    ],
  },
  {
    title: 'Misuse Potential',
    icon: '⚠️',
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-blue-900/20 border-blue-700/30',
    points: [
      'Deepfakes and manipulation',
      'Identity theft risks',
      'Autonomous weapons concerns',
    ],
  },
];

export default function EthicsSection() {
  const [revealedCards, setRevealedCards] = useState(0);

  useEffect(() => {
    if (revealedCards < ETHICS_CARDS.length) {
      const timer = setTimeout(() => setRevealedCards(c => c + 1), 400);
      return () => clearTimeout(timer);
    }
  }, [revealedCards]);

  return (
    <SectionWrapper id="ethics" title="Ethics in Computer Vision" label="Important considerations for AI development" number={39}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ETHICS_CARDS.map((card, i) => (
          <div
            key={i}
            className={`p-5 rounded-xl border transition-all duration-700 ${card.bgColor} ${
              i < revealedCards ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{card.icon}</span>
              <h3 className={`text-lg font-bold bg-gradient-to-r ${card.color} bg-clip-text text-transparent`}>
                {card.title}
              </h3>
            </div>
            <ul className="space-y-2">
              {card.points.map((point, j) => (
                <li key={j} className="flex items-start gap-2 text-gray-300 text-sm">
                  <span className="text-gray-600 mt-0.5">•</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <button
        onClick={() => setRevealedCards(0)}
        className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
      >
        Replay Animation
      </button>
    </SectionWrapper>
  );
}
