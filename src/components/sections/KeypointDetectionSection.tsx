import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const KEYPOINTS = [
  { name: 'Head', x: 50, y: 8 },
  { name: 'Neck', x: 50, y: 18 },
  { name: 'L Shoulder', x: 35, y: 22 },
  { name: 'R Shoulder', x: 65, y: 22 },
  { name: 'L Elbow', x: 25, y: 38 },
  { name: 'R Elbow', x: 75, y: 38 },
  { name: 'L Wrist', x: 20, y: 52 },
  { name: 'R Wrist', x: 80, y: 52 },
  { name: 'L Hip', x: 40, y: 52 },
  { name: 'R Hip', x: 60, y: 52 },
  { name: 'L Knee', x: 38, y: 70 },
  { name: 'R Knee', x: 62, y: 70 },
  { name: 'L Ankle', x: 36, y: 90 },
  { name: 'R Ankle', x: 64, y: 90 },
];

const CONNECTIONS = [
  [0, 1], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7],
  [1, 8], [1, 9], [8, 10], [9, 11], [10, 12], [11, 13],
];

export default function KeypointDetectionSection() {
  const [visiblePoints, setVisiblePoints] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const animate = () => {
    setVisiblePoints(0);
    setIsAnimating(true);
  };

  useEffect(() => {
    if (!isAnimating) return;
    if (visiblePoints < KEYPOINTS.length) {
      const timer = setTimeout(() => setVisiblePoints(v => v + 1), 200);
      return () => clearTimeout(timer);
    } else {
      setIsAnimating(false);
    }
  }, [visiblePoints, isAnimating]);

  useEffect(() => { animate(); }, []);

  return (
    <SectionWrapper id="keypoint-detection" title="Keypoint Detection" label="AI tracks important points like joints" number={26}>
      <div className="flex flex-col items-center gap-4">
        <div className="relative w-64 h-80 bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
          {/* Body silhouette */}
          <div className="absolute inset-0 flex items-center justify-center opacity-20">
            <svg viewBox="0 0 100 100" className="w-48 h-64">
              <ellipse cx="50" cy="10" rx="8" ry="9" fill="#6b7280" />
              <rect x="38" y="19" width="24" height="35" rx="5" fill="#6b7280" />
              <rect x="35" y="54" width="12" height="38" rx="4" fill="#6b7280" />
              <rect x="53" y="54" width="12" height="38" rx="4" fill="#6b7280" />
            </svg>
          </div>

          <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full">
            {/* Connections */}
            {CONNECTIONS.map(([a, b], i) => {
              if (a >= visiblePoints || b >= visiblePoints) return null;
              const from = KEYPOINTS[a];
              const to = KEYPOINTS[b];
              return (
                <line
                  key={i}
                  x1={from.x} y1={from.y}
                  x2={to.x} y2={to.y}
                  stroke="#3b82f6"
                  strokeWidth="1"
                  className="transition-opacity duration-300"
                />
              );
            })}

            {/* Points */}
            {KEYPOINTS.map((kp, i) => (
              i < visiblePoints && (
                <g key={i}>
                  <circle
                    cx={kp.x} cy={kp.y} r="2.5"
                    fill="#22d3ee"
                    className="animate-pulse"
                  />
                  <circle
                    cx={kp.x} cy={kp.y} r="4"
                    fill="none" stroke="#22d3ee" strokeWidth="0.5" opacity="0.5"
                  />
                </g>
              )
            ))}
          </svg>
        </div>

        <div className="text-gray-400 text-xs">
          {visiblePoints}/{KEYPOINTS.length} keypoints detected
        </div>
        <button
          onClick={animate}
          disabled={isAnimating}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 text-white text-sm rounded-lg transition-colors"
        >
          {isAnimating ? 'Detecting...' : 'Detect Pose'}
        </button>
      </div>
    </SectionWrapper>
  );
}
