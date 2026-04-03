import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const TIMELINE = [
  { year: '2020s', title: 'Self-Driving Cars', icon: '🚗', desc: 'Autonomous vehicles navigating roads', color: '#3b82f6' },
  { year: '2025+', title: 'Smart Healthcare', icon: '🏥', desc: 'AI diagnosing diseases from scans', color: '#22c55e' },
  { year: '2027+', title: 'Smart Cities', icon: '🏙️', desc: 'Traffic, safety, energy optimization', color: '#a855f7' },
  { year: '2030+', title: 'Advanced Robotics', icon: '🤖', desc: 'Robots that see and understand the world', color: '#f59e0b' },
  { year: '2035+', title: 'Augmented Reality', icon: '👓', desc: 'Seamless AR overlays on real world', color: '#ef4444' },
  { year: '2040+', title: 'AGI Vision', icon: '🧠', desc: 'Human-level visual understanding', color: '#06b6d4' },
];

export default function FutureSection() {
  const [activeIdx, setActiveIdx] = useState(-1);
  const [isAnimating, setIsAnimating] = useState(false);

  const animate = () => {
    setActiveIdx(-1);
    setIsAnimating(true);
  };

  useEffect(() => {
    if (!isAnimating) return;
    if (activeIdx < TIMELINE.length - 1) {
      const timer = setTimeout(() => setActiveIdx(a => a + 1), 600);
      return () => clearTimeout(timer);
    } else {
      setIsAnimating(false);
    }
  }, [activeIdx, isAnimating]);

  useEffect(() => { animate(); }, []);

  return (
    <SectionWrapper id="future" title="Future of Computer Vision" label="What lies ahead for AI vision systems" number={40}>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-800" />

        <div className="space-y-6">
          {TIMELINE.map((item, i) => (
            <div
              key={i}
              className={`flex items-start gap-4 ml-2 transition-all duration-700 ${
                i <= activeIdx ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'
              }`}
            >
              {/* Timeline dot */}
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 z-10 transition-all duration-500"
                style={{
                  backgroundColor: i <= activeIdx ? item.color : '#1f2937',
                  boxShadow: i <= activeIdx ? `0 0 15px ${item.color}40` : 'none',
                }}
              >
                <span className="text-lg">{item.icon}</span>
              </div>

              <div className={`flex-1 p-4 rounded-xl border transition-all duration-500 ${
                i <= activeIdx ? 'bg-gray-800/60 border-gray-700/50' : 'bg-gray-900/30 border-gray-800/30'
              }`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full" style={{ backgroundColor: `${item.color}20`, color: item.color }}>
                    {item.year}
                  </span>
                  <h3 className="text-white font-semibold text-sm">{item.title}</h3>
                </div>
                <p className="text-gray-400 text-xs">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={animate}
        disabled={isAnimating}
        className="mt-6 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-700 disabled:to-gray-700 text-white text-sm rounded-lg transition-all"
      >
        {isAnimating ? 'Revealing...' : 'Replay Timeline'}
      </button>
    </SectionWrapper>
  );
}
