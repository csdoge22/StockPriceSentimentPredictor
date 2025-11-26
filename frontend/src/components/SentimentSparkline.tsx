// src/components/SentimentSparkline.tsx
import React from "react";
import { Sparklines, SparklinesLine, SparklinesSpots } from "react-sparklines";

export interface SentimentSparklineProps {
  data: number[];
  label: "positive" | "neutral" | "negative";
}

const SentimentSparkline: React.FC<SentimentSparklineProps> = ({ data, label }) => {
  const color = label === "positive" ? "green" : label === "neutral" ? "gray" : "red";

  return (
    <div className="flex flex-col items-center">
      <Sparklines data={data} limit={30} width={100} height={20} min={-1} max={1}>
        <SparklinesLine color={color} />
        <SparklinesSpots size={2} style={{ stroke: color, strokeWidth: 1, fill: color }} />
      </Sparklines>
    </div>
  );
};

export default SentimentSparkline;
