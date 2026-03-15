import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  change?: string;
  positive?: boolean;
  icon?: LucideIcon;
}

const MetricCard = ({ label, value, change, positive, icon: Icon }: MetricCardProps) => (
  <motion.div
    whileHover={{ y: -2 }}
    className="bg-card rounded-xl p-5 card-shadow border border-border/60 transition-shadow hover:hover-glow"
  >
    <div className="flex items-start justify-between">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
      {Icon && <Icon className="w-4 h-4 text-muted-foreground" />}
    </div>
    <p className="text-2xl font-bold mt-2 tabular-nums">{value}</p>
    {change && (
      <p className={`text-xs font-medium mt-1 ${positive ? "text-accent" : "text-destructive"}`}>
        {change}
      </p>
    )}
  </motion.div>
);

export default MetricCard;
