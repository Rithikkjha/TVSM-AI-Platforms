import axios from 'axios';

const API = process.env.REACT_APP_API_URL;
const BOOKING_API = process.env.REACT_APP_BOOKING_API_URL || 'http://uat-bookings.example.net/bookings';

export const dataService = {
  getDealers: () => axios.get(`${API}/dealers`),
  getDealer: (id) => axios.get(`${API}/dealers/${id}`),
  pushVehicleMaster: (data) => axios.post(`${BOOKING_API}/dms-vehicle-master`, data),
};
