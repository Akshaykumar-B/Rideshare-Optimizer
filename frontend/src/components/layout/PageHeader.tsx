import { motion } from "framer-motion";

interface PageHeaderProps {
  breadcrumb: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

const PageHeader = ({ breadcrumb, title, description, actions }: PageHeaderProps) => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex items-start justify-between px-8 pt-8 pb-6"
  >
    <div>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">{breadcrumb}</p>
      <h1 className="text-2xl font-bold">{title}</h1>
      {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
    </div>
    {actions && <div className="flex items-center gap-3">{actions}</div>}
  </motion.div>
);

export default PageHeader;
