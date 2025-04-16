import React from "react";
import { cn } from "@/lib/utils";

export const GradientBackground = ({
  className,
  containerClassName,
  children,
}: {
  className?: string;
  containerClassName?: string;
  children?: React.ReactNode;
}) => {
  return (
    <div className={cn("h-full w-full relative", containerClassName)}>
      <div
        className={cn(
          "absolute inset-0 h-full w-full bg-black opacity-80",
          className
        )}
      />
      <div
        className="absolute inset-0 h-full w-full bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-pink-500/20"
        style={{
          filter: "blur(100px)",
        }}
      />
      <div className="absolute inset-0 h-full w-full bg-black opacity-50" />
      <div className="relative">{children}</div>
    </div>
  );
}; 