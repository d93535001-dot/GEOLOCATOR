import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ClickSpark({ children }) {
  const [clicks, setClicks] = useState([]);

  const handleClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const id = Date.now();
    setClicks([...clicks, { x, y, id }]);
    setTimeout(() => {
      setClicks((prev) => prev.filter(c => c.id !== id));
    }, 500);
  };

  return (
    <div className="relative inline-block" onClick={handleClick}>
      {children}
      <AnimatePresence>
        {clicks.map((click) => (
          <motion.div
            key={click.id}
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: 2, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="absolute rounded-full bg-blue-400 pointer-events-none"
            style={{
              left: click.x,
              top: click.y,
              width: 10,
              height: 10,
              transform: 'translate(-50%, -50%)',
            }}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
