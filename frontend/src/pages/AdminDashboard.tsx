import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Leaf, TrendingUp, Users, Route, Shield, UserCheck, UserPlus } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import MetricCard from "@/components/visualization/MetricCard";
import ComparisonChart from "@/components/visualization/ComparisonChart";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import Map, { Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { getCarbonSummary, getHeatmap, promoteToDriver, getUsers } from "@/api/client";
import { Button } from "@/components/ui/button";

const tripAnalytics = [
  { day: "Mon", trips: 120 },
  { day: "Tue", trips: 180 },
  { day: "Wed", trips: 210 },
  { day: "Thu", trips: 190 },
  { day: "Fri", trips: 260 },
  { day: "Sat", trips: 310 },
  { day: "Sun", trips: 240 },
];

const algorithmPerf = [
  { name: "DP", value: 142 },
  { name: "NN", value: 28 },
  { name: "CI", value: 64 },
];

const AdminDashboard = () => {
  const [carbonSummary, setCarbonSummary] = useState<any>(null);
  const [heatmapZones, setHeatmapZones] = useState<any[]>([]);
  const [userCount, setUserCount] = useState<number>(0);

  useEffect(() => {
    getCarbonSummary().then((res: any) => setCarbonSummary(res.data.carbon_summary)).catch(console.error);
    getHeatmap().then((res: any) => setHeatmapZones(res.data.zones)).catch(console.error);
    getUsers().then((res: any) => setUserCount(res.data.users.length)).catch(console.error);
  }, []);

  const heatmapGeoJSON = {
    type: 'FeatureCollection',
    features: heatmapZones.map((zone: any) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [zone.lng, zone.lat] },
      properties: { weight: zone.multiplier }
    }))
  };

  return (
    <div className="pb-8">
      <PageHeader
        breadcrumb="Analytics"
        title="Platform Analytics"
        description="Monitor system performance, demand density, and environmental impact"
      />
      <div className="px-8 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Total Trips" value={carbonSummary ? carbonSummary.total_trips.toString() : '—'} icon={Route} />
          <MetricCard 
            label="Avg Savings" 
            value={carbonSummary?.avg_savings_pct !== undefined ? `${carbonSummary.avg_savings_pct.toFixed(1)}%` : '—'} 
            icon={TrendingUp} 
          />
          <MetricCard label="CO2 Saved" value={carbonSummary?.total_co2_saved_kg !== undefined ? `${carbonSummary.total_co2_saved_kg.toFixed(1)} kg` : '—'} icon={Leaf} />
          <MetricCard label="Total Users" value={userCount.toString()} icon={Users} />
        </div>

      {/* Demand Heatmap */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-card rounded-xl p-5 card-shadow border border-border/60"
      >
        <h3 className="text-sm font-semibold mb-4 text-slate-900 dark:text-white">Live Demand Density</h3>
        <div className="h-[400px] bg-slate-100 rounded-lg overflow-hidden relative border border-border">
          <Map
            initialViewState={{
              longitude: 77.5946,
              latitude: 12.9716,
              zoom: 11
            }}
            style={{ width: '100%', height: '100%' }}
            mapStyle={{
              version: 8,
              sources: {
                'osm': { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '&copy; OpenStreetMap' }
              },
              layers: [{ id: 'osm-layer', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19 }]
            }}
          >
            {heatmapZones.length > 0 && (
              <Source id="heatmap-data" type="geojson" data={heatmapGeoJSON as any}>
                <Layer
                  id="demand-heat"
                  type="heatmap"
                  paint={{
                    'heatmap-weight': ['interpolate', ['linear'], ['get', 'weight'], 1, 0, 2, 1],
                    'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 11, 1, 15, 3],
                    'heatmap-color': [
                      'interpolate', ['linear'], ['heatmap-density'],
                      0, 'rgba(6, 182, 212, 0)',
                      0.2, 'rgba(6, 182, 212, 0.5)',
                      0.5, 'rgba(16, 185, 129, 0.6)',
                      0.8, 'rgba(234, 179, 8, 0.7)',
                      1, 'rgba(239, 68, 68, 0.8)'
                    ],
                    'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 11, 20, 15, 50],
                    'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 13, 1, 16, 0]
                  }}
                />
              </Source>
            )}
          </Map>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card rounded-xl p-5 card-shadow border border-border/60"
        >
          <h3 className="text-sm font-semibold mb-4 text-slate-900 dark:text-white">Weekly Trip Volume</h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={tripAnalytics}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(214, 32%, 91%)" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="hsl(215, 16%, 47%)" />
                <YAxis tick={{ fontSize: 12 }} stroke="hsl(215, 16%, 47%)" />
                <Tooltip
                  contentStyle={{
                    borderRadius: "0.75rem",
                    border: "1px solid hsl(214, 32%, 91%)",
                    boxShadow: "var(--shadow-md)",
                    fontSize: 12,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="trips"
                  stroke="hsl(187, 92%, 41%)"
                  fill="hsla(187, 92%, 41%, 0.1)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <ComparisonChart title="Algorithm Runtime (ms)" data={algorithmPerf} unit=" ms" />
      </div>
      </div>
    </div>
  );
};

export default AdminDashboard;

