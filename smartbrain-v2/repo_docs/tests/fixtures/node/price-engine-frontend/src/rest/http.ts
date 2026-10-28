import axios from 'axios';
const baseUrl = process.env.REACT_APP_PRICE_ENGINE_BFF_BASE_URL;
export const getRegions = (country: string) => axios.get(`${baseUrl}/regions/${country}/states`);
