import { motion } from 'framer-motion';

const Mouth = ({
    x = 200, // Center X
    y = 280, // Base Y
    width = 80,
    curve = 0, // -100 (Sad/Frown) to 100 (Happy/Smile)
    openness = 0, // 0 (Closed) to 100 (Open/Surprised)
    color = "#FFFFFF",
    glowIntensity = 0.5
}) => {

    // Bezier Control Points
    // Start and End points
    const startX = x - width / 2;
    const endX = x + width / 2;

    // Control Point (determines curve)
    // Curve affects the Y position of the control point
    const controlY = y + (curve * 1.5) + openness;

    // When open, the bottom lip also moves down
    const bottomY = y + (openness * 1.5);

    // Simple Line or Curve (Mouth closed)
    const dClosed = `M ${startX} ${y} Q ${x} ${controlY} ${endX} ${y}`;

    // Open Mouth (Oval-ish shape)
    // To simulate opening, we can add a second curve back?
    // Or just thicken the stroke?
    // Let's implement an open mouth as a path that returns to start
    // For simplicity, if openness > 10, we draw an open shape

    let d = dClosed;
    if (openness > 10) {
        // Upper lip (curve) + Lower lip (inverse curve or drop)
        // d = `M ${startX} ${y} Q ${x} ${controlY} ${endX} ${y} Q ${x} ${bottomY} ${startX} ${y}`;
        // Actually, standard mouth opening:
        // Upper lip stays roughly put or curves up (smile)
        // Lower lip drops

        const upperControlY = y + (curve * 0.5); // Slight curve on top
        const lowerControlY = y + openness + (curve * 0.5); // Open + Curve

        // If curve is negative (frown), lips curve down.

        d = `M ${startX} ${y} 
           Q ${x} ${upperControlY} ${endX} ${y}
           Q ${x} ${lowerControlY} ${startX} ${y}`;
    }

    return (
        <motion.path
            d={d}
            stroke={color}
            strokeWidth={openness > 10 ? 0 : 8}
            fill={openness > 10 ? color : "transparent"}
            strokeLinecap="round"
            strokeLinejoin="round"

            animate={{
                d: d,
                stroke: color,
                fill: openness > 10 ? color : "transparent",
                filter: `drop-shadow(0 0 ${glowIntensity * 20}px ${color})`
            }}
            transition={{
                type: "spring",
                stiffness: 300,
                damping: 30
            }}

            style={{
                strokeWidth: openness > 10 ? 0 : 8
            }}
        />
    );
};

export default Mouth;
