import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MapPin, Clock, Send, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import PageHeader from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import Map, { Marker } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { getMyRequests, createRideRequest } from "@/api/client";

const RiderDashboard = () => {
  const [pickup, setPickup] = useState<any>(null);
  const [dropoff, setDropoff] = useState<any>(null);
  const [pickupTime, setPickupTime] = useState("");
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Selection state: 'pickup' | 'dropoff' | null
  const [selecting, setSelecting] = useState<'pickup' | 'dropoff' | null>(null);

  const fetchRequests = () => {
    getMyRequests().then(r => setRequests(r.data.rides || [])).catch(console.error);
  };

  useEffect(() => {
    fetchRequests();
    // Poll every 5s
    const intv = setInterval(fetchRequests, 5000);
    return () => clearInterval(intv);
  }, []);

  const handleMapClick = (e: any) => {
    if (selecting === 'pickup') {
      setPickup(e.lngLat);
      setSelecting('dropoff');
    } else if (selecting === 'dropoff') {
      setDropoff(e.lngLat);
      setSelecting(null);
    }
  };

  const handleSubmit = async () => {
    if (!pickup || !dropoff) return alert("Please select both pickup and dropoff on the map.");
    setLoading(true);
    try {
      await createRideRequest({
        pickup_lat: pickup.lat,
        pickup_lng: pickup.lng,
        dropoff_lat: dropoff.lat,
        dropoff_lng: dropoff.lng,
        pickup_time: pickupTime || new Date().toISOString()
      });
      setPickup(null);
      setDropoff(null);
      setPickupTime("");
      fetchRequests();
      alert("Ride requested!");
    } catch (err: any) {
      alert(err.response?.data?.message || "Error requesting ride");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pb-8">
      <PageHeader
        breadcrumb="Rider"
        title="Request a Ride"
        description="Submit ride requests and track your trips"
      />
      <div className="px-8 flex flex-col gap-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-6">
          {/* Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-card rounded-xl p-6 card-shadow border border-border/60 space-y-5 h-fit"
          >
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">New Request</h2>
            
            <div className="space-y-4">
              <Button 
                variant={selecting === 'pickup' ? 'default' : 'outline'} 
                className="w-full justify-start gap-2" 
                onClick={() => setSelecting('pickup')}
              >
                <MapPin className="w-4 h-4 text-cyan-500" />
                {pickup ? `${pickup.lat.toFixed(4)}, ${pickup.lng.toFixed(4)}` : "Click Map for Pickup"}
                {pickup && <Check className="w-4 h-4 ml-auto text-green-500" />}
              </Button>

              <Button 
                variant={selecting === 'dropoff' ? 'default' : 'outline'} 
                className="w-full justify-start gap-2" 
                onClick={() => setSelecting('dropoff')}
              >
                <MapPin className="w-4 h-4 text-pink-500" />
                {dropoff ? `${dropoff.lat.toFixed(4)}, ${dropoff.lng.toFixed(4)}` : "Click Map for Drop-off"}
                {dropoff && <Check className="w-4 h-4 ml-auto text-green-500" />}
              </Button>
            </div>

            <div className="space-y-2 pt-2 border-t border-border">
              <Label htmlFor="time" className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-secondary" /> Request Time (Optional)
              </Label>
              <Input id="time" type="datetime-local" value={pickupTime} onChange={(e) => setPickupTime(e.target.value)} />
            </div>

            <Button variant="cyan" className="w-full gap-2 mt-4" onClick={handleSubmit} disabled={loading || !pickup || !dropoff}>
              <Send className="w-4 h-4" /> {loading ? "Submitting..." : "Submit Request"}
            </Button>
          </motion.div>

          {/* Map placeholder */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`bg-card rounded-xl card-shadow border overflow-hidden ${selecting ? 'ring-2 ring-cyan-500 border-cyan-500' : 'border-border/60'}`}
          >
            <div className="h-[400px] w-full bg-slate-100 relative">
              {selecting && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-background/90 backdrop-blur-sm px-4 py-2 rounded-full border border-border shadow-md text-sm font-medium animate-pulse">
                  Click on map to set {selecting}
                </div>
              )}
              <Map
                initialViewState={{ longitude: 77.5946, latitude: 12.9716, zoom: 11 }}
                style={{ width: '100%', height: '100%' }}
                mapStyle={{
                  version: 8,
                  sources: {
                    'osm': { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '&copy; OpenStreetMap' }
                  },
                  layers: [{ id: 'osm-layer', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19 }]
                }}
                onClick={handleMapClick}
                cursor={selecting ? 'crosshair' : 'grab'}
              >
                {pickup && (
                  <Marker longitude={pickup.lng} latitude={pickup.lat} anchor="bottom">
                    <div className="text-3xl filter drop-shadow-md">📍</div>
                  </Marker>
                )}
                {dropoff && (
                  <Marker longitude={dropoff.lng} latitude={dropoff.lat} anchor="bottom">
                    <div className="text-3xl filter drop-shadow-md hue-rotate-180">📍</div>
                  </Marker>
                )}
              </Map>
            </div>
          </motion.div>
        </div>

        {/* Ride History */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-card rounded-xl p-6 card-shadow border border-border/60"
        >
          <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4">Ride History</h2>
          <div className="space-y-3">
            {requests.length === 0 ? (
              <p className="text-sm text-muted-foreground">No rides requested yet.</p>
            ) : (
              requests.map((ride) => (
                <div key={ride.id} className="flex items-center justify-between py-3 border-b border-border/60 last:border-0 hover:bg-muted/50 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${ride.status === "completed" ? "bg-green-500" : ride.status === "pending" ? "bg-amber-500" : "bg-cyan-500"}`} />
                    <div>
                      <p className="text-sm font-medium">#{ride.id} · {ride.status}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(ride.pickup_time).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant={ride.status === "completed" ? "default" : "secondary"} className="capitalize">
                    {ride.status}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default RiderDashboard;
