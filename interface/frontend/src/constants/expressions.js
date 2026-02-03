/**
 * EXPRESSIONS
 * 20가지 동적 표정 프리셋 정의
 * base: 기본 파라미터 값 (상태 업데이트용)
 * motion: 실시간 모션 오프셋 (진폭 amp, 주파수 freq)
 */
export const EXPRESSIONS = [
    {
        id: "neutral",
        label: "평온",
        base: {
            leftEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: 0, mouthOpenness: 0, mouthX: 0, mouthY: 0, mouthRoundness: 0.2
        },
        motion: {
            gazeY: { amp: 1, freq: 0.2 },
            mouthCurve: { amp: 2, freq: 0.1 },
            mouthRoundness: { amp: 0.2, freq: 0.5 }
        }
    },
    {
        id: "happy",
        label: "기쁨",
        base: {
            leftEye: { openness: 0.9, squeeze: 0, smile: 0.25, rotation: -9 },
            rightEye: { openness: 0.9, squeeze: 0, smile: 0.25, rotation: -9 },
            gazeX: 0, gazeY: 23, mouthCurve: 15, mouthOpenness: -15, mouthX: 0, mouthY: -10, mouthRoundness: 0.05,
            color: "#f7e573"
        },
        motion: {
            leftEye: {
                openness: { amp: 0.1, freq: 1 },
                smile: { amp: 0.05, freq: 1 }
            },
            rightEye: {
                openness: { amp: 0.1, freq: 1 },
                smile: { amp: 0.05, freq: 1 }
            },
            mouthRoundness: { amp: 0.05, freq: 1.5 }
        }
    },
    {
        id: "joy",
        label: "환희",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.3, smile: 0.3, rotation: -15 },
            rightEye: { openness: 0.9, squeeze: 0.3, smile: 0.3, rotation: -15 },
            gazeX: 0, gazeY: 23, mouthCurve: 20, mouthOpenness: 20.5, mouthX: 0, mouthY: -10, mouthRoundness: 0.6,
            color: "#ffd129"
        },
        motion: {
            leftEye: {
                openness: { amp: 0.1, freq: 1 },
                smile: { amp: 0.05, freq: 1 }
            },
            rightEye: {
                openness: { amp: 0.1, freq: 1 },
                smile: { amp: 0.05, freq: 1 }
            },
            mouthRoundness: { amp: 0.05, freq: 1.5 },
            mouthOpenness: { amp: 10.5, freq: 1.5 }
        }
    },
    {
        id: "sad",
        label: "슬픔",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.1, smile: -0.1, rotation: 15 },
            rightEye: { openness: 0.9, squeeze: 0.1, smile: -0.1, rotation: 15 },
            gazeX: 0, gazeY: 15, mouthCurve: -70, mouthOpenness: -10, mouthX: 0, mouthY: 10, mouthRoundness: 0.25,
            color: "#2990ff"
        },
        motion: {
            mouthRoundness: { amp: 0.25, freq: 0.5 },
            leftEye: {
                squeeze: { amp: 0.1, freq: 1 },
                openness: { amp: 0.1, freq: 0.5 }
            },
            rightEye: {
                squeeze: { amp: 0.1, freq: 1 },
                openness: { amp: 0.1, freq: 0.5 }
            }
        }
    },
    {
        id: "angry",
        label: "분노",
        base: {
            leftEye: { openness: 1, squeeze: 0, smile: -0.3, rotation: -25 },
            rightEye: { openness: 1, squeeze: 0, smile: -0.3, rotation: -25 },
            gazeX: 0, gazeY: 0, mouthCurve: -100, mouthOpenness: -12.5, mouthX: 0, mouthY: 7.5, mouthRoundness: 0.2,
            color: "#ff2929"
        },
        motion: {
            leftEye: { rotation: { amp: 5, freq: 4 } },
            rightEye: { rotation: { amp: 5, freq: 4 } },
            mouthY: { amp: 2.5, freq: 3 },
            mouthOpenness: { amp: 2.5, freq: 3 }
        }
    },
    {
        id: "surprised",
        label: "놀람",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.0, smile: 0, rotation: 0 },
            rightEye: { openness: 0.9, squeeze: 0.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: -15, mouthCurve: -50, mouthOpenness: 25.5, mouthX: 0, mouthY: 10, mouthRoundness: 1,
            color: "#fe8b20"
        },
        motion: {
            leftEye: { openness: { amp: 0.1, freq: 2 } },
            rightEye: { openness: { amp: 0.1, freq: 2 } },
            mouthOpenness: { amp: 5.5, freq: 2 }
        }
    },
    {
        id: "suspicious",
        label: "의심",
        base: {
            leftEye: { openness: 0.45, squeeze: 1, smile: -0.06, rotation: -15 },
            rightEye: { openness: 0.45, squeeze: 1, smile: -0.06, rotation: -15 },
            gazeX: 0, gazeY: 0, mouthCurve: -60, mouthOpenness: -1, mouthX: 10, mouthY: -7, mouthRoundness: 0.15,
            color: "#3f00d1"
        },
        motion: {
            gazeX: { amp: 10, freq: 0.5 },
            mouthX: { amp: 10, freq: 0.5 }
        }
    },
    {
        id: "thinking",
        label: "고민",
        base: {
            leftEye: { openness: 1, squeeze: 0, smile: 0, rotation: 11 },
            rightEye: { openness: 1, squeeze: 0, smile: 0, rotation: 11 },
            gazeX: 0, gazeY: -40, mouthCurve: -33, mouthOpenness: -18, mouthX: 5, mouthY: 20, mouthRoundness: 1,
            color: "#00bfff"
        },
        motion: {
            gazeX: { amp: 30, freq: 0.25 },
            mouthX: { amp: 25, freq: 0.25 }
        }
    },
    {
        id: "fear",
        label: "공포",
        base: {
            leftEye: { openness: 1, squeeze: 0.25, smile: 0, rotation: 10 },
            rightEye: { openness: 1, squeeze: 0.25, smile: 0, rotation: 10 },
            gazeX: 0, gazeY: 10, mouthCurve: -31, mouthOpenness: -17, mouthX: 0, mouthY: 0, mouthRoundness: 1,
            color: "#5000b3"
        },
        motion: {
            gazeX: { amp: 5, freq: 6 },
            gazeY: { amp: 5, freq: 6 },
            leftEye: { openness: { amp: 0.1, freq: 6 }, squeeze: { amp: 0.05, freq: 6 } },
            rightEye: { openness: { amp: 0.1, freq: 6 }, squeeze: { amp: 0.05, freq: 6 } }
        }
    },
    {
        id: "bored",
        label: "지루함",
        base: {
            leftEye: { openness: 0.3, squeeze: 0.4, smile: -0.05, rotation: 0 },
            rightEye: { openness: 0.3, squeeze: 0.4, smile: -0.05, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: -30, mouthOpenness: -29, mouthX: 0, mouthY: 10, mouthRoundness: 0.3,
            color: "#7d8d97"
        },
        motion: {
            leftEye: { openness: { amp: 0.1, freq: 0.1 } },
            rightEye: { openness: { amp: 0.1, freq: 0.1 } },
            gazeY: { amp: 20, freq: 0.1 }
        }
    },
    //현재 여기까지 구현 완료 아래부터는 구현 예정이며, 현재 아무 값이나 적당히 입력된 상태
    {
        id: "tired",
        label: "피곤함",
        base: {
            leftEye: { openness: 0.2, squeeze: 0, smile: -0.4, rotation: -5 },
            rightEye: { openness: 0.2, squeeze: 0, smile: -0.4, rotation: 5 },
            gazeX: 0, gazeY: 30, mouthCurve: -20, mouthOpenness: 10, mouthX: 0, mouthY: 20, mouthRoundness: 0.3
        },
        motion: {
            leftEye: { openness: { amp: 0.05, freq: 0.1 } },
            rightEye: { openness: { amp: 0.05, freq: 0.1 } }
        }
    },
    {
        id: "excited",
        label: "흥분",
        base: {
            leftEye: { openness: 1.0, squeeze: 0.1, smile: 0.2, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.1, smile: 0.2, rotation: 0 },
            gazeX: 0, gazeY: -5, mouthCurve: 40, mouthOpenness: 20, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            leftEye: { openness: { amp: 0.2, freq: 4 } },
            rightEye: { openness: { amp: 0.2, freq: 4 } },
            mouthOpenness: { amp: 10, freq: 3 }
        }
    },
    {
        id: "proud",
        label: "자부심",
        base: {
            leftEye: { openness: 0.8, squeeze: 0.4, smile: 0.1, rotation: -10 },
            rightEye: { openness: 0.8, squeeze: 0.4, smile: 0.1, rotation: 10 },
            gazeX: 0, gazeY: -20, mouthCurve: 20, mouthOpenness: -10, mouthX: 0, mouthY: -15, mouthRoundness: 0
        },
        motion: {
            mouthCurve: { amp: 5, freq: 0.3 }
        }
    },
    {
        id: "shy",
        label: "부끄러움",
        base: {
            leftEye: { openness: 0.7, squeeze: 0.5, smile: 0, rotation: 10 },
            rightEye: { openness: 0.7, squeeze: 0.5, smile: 0, rotation: -10 },
            gazeX: 15, gazeY: 40, mouthCurve: 15, mouthOpenness: -5, mouthX: 0, mouthY: 5, mouthRoundness: 0.4
        },
        motion: {
            gazeX: { amp: 5, freq: 1 }
        }
    },
    {
        id: "confused",
        label: "혼란",
        base: {
            leftEye: { openness: 0.9, squeeze: 0, smile: -0.2, rotation: 20 },
            rightEye: { openness: 0.6, squeeze: 0.4, smile: 0.1, rotation: -5 },
            gazeX: -10, gazeY: -10, mouthCurve: -30, mouthOpenness: 10, mouthX: -10, mouthY: 5, mouthRoundness: 0.1
        },
        motion: {
            leftEye: { rotation: { amp: 10, freq: 2 } },
            rightEye: { openness: { amp: 0.2, freq: 1.5 } }
        }
    },
    {
        id: "focused",
        label: "집중",
        base: {
            leftEye: { openness: 0.6, squeeze: 0.8, smile: 0.1, rotation: 15 },
            rightEye: { openness: 0.6, squeeze: 0.8, smile: 0.1, rotation: -15 },
            gazeX: 0, gazeY: 0, mouthCurve: -5, mouthOpenness: -20, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            gazeX: { amp: 1, freq: 2 }
        }
    },
    {
        id: "mischievous",
        label: "장난",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.5, smile: 0, rotation: -20 },
            rightEye: { openness: 0.4, squeeze: 0.8, smile: 0, rotation: 20 },
            gazeX: 20, gazeY: -10, mouthCurve: 40, mouthOpenness: 0, mouthX: 15, mouthY: -5, mouthRoundness: 0
        },
        motion: {
            mouthCurve: { amp: 10, freq: 3 }
        }
    },
    {
        id: "sarcastic",
        label: "냉소",
        base: {
            leftEye: { openness: 0.5, squeeze: 0.2, smile: -0.1, rotation: 5 },
            rightEye: { openness: 0.9, squeeze: 0, smile: -0.3, rotation: -5 },
            gazeX: -30, gazeY: 0, mouthCurve: -40, mouthOpenness: 5, mouthX: -20, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            leftEye: { openness: { amp: 0.1, freq: 0.5 } }
        }
    },
    {
        id: "pain",
        label: "고통",
        base: {
            leftEye: { openness: 0.1, squeeze: 1.0, smile: 0, rotation: 0 },
            rightEye: { openness: 0.1, squeeze: 1.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: -60, mouthOpenness: 25, mouthX: 0, mouthY: 10, mouthRoundness: 0.5
        },
        motion: {
            all: { amp: 5, freq: 12 }
        }
    },
    {
        id: "wink",
        label: "윙크",
        base: {
            leftEye: { openness: 0.0, squeeze: 1.0, smile: 0, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: 35, mouthOpenness: 5, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            rightEye: { smile: { amp: 0.1, freq: 1 } }
        }
    }
];
