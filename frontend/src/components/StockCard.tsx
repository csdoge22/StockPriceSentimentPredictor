// src/components/StockCard.tsx
import React from "react";

interface StockCardProps {
  data: {
    symbol: string;
    current_price: number;
    previous_close: number;
    timestamp: string;
  };
}

const StockCard: React.FC<StockCardProps> = ({ data }) => {
  return (
    <div className="bg-white shadow rounded p-4">
      <h2 className="text-xl font-bold">{data.symbol} Stock Info</h2>
      <p>Current Price: ${data.current_price.toFixed(2)}</p>
      <p>Previous Close: ${data.previous_close.toFixed(2)}</p>
      <p>Timestamp: {data.timestamp}</p>
    </div>
  );
};

export default StockCard;
