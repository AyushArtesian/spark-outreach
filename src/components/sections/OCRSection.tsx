import { useState, useEffect } from 'react';
import SectionWrapper from '../SectionWrapper';

const SAMPLE_TEXTS = [
  { image: 'STOP', extracted: 'STOP', type: 'Road Sign' },
  { image: 'Hello World', extracted: 'Hello World', type: 'Handwritten' },
  { image: 'OPEN 24/7', extracted: 'OPEN 24/7', type: 'Store Sign' },
];

export default function OCRSection() {
  const [selectedText, setSelectedText] = useState(0);
  const [extractedChars, setExtractedChars] = useState(0);
  const [isExtracting, setIsExtracting] = useState(false);

  const sample = SAMPLE_TEXTS[selectedText];

  const startExtraction = (idx: number) => {
    setSelectedText(idx);
    setExtractedChars(0);
    setIsExtracting(true);
  };

  useEffect(() => {
    if (!isExtracting) return;
    if (extractedChars < sample.extracted.length) {
      const timer = setTimeout(() => setExtractedChars(c => c + 1), 80);
      return () => clearTimeout(timer);
    } else {
      setIsExtracting(false);
    }
  }, [extractedChars, isExtracting, sample.extracted.length]);

  useEffect(() => { startExtraction(0); }, []);

  return (
    <SectionWrapper id="ocr" title="OCR (Text from Images)" label="AI can read text from images" number={36}>
      <div className="flex flex-col items-center gap-6">
        <div className="flex gap-3">
          {SAMPLE_TEXTS.map((s, i) => (
            <button
              key={i}
              onClick={() => startExtraction(i)}
              className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                i === selectedText ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {s.type}
            </button>
          ))}
        </div>

        <div className="flex flex-col md:flex-row items-center gap-8">
          {/* Image with text */}
          <div className="w-56 h-40 bg-gray-800 rounded-xl border border-gray-700 flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-700/20 to-gray-900/20" />
            <span className="text-2xl font-bold text-white tracking-wider relative z-10" style={{ fontFamily: sample.type === 'Handwritten' ? 'cursive' : 'monospace' }}>
              {sample.image}
            </span>
            {/* Highlight scanning effect */}
            {isExtracting && (
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent animate-pulse" />
            )}
            <span className="absolute bottom-1 right-2 text-xs text-gray-500">{sample.type}</span>
          </div>

          {/* Arrow */}
          <div className="flex flex-col items-center gap-1">
            <svg viewBox="0 0 24 24" className="w-8 h-8 text-cyan-400 rotate-0 md:rotate-0" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M5 12h14m-7-7l7 7-7 7" />
            </svg>
            <span className="text-xs text-gray-500">Extract</span>
          </div>

          {/* Extracted text */}
          <div className="w-56 h-40 bg-gray-900 rounded-xl border border-cyan-700/30 flex flex-col items-center justify-center p-4">
            <span className="text-xs text-gray-500 mb-2">Extracted Text:</span>
            <span className="text-xl font-mono text-cyan-400 tracking-wide">
              {sample.extracted.slice(0, extractedChars)}
              {isExtracting && <span className="animate-pulse text-cyan-300">|</span>}
            </span>
            {!isExtracting && extractedChars > 0 && (
              <span className="text-green-400 text-xs mt-3 flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                Extraction complete
              </span>
            )}
          </div>
        </div>
      </div>
    </SectionWrapper>
  );
}
