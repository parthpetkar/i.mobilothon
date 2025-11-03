export const calculateDistance = (
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number => {
  const R = 6371; // Radius of the Earth in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

export const getAvailabilityColor = (available: number, total: number): string => {
  const ratio = available / total;
  if (ratio > 0.5) return '#22c55e'; // green
  if (ratio > 0.2) return '#eab308'; // yellow
  return '#ef4444'; // red
};

export const getAvailabilityLabel = (available: number, total: number): string => {
  const ratio = available / total;
  if (ratio > 0.5) return 'High Availability';
  if (ratio > 0.2) return 'Medium Availability';
  return 'Low Availability';
};

export const getProbabilityLabel = (probability: number): string => {
  if (probability >= 0.8) return 'High';
  if (probability >= 0.6) return 'Medium';
  return 'Low';
};

export const generateQRCode = (bookingId: string): string => {
  return `PARKING-${bookingId}-${Date.now()}`;
};

export const formatCurrency = (amount: number): string => {
  return `₹${amount}`;
};

export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const amenityIcons: { [key: string]: string } = {
  'Covered': '☂',
  'CCTV': '🎥',
  'EV Charging': '🔌',
  'Toilets': '🚻',
};
