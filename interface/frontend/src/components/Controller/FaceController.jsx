import React from 'react';
/*
 * FaceController.jsx
 * 얼굴 표정 파라미터(눈, 입, 고개 등)를 실시간으로 제어하는 디버깅용 UI 패널입니다.
 * 슬라이더를 통해 각 부위별 값을 미세 조정할 수 있습니다.
 */
import { Settings, Eye, MessageSquare, Sun, Move } from 'lucide-react';

const Slider = ({ label, value, onChange, min, max, step = 1, icon: Icon }) => (
    <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
            <div className="flex items-center text-gray-200 text-sm font-medium">
                {Icon && <Icon size={14} className="mr-2" />}
                {label}
            </div>
            <span className="text-xs text-gray-400 font-mono">{value}</span>
        </div>
        <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            className="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-all"
        />
    </div>
);

const FaceController = ({ params, setParams }) => {
    const handleChange = (key, value) => {
        setParams(prev => ({ ...prev, [key]: value }));
    };

    return (
        // Floating Glass Panel - Black Glass Style
        <div className="w-80 max-h-[90vh] bg-black/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 overflow-y-auto text-white shadow-2xl transition-all duration-300">
            <h2 className="text-xl font-bold mb-6 flex items-center tracking-tight text-white">
                <Settings className="mr-2" size={20} />
                Face Control
            </h2>

            {/* Group: Eyes */}
            <div className="mb-6">
                <h3 className="text-xs uppercase tracking-wider text-white/50 font-semibold mb-4 border-b border-white/10 pb-2">Eyes</h3>
                <Slider
                    label="시선 좌우 (Gaze X)" value={params.gazeX} min={-40} max={40} icon={Move}
                    onChange={(v) => handleChange('gazeX', v)}
                />
                <Slider
                    label="시선 상하 (Gaze Y)" value={params.gazeY} min={-50} max={60} icon={Move}
                    onChange={(v) => handleChange('gazeY', v)}
                />
                <Slider
                    label="눈 크기 (Openness)" value={params.eyeOpenness} min={0} max={1} step={0.01} icon={Eye}
                    onChange={(v) => handleChange('eyeOpenness', v)}
                />
                <Slider
                    label="눈웃음 / 눈꺼풀" value={params.eyeSmile} min={-0.3} max={0.3} step={0.01} icon={Eye}
                    onChange={(v) => handleChange('eyeSmile', v)}
                />
                <Slider
                    label="눈 회전" value={params.eyeRotation} min={-30} max={30} icon={Eye}
                    onChange={(v) => handleChange('eyeRotation', v)}
                />
                <Slider
                    label="찡그리기 (Squeeze)" value={params.eyeSqueeze} min={0} max={1} step={0.01} icon={Eye}
                    onChange={(v) => handleChange('eyeSqueeze', v)}
                />
            </div>

            {/* Group: Mouth */}
            <div className="mb-6">
                <h3 className="text-xs uppercase tracking-wider text-white/50 font-semibold mb-4 border-b border-white/10 pb-2">Mouth</h3>
                <Slider
                    label="입꼬리 (미소/슬픔)" value={params.mouthCurve} min={-100} max={50} icon={MessageSquare}
                    onChange={(v) => handleChange('mouthCurve', v)}
                />
                <Slider
                    label="입 벌림" value={params.mouthOpenness} min={-29} max={31} icon={MessageSquare}
                    onChange={(v) => handleChange('mouthOpenness', v)}
                />
                <Slider
                    label="입 위치 좌우" value={params.mouthX} min={-50} max={50} icon={Move}
                    onChange={(v) => handleChange('mouthX', v)}
                />
                <Slider
                    label="입 위치 상하" value={params.mouthY} min={-50} max={50} icon={Move}
                    onChange={(v) => handleChange('mouthY', v)}
                />
            </div>

            {/* Group: Styling */}
            <div className="mb-6">
                <h3 className="text-xs uppercase tracking-wider text-white/50 font-semibold mb-4 border-b border-white/10 pb-2">스타일 (Style)</h3>

                <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-300">색상 테마</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <input
                            type="color"
                            value={params.color}
                            onChange={(e) => handleChange('color', e.target.value)}
                            className="w-8 h-8 rounded-full cursor-pointer bg-transparent border border-gray-500 p-0 overflow-hidden"
                            title="Choose color"
                        />
                        <span className="text-xs font-mono text-gray-400 uppercase">{params.color}</span>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default FaceController;
