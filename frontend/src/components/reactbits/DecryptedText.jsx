import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export default function DecryptedText({ text, duration = 2000 }) {
  const [displayText, setDisplayText] = useState('');
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()';

  useEffect(() => {
    let iteration = 0;
    let interval = null;

    interval = setInterval(() => {
      setDisplayText(text.split('').map((char, index) => {
        if(index < iteration) {
          return text[index];
        }
        return chars[Math.floor(Math.random() * chars.length)];
      }).join(''));

      if(iteration >= text.length) {
        clearInterval(interval);
      }

      iteration += 1 / (duration / 50); // controls speed
    }, 50);

    return () => clearInterval(interval);
  }, [text, duration]);

  return (
    <motion.span className="font-mono" initial={{opacity:0}} animate={{opacity:1}}>
      {displayText}
    </motion.span>
  );
}
