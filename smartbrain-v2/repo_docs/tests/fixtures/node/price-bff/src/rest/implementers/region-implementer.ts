import { http } from '..';
import { RegionUrls } from '../API-directories';
class RegionImplementer {
  public async fetchStateNames(country: string): Promise<any> {
    const url = RegionUrls.getStateNamesUrl(country);
    const headerObject = {};
    const regionData = await http.get(url, headerObject);
    return regionData;
  }
  public async fetchCityNames(query: { [key: string]: any }): Promise<any> {
    const url = RegionUrls.getCityNamesUrl(query);
    const regionData = await http.get(url, {});
    return regionData;
  }
}
const regionImplementer = new RegionImplementer();
export default regionImplementer;
