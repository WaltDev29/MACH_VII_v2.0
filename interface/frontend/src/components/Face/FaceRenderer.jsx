import React, { useState, useEffect } from 'react';
import Eye from './Eye';
import Mouth from './Mouth';
import { motion } from 'framer-motion';

const FaceRenderer = ({
    leftEye = { openness: 1.0, squeeze: 0.0, smile: 0.0, rotation: 0.0 },
    rightEye = { openness: 1.0, squeeze: 0.0, smile: 0.0, rotation: 0.0 },
    mouthCurve = 0,
    mouthOpenness = 0,
    mouthX = 0,
    mouthY = 0,
    mouthRoundness = 0,
    gazeX = 0,
    gazeY = 0,
    color = "#FFFFFF",
    glowIntensity = 0.5,
    isAlive = true
}) => {
    const CANVAS_SIZE = 400;

    // 계산 (간단한 눈 크기 보정) - Context에서 이미 처리되지만, 안전장치로 남겨둠
    // Context에서 넘어오는 값은 이미 blink가 반영된 값이므로 여기서는 1을 곱하는 셈이 됨 (혹은 props에 따라 다름)
    // 하지만 Liveness Layer에서 처리했으므로, 여기서는 그냥 props 값을 그대로 씁니다.

    // 좌표 계산 (기본값 + 사용자 오프셋)
    // 눈 Y 좌표: 160 + 15 (기준점 + 보정) = 175
    const leftEyeX = 110 + gazeX;
    const rightEyeX = 290 + gazeX;
    const eyeY = 175 + gazeY;

    const mouthXPos = 200 + (gazeX * 0.3) + mouthX;
    const mouthYPos = 260 + (gazeY * 0.3) + mouthY;

    // 입 모양 (기본값 + 사용자 오프셋)
    // 곡률 기본값: 14, 개방 기본값: 29
    const finalMouthCurve = 14 + mouthCurve;
    const finalMouthOpenness = 29 + mouthOpenness;

    return (
        <div className="w-full h-full flex justify-center items-center">
            {/* 
                얼굴 컨테이너 (Face Container)
                - 검은색 배경과 전반적인 형상을 정의합니다.
                - 스타일: bg-black, 둥근 모서리, 그림자
            */}
            <motion.div
                className="relative w-full h-full bg-black rounded-[3rem] border border-white/5 shadow-2xl overflow-hidden flex items-center justify-center"
                animate={{
                    boxShadow: `0 0 20px rgba(0,0,0,0.5)` // 네온 효과가 아닌 은은한 그림자 효과 유지
                }}
                transition={{ duration: 0.5 }}
                style={{ aspectRatio: '1/1' }}
            >
                {/* 내부 앰비언트 글로우 (Ambient Glow) - 요청에 따라 매우 은은하게 유지하거나 제거 가능 */}
                <div
                    className="absolute inset-0 opacity-10 pointer-events-none"
                    style={{ background: `radial-gradient(circle at 50% 50%, ${color}, transparent 70%)` }}
                />

                <svg
                    width="100%"
                    height="100%"
                    viewBox={`0 0 ${CANVAS_SIZE} ${CANVAS_SIZE}`}
                    preserveAspectRatio="xMidYMid meet"
                    className="overflow-visible w-full h-full"
                >
                    <Eye
                        x={leftEyeX}
                        y={eyeY}
                        width={100}
                        height={110}
                        scaleY={leftEye.openness}
                        squeeze={leftEye.squeeze}
                        smile={leftEye.smile}
                        rotation={leftEye.rotation}
                        isLeft={true}
                        color={color}
                        glowIntensity={glowIntensity}
                    />

                    <Eye
                        x={rightEyeX}
                        y={eyeY}
                        width={100}
                        height={110}
                        scaleY={rightEye.openness}
                        squeeze={rightEye.squeeze}
                        smile={rightEye.smile}
                        rotation={rightEye.rotation}
                        isLeft={false}
                        color={color}
                        glowIntensity={glowIntensity}
                    />

                    <Mouth
                        x={mouthXPos}
                        y={mouthYPos}
                        curve={finalMouthCurve}
                        openness={finalMouthOpenness}
                        roundness={mouthRoundness}
                        color={color}
                        glowIntensity={glowIntensity}
                    />
                </svg>
            </motion.div>
        </div>
    );
};

export default FaceRenderer;