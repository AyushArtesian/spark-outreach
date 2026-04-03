import { useState, useEffect, useCallback } from 'react';
import SectionWrapper from '../SectionWrapper';

const IMAGE_GRID = [
  [50, 80, 100, 120, 90, 60, 40],
  [60, 110, 150, 180, 140, 80, 50],
  [40, 90, 200, 240, 200, 100, 60],
  [30, 70, 180, 255, 220, 120, 70],
  [50, 80, 160, 220, 180, 90, 50],
  [60, 60, 100, 140, 110, 70, 40],
  [40, 50, 60, 80, 70, 50, 30],
];

const FILTER = [
  [-1, -1, -1],
  [-1, 8, -1],
  [-1, -1, -1],
];

export default function ConvolutionSection() {
  const [filterPos, setFilterPos] = useState({ row: 0, col: 0 });
  const [outputGrid, setOutputGrid] = useState<number[][]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const maxRow = IMAGE_GRID.length - 3;
  const maxCol = IMAGE_GRID[0].length - 3;

  const computeConv = useCallback((r: number, c: number) => {
    let sum = 0;
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) {
        sum += IMAGE_GRID[r + i][c + j] * FILTER[i][j];
      }
    }
    return Math.max(0, Math.min(255, sum));
  }, []);

  const runConvolution = useCallback(() => {
    setIsRunning(true);
    setOutputGrid([]);
    setFilterPos({ row: 0, col: 0 });
  }, []);

  useEffect(() => {
    if (!isRunning) return;
    const timer = setTimeout(() => {
      const { row, col } = filterPos;
      const val = computeConv(row, col);
      setOutputGrid(prev => {
        const copy = prev.map(r => [...r]);
        if (!copy[row]) copy[row] = [];
        copy[row][col] = val;
        return copy;
      });

      if (col < maxCol) {
        setFilterPos({ row, col: col + 1 });
      } else if (row < maxRow) {
        setFilterPos({ row: row + 1, col: 0 });
      } else {
        setIsRunning(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [filterPos, isRunning, maxCol, maxRow, computeConv]);

  return (
    <SectionWrapper id="convolution" title="Convolution" label="AI scans images using small filters" number={21}>
      <div className="flex flex-col lg:flex-row gap-8 items-start">
        <div>
          <h3 className="text-white text-sm font-semibold mb-2">Input Image Patch</h3>
          <div className="inline-grid gap-0.5">
            {IMAGE_GRID.map((row, ri) => (
              <div key={ri} className="flex gap-0.5">
                {row.map((val, ci) => {
                  const inFilter = isRunning && ri >= filterPos.row && ri < filterPos.row + 3 && ci >= filterPos.col && ci < filterPos.col + 3;
                  return (
                    <div
                      key={ci}
                      className={`w-9 h-9 flex items-center justify-center text-xs font-mono rounded transition-all duration-200 ${
                        inFilter ? 'ring-2 ring-yellow-400 bg-yellow-400/20 text-yellow-300 scale-110' : 'bg-gray-800 text-gray-400'
                      }`}
                    >
                      {val}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-white text-sm font-semibold mb-2">Filter (3x3)</h3>
          <div className="inline-grid gap-0.5 mb-4">
            {FILTER.map((row, ri) => (
              <div key={ri} className="flex gap-0.5">
                {row.map((val, ci) => (
                  <div key={ci} className="w-9 h-9 flex items-center justify-center text-xs font-mono bg-purple-900/60 text-purple-300 rounded">
                    {val}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <button
            onClick={runConvolution}
            disabled={isRunning}
            className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white text-sm rounded-lg transition-colors"
          >
            {isRunning ? 'Running...' : 'Run Convolution'}
          </button>
        </div>

        <div>
          <h3 className="text-white text-sm font-semibold mb-2">Output (Feature Map)</h3>
          <div className="inline-grid gap-0.5">
            {Array.from({ length: maxRow + 1 }, (_, ri) => (
              <div key={ri} className="flex gap-0.5">
                {Array.from({ length: maxCol + 1 }, (_, ci) => {
                  const val = outputGrid[ri]?.[ci];
                  const hasVal = val !== undefined;
                  return (
                    <div
                      key={ci}
                      className={`w-9 h-9 flex items-center justify-center text-xs font-mono rounded transition-all duration-300 ${
                        hasVal ? 'bg-green-900/60 text-green-300 scale-100' : 'bg-gray-800/40 text-gray-600 scale-95'
                      }`}
                    >
                      {hasVal ? val : '?'}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </SectionWrapper>
  );
}
