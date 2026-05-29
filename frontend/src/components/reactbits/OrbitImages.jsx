import React from 'react';
import { motion } from 'framer-motion';

export default function OrbitImages({ images }) {
  return (
    <div className="relative w-32 h-32 flex items-center justify-center">
      <div className="absolute w-full h-full rounded-full border border-gray-700"></div>
      {images.map((img, i) => {
        const angle = (i / images.length) * 360;
        return (
          <motion.div
            key={i}
            className="absolute w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center border border-gray-600 text-xs text-white"
            animate={{ rotate: 360 }}
            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
            style={{
              transformOrigin: "64px 64px",
              top: "-16px",
              left: "48px",
              transform: `rotate(${angle}deg)`
            }}
          >
            <span style={{ transform: `rotate(-${angle}deg)` }}>{img[0]}</span>
          </motion.div>
        );
      })}
      <div className="absolute w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center shadow-[0_0_15px_#2563eb]">
        OSINT
      </div>
    </div>
  );
}
