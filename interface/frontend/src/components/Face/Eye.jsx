import { motion } from 'framer-motion';

const Eye = ({
    x = 0,
    y = 0,
    scaleY = 1,
    squeeze = 0, // 0에서 1 사이의 값 (1 = 완전히 찡그림/웃음)
    smile = 0,   // -1에서 0.3 사이의 값 (0.3 = 활짝 웃음, -1 = 눈꺼풀이 내려옴)
    rotation = 0, // -45에서 45도 사이의 회전값
    isLeft = true,
    width = 100,
    height = 110,
    color = "#FFFFFF",
    glowIntensity = 0.5
}) => {
    // 기본 치수 계산
    const baseWidth = width + (squeeze * 20);
    const baseHeight = height * (1 - squeeze * 0.5);
    const r = squeeze > 0.5 ? 20 : (scaleY < 0.3 ? 5 : 40);

    // "눈웃음" 및 "눈꺼풀" 동작을 위한 SVG 경로(Path) 로직
    const w2 = baseWidth / 2;
    const h2 = baseHeight / 2;

    // 일반적인 둥근 사각형 경로 (Normal Rounded Rect Path)
    const normalPath = `
        M ${-w2 + r}, ${-h2} 
        L ${w2 - r}, ${-h2} 
        Q ${w2}, ${-h2} ${w2}, ${-h2 + r} 
        L ${w2}, ${h2 - r} 
        Q ${w2}, ${h2} ${w2 - r}, ${h2} 
        L ${-w2 + r}, ${h2} 
        Q ${-w2}, ${h2} ${-w2}, ${h2 - r} 
        L ${-w2}, ${-h2 + r} 
        Q ${-w2}, ${-h2} ${-w2 + r}, ${-h2} 
        Z
    `.replace(/\s+/g, ' ');

    // 웃는 눈 경로 (아래쪽 테두리가 위로 휘어짐)
    const smilePath = `
        M ${-w2 + r}, ${-h2} 
        L ${w2 - r}, ${-h2} 
        Q ${w2}, ${-h2} ${w2}, ${-h2 + r} 
        L ${w2}, ${h2 - r - smile * h2} 
        Q ${0}, ${h2 - r - smile * height} ${-w2}, ${h2 - r - smile * h2} 
        L ${-w2}, ${-h2 + r} 
        Q ${-w2}, ${-h2} ${-w2 + r}, ${-h2} 
        Z
    `.replace(/\s+/g, ' ');

    // 눈꺼풀 경로 (위쪽 테두리가 아래로 휘어짐)
    // smile 값이 음수일 때 위쪽 가장자리를 낮춥니다.
    const absSmile = Math.abs(smile);
    const lidPath = `
        M ${-w2}, ${-h2 + r + absSmile * h2} 
        Q ${0}, ${-h2 + r + absSmile * height} ${w2}, ${-h2 + r + absSmile * h2} 
        L ${w2}, ${h2 - r} 
        Q ${w2}, ${h2} ${w2 - r}, ${h2} 
        L ${-w2 + r}, ${h2} 
        Q ${-w2}, ${h2} ${-w2}, ${h2 - r} 
        Z
    `.replace(/\s+/g, ' ');

    // [Path Switching Logic]
    // smile 값에 따라 눈 모양 경로를 바꿉니다.
    // 기존 로직은 0을 기준으로 strict하게 분기하여, 부동소수점 노이즈(-0.000001 등) 만으로도
    // lidPath(눈꺼풀)로 진입해 눈 윗부분이 잘리는(반달 모양) 시각적 결함을 유발했습니다.
    // 이를 방지하기 위해 0.05 정도의 여유폭(Threshold)을 둡니다.
    const THRESHOLD = 0.05;

    let currentPath = normalPath;
    if (smile > THRESHOLD) {
        currentPath = smilePath;
    } else if (smile < -THRESHOLD) {
        currentPath = lidPath;
    } else {
        currentPath = normalPath;
    }

    // 회전: 왼쪽 눈과 오른쪽 눈이 대칭적으로 회전하도록 설정합니다.
    // 회전값이 양수일 때 왼쪽 눈은 시계 반대 방향, 오른쪽 눈은 시계 방향으로 회전하여 "화난" 또는 "집중한" 표정을 만듭니다.
    const finalRotation = isLeft ? -rotation : rotation;

    return (
        <motion.g
            initial={false}
            animate={{ x, y }}
            transition={{
                type: "spring",
                stiffness: 400,
                damping: 40
            }}
        >
            <motion.path
                d={currentPath}
                fill={color}
                animate={{
                    d: currentPath,
                    scaleY: scaleY,
                    rotate: finalRotation,
                    filter: `drop-shadow(0 0 ${glowIntensity * 20}px ${color})`
                }}
                transition={{
                    type: "spring",
                    stiffness: 400,
                    damping: 40
                }}
                style={{
                    transformOrigin: 'center',
                    transformBox: 'fill-box'
                }}
            />
        </motion.g>
    );
};

export default Eye;
