"use client";

import { motion } from "framer-motion";

export const PageHeader = () => (
  <motion.header
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
    className="z-20 py-6 pl-6"
    role="banner"
  >
    <div className="mb-2.5 flex items-center gap-2 pt-4">
      <div
        className="size-6 rounded-full border-5 border-black border-dashed"
        aria-hidden="true"
      />
      <h1 className="font-semibold text-3xl text-neutral-900 tracking-tight">
        Fact Checker
      </h1>
    </div>
    <p className="text-neutral-500 text-sm">
      LLM-powered factual verification system with claim extraction and
      evidence-based assessment
    </p>
  </motion.header>
);
