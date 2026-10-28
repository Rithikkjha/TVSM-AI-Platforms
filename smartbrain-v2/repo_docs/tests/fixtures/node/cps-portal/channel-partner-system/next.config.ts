import { BASE_PATH } from "@/constants/route.constant";
import type { NextConfig } from "next";
const config: NextConfig = {
  distDir: "dist",
  basePath: BASE_PATH,
};
export default config;
