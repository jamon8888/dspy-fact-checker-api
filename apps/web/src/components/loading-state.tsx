import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface LoadingStateProps {
  message: string;
}

export const LoadingState = ({ message }: LoadingStateProps) => (
  <div className="flex flex-col items-center justify-center py-24">
    <motion.div
      className={cn(
        "mb-3 h-6 w-6 rounded-full border-2 border-blue-100 border-t-blue-600"
      )}
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Number.POSITIVE_INFINITY,
        ease: "linear",
      }}
    />
    <motion.p
      className="text-neutral-500 text-xs"
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      {message}
    </motion.p>
  </div>
);

export const ProcessingIndicator = ({ message }: { message: string }) => (
  <motion.div
    initial={{ opacity: 0, y: -5 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.2 }}
    className={cn(
      "flex items-center gap-2.5 rounded-[4px] border border-blue-100 bg-blue-50 px-3 py-2"
    )}
  >
    <motion.div
      className="h-3 w-3 rounded-full border-[1.5px] border-blue-100 border-t-blue-500"
      animate={{ rotate: 360 }}
      transition={{
        duration: 1.2,
        repeat: Number.POSITIVE_INFINITY,
        ease: "linear",
      }}
    />
    <p className="font-medium text-blue-600 text-xs">{message}</p>
  </motion.div>
);
