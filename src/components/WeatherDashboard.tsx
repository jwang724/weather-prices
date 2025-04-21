// weather-prices/components/WeatherDashboard.tsx

import React, { useState, useEffect, useMemo } from "react";
import {
  Container,
  Card,
  CardContent,
  Typography,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  TextField,
  Box,
} from "@mui/material";
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  timestamp: string;
  SettlementPointName: string;
  SettlementPointPrice: number;
  windspeed: number;
}

export default function WeatherDashboard() {
  const [data, setData] = useState<DataPoint[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  //fetch json data
  useEffect(() => {
    fetch("ercot_weather_merged.json")
      .then((res) => res.json())
      .then((json) => {
        console.log("json here", json);
        const formatted = json.map((d: any) => ({
          ...d,
          timestamp: new Date(d.timestamp),
        }));
        setData(formatted);
        const uniqueRegions = Array.from(
          new Set(json.map((d: any) => d.SettlementPointName))
        ) as string[];
        console.log(uniqueRegions);
        setRegions(uniqueRegions);
        setSelectedRegion(uniqueRegions[0]);
      })
      .catch((err) => console.error("Failed to load JSON:", err));
  }, []);

  //filters data based on selected region and date range
  const filteredData = data.filter((d) => {
    const ts = new Date(d.timestamp);
    return (
      d.SettlementPointName === selectedRegion &&
      (!startDate || ts >= new Date(startDate)) &&
      (!endDate || ts <= new Date(endDate))
    );
  });

  //sorts data by timestamp
  const sortedTimeData = [...filteredData].sort((a, b) => {
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
  });

  //sorts data by windspeed
  const sortedWindSpeedData = [...filteredData].sort((a, b) => a.windspeed - b.windspeed);

  //get correlation
  const correlation = useMemo(() => {
    const x = filteredData.map((data) => data.windspeed);
    const y = filteredData.map((data) => data.SettlementPointPrice);
  
    if (x.length !== y.length || x.length === 0) return null;
  
    const n = x.length;
    const avgX = x.reduce((a, b) => a + b, 0) / n;
    const avgY = y.reduce((a, b) => a + b, 0) / n;
  
    const numerator = x.reduce((sum, x, i) => sum + (x - avgX) * (y[i] - avgY), 0);
    const denominator = Math.sqrt(
      x.reduce((sum, x) => sum + Math.pow(x - avgX, 2), 0) *
      y.reduce((sum, y) => sum + Math.pow(y - avgY, 2), 0)
    );
  
    const r = denominator === 0 ? 0 : numerator / denominator;
    return r;
  }, [filteredData]);

  const summaryText = useMemo(() => {
    if (correlation === null) return "Not enough data to compute correlation.";
    if (correlation > 0.7) return "Wind speed has a strong positive correlation with energy prices.";
    if (correlation < -0.7) return "Wind speed has a strong negative correlation with energy prices.";
    if (Math.abs(correlation) > 0.3) return "Wind speed has a moderate correlation with energy prices.";
    return "Wind speed has little to no correlation with energy prices.";
  }, [correlation]);


  return (
    <Container>
      <Typography variant="h4" sx={{ mt: 4, mb: 2 }}>
        ERCOT Energy Price Dashboard
      </Typography>

      <Box display="flex" flexWrap="wrap" gap={2} mb={3} justifyContent="space-between">
        <FormControl sx={{ minWidth: 200, flex: 1 }}>
          <InputLabel id="region-select-label">Region</InputLabel>
          <Select
            labelId="region-select-label"
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            label="Region"
          >
            {regions.map((r) => (
              <MenuItem key={r} value={r}>
                {r}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          sx={{ flex: 1, minWidth: 200 }}
          label="Start Date"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
        />

        <TextField
          sx={{ flex: 1, minWidth: 200 }}
          label="End Date"
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
        />
      </Box>

      {/* Summary */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
            <Typography variant="h6">Key Finding</Typography>
            <Typography variant="body1">{summaryText}</Typography>
            {correlation !== null && (
            <Typography variant="caption" color="text.secondary">
                Correlation coefficient: {correlation.toFixed(2)}
            </Typography>
            )}
        </CardContent>
      </Card>

      {/* Time Series Line Chart */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6">Price vs Wind Speed Over Time</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sortedTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
              />
              <YAxis
                yAxisId="left"
                label={{ value: "Price", angle: -90, position: "insideLeft" }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                label={{ value: "Wind Speed", angle: 90, position: "insideRight" }}
              />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="SettlementPointPrice"
                name="Price"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="windspeed"
                stroke="#82ca9d"
                name="Wind Speed"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Scatter Plot */}
      <Card>
        <CardContent>
          <Typography variant="h6">Wind Speed vs Price</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis dataKey="windspeed" name="Wind Speed" />
              <YAxis dataKey="SettlementPointPrice" name="Price" />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Scatter name="Data Points" data={sortedWindSpeedData} fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Container>
  );
}
