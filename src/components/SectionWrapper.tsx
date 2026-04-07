import { useEffect, useRef, useState, ReactNode } from 'react';

interface SectionWrapperProps {
  id: string;
  title: string;
  label: string;
  number: number;
  children: ReactNode;
}

export default function SectionWrapper({ id, title, label, number, children }: SectionWrapperProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
        }
      },
      { threshold: 0.15 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      id={id}
      ref={ref}
      className={`min-h-screen flex flex-col items-center justify-center px-4 py-16 transition-all duration-1000 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
      }`}
    >
      <div className="max-w-5xl w-full">
        <div className="flex items-center gap-3 mb-2">
          <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold text-sm shrink-0">
            {number}
          </span>
          <h2 className="text-2xl md:text-3xl font-bold text-white">{title}</h2>
        </div>
        <p className="text-blue-300 text-sm mb-8 pl-14">{label}</p>
        <div className="bg-gray-900/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 md:p-8">
          {children}
        </div>
      </div>
    </section>
  );
}
