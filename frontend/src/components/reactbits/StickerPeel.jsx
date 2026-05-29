import React from 'react';
import { motion } from 'framer-motion';

export default function StickerPeel({ children }) {
  return (
    <motion.div
      className="relative bg-yellow-100 text-yellow-900 p-2 shadow-sm origin-bottom-right"
      whileHover={{
        rotate: -2,
        scale: 1.05,
        boxShadow: "-5px 5px 15px rgba(0,0,0,0.2)"
      }}
      style={{
        clipPath: "polygon(0 0, 100% 0, 100% 85%, 85% 100%, 0 100%)"
      }}
    >
      <div className="absolute bottom-0 right-0 w-4 h-4 bg-yellow-200 border-l border-t border-yellow-300" style={{ transform: "rotate(-45deg) translate(2px, 2px)" }}></div>
      {children}
    </motion.div>
  );
}
