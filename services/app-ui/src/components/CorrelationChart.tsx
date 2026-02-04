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
    <ResponsiveContainer width="100%" height={350}>
      <ComposedChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis yAxisId="left" domain={[0, 1]} label={{ value: "Vigor", angle: -90, position: "insideLeft" }} />
        <YAxis
          yAxisId="right"
          orientation="right"
          label={{ value: "Chuva (mm)", angle: 90, position: "insideRight" }}
        />
        <Tooltip />
        <Legend />
        <Bar yAxisId="right" dataKey="rain_mm" name="Chuva (mm)" fill="hsl(var(--chart-1))" opacity={0.6} />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="ndvi"
          name="NDVI"
          stroke="hsl(var(--chart-2))"
          strokeWidth={2}
          connectNulls={false}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="rvi"
          name="RVI (Radar)"
          stroke="hsl(var(--chart-3))"
          strokeWidth={2}
          strokeDasharray="5 5"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
