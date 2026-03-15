import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { motion } from "framer-motion";

interface ComparisonChartProps {
  title: string;
  data: { name: string; value: number }[];
  unit?: string;
}

const COLORS = ["hsl(215, 25%, 17%)", "hsl(187, 92%, 41%)", "hsl(160, 84%, 39%)"];

const ComparisonChart = ({ title, data, unit = "" }: ComparisonChartProps) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-card rounded-xl p-5 card-shadow border border-border/60"
  >
    <h3 className="text-sm font-semibold mb-4">{title}</h3>
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barCategoryGap="30%">
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(214, 32%, 91%)" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="hsl(215, 16%, 47%)" />
          <YAxis tick={{ fontSize: 12 }} stroke="hsl(215, 16%, 47%)" />
          <Tooltip
            contentStyle={{
              borderRadius: "0.75rem",
              border: "1px solid hsl(214, 32%, 91%)",
              boxShadow: "var(--shadow-md)",
              fontSize: 12,
            }}
            formatter={(value: number) => [`${value}${unit}`, ""]}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  </motion.div>
);

export default ComparisonChart;
