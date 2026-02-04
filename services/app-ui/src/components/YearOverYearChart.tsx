"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type YearOverYearPoint = {
  week: number;
  current: number | null;
  previous: number | null;
};

export function YearOverYearChart({
  data,
  currentYear,
  previousYear,
}: {
  data: YearOverYearPoint[];
  currentYear: number;
  previousYear: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="week" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="current"
          name={`Safra ${currentYear}`}
          stroke="hsl(var(--chart-2))"
          strokeWidth={2}
          connectNulls={false}
        />
        <Line
          type="monotone"
          dataKey="previous"
          name={`Safra ${previousYear}`}
          stroke="hsl(var(--chart-3))"
          strokeWidth={2}
          strokeDasharray="5 5"
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
