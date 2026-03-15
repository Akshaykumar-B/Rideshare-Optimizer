import { useState, useEffect, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import { Play, ChevronDown, Clock, Route, Percent, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import PageHeader from "@/components/layout/PageHeader";
import AlgorithmCard from "@/components/visualization/AlgorithmCard";
import ProcessRibbon from "@/components/visualization/ProcessRibbon";
import ComparisonChart from "@/components/visualization/ComparisonChart";
import MetricCard from "@/components/visualization/MetricCard";
import Map, { Marker, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import * as turf from '@turf/turf';
import { useAppStore } from "@/store";
import { getScenarios, loadScenario, runComparison } from "@/api/client";

const COLORS = {
  dp: '#22c55e',
  nn: '#f97316',
  ci: '#a855f7',
};

const DriverIcon = ({ color }: { color: string }) => (
  <div style={{
    width: 28, height: 28, borderRadius: '50%',
    background: color, border: '3px solid white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 12, fontWeight: 700, color: 'white'
  }}>🚙</div>
);

const NumberIcon = ({ number, color, type }: { number: number, color: string, type: string }) => {
  const emoji = type === 'pickup' ? '📍' : '🏁';
  return (
    <div style={{
      padding: '4px 8px', borderRadius: 12,
      background: color, color: 'white',
      fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap',
      boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
      border: '2px solid white',
    }}>
      {emoji} {number}
    </div>
  );
};

function RouteMap({ result, color, name, isOptimal }: { result: any, color: string, name: string, isOptimal?: boolean }) {
  if (!result || !result.feasible) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm h-[350px] flex items-center justify-center">
        <p className="text-muted-foreground">No feasible route</p>
      </div>
    );
  }

  const polylineCoords = result.polyline?.map((p: any) => [p.lng, p.lat]) || [];

  const initialViewState = useMemo(() => {
    const coords: any[] = [];
    if (result.driver_start) coords.push([result.driver_start.lng, result.driver_start.lat]);
    result.route?.forEach((s: any) => coords.push([s.lng, s.lat]));
    if (coords.length < 2) return { longitude: 77.5946, latitude: 12.9716, zoom: 11 };
    const line = turf.lineString(coords);
    const box = turf.bbox(line);
    return {
      bounds: [[box[0], box[1]], [box[2], box[3]]] as [number, number, number, number],
      fitBoundsOptions: { padding: 40 }
    };
  }, [result]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-card border rounded-xl shadow-sm overflow-hidden relative ${isOptimal ? 'ring-2 ring-primary/20 border-primary' : 'border-border'}`}
    >
      {isOptimal && (
        <span className="absolute top-3 right-3 bg-secondary text-secondary-foreground text-[10px] font-bold px-2 py-1 rounded-full z-10">
          ✅ OPTIMAL
        </span>
      )}
      <div className="px-4 py-3 border-b border-border bg-card/50">
        <div className="text-sm font-bold flex items-center gap-2">
          <span style={{ backgroundColor: color }} className="w-3 h-3 rounded-full inline-block" />
          {name}
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {result.total_distance_km} km · {result.total_time_min} min · {result.computation_time_ms}ms compute
        </div>
      </div>
      <div className="h-[300px] cursor-default bg-slate-100">
        <Map
          initialViewState={initialViewState}
          style={{ height: '100%', width: '100%' }}
          mapStyle={{
            version: 8,
            sources: {
              'osm': { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '&copy; OpenStreetMap' }
            },
            layers: [{ id: 'osm-layer', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19 }]
          }}
          scrollZoom={false}
          dragPan={false}
          doubleClickZoom={false}
        >
          {polylineCoords.length > 1 && (
            <Source id={`route-${name}`} type="geojson" data={turf.lineString(polylineCoords)}>
              <Layer
                id={`route-line-${name}`}
                type="line"
                paint={{
                  'line-color': color,
                  'line-width': 4,
                  'line-dasharray': isOptimal ? [1] : [2, 2],
                  'line-opacity': 0.8
                }}
              />
            </Source>
          )}

          {result.driver_start && (
            <Marker longitude={result.driver_start.lng} latitude={result.driver_start.lat} anchor="center">
              <DriverIcon color="#6373ff" />
            </Marker>
          )}

          {result.route?.map((stop: any, i: number) => (
            <Marker key={i} longitude={stop.lng} latitude={stop.lat} anchor="bottom">
              <NumberIcon number={stop.order} color={stop.type === 'pickup' ? '#22d3ee' : '#ec4899'} type={stop.type} />
            </Marker>
          ))}
        </Map>
      </div>
    </motion.div>
  );
}

const ComparisonPage = () => {
  const {
    scenarios, setScenarios, selectedScenario, setSelectedScenario,
    scenarioData, setScenarioData, comparisonResult, setComparisonResult,
    isComparing, setIsComparing,
  } = useAppStore();

  const [activeStep, setActiveStep] = useState(3);
  const [isRunning, setIsRunning] = useState(false);
  const [hasRunOnce, setHasRunOnce] = useState(false);

  useEffect(() => {
    getScenarios().then((res: any) => {
      setScenarios(res.data.scenarios, res.data.landmarks);
      if (!selectedScenario) setSelectedScenario('5_rider_spread');
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedScenario) return;
    setComparisonResult(null);
    setHasRunOnce(false);
    loadScenario(selectedScenario).then((res: any) => {
      setScenarioData(res.data);
    }).catch(console.error);
  }, [selectedScenario]);

  const handleCompare = useCallback(async () => {
    if (!scenarioData) return;
    setIsComparing(true);
    setComparisonResult(null);
    setIsRunning(true);
    setActiveStep(0);

    const stepInterval = setInterval(() => {
      setActiveStep((s) => {
        if (s >= 3) {
          clearInterval(stepInterval);
          setIsRunning(false);
          return 3;
        }
        return s + 1;
      });
    }, 600);

    try {
      const res = await runComparison({
        driver_start: scenarioData.driver_start,
        riders: scenarioData.riders,
        vehicle_capacity: scenarioData.vehicle_capacity || 4,
      });
      setTimeout(() => {
        setComparisonResult(res.data);
        setHasRunOnce(true);
      }, 2000);
    } catch (err) {
      console.error(err);
      setIsComparing(false);
    }
  }, [scenarioData]);

  // Auto-run comparison when scenario data loads
  useEffect(() => {
    if (scenarioData && !comparisonResult && !isComparing && !hasRunOnce) {
      handleCompare();
    }
  }, [scenarioData, handleCompare]);

  const dpResult = comparisonResult?.dp;
  const nnResult = comparisonResult?.nearest_neighbor;
  const ciResult = comparisonResult?.cheapest_insertion;

  const algorithms = [
    {
      name: "Dynamic Programming",
      badge: "Optimal",
      distance: dpResult ? `${dpResult.total_distance_km} km` : "—",
      efficiency: dpResult ? `${(100 - (comparisonResult?.comparison?.dp?.optimality_gap_distance_pct || 0))}%` : "—",
      color: "hsl(215, 25%, 17%)",
      routePoints: [ { x: 30, y: 160 }, { x: 80, y: 60 }, { x: 140, y: 120 }, { x: 200, y: 40 }, { x: 260, y: 100 }, { x: 280, y: 170 } ],
      loading: isComparing,
    },
    {
      name: "Nearest Neighbor",
      badge: "Fastest",
      distance: nnResult ? `${nnResult.total_distance_km} km` : "—",
      efficiency: nnResult ? `${100 - (comparisonResult?.comparison?.nearest_neighbor?.optimality_gap_distance_pct || 12)}%` : "—",
      color: "hsl(187, 92%, 41%)",
      routePoints: [ { x: 30, y: 160 }, { x: 60, y: 80 }, { x: 130, y: 40 }, { x: 180, y: 130 }, { x: 240, y: 60 }, { x: 280, y: 170 } ],
      loading: isComparing,
    },
    {
      name: "Cheapest Insertion",
      badge: "Balanced",
      distance: ciResult ? `${ciResult.total_distance_km} km` : "—",
      efficiency: ciResult ? `${100 - (comparisonResult?.comparison?.cheapest_insertion?.optimality_gap_distance_pct || 8)}%` : "—",
      color: "hsl(160, 84%, 39%)",
      routePoints: [ { x: 30, y: 160 }, { x: 100, y: 50 }, { x: 150, y: 140 }, { x: 210, y: 70 }, { x: 250, y: 130 }, { x: 280, y: 170 } ],
      loading: isComparing,
    },
  ];

  const distanceData = comparisonResult ? [
    { name: "DP", value: dpResult.total_distance_km },
    { name: "NN", value: nnResult.total_distance_km },
    { name: "CI", value: ciResult.total_distance_km },
  ] : [];

  const detourData = comparisonResult ? [
    { name: "DP", value: comparisonResult.comparison?.dp?.max_detour ? parseFloat((comparisonResult.comparison.dp.max_detour * 100).toFixed(1)) : 0 },
    { name: "NN", value: comparisonResult.comparison?.nearest_neighbor?.max_detour ? parseFloat((comparisonResult.comparison.nearest_neighbor.max_detour * 100).toFixed(1)) : 0 },
    { name: "CI", value: comparisonResult.comparison?.cheapest_insertion?.max_detour ? parseFloat((comparisonResult.comparison.cheapest_insertion.max_detour * 100).toFixed(1)) : 0 },
  ] : [];

  return (
    <div className="pb-8">
      <PageHeader
        breadcrumb="Simulations"
        title={selectedScenario ? (scenarios[selectedScenario]?.name || "Algorithm Comparison") : "Algorithm Comparison"}
        description="Compare route optimization algorithms side-by-side"
        actions={
          <div className="flex gap-3">
            <div className="relative">
              <select
                value={selectedScenario || ""}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="appearance-none bg-card border border-border rounded-lg px-4 py-2 pr-8 text-sm font-medium cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring min-w-[200px]"
              >
                {Object.entries(scenarios || {}).map(([key, sc]: [string, any]) => (
                  <option key={key} value={key}>
                    {sc.name} ({sc.rider_count} riders)
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>
            <Button variant="cyan" onClick={handleCompare} disabled={isComparing || !scenarioData} className="gap-2">
              <Play className="w-4 h-4" />
              {isComparing ? "Computing..." : "Run Optimization"}
            </Button>
          </div>
        }
      />

      <div className="px-8 space-y-6">
        {scenarioData?.riders && (
          <div className="flex gap-2 flex-wrap text-xs">
            {scenarioData.driver_start?.address && (
              <span className="bg-blue-100/50 text-blue-700 px-3 py-1.5 rounded-full font-medium border border-blue-200">
                📍 {scenarioData.driver_start.address}
              </span>
            )}
            <span className="bg-purple-100/50 text-purple-700 px-3 py-1.5 rounded-full font-medium border border-purple-200">
              👥 {scenarioData.riders.length} riders
            </span>
          </div>
        )}

        <ProcessRibbon activeStep={activeStep} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {algorithms.map((alg, i) => (
            <motion.div
              key={alg.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.15 }}
            >
              <AlgorithmCard {...alg} />
            </motion.div>
          ))}
        </div>

        {comparisonResult && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard 
                label="Best Distance" 
                value={`${dpResult?.total_distance_km} km`} 
                change={`-${((nnResult.total_distance_km - dpResult.total_distance_km) / nnResult.total_distance_km * 100).toFixed(0)}% vs NN`} 
                positive 
                icon={Route} 
              />
              <MetricCard label="Avg Travel Time" value={`${dpResult?.total_time_min} min`} icon={Clock} />
              <MetricCard 
                label="Max Detour" 
                value={`${(comparisonResult?.comparison?.dp?.max_detour * 100).toFixed(1)}%`} 
                icon={Percent} 
              />
              <MetricCard label="Runtime" value={`${comparisonResult?.comparison?.dp?.computation_ms} ms`} icon={Zap} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <RouteMap result={dpResult} color={COLORS.dp} name="Bitmask DP (Optimal)" isOptimal />
              <RouteMap result={nnResult} color={COLORS.nn} name="Nearest-Neighbor" />
              <RouteMap result={ciResult} color={COLORS.ci} name="Cheapest Insertion" />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <ComparisonChart title="Distance Comparison" data={distanceData} unit=" km" />
              <ComparisonChart title="Max Detour (%)" data={detourData} unit="%" />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ComparisonPage;
