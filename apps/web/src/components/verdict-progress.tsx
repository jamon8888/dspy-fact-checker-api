import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Verdict } from "@/lib/event-schema";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { InfoIcon } from "lucide-react";
import { useMemo } from "react";

interface VerdictProgressProps {
  verdicts: Verdict[];
  isLoading: boolean;
}

interface VerdictDistribution {
  Supported: number;
  Refuted: number;
  "Insufficient Information": number;
  "Conflicting Evidence": number;
}

interface VerdictConfig {
  bgClass: string;
  shortLabel: string;
  description: string;
}

export const VerdictProgress = ({
  verdicts,
  isLoading,
}: VerdictProgressProps) => {
  // Calculate verdict distribution
  const distribution = useMemo(() => {
    const stats: VerdictDistribution = {
      Supported: 0,
      Refuted: 0,
      "Insufficient Information": 0,
      "Conflicting Evidence": 0,
    };

    if (verdicts.length === 0) return stats;

    for (const verdict of verdicts) {
      if (verdict.result in stats) {
        stats[verdict.result as keyof VerdictDistribution]++;
      }
    }

    return stats;
  }, [verdicts]);

  // Calculate percentages for the progress bar
  const percentages = useMemo(() => {
    if (verdicts.length === 0) {
      return {
        Supported: 0,
        Refuted: 0,
        "Insufficient Information": 0,
        "Conflicting Evidence": 0,
      };
    }

    return {
      Supported: (distribution.Supported / verdicts.length) * 100,
      Refuted: (distribution.Refuted / verdicts.length) * 100,
      "Insufficient Information":
        (distribution["Insufficient Information"] / verdicts.length) * 100,
      "Conflicting Evidence":
        (distribution["Conflicting Evidence"] / verdicts.length) * 100,
    };
  }, [distribution, verdicts]);

  if (verdicts.length === 0) return null;

  // Config for verdict types
  const verdictConfig: Record<keyof VerdictDistribution, VerdictConfig> = {
    Supported: {
      bgClass: "bg-emerald-500",
      shortLabel: "Supported",
      description: "Claims verified as correct",
    },
    Refuted: {
      bgClass: "bg-red-500",
      shortLabel: "Refuted",
      description: "Claims verified as incorrect",
    },
    "Insufficient Information": {
      bgClass: "bg-amber-500",
      shortLabel: "Insufficient",
      description: "Claims that cannot be verified",
    },
    "Conflicting Evidence": {
      bgClass: "bg-purple-500",
      shortLabel: "Conflicting",
      description: "Claims with mixed evidence",
    },
  };

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex items-center justify-between">
          <h3 className="my-2.5 mt-6 font-medium text-neutral-900 text-sm">
            Verification Results
          </h3>
          <div className="flex items-center gap-1.5">
            <span className="text-neutral-500 text-xs tracking-wide">
              {verdicts.length} claim{verdicts.length !== 1 ? "s" : ""} verified
            </span>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="cursor-help">
                  <InfoIcon
                    className="h-3.5 w-3.5 text-neutral-400 transition-colors hover:text-neutral-500"
                    aria-hidden="true"
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent
                side="top"
                className="border-0 bg-black px-3 py-1.5 text-white text-xs"
              >
                Distribution of verification results
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        <div className="relative h-2 w-full overflow-hidden rounded-full bg-neutral-100">
          {/* Fluid progress bar */}
          <motion.div
            className="absolute inset-0 flex"
            initial={{ width: 0 }}
            animate={{ width: "100%" }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            {/* Supported section */}
            {percentages.Supported > 0 && (
              <motion.div
                className="h-full bg-emerald-500"
                style={{ width: `${percentages.Supported}%` }}
              />
            )}

            {/* Refuted section */}
            {percentages.Refuted > 0 && (
              <motion.div
                className="h-full bg-red-500"
                style={{ width: `${percentages.Refuted}%` }}
              />
            )}

            {/* Insufficient Information section */}
            {percentages["Insufficient Information"] > 0 && (
              <motion.div
                className="h-full bg-amber-500"
                style={{ width: `${percentages["Insufficient Information"]}%` }}
              />
            )}

            {/* Conflicting Evidence section */}
            {percentages["Conflicting Evidence"] > 0 && (
              <motion.div
                className="h-full bg-purple-500"
                style={{ width: `${percentages["Conflicting Evidence"]}%` }}
              />
            )}
          </motion.div>

          {/* Loading effect */}
          {isLoading && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400/30 to-transparent"
              animate={{
                x: ["-100%", "200%"],
              }}
              transition={{
                duration: 1.0,
                repeat: Number.POSITIVE_INFINITY,
                ease: "linear",
              }}
            />
          )}
        </div>

        {/* Legend */}
        <motion.div
          className="mt-2.5 flex items-center justify-between px-0.5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          {Object.entries(verdictConfig).map(([verdict, config]) => {
            const key = verdict as keyof VerdictDistribution;
            const count = distribution[key];
            const percent = (count / verdicts.length) * 100;
            const formattedPercent =
              percent > 0 ? `${Math.round(percent)}%` : "0%";

            return (
              <Tooltip key={verdict}>
                <TooltipTrigger asChild>
                  <div className="flex cursor-default items-center gap-1.5">
                    <div
                      className={cn(
                        "h-2 w-2 rounded-full",
                        count > 0 ? config.bgClass : "bg-neutral-300"
                      )}
                      aria-hidden="true"
                    />
                    <div
                      className={cn(
                        "text-neutral-600 text-xs",
                        count === 0 && "text-neutral-400"
                      )}
                    >
                      <span className="font-medium">{config.shortLabel}</span>
                      <span className="ml-1 tabular-nums">
                        {formattedPercent}
                      </span>
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent
                  side="bottom"
                  className="border-0 bg-black px-2.5 py-1.5 text-white text-xs"
                >
                  {config.description} · {count} claims
                </TooltipContent>
              </Tooltip>
            );
          })}
        </motion.div>
      </motion.div>
    </TooltipProvider>
  );
};
