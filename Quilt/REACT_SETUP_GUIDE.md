# React Setup Guide

## Step 1: Install Node.js

You need to install Node.js first. Here's how:

1. **Download Node.js:**
   - Go to https://nodejs.org/
   - Download the LTS (Long Term Support) version (recommended for beginners)
   - Run the installer and follow the setup wizard
   - Make sure to check "Add to PATH" during installation

2. **Verify Installation:**
   After installation, open a new terminal and run:
   ```powershell
   node --version
   npm --version
   ```
   Both commands should show version numbers.

## Step 2: Create Your React Project

Once Node.js is installed, you can create a React project using one of these methods:

### Option A: Using Vite (Recommended - Fast & Modern)
```powershell
npm create vite@latest my-react-app -- --template react
cd my-react-app
npm install
npm run dev
```

### Option B: Using Create React App (Traditional)
```powershell
npx create-react-app my-react-app
cd my-react-app
npm start
```

## Step 3: Start Coding!

After running `npm run dev` (Vite) or `npm start` (Create React App):
- Your app will be available at http://localhost:5173 (Vite) or http://localhost:3000 (Create React App)
- Edit `src/App.jsx` (or `src/App.js`) to start coding
- The page will automatically reload when you save changes

## Project Structure

```
my-react-app/
├── src/
│   ├── App.jsx       # Main component (start here!)
│   ├── main.jsx      # Entry point
│   └── index.css     # Styles
├── public/           # Static files
├── package.json      # Dependencies
└── vite.config.js    # Vite configuration
```

## Next Steps

1. Open `src/App.jsx` and start editing
2. Learn React basics: Components, JSX, Props, State
3. Check out the React documentation: https://react.dev/


