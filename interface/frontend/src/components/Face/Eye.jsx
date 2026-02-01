import { motion } from 'framer-motion';

const Eye = ({
    x = 0,
    y = 0,
    scaleY = 1,
    squeeze = 0, // 0 to 1 (1 = fully squeezed/happy)
    smile = 0,   // -1 to 0.3 (0.3 = full smile, -1 = full eyelid)
    rotation = 0, // -45 to 45
    isLeft = true,
    width = 100,
    height = 110,
    color = "#FFFFFF",
    glowIntensity = 0.5
}) => {
    // Basic dimensions
    const baseWidth = width + (squeeze * 20);
    const baseHeight = height * (1 - squeeze * 0.5);
    const r = squeeze > 0.5 ? 20 : (scaleY < 0.3 ? 5 : 40);

    // Path Logic for "Smiling Eyes" and "Eyelids"
    const w2 = baseWidth / 2;
    const h2 = baseHeight / 2;

    // Normal Rounded Rect Path
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

    // Smiling Eye Path (Bottom curves up)
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

    // Eyelid Path (Top curves down)
    // When smile is negative, we lower the top edge
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

    const currentPath = smile > 0 ? smilePath : (smile < 0 ? lidPath : normalPath);

    // Rotation: Left eye and right eye should rotate symmetrically
    // If rotation is positive, left eye rotates clockwise, right eye rotates counter-clockwise?
    // User requested "rotation +_ 45". Usually positive means "angry" or "focused".
    // Let's make it so left eye uses -rotation and right eye uses +rotation for "angry" look when positive.
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
