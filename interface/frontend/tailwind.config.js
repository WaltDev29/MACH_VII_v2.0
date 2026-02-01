/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'apple-gray': '#F5F5F7',
                'apple-dark': '#1D1D1F',
            },
            fontFamily: {
                sans: ['"SF Pro Display"', '"SF Pro Text"', 'Inter', 'system-ui', 'sans-serif'],
            },
            dropShadow: {
                'glow': '0 0 20px rgba(255, 255, 255, 0.5)',
            }
        },
    },
    plugins: [],
}
