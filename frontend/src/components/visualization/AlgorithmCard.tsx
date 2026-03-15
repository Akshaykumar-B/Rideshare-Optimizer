import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

interface AlgorithmCardProps {
  name: string;
  badge: string;
  distance: string;
  efficiency: string;
  color: string;
  routePoints: { x: number; y: number }[];
  loading?: boolean;
}

const AlgorithmCard = ({ name, badge, distance, efficiency, color, routePoints, loading }: AlgorithmCardProps) => {
  const pathD = routePoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
    .join(" ");

  const isPlaceholder = distance === "—";

  return (
    <motion.div
      whileHover={{ y: -4 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border/60 rounded-xl p-5 card-shadow transition-shadow hover:hover-glow"
    >
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-bold tracking-tight uppercase text-muted-foreground">{name}</h3>
        <Badge variant="secondary" className="text-xs">{badge}</Badge>
      </div>
      <div className="h-48 bg-muted rounded-lg overflow-hidden relative">
        {loading ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-3">
            <motion.div
              className="w-10 h-10 rounded-full border-3 border-t-transparent"
              style={{ borderColor: color, borderTopColor: 'transparent', borderWidth: 3 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
            <span className="text-xs text-muted-foreground font-medium animate-pulse">Computing route...</span>
          </div>
        ) : (
          <svg viewBox="0 0 300 200" className="w-full h-full">
            {/* Grid */}
            {Array.from({ length: 6 }).map((_, i) => (
              <line key={`h${i}`} x1="0" y1={i * 40} x2="300" y2={i * 40} stroke="hsl(214, 32%, 91%)" strokeWidth="0.5" />
            ))}
            {Array.from({ length: 8 }).map((_, i) => (
              <line key={`v${i}`} x1={i * 43} y1="0" x2={i * 43} y2="200" stroke="hsl(214, 32%, 91%)" strokeWidth="0.5" />
            ))}
            {/* Route */}
            <motion.path
              d={pathD}
              fill="none"
              stroke={color}
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, ease: "easeInOut" }}
            />
            {/* Stops */}
            {routePoints.map((p, i) => (
              <motion.circle
                key={i}
                cx={p.x}
                cy={p.y}
                r="5"
                fill={i === 0 ? color : "white"}
                stroke={color}
                strokeWidth="2"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.3 + i * 0.15 }}
              />
            ))}
          </svg>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div>
          <p className="text-xs text-muted-foreground">Distance</p>
          {loading ? (
            <div className="h-7 w-20 bg-muted rounded animate-pulse mt-1" />
          ) : (
            <p className={`text-lg font-bold tabular-nums ${isPlaceholder ? 'text-muted-foreground' : ''}`}>{distance}</p>
          )}
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Efficiency</p>
          {loading ? (
            <div className="h-7 w-16 bg-muted rounded animate-pulse mt-1" />
          ) : (
            <p className={`text-lg font-bold tabular-nums ${isPlaceholder ? 'text-muted-foreground' : ''}`}>{efficiency}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default AlgorithmCard;
