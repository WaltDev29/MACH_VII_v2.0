import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { EXPRESSIONS } from '../constants/expressions';

const FaceContext = createContext(null);

export const useFace = () => useContext(FaceContext);

/**
 * 선형 보간 함수 (Linear Interpolation)
 * @param {number} start 시작 값
 * @param {number} end 목표 값
 * @param {number} factor 보간 계수 (0~1)
 */
const lerp = (start, end, factor) => start + (end - start) * factor;

/**
 * 재귀적 객체 보간 (Deep Object Interpolation)
 * 객체 구조가 동일하다고 가정하고, 숫자 값만 찾아 깊은 보간을 수행합니다.
 */
const deepLerp = (current, target, factor) => {
    if (typeof target === 'number') {
        return lerp(current || 0, target, factor);
    }
    if (Array.isArray(target)) {
        return target.map((v, i) => deepLerp(current[i], v, factor));
    }
    if (typeof target === 'object' && target !== null) {
        const result = { ...(current || {}) };
        for (const key in target) {
            result[key] = deepLerp(result[key], target[key], factor);
        }
        return result;
    }
    return target; // 문자열 등은 보간 없이 즉시 교체
};

export const FaceProvider = ({ children }) => {
    const [currentExprId, setCurrentExprId] = useState('neutral');

    // 1. 현재 렌더링 값 (Base + Motion + Liveness가 모두 합산된 최종 값)
    // 초기는 neutral의 base 값으로 시작
    const neutralBase = EXPRESSIONS.find(e => e.id === 'neutral').base;

    // *중요*: 성능을 위해 React State 대신 Ref를 사용하여 애니메이션 루프에서 직접 관리할 수도 있으나,
    // 컴포넌트 리렌더링이 필요하므로(화면 갱신) state를 쓰되 최적화에 유의합니다.
    // 여기서는 "논리적 목표값(Target)"과 "현재 렌더링값(Current)"을 분리합니다.

    // 목표로 하는 Base Parameter (표정 프리셋에 정의된 원본 값)
    const targetBaseRef = useRef(neutralBase);

    // 현재 화면에 보여지고 있는 실제 Base Parameter (보간 진행 중인 값)
    const currentBaseRef = useRef(neutralBase);

    // 색상 상태 (색상은 부드럽게 변하는 것보다 즉시 변하거나 별도 트랜지션이 나음, 여기선 보간 대상 아님)
    const [faceColor, setFaceColor] = useState(neutralBase.color || "#FFFFFF");

    // Liveness 상태 (Blink, Jitter 등)
    const livenessRef = useRef({
        blinkScale: 1.0, // 눈 깜빡임 (0~1)
        jitterX: 0,
        jitterY: 0
    });

    // 최종 렌더링용 State (자식 컴포넌트가 구독)
    const [renderValues, setRenderValues] = useState(neutralBase);

    // [New] UI 제어용 Target State (슬라이더 등과 연동)
    // Ref와 State를 동기화하여 애니메이션 루프(Ref 사용)와 UI 렌더링(State 사용)을 모두 만족시킵니다.
    const [targetValues, _setTargetValues] = useState(neutralBase);

    // Target 변경 헬퍼 (State와 Ref 동시 업데이트)
    const setManualParams = useCallback((newValOrFunc) => {
        _setTargetValues(prev => {
            const next = typeof newValOrFunc === 'function' ? newValOrFunc(prev) : newValOrFunc;
            targetBaseRef.current = next; // Loop용 Ref 즉시 동기화
            return next;
        });
    }, []);

    // -------------------------------------------------------------------------
    // 1. 표정 교체 핸들러 (Async Interface)
    // -------------------------------------------------------------------------
    const setExpression = useCallback((id) => {
        const expr = EXPRESSIONS.find(e => e.id === id);
        if (!expr) {
            console.warn(`[FaceSystem] Unknown expression id: ${id}`);
            return;
        }

        console.log(`[FaceSystem] Transitioning to: ${expr.label} (${id})`);
        setCurrentExprId(id);

        // Target 업데이트 (보간 시작)
        // 색상 처리
        const nextColor = expr.base.color || "#FFFFFF";
        setFaceColor(nextColor);

        // Base 파라미터 업데이트 - 기존의 color 정보 등도 유지하거나 덮어씀
        // 여기서는 expr.base를 그대로 적용 (targetValues 업데이트)
        setManualParams(prev => ({
            ...JSON.parse(JSON.stringify(expr.base)),
            color: nextColor // 색상도 base에 포함되어 있다면 갱신
        }));

    }, [setManualParams]);

    // 외부 제어 인터페이스 노출 (window.setFace)
    useEffect(() => {
        window.setFace = setExpression;
        return () => { delete window.setFace; };
    }, [setExpression]);


    // -------------------------------------------------------------------------
    // 2. [Phase 2] WebSocket Bridge (Backend -> Frontend)
    // -------------------------------------------------------------------------
    useEffect(() => {
        const wsUrl = "ws://localhost:8000/ws";
        let socket;
        let retryTimeout;

        const connect = () => {
            console.log(`[FaceSystem] Connecting to WebSocket: ${wsUrl}`);
            socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                console.log("[FaceSystem] WebSocket Connected.");
            };

            socket.onmessage = (event) => {
                try {
                    const packet = JSON.parse(event.data);

                    // [SystemSnapshot] 패킷 구조 확인
                    // packet = { emotion: { preset_id: "happy", ... }, ... }
                    if (packet && packet.emotion && packet.emotion.preset_id) {
                        const targetId = packet.emotion.preset_id;

                        // 현재 표정과 다르면 전환 (중복 호출 방지는 setExpression 내부보다는 여기서 1차 필터링)
                        // 주의: currentExprId는 state이므로 의존성 배열에 없으면 stale 값일 수 있음.
                        // 하지만 setExpression 내부에서 처리가능하거나, 
                        // 여기서는 단순히 trigger만 해주고 내부에서 필터링하는게 안전함.

                        // React State의 'currentExprId'와 비교하기 위해선 ref나 함수형 업데이트가 필요하나,
                        // setExpression 자체가 최적화되어 있다면 그냥 호출해도 무방.
                        // 다만 과도한 리렌더 방지를 위해 로컬 변수로 체크.

                        // * 중요: setExpression은 변경이 필요할 때만 실제 업데이트를 수행하도록 구현되어야 함.
                        // 현재 구조상 호출하면 애니메이션 타겟이 갱신되므로, 변경시에만 호출하는 것이 효율적.

                        // 여기서는 Context 내부의 currentBaseRef 등이 아닌, 
                        // 단순히 수신된 ID가 직전 수신된 ID와 다른지 체크하는 것이 좋음.
                    }
                } catch (e) {
                    // JSON 파싱 에러 등은 무시 (가끔 불완전 패킷 온다고 가정)
                    console.warn("[FaceSystem] WS Packet Error", e);
                }
            };

            // Phase 2 실제 구현: 메시지 수신 시 상태 업데이트
            socket.addEventListener('message', (event) => {
                try {
                    const packet = JSON.parse(event.data);
                    if (packet?.emotion?.preset_id) {
                        // 여기서 바로 setExpression을 호출하면 무한 루프나 과부하가 걸릴 수 있으므로
                        // 실제로는 currentExprId와 비교해야 합니다.
                        // 하지만 useEffect 내부에서 currentExprId를 쓰면 의존성 때문에 소켓이 계속 재연결됨.
                        // 따라서 setExpression을 신뢰하고 호출하되, 
                        // *팁*: useRef로 lastReceivedId를 관리하여 중복 필터링.
                        handleServerPacket(packet);
                    }
                } catch (err) { }
            });

            socket.onclose = () => {
                console.log("[FaceSystem] WebSocket Disconnected. Retrying in 3s...");
                retryTimeout = setTimeout(connect, 3000);
            };
        };

        // 수신된 패킷 처리 (Closure 문제 회피를 위해 별도 함수 및 Ref 사용 권장)
        // 하지만 간단하게 구현하기 위해 여기서 직접 처리하지 않고, 별도 Ref를 둡니다.

        connect();

        return () => {
            if (socket) socket.close();
            if (retryTimeout) clearTimeout(retryTimeout);
        };
    }, []); // 마운트 시 1회 실행

    // WebSocket 메시지 처리를 위한 헬퍼 (Closuretrap 회피용)
    const lastServerPresetRef = useRef("neutral");

    const handleServerPacket = useCallback((packet) => {
        const serverPreset = packet.emotion.preset_id;

        if (serverPreset && serverPreset !== lastServerPresetRef.current) {
            console.log(`[FaceSystem] Syncing with Server: ${serverPreset}`);
            setExpression(serverPreset);
            lastServerPresetRef.current = serverPreset;
        }
    }, [setExpression]);


    // -------------------------------------------------------------------------
    // 3. Liveness Layer Logic (Blink & Jitter)
    // -------------------------------------------------------------------------
    useEffect(() => {
        // 눈 깜빡임 루프
        let blinkTimeout;
        const scheduleBlink = () => {
            // 눈 감기
            livenessRef.current.blinkScale = 0;

            // 150ms 후 눈 뜨기
            setTimeout(() => {
                livenessRef.current.blinkScale = 1.0;
            }, 150);

            // 다음 깜빡임 스케줄링 (2~6초 랜덤)
            const nextInterval = Math.random() * 4000 + 2000;
            blinkTimeout = setTimeout(scheduleBlink, nextInterval);
        };

        blinkTimeout = setTimeout(scheduleBlink, 3000);

        // 미세 떨림 (Jitter) 루프
        const jitterInterval = setInterval(() => {
            livenessRef.current.jitterX = (Math.random() - 0.5) * 2;
            livenessRef.current.jitterY = (Math.random() - 0.5) * 2;
        }, 500);

        return () => {
            clearTimeout(blinkTimeout);
            clearInterval(jitterInterval);
        };
    }, []);


    // -------------------------------------------------------------------------
    // 3. Animation Core Loop (Interpolation + Motion Synthesis)
    // -------------------------------------------------------------------------
    useEffect(() => {
        let frameId;
        const startTime = Date.now();

        const loop = () => {
            const now = Date.now();
            const elapsed = (now - startTime) / 1000;

            // A. Base Parameter Interpolation (현재 -> 목표 부드럽게 이동)
            // 보간 속도 0.1 (매 프레임 10%씩 접근) -> 부드러운 감속 효과
            const interpFactor = 0.1;
            currentBaseRef.current = deepLerp(currentBaseRef.current, targetBaseRef.current, interpFactor);

            // B. Motion Calculation (현재 표정의 Motion 정의에 따른 오프셋 계산)
            const currentExpr = EXPRESSIONS.find(e => e.id === currentExprId);
            const motionOffsets = {};

            if (currentExpr && currentExpr.motion) {
                // 사인파 기반 모션 계산 헬퍼
                const calcWave = (m) => Math.sin(elapsed * m.freq * Math.PI * 2) * m.amp;

                const processMotion = (targetObj, motionDef) => {
                    Object.entries(motionDef).forEach(([key, value]) => {
                        if (key === 'all') { // 전체 랜덤 지터
                            const val = (Math.random() - 0.5) * value.amp;
                            targetObj.gazeX = (targetObj.gazeX || 0) + val;
                            targetObj.gazeY = (targetObj.gazeY || 0) + val;
                            targetObj.mouthX = (targetObj.mouthX || 0) + val;
                            targetObj.mouthY = (targetObj.mouthY || 0) + val;
                        } else if (typeof value === 'object' && !value.amp) {
                            // 중첩 객체 (예: leftEye: { openness: ... })
                            if (!targetObj[key]) targetObj[key] = {};
                            processMotion(targetObj[key], value);
                        } else {
                            // 일반 수치 모션
                            targetObj[key] = (targetObj[key] || 0) + calcWave(value);
                        }
                    });
                };

                // 빈 객체에 모션 오프셋만 계산
                processMotion(motionOffsets, currentExpr.motion);
            }

            // C. Layer Synthesis (합성)
            // Final = CurrentBase + Motion + Liveness

            // 1. Base 값을 깊은 복사하여 시작
            const finalValues = JSON.parse(JSON.stringify(currentBaseRef.current));

            // 2. Motion 오프셋 더하기 (재귀적 합산)
            const applyMotion = (target, motion) => {
                Object.keys(motion).forEach(key => {
                    if (typeof motion[key] === 'object') {
                        if (!target[key]) target[key] = {};
                        applyMotion(target[key], motion[key]);
                    } else if (typeof motion[key] === 'number') {
                        target[key] = (target[key] || 0) + motion[key];
                    }
                });
            };
            applyMotion(finalValues, motionOffsets);

            // 3. Liveness 적용 (Blink, Jitter)
            // Jitter 적용
            finalValues.gazeX += livenessRef.current.jitterX;
            finalValues.gazeY += livenessRef.current.jitterY;
            finalValues.mouthX += livenessRef.current.jitterX; // 입도 같이 미세하게
            finalValues.mouthY += livenessRef.current.jitterY;

            // Blink 적용 (눈 Openness에 곱하기)
            if (finalValues.leftEye) finalValues.leftEye.openness *= livenessRef.current.blinkScale;
            if (finalValues.rightEye) finalValues.rightEye.openness *= livenessRef.current.blinkScale;

            // 색상 주입
            finalValues.color = faceColor;

            // 렌더링 업데이트
            setRenderValues(finalValues);

            frameId = requestAnimationFrame(loop);
        };

        frameId = requestAnimationFrame(loop);
        return () => cancelAnimationFrame(frameId);
    }, [currentExprId, faceColor]); // 표정이 바뀌면 모션 정의도 바뀌므로 의존성 추가


    return (
        <FaceContext.Provider value={{
            currentExprId,
            setExpression,
            renderValues,
            targetValues,          // UI 표시용 (목표값)
            setParams: setManualParams, // UI 제어용 (목표값 수정)
            isReady: true
        }}>
            {children}
        </FaceContext.Provider>
    );
};
