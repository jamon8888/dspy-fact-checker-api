import { cn } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, ChevronRight, Circle, Loader } from "lucide-react";
import React, { memo, useMemo } from "react";
import { StreamingIndicator } from "./ui/streaming-indicator";

interface ProgressBarProps {
  stages: { name: string; count: number; description?: string }[];
  isLoading: boolean;
}

export const ProgressBar = memo(({ stages, isLoading }: ProgressBarProps) => {
  const activeStageIndex = useMemo(
    () => stages.findIndex((stage) => stage.count === 0),
    [stages]
  );
  const currentStage =
    activeStageIndex === -1
      ? stages.length - 1
      : Math.max(0, activeStageIndex - 1);

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.05, delayChildren: 0.05 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 3 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.25, ease: "easeOut" },
    },
  };

  return (
    <div className="select-none">
      <div className="mb-3 flex items-center justify-between text-xs">
        <span className="font-medium text-neutral-800 text-sm dark:text-neutral-200">
          Verification
        </span>
        <StreamingIndicator isActive={isLoading} />
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="hide-scrollbar flex items-center gap-x-1.5 overflow-x-auto"
      >
        {stages.map((stage, idx) => {
          const isCompleted = idx < currentStage;
          const isCurrent = idx === currentStage;

          return (
            <React.Fragment key={stage.name}>
              <motion.div
                variants={itemVariants}
                className={cn(
                  "group relative flex h-6 items-center gap-1.5 rounded-full px-1 text-xs transition-all duration-300",
                  isCurrent && isLoading
                    ? "border border-neutral-200 bg-neutral-100 text-neutral-900 shadow-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
                    : isCompleted
                      ? "border border-neutral-200 bg-neutral-100 text-neutral-900 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
                      : "border border-neutral-100 bg-neutral-50 text-neutral-400 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-500"
                )}
              >
                <span className="flex-shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="size-4 text-neutral-900 dark:text-neutral-100" />
                  ) : isCurrent && isLoading ? (
                    <Loader className="size-4 animate-spin text-neutral-900 dark:text-neutral-100" />
                  ) : (
                    <Circle className="size-4 text-neutral-400 dark:text-neutral-500" />
                  )}
                </span>
                <span
                  className={cn(
                    "whitespace-nowrap font-medium",
                    isCompleted || (isCurrent && isLoading)
                      ? "text-neutral-900 dark:text-neutral-100"
                      : "text-neutral-400 dark:text-neutral-500"
                  )}
                >
                  {stage.name}
                </span>
                <AnimatePresence>
                  {stage.count > 0 && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.5 }}
                      className={cn(
                        "flex h-4 min-w-4 items-center justify-center rounded-full px-1 font-medium text-[10px]",
                        isCurrent && isLoading
                          ? "bg-neutral-900 text-neutral-50 dark:bg-neutral-100 dark:text-neutral-900"
                          : isCompleted
                            ? "bg-neutral-900 text-neutral-50 dark:bg-neutral-100 dark:text-neutral-900"
                            : "bg-neutral-200 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300"
                      )}
                    >
                      {stage.count}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Tooltip with description on hover */}
                {stage.description && (
                  <div className="-translate-x-1/2 pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                    <div className="max-w-[200px] rounded-md bg-neutral-900 px-2.5 py-1.5 text-center text-neutral-100 text-xs shadow-md dark:bg-neutral-800">
                      {stage.description}
                      <div className="-translate-x-1/2 -bottom-1 absolute left-1/2 h-2 w-2 rotate-45 bg-neutral-900 dark:bg-neutral-800" />
                    </div>
                  </div>
                )}
              </motion.div>
              {idx < stages.length - 1 && (
                <ChevronRight
                  className={cn(
                    "h-3.5 w-3.5 flex-shrink-0",
                    idx < currentStage
                      ? "text-neutral-400 dark:text-neutral-500"
                      : "text-neutral-300 dark:text-neutral-700"
                  )}
                  strokeWidth={1.5}
                />
              )}
            </React.Fragment>
          );
        })}
      </motion.div>
    </div>
  );
});

ProgressBar.displayName = "ProgressBar";
