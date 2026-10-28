import httpAdmin from '../rest/httpAdmin'
import httpDealer from '../rest/httpDealer'

export const getCountries = async (userId: string) => {
  try {
    const response = await httpDealer.get(`/api/v1/user-x/${userId}/countries`);
    return response;
  } catch (error) {
    console.error('Error fetching countries:', error);
    throw error;
  }
};

export const submitLocation = async (payload: any) => {
  return httpDealer.post('/v1/dealer-location/submit', payload);
};

export const getSummary = async () => httpAdmin.get('/summary');
