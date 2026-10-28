import { EnvironmentConstants } from "@/constants/environment.constant";
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
let api: AxiosInstance | null = null;
export interface ApiResponse<T = any> {
  status: string;
  data: T;
}
export function createApiInstance(): AxiosInstance {
  const baseURL =
    EnvironmentConstants.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  const instance = axios.create({
    baseURL,
    withCredentials: true,
  });
  instance.interceptors.response.use((response) => {
    return response;
  });
  api = instance;
  return instance;
}
function getApiInstance(): AxiosInstance {
  if (!api) {
    return createApiInstance();
  }
  return api;
}
async function withLoading<T>(apiCall: () => Promise<T>): Promise<T> {
  return await apiCall();
}
async function get<AxiosResponse>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<AxiosResponse> | null> {
  return withLoading(async () => {
    const response = await getApiInstance().get<ApiResponse<AxiosResponse>>(url, config);
    return response.data;
  });
}
async function post<T>(
  url: string,
  data: any,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T> | null> {
  return withLoading(async () => {
    const response = await getApiInstance().post<ApiResponse<T>>(url, data, config);
    return response.data;
  });
}
export { get, post };
