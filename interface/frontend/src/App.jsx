import React from 'react';
import FaceControl from './components/FaceControl';
import { FaceProvider } from './context/FaceContext';

function App() {
  return (
    <div className="App">
      <FaceProvider>
        <FaceControl />
      </FaceProvider>
    </div>
  );
}

export default App;
