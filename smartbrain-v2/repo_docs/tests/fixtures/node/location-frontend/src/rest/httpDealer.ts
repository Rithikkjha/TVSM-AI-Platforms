import axios from "axios";
const baseURL = process.env.REACT_APP_DEALER_BASE_URL;
export const setRequestHeaders = (requestHeaders: any = {}, contentType = "application/json") => {
  return { "Content-Type": contentType, ...requestHeaders };
};
const httpDealer = {
  get: async (url: string, config: any = {}) => {
    try {
      let requestHeaders: any = setRequestHeaders();
      const response = await axios.get(`${baseURL}${url}`, {
        headers: requestHeaders, ...config
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  post: async (url: string, data: any, contentType = "application/json") => {
    const response = await axios.post(`${baseURL}${url}`, data, {
      headers: setRequestHeaders({}, contentType),
    });
    return response.data;
  },
  getWithoutBaseURL: async (url: string) => {
    const response = await axios.get(url, { headers: setRequestHeaders() });
    return response.data;
  },
};
export default httpDealer;
