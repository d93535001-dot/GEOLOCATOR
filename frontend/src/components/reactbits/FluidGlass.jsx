import React from 'react';

export default function FluidGlass({ children, className = '', highlightColor = 'rgba(59, 130, 246, 0.15)' }) {
  return (
    <div className={`relative overflow-hidden bg-black/40 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.4)] ${className}`}>
      <div
        className="absolute inset-0 z-0 pointer-events-none mix-blend-screen"
        style={{
          background: `radial-gradient(circle at 50% -20%, ${highlightColor}, transparent 60%)`
        }}
      />
      <div className="relative z-10 w-full h-full">
        {children}
      </div>
    </div>
  );
}
