import axios from "axios";
const createAxiosInstance = (baseURL: string) => {
  const axiosInstance = axios.create({
    baseURL,
    headers: { "Content-Type": "application/json" },
  });
  return axiosInstance;
};
export const createHttpService = (baseURL: any) => {
  const axiosInstance = createAxiosInstance(baseURL);
  return {
    get: async (url: string, config: any = {}) => {
      const response = await axiosInstance.get(url, { ...config });
      return response.data;
    },
    post: async (url: string, data: any) => {
      const response = await axiosInstance.post(url, data);
      return response.data;
    },
  };
};
