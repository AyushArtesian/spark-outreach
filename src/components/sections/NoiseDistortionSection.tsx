import { useState, useEffect, useRef } from 'react';
import SectionWrapper from '../SectionWrapper';

export default function NoiseDistortionSection() {
  const [noiseLevel, setNoiseLevel] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = 200;
    const h = 200;
    canvas.width = w;
    canvas.height = h;

    // Draw a simple scene
    ctx.fillStyle = '#1e3a5f';
    ctx.fillRect(0, 0, w, h);

    // Sky gradient
    const skyGrad = ctx.createLinearGradient(0, 0, 0, h * 0.6);
    skyGrad.addColorStop(0, '#0f172a');
    skyGrad.addColorStop(1, '#1e40af');
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, w, h * 0.6);

    // Ground
    ctx.fillStyle = '#166534';
    ctx.fillRect(0, h * 0.6, w, h * 0.4);

    // House
    ctx.fillStyle = '#dc2626';
    ctx.beginPath();
    ctx.moveTo(60, 80);
    ctx.lineTo(100, 50);
    ctx.lineTo(140, 80);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#2563eb';
    ctx.fillRect(65, 80, 70, 50);

    ctx.fillStyle = '#fbbf24';
    ctx.fillRect(80, 90, 15, 15);
    ctx.fillRect(105, 90, 15, 15);

    ctx.fillStyle = '#78350f';
    ctx.fillRect(90, 105, 20, 25);

    // Sun
    ctx.fillStyle = '#fbbf24';
    ctx.beginPath();
    ctx.arc(160, 30, 15, 0, Math.PI * 2);
    ctx.fill();

    // Tree
    ctx.fillStyle = '#15803d';
    ctx.beginPath();
    ctx.arc(35, 100, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#78350f';
    ctx.fillRect(32, 118, 6, 20);

    // Add noise
    if (noiseLevel > 0) {
      const imageData = ctx.getImageData(0, 0, w, h);
      const data = imageData.data;
      const intensity = noiseLevel * 2.55;
      for (let i = 0; i < data.length; i += 4) {
        const noise = (Math.random() - 0.5) * intensity;
        data[i] = Math.max(0, Math.min(255, data[i] + noise));
        data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
        data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
      }
      ctx.putImageData(imageData, 0, 0);
    }
  }, [noiseLevel]);

  const getQualityLabel = () => {
    if (noiseLevel === 0) return { text: 'Perfect Quality', color: 'text-green-400' };
    if (noiseLevel <= 30) return { text: 'Slight Noise', color: 'text-yellow-400' };
    if (noiseLevel <= 60) return { text: 'Moderate Noise', color: 'text-orange-400' };
    return { text: 'Heavy Noise', color: 'text-red-400' };
  };

  const quality = getQualityLabel();

  return (
    <SectionWrapper id="noise" title="Noise & Distortion" label="Poor quality affects AI performance" number={29}>
      <div className="flex flex-col items-center gap-6">
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="rounded-xl border border-gray-700"
            style={{ width: 256, height: 256, imageRendering: 'pixelated' }}
          />
          <div className="absolute top-2 right-2">
            <span className={`text-xs font-semibold px-2 py-1 rounded-full bg-gray-900/80 ${quality.color}`}>
              {quality.text}
            </span>
          </div>
        </div>

        <div className="w-64 flex flex-col gap-2">
          <label className="text-gray-400 text-sm flex justify-between">
            <span>Noise Level</span>
            <span className="font-mono">{noiseLevel}%</span>
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={noiseLevel}
            onChange={e => setNoiseLevel(Number(e.target.value))}
            className="w-full accent-red-500"
          />
          <div className="flex justify-between text-xs text-gray-600">
            <span>Clean</span>
            <span>Noisy</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-400">AI Accuracy:</span>
          <div className="w-32 h-3 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.max(5, 100 - noiseLevel * 0.9)}%`,
                background: noiseLevel < 30 ? '#22c55e' : noiseLevel < 60 ? '#f59e0b' : '#ef4444',
              }}
            />
          </div>
          <span className="font-mono text-xs text-gray-400">{Math.max(5, Math.round(100 - noiseLevel * 0.9))}%</span>
        </div>
      </div>
    </SectionWrapper>
  );
}
