"use client";

import { motion } from "framer-motion";
import { ExternalLink, Github } from "lucide-react";

export const PageFooter = () => {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full border-x border-t bg-white px-6 py-8"
    >
      <div className="mx-auto max-w-5xl">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          <motion.section
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.3,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="space-y-3"
            aria-labelledby="about-heading"
          >
            <h3
              id="about-heading"
              className="font-semibold text-neutral-900 text-sm"
            >
              About Fact Checker
            </h3>
            <p className="text-neutral-500 text-xs leading-relaxed">
              Our modular LangGraph system breaks down text into individual
              claims, verifies each against reliable sources, and provides a
              detailed report on what's accurate and what's not. Built with
              advanced Claimify methodology for high-precision fact extraction.
            </p>
          </motion.section>

          <motion.section
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.4,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="space-y-3"
            aria-labelledby="resources-heading"
          >
            <h3
              id="resources-heading"
              className="font-semibold text-neutral-900 text-sm"
            >
              Resources
            </h3>
            <nav aria-label="Resource links">
              <ul className="space-y-2">
                <li>
                  <a
                    href="/#"
                    className="flex items-center gap-1 text-neutral-500 text-xs transition-colors hover:text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                    aria-label="View documentation (opens in same tab)"
                  >
                    Documentation{" "}
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                </li>
                <li>
                  <a
                    href="/#"
                    className="flex items-center gap-1 text-neutral-500 text-xs transition-colors hover:text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                    aria-label="View API reference (opens in same tab)"
                  >
                    API Reference{" "}
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                </li>
                <li>
                  <a
                    href="/#"
                    className="flex items-center gap-1 text-neutral-500 text-xs transition-colors hover:text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                    aria-label="View privacy policy (opens in same tab)"
                  >
                    Privacy Policy{" "}
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                </li>
              </ul>
            </nav>
          </motion.section>

          <motion.section
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.5,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="space-y-3"
            aria-labelledby="research-heading"
          >
            <h3
              id="research-heading"
              className="font-semibold text-neutral-900 text-sm"
            >
              Research
            </h3>
            <nav aria-label="Research papers">
              <ul className="space-y-2">
                <li>
                  <a
                    href="https://arxiv.org/abs/2502.10855"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-neutral-500 text-xs transition-colors hover:text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                    aria-label="Read Claimify Methodology paper by Metropolitansky & Larson, 2025 (opens in new tab)"
                  >
                    Claimify Methodology{" "}
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                  <div className="text-neutral-400 text-xs">
                    Metropolitansky & Larson, 2025
                  </div>
                </li>
                <li>
                  <a
                    href="https://arxiv.org/abs/2403.18802"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-neutral-500 text-xs transition-colors hover:text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                    aria-label="Read SAFE Methodology paper by Wei et al., 2024 (opens in new tab)"
                  >
                    SAFE Methodology{" "}
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                  <div className="text-neutral-400 text-xs">
                    Wei et al., 2024
                  </div>
                </li>
              </ul>
            </nav>
          </motion.section>

          <motion.section
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.6,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="space-y-3"
            aria-labelledby="connect-heading"
          >
            <h3
              id="connect-heading"
              className="font-semibold text-neutral-900 text-sm"
            >
              Connect
            </h3>
            <a
              href="https://github.com/BharathXD/fact-checker"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-md border border-neutral-200 px-3 py-1.5 text-neutral-700 text-xs transition-colors hover:border-neutral-300 hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="View Fact Checker project on GitHub (opens in new tab)"
            >
              <Github className="h-3.5 w-3.5" aria-hidden="true" />
              <span>View on GitHub</span>
            </a>
          </motion.section>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="mt-8 flex flex-col items-center justify-between border-neutral-100 border-t pt-6 sm:flex-row"
        >
          <div className="flex items-center gap-2">
            <div
              className="h-5 w-5 rounded-full border-4 border-black border-dashed"
              aria-hidden="true"
            />
            <p className="font-semibold text-neutral-600 text-xs">
              Fact Checker
            </p>
          </div>
          <p className="mt-3 text-neutral-400 text-xs sm:mt-0">
            © {new Date().getFullYear()} Fact Checker. All rights reserved.
          </p>
        </motion.div>
      </div>
    </motion.footer>
  );
};
