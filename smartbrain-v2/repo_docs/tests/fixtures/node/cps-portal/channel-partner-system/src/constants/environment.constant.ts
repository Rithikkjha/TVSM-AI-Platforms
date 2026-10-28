import axios from "axios";
import { BASE_PATH } from "@/constants/route.constant";
type Config = {
  NEXT_PUBLIC_API_BASE_URL: string;
};
export class EnvironmentConstants {
  static config: Config;
  static readonly BASE_PATH = BASE_PATH;
  static async loadConfig() {
    const response: any = await axios.get(`${EnvironmentConstants.BASE_PATH}/api/getEnvConfig`);
    this.config = response.data;
    return this.config;
  }
  static get API_BASE_URL(): string {
    return this.config?.NEXT_PUBLIC_API_BASE_URL;
  }
}
