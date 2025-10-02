import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import type { LatLngTuple } from 'leaflet';
import { Icon } from 'leaflet';
import { Button, Card } from './ui';
import { cn, formatLatLon } from '../lib/utils';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface LocationMapProps {
  lat: number;
  lon: number;
  onLocationChange: (lat: number, lon: number) => void;
  className?: string;
  height?: string;
}

interface MapClickHandlerProps {
  onLocationChange: (lat: number, lon: number) => void;
}

const MapClickHandler: React.FC<MapClickHandlerProps> = ({ onLocationChange }) => {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;
      onLocationChange(lat, lng);
    },
  });
  return null;
};

export const LocationMap: React.FC<LocationMapProps> = ({
  lat,
  lon,
  onLocationChange,
  className,
  height = '400px',
}) => {
  const [isClient, setIsClient] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser.');
      return;
    }

    setIsLocating(true);
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        onLocationChange(latitude, longitude);
        setIsLocating(false);
      },
      (error) => {
        let errorMessage = 'Unable to retrieve your location.';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied by user.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out.';
            break;
        }
        setLocationError(errorMessage);
        setIsLocating(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  };

  if (!isClient) {
    return (
      <Card className={cn('flex items-center justify-center', className)}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600 dark:text-gray-400">Loading map...</p>
        </div>
      </Card>
    );
  }

  const position: LatLngTuple = [lat, lon];

  return (
    <Card className={cn('p-0 overflow-hidden', className)}>
      <div className="p-4 border-b border-gray-200 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Select Location
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Click on the map to select a location, or use your current location.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Button
            onClick={handleUseMyLocation}
            loading={isLocating}
            variant="outline"
            size="sm"
            className="flex-1 sm:flex-none"
          >
            📍 Use My Location
          </Button>
          
          <div className="flex-1 sm:flex-none">
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={lat.toFixed(4)}
                  onChange={(e) => {
                    const newLat = parseFloat(e.target.value);
                    if (!isNaN(newLat) && newLat >= -90 && newLat <= 90) {
                      onLocationChange(newLat, lon);
                    }
                  }}
                  className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="flex-1">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={lon.toFixed(4)}
                  onChange={(e) => {
                    const newLon = parseFloat(e.target.value);
                    if (!isNaN(newLon) && newLon >= -180 && newLon <= 180) {
                      onLocationChange(lat, newLon);
                    }
                  }}
                  className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>
        </div>

        {locationError && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded border border-red-200 dark:border-red-800">
            {locationError}
          </div>
        )}

        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <span>📍</span>
          <span>Current: {formatLatLon(lat, lon)}</span>
        </div>
      </div>

      <div style={{ height }} className="relative">
        <MapContainer
          center={position}
          zoom={10}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={position}>
            <Popup>
              <div className="text-center">
                <p className="font-medium">Selected Location</p>
                <p className="text-sm text-gray-600">{formatLatLon(lat, lon)}</p>
              </div>
            </Popup>
          </Marker>
          <MapClickHandler onLocationChange={onLocationChange} />
        </MapContainer>
      </div>
    </Card>
  );
};

export default LocationMap;