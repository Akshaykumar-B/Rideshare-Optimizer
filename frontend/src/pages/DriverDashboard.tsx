import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Users, Clock, Route, MapPin } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import MetricCard from "@/components/visualization/MetricCard";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import Map, { Source, Layer, Marker } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import * as turf from '@turf/turf';
import { getCurrentTrip, toggleAvailability } from "@/api/client";
import { useAuthStore } from "@/store";

const DriverDashboard = () => {
  const [isOnline, setIsOnline] = useState(false);
  const [trip, setTrip] = useState<any>(null);
  const { user } = useAuthStore();

  const fetchTrip = () => {
    getCurrentTrip().then(res => {
      setTrip(res.data.trip);
      if (res.data.driver) {
        setIsOnline(res.data.driver.is_available);
      }
    }).catch(console.error);
  };

  useEffect(() => {
    fetchTrip();
    const interval = setInterval(fetchTrip, 5000); // pull every 5s
    return () => clearInterval(interval);
  }, []);

  const handleToggle = async (val: boolean) => {
    setIsOnline(val);
    try {
      await toggleAvailability(val);
      fetchTrip();
    } catch (e) {
      setIsOnline(!val); // revert on error
    }
  };

  const initialViewState = useMemo(() => {
    if (!trip || !trip.polyline) return { longitude: 77.5946, latitude: 12.9716, zoom: 11 };
    const coords = trip.polyline.map((p: any) => [p.lng, p.lat]);
    if (coords.length < 2) return { longitude: 77.5946, latitude: 12.9716, zoom: 11 };
    const line = turf.lineString(coords);
    const box = turf.bbox(line);
    return {
      bounds: [box[0], box[1], box[2], box[3]] as [number, number, number, number],
      fitBoundsOptions: { padding: 40 }
    };
  }, [trip]);

  return (
    <div className={`pb-8 transition-colors duration-500 ${isOnline ? "bg-secondary/5" : ""}`}>
      <PageHeader
        breadcrumb="Driver"
        title={trip ? "Active Route" : "Overview"}
        description={trip ? "Manage your current trip and stops" : "Waiting for ride requests..."}
        actions={
          <div className="flex items-center gap-3">
            <Label htmlFor="online" className="text-sm font-medium">
              {isOnline ? "Online" : "Offline"}
            </Label>
            <Switch id="online" checked={isOnline} onCheckedChange={handleToggle} />
          </div>
        }
      />
      <div className="px-8 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Distance" value={trip ? `${trip.total_distance_km} km` : "—"} icon={Route} />
          <MetricCard label="Est. Time" value={trip ? `${trip.total_time_min} min` : "—"} icon={Clock} />
          <MetricCard label="Passengers" value={trip ? "Active" : "—"} icon={Users} />
          <MetricCard label="Stops" value={trip ? `${trip.route.length}` : "—"} icon={MapPin} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-6">
          {/* Stop sequence */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-card rounded-xl p-6 card-shadow border border-border/60"
          >
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-5">Stop Sequence</h2>
            <div className="relative">
              <div className="absolute left-[11px] top-2 bottom-2 w-px bg-border" />
              <div className="space-y-5">
                {trip ? trip.route.map((stop: any, i: number) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-3 relative"
                  >
                    <div className={`w-[22px] h-[22px] rounded-full flex items-center justify-center z-10 shrink-0 ${
                      stop.type === "pickup" ? "bg-cyan-500/10" : "bg-pink-500/10"
                    }`}>
                      <div className={`w-2.5 h-2.5 rounded-full ${
                        stop.type === "pickup" ? "bg-cyan-500" : "bg-pink-500"
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase text-muted-foreground">
                          {stop.type}
                        </span>
                        <span className="text-xs text-muted-foreground">· #{stop.ride_id}</span>
                      </div>
                      <p className="text-sm font-medium truncate">{stop.address || "Unknown Location"}</p>
                      <p className="text-xs text-muted-foreground">{stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}</p>
                    </div>
                  </motion.div>
                )) : (
                  <p className="text-sm text-muted-foreground py-4">No active trip</p>
                )}
              </div>
            </div>
          </motion.div>

          {/* Map */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-card rounded-xl card-shadow border border-border/60 overflow-hidden"
          >
            <div className="h-[500px] bg-slate-100 relative">
              <Map
                initialViewState={initialViewState}
                style={{ width: '100%', height: '100%' }}
                mapStyle={{
                  version: 8,
                  sources: {
                    'osm': { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '&copy; OpenStreetMap' }
                  },
                  layers: [{ id: 'osm-layer', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19 }]
                }}
              >
                {trip?.polyline && (
                  <Source id="route" type="geojson" data={turf.lineString(trip.polyline.map((p: any) => [p.lng, p.lat]))}>
                    <Layer
                      id="route-line"
                      type="line"
                      paint={{
                        'line-color': '#f97316',
                        'line-width': 4,
                        'line-opacity': 0.8
                      }}
                    />
                  </Source>
                )}

                {/* Driver */}
                {user && trip?.route?.[0] && (
                  <Marker longitude={trip.route[0].lng} latitude={trip.route[0].lat} anchor="center">
                    <div className="w-8 h-8 rounded-full bg-blue-500 border-[3px] border-white shadow-md flex items-center justify-center text-xs text-white">
                      🚙
                    </div>
                  </Marker>
                )}

                {/* Stops */}
                {trip?.route?.map((stop: any, i: number) => (
                  <Marker key={i} longitude={stop.lng} latitude={stop.lat} anchor="bottom">
                    <div className={`px-2 py-1 rounded-lg text-white text-xs font-bold border-2 border-white shadow-md ${
                      stop.type === 'pickup' ? 'bg-cyan-500' : 'bg-pink-500'
                    }`}>
                      {stop.type === 'pickup' ? '📍' : '🏁'} {stop.order}
                    </div>
                  </Marker>
                ))}
              </Map>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default DriverDashboard;
