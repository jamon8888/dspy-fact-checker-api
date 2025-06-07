import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export const extractDomain = (url: string): string => {
  try {
    const hostname = new URL(url).hostname;
    return hostname.startsWith("www.") ? hostname.substring(4) : hostname;
  } catch (_e) {
    return url;
  }
};
