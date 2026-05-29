# Frontend Setup Instructions

This document provides instructions on how to set up the React + Tailwind + Vite frontend for GeoLocator OSINT Tool v3.0, incorporating UI components from `reactbits.dev`.

## 1. Create the Vite Project

Run the following commands to create a new Vite project and navigate into it:

```bash
npm create vite@latest geolocator-ui -- --template react
cd geolocator-ui
```

## 2. Install Dependencies

Install Tailwind CSS v4, its vite plugin, and `lucide-react` for icons:

```bash
npm install -D tailwindcss @tailwindcss/vite
npm install lucide-react axios clsx tailwind-merge framer-motion react-spring
```

## 3. Configure Tailwind

Update your `vite.config.js` to include the Tailwind CSS plugin:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

Update your `src/index.css` to import Tailwind directives and set default body styling:

```css
@import "tailwindcss";

@theme {
  --color-background: #09090b;
  --color-surface: #18181b;
  --color-primary: #3b82f6;
}

body {
  background-color: var(--color-background);
  color: white;
}
```

## 4. Install React Bits Components

According to the requirements, we will implement components from React Bits:
- Light Pillar (Background)
- Decrypted Text
- Fuzzy Text
- Pill Nav
- Click Spark
- Sticker Peel
- Orbit Images
- Text Type

Some components may require specific raw CSS or JS files provided in the `src/components/` directory.

## 5. Start the Development Server

```bash
npm run dev &
```
