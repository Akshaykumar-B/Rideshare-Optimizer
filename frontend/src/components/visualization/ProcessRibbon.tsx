import { motion } from "framer-motion";
import { Database, Cpu, Route, CheckCircle2 } from "lucide-react";

const steps = [
  { label: "Data Ingest", icon: Database },
  { label: "Matrix Calc", icon: Cpu },
  { label: "Heuristic Run", icon: Route },
  { label: "Path Found", icon: CheckCircle2 },
];

interface ProcessRibbonProps {
  activeStep?: number;
}

const ProcessRibbon = ({ activeStep = 3 }: ProcessRibbonProps) => (
  <div className="flex items-center gap-2 bg-card rounded-xl px-5 py-3 card-shadow border border-border/60">
    {steps.map((step, i) => (
      <div key={step.label} className="flex items-center gap-2">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.2 }}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
            i <= activeStep
              ? "bg-secondary/10 text-secondary"
              : "bg-muted text-muted-foreground"
          }`}
        >
          <step.icon className="w-3.5 h-3.5" />
          {step.label}
        </motion.div>
        {i < steps.length - 1 && (
          <div className={`w-8 h-px ${i < activeStep ? "bg-secondary" : "bg-border"}`} />
        )}
      </div>
    ))}
  </div>
);

export default ProcessRibbon;
