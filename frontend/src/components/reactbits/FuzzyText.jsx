import React from 'react';
import { motion } from 'framer-motion';

export default function FuzzyText({ children }) {
  return (
    <motion.span
      className="text-gray-400 opacity-60 mix-blend-screen inline-block"
      animate={{ filter: ["blur(2px)", "blur(0px)", "blur(3px)", "blur(1px)"] }}
      transition={{ duration: 3, repeat: Infinity, repeatType: "mirror" }}
    >
      {children}
    </motion.span>
  );
}
