import { useState } from 'react';
import ConvolutionSection from '../components/sections/ConvolutionSection';
import FeatureMapsSection from '../components/sections/FeatureMapsSection';
import LayersSection from '../components/sections/LayersSection';
import FaceDetectionSection from '../components/sections/FaceDetectionSection';
import FaceRecognitionSection from '../components/sections/FaceRecognitionSection';
import KeypointDetectionSection from '../components/sections/KeypointDetectionSection';
import MotionDetectionSection from '../components/sections/MotionDetectionSection';
import ImageTransformSection from '../components/sections/ImageTransformSection';
import NoiseDistortionSection from '../components/sections/NoiseDistortionSection';
import DataAugmentationSection from '../components/sections/DataAugmentationSection';
import OverfittingSection from '../components/sections/OverfittingSection';
import GeneralizationSection from '../components/sections/GeneralizationSection';
import ConfidenceScoreSection from '../components/sections/ConfidenceScoreSection';
import MultiObjectSection from '../components/sections/MultiObjectSection';
import DepthPerceptionSection from '../components/sections/DepthPerceptionSection';
import OCRSection from '../components/sections/OCRSection';
import RealTimeVisionSection from '../components/sections/RealTimeVisionSection';
import EdgeCasesSection from '../components/sections/EdgeCasesSection';
import EthicsSection from '../components/sections/EthicsSection';
import FutureSection from '../components/sections/FutureSection';

const NAV_ITEMS = [
  { id: 'convolution', label: '21. Convolution' },
  { id: 'feature-maps', label: '22. Feature Maps' },
  { id: 'layers', label: '23. Layers' },
  { id: 'face-detection', label: '24. Face Detection' },
  { id: 'face-recognition', label: '25. Face Recognition' },
  { id: 'keypoint-detection', label: '26. Keypoints' },
  { id: 'motion-detection', label: '27. Motion' },
  { id: 'image-transform', label: '28. Transform' },
  { id: 'noise', label: '29. Noise' },
  { id: 'data-augmentation', label: '30. Augmentation' },
  { id: 'overfitting', label: '31. Overfitting' },
  { id: 'generalization', label: '32. Generalization' },
  { id: 'confidence', label: '33. Confidence' },
  { id: 'multi-object', label: '34. Multi-Object' },
  { id: 'depth', label: '35. Depth' },
  { id: 'ocr', label: '36. OCR' },
  { id: 'realtime', label: '37. Real-Time' },
  { id: 'edge-cases', label: '38. Edge Cases' },
  { id: 'ethics', label: '39. Ethics' },
  { id: 'future', label: '40. Future' },
];

export default function CVInteractiveLab() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white" style={{ maxWidth: 'none', width: '100%', margin: 0, padding: 0, textAlign: 'left' as const }}>
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/80 backdrop-blur-md border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(s => !s)}
              className="lg:hidden p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <svg viewBox="0 0 24 24" className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2}>
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
              </div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Computer Vision Lab
              </h1>
            </div>
          </div>
          <span className="text-xs text-gray-500 hidden sm:block">Interactive Visual AI Learning</span>
        </div>
      </header>

      {/* Sidebar Nav */}
      <nav className={`fixed top-14 left-0 bottom-0 z-40 w-56 bg-gray-950/95 backdrop-blur-md border-r border-gray-800/50 overflow-y-auto transition-transform duration-300 lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="p-3 space-y-0.5">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="w-full text-left px-3 py-2 text-xs text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-colors"
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main Content */}
      <main className="pt-14 lg:pl-56">
        {/* Hero */}
        <section className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
          <div className="mb-6 relative">
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-500/20">
              <svg viewBox="0 0 24 24" className="w-12 h-12 text-white" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <circle cx="12" cy="12" r="3" />
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
              </svg>
            </div>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Computer Vision Lab
          </h1>
          <p className="text-gray-400 text-lg md:text-xl max-w-2xl mb-8">
            Explore how AI sees and understands the visual world through interactive demonstrations
          </p>
          <button
            onClick={() => scrollTo('convolution')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40"
          >
            Start Exploring
          </button>
          <div className="mt-12 animate-bounce text-gray-600">
            <svg viewBox="0 0 24 24" className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M12 5v14m-7-7l7 7 7-7" />
            </svg>
          </div>
        </section>

        <ConvolutionSection />
        <FeatureMapsSection />
        <LayersSection />
        <FaceDetectionSection />
        <FaceRecognitionSection />
        <KeypointDetectionSection />
        <MotionDetectionSection />
        <ImageTransformSection />
        <NoiseDistortionSection />
        <DataAugmentationSection />
        <OverfittingSection />
        <GeneralizationSection />
        <ConfidenceScoreSection />
        <MultiObjectSection />
        <DepthPerceptionSection />
        <OCRSection />
        <RealTimeVisionSection />
        <EdgeCasesSection />
        <EthicsSection />
        <FutureSection />

        {/* Footer */}
        <footer className="border-t border-gray-800/50 py-8 text-center text-gray-600 text-sm">
          <p>Computer Vision Interactive Lab — Learn how AI sees the world</p>
        </footer>
      </main>
    </div>
  );
}
