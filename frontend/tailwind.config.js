/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#4F46E5", // calm indigo
        user: "#E0E7FF",     // user bubble
        bot: "#F3F4F6",      // bot bubble
      },
    },
  },
  plugins: [],
};
