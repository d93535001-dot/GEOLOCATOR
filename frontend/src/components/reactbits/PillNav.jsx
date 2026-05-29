import React, { useState } from 'react';
import { motion } from 'framer-motion';

export default function PillNav({ items, activeItem, onChange }) {
  return (
    <div className="flex space-x-1 bg-surface p-1 rounded-full border border-gray-800">
      {items.map((item) => (
        <button
          key={item}
          onClick={() => onChange(item)}
          className={`relative px-4 py-2 text-sm font-medium rounded-full transition-colors ${
            activeItem === item ? "text-white" : "text-gray-400 hover:text-white"
          }`}
        >
          {activeItem === item && (
            <motion.div
              layoutId="pillnav-bg"
              className="absolute inset-0 bg-gray-800 rounded-full"
              initial={false}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          )}
          <span className="relative z-10">{item}</span>
        </button>
      ))}
    </div>
  );
}
