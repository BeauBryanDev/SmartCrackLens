/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          // Paleta Monocromática Azul Cyberpunk
          crack: {
            dark: "#000814",      // Dark Blue for Background
            deep: "#001D3D",      // Deep Blue for cards
            electric: "#003566",  // Base Commond Blue
            neon: "#0077B6",      // Borders 
            cyan: "#90E0EF",      // Cyan for titles 
          }
        },
        fontFamily: {
          orbitron: ["Orbitron", "sans-serif"],
          mono: ["JetBrains Mono", "monospace"],
        },
        boxShadow: {
          'hud': '0 0 15px rgba(0, 119, 182, 0.4)',
          'neon-border': '0 0 10px #0077B6, inset 0 0 5px #0077B6',
        },
        backgroundImage: {
          'scanline': 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
        },
        animation: {
          'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          'glitch': 'glitch 1s linear infinite',
        },
        keyframes: {
          glitch: {
            '0%, 100%': { transform: 'translate(0)' },
            '33%': { transform: 'translate(-2px, 2px)' },
            '66%': { transform: 'translate(2px, -2px)' },
          }
        }
      },
    },
    plugins: [],
  }