import { utilFunctions } from '../../utils';
require('dotenv').config();
const priceMicroserviceBaseUrl = process.env.PRICE_MICROSERVICE_BASE_URL;
export const getStateNamesUrl = (country: string) => {
  return `${priceMicroserviceBaseUrl}/regions/${country}/states`;
};
export const getCityNamesUrl = (queryParams: { [key: string]: any }) => {
  const query = utilFunctions.convertToQueryFormate(queryParams);
  return `${priceMicroserviceBaseUrl}/regions/cities?${query}`;
};
