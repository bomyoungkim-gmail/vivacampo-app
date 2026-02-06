"use client";

import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type CorrelationPoint = {
  date: string;
  ndvi: number | null;
  rvi: number | null;
  rain_mm: number | null;
  temp_avg?: number | null;
};

export function CorrelationChart({ data }: { data: CorrelationPoint[] }) {
  return (
    <div className="w-full rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="w-full" style={{ height: "300px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9ca3af" }} stroke="#e5e7eb" />
            <YAxis
              yAxisId="left"
              domain={[0, 1]}
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              stroke="#e5e7eb"
              label={{ value: "Vigor", position: "insideTopLeft", fontSize: 10, fill: "#9ca3af" }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 10, fill: "#3b82f6" }}
              stroke="#e5e7eb"
              label={{ value: "mm", position: "insideTopRight", fontSize: 10, fill: "#3b82f6" }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "none",
                boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
            <Bar yAxisId="right" dataKey="rain_mm" name="Chuva (mm)" fill="#93c5fd" opacity={0.8} />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="ndvi"
              name="NDVI"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="rvi"
              name="RVI (Radar)"
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
