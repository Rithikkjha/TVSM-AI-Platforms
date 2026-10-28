import { createHttpService } from "./httpCommon";
const baseURL = process.env.REACT_APP_ADMIN_BASE_URL;
const httpAdmin = createHttpService(baseURL);
export default httpAdmin;
