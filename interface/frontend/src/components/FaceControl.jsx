import React, { useState } from 'react';
import FaceRenderer from './Face/FaceRenderer';
import FaceController from './Controller/FaceController';

function FaceControl() {
    const [params, setParams] = useState({
        eyeOpenness: 1.0,
        eyeSqueeze: 0.0,
        eyeSmile: 0.0,
        gazeX: 0,
        gazeY: 0,
        mouthCurve: 0,
        mouthOpenness: 0,
        mouthX: 0,
        mouthY: 0,
        eyeRotation: 0,
        color: '#00FFFF'
    });

    // Glow is now fixed to 0.6 as per user request (removed from controller).
    const glowIntensity = 0.6;

    return (
        // Global Container: Light Mode Background
        <div className="flex w-full h-screen bg-[#f5f5f7] overflow-hidden font-sans relative">

            {/* 
        Left Area: Face Rendering 
        - Aligned to Start (Left)
        - No padding (flush to left)
      */}
            {/* 
        Left Area: Face Rendering 
        - Aligned to Center (Prevent visual shift due to left padding)
        - No hardcoded padding, utilize flex centering
      */}
            {/* 
        Background Face Layer
        - Occupies full screen (absolute inset-0)
        - Slightly shifted to the left (justify-start + pl-32)
        - Independent of Controller layer
      */}
            <div className="absolute inset-0 flex justify-start items-center h-full pl-32 pointer-events-none">
                {/* Face Container 
             - Shifted left via pl-32
             - h-[80vh]: Target size based on height
             - max-w-full: Safety constraint
            */}
                <div className="relative aspect-square h-[80vh] max-w-full flex justify-center items-center pointer-events-auto">
                    <FaceRenderer {...params} glowIntensity={glowIntensity} />
                </div>

                {/* Version Text */}
                <div className="absolute bottom-8 left-16 text-black/30 text-xs font-mono tracking-widest uppercase select-none">
                    MACH-VII v2.0 // Emotion Core
                </div>
            </div>

            {/* 
        Floating Controller Layer
        - Absolute positioned to right
        - Does not affect Face layout
      */}
            <div className="absolute right-8 top-1/2 -translate-y-1/2 w-auto h-auto z-50">
                <FaceController params={params} setParams={setParams} />
            </div>

        </div>
    );
}

export default FaceControl;