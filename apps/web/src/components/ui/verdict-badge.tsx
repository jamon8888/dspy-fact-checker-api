import { Badge, type BadgeProps } from "@/components/ui/badge";
import type { Verdict } from "@/lib/event-schema";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { AlertCircle, Check, Info, X } from "lucide-react";

interface VerdictBadgeProps {
  verdict: Verdict;
}

const getBadgeVariant = (result: string): BadgeProps["variant"] => {
  switch (result) {
    case "Supported":
      return "success-subtle";
    case "Refuted":
      return "destructive-subtle";
    case "Insufficient Information":
      return "warning-subtle";
    case "Conflicting Evidence":
      return "outline-subtle";
    default:
      return "secondary";
  }
};

const getIcon = (result: string) => {
  switch (result) {
    case "Supported":
      return <Check className="mr-1.5 h-3.5 w-3.5 flex-shrink-0" />;
    case "Refuted":
      return <X className="mr-1.5 h-3.5 w-3.5 flex-shrink-0" />;
    case "Insufficient Information":
      return <Info className="mr-1.5 h-3.5 w-3.5 flex-shrink-0" />;
    case "Conflicting Evidence":
      return <AlertCircle className="mr-1.5 h-3.5 w-3.5 flex-shrink-0" />;
    default:
      return null;
  }
};

export const VerdictBadge = ({ verdict }: VerdictBadgeProps) => (
  <Badge
    variant={getBadgeVariant(verdict.result)}
    className={cn("flex w-fit items-center rounded-sm px-2 py-0.5 text-[11px]")}
  >
    {getIcon(verdict.result)}
    <motion.span
      initial={{ opacity: 0, x: -2 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2 }}
      className="truncate"
    >
      {verdict.result}
    </motion.span>
  </Badge>
);
