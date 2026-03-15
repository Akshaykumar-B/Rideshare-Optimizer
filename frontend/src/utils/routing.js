import axios from 'axios';

/**
 * Fetches routing geometry (GeoJSON LineString) between two or more coordinates using the public OSRM API.
 * This ensures the routes on the map follow physical streets instead of straight lines.
 * 
 * @param {Array<{lat: number, lng: number}>} coordinates - Array of waypoints to route between.
 * @returns {Promise<Object>} A GeoJSON Feature containing a LineString of the route.
 */
export const getRouteGeometry = async (coordinates) => {
  if (!coordinates || coordinates.length < 2) return null;

  try {
    // OSRM expects coordinates in lng,lat format joined by semicolons
    const coordsString = coordinates.map(c => `${c.lng},${c.lat}`).join(';');
    
    const response = await axios.get(
      `https://router.project-osrm.org/route/v1/driving/${coordsString}?overview=full&geometries=geojson`
    );

    if (response.data && response.data.routes && response.data.routes.length > 0) {
      // The geometry is a GeoJSON LineString
      return {
        type: 'Feature',
        geometry: response.data.routes[0].geometry,
        properties: {
          distance: response.data.routes[0].distance,
          duration: response.data.routes[0].duration
        }
      };
    }
    return null;
  } catch (err) {
    console.error('Failed to fetch route geometry from OSRM:', err);
    // Fallback logic could go here if OSRM fails
    return null;
  }
};
