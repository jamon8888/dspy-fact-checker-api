import { VerdictBadge } from "@/components/ui/verdict-badge";
import type { Verdict } from "@/lib/event-schema";
import { cn, extractDomain } from "@/lib/utils";
import { motion } from "framer-motion";
import { Link as LinkIcon, PlusCircle } from "lucide-react";
import { memo } from "react";
import Image from "next/image";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface VerdictSummaryProps {
  verdicts: Verdict[];
  isLoading: boolean;
}

const MAX_VISIBLE_SOURCES = 4;

const SourceFavicon = ({ url }: { url: string }) => {
  const domain = extractDomain(url);
  const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=16`;

  return (
    <div className="relative h-3.5 w-3.5 flex-shrink-0 overflow-hidden rounded-[2px]">
      <Image
        src={faviconUrl}
        width={14}
        height={14}
        className="h-full w-full object-cover"
        onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
          const parent = e.currentTarget.parentNode as HTMLElement | null;
          if (parent) {
            parent.innerHTML = `
              <div class="w-full h-full flex items-center justify-center bg-neutral-200 text-[8px] font-medium text-neutral-700">
                ${domain.charAt(0).toUpperCase()}
              </div>
            `;
          }
        }}
        alt={`${domain} favicon`}
      />
    </div>
  );
};

export const VerdictSummary = memo(function VerdictSummary({
  verdicts,
  isLoading,
}: VerdictSummaryProps) {
  if (verdicts.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-3 "
    >
      <h3 className="my-2.5 mt-6 flex items-center font-medium text-neutral-900 text-sm">
        Fact Check Summary
        {isLoading && (
          <motion.span
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            className="ml-2 font-normal text-neutral-500 text-xs"
          >
            Processing...
          </motion.span>
        )}
      </h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {verdicts.map((verdict, idx) => {
          const visibleSources = verdict.sources.slice(0, MAX_VISIBLE_SOURCES);
          const hiddenSources = verdict.sources.slice(MAX_VISIBLE_SOURCES);
          const remainingSourcesCount = hiddenSources.length;

          return (
            <motion.div
              key={`verdict-${verdict.claim_text.slice(0, 20)}-${idx}`}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: idx * 0.05 }}
              className={cn(
                "rounded-lg border border-neutral-200 border-dashed bg-neutral-50 p-3 transition-all dark:border-neutral-800 dark:bg-neutral-900/90"
              )}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <VerdictBadge verdict={verdict} />
                {verdict.sources && verdict.sources.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    {visibleSources.map((source, sourceIdx) => (
                      <a
                        key={`${source.url}-${sourceIdx}-visible`}
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 rounded-sm border border-neutral-300 p-1 transition-all hover:border-neutral-400 hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        aria-label={`View source: ${
                          source.title || source.url
                        } (opens in new tab)`}
                        title={source.title || source.url}
                      >
                        <SourceFavicon url={source.url} />
                      </a>
                    ))}
                    {remainingSourcesCount > 0 && (
                      <Popover>
                        <PopoverTrigger asChild>
                          <button
                            type="button"
                            className="flex h-6 w-6 items-center justify-center rounded-sm border border-neutral-300 bg-neutral-100 text-neutral-500 transition-all hover:border-neutral-400 hover:bg-neutral-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                            aria-label={`Show ${remainingSourcesCount} more sources`}
                          >
                            <PlusCircle className="h-3.5 w-3.5" />
                          </button>
                        </PopoverTrigger>
                        <PopoverContent
                          className="w-auto max-w-xs p-2"
                          side="top"
                          align="end"
                        >
                          <div className="space-y-1.5">
                            <p className="text-xs font-medium text-neutral-600">
                              Additional Sources
                            </p>
                            {hiddenSources.map((source, sourceIdx) => (
                              <a
                                key={`${source.url}-${sourceIdx}-hidden`}
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 rounded-md p-1.5 text-xs text-neutral-700 transition-colors hover:bg-neutral-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                aria-label={`View source: ${
                                  source.title || source.url
                                } (opens in new tab)`}
                                title={source.title || source.url}
                              >
                                <SourceFavicon url={source.url} />
                                <span className="truncate">
                                  {source.title || extractDomain(source.url)}
                                </span>
                                <LinkIcon className="ml-auto h-3 w-3 flex-shrink-0 text-neutral-400" />
                              </a>
                            ))}
                          </div>
                        </PopoverContent>
                      </Popover>
                    )}
                  </div>
                )}
              </div>
              <p className="mb-1.5 font-medium text-neutral-900 text-sm">
                {verdict.claim_text}
              </p>
              {verdict.reasoning && (
                <p className="text-neutral-600 text-xs leading-relaxed">
                  {verdict.reasoning}
                </p>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
});
