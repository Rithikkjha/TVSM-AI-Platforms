import axios from 'axios';
class Http {
  setHeaders = (headerObject: any) => {
    headerObject['Content-Type'] = 'application/json';
    return headerObject;
  };
  public get = async (url: string, header: object) => {
    try {
      const response = await axios.get(url, { headers: this.setHeaders(header) });
      return response.data;
    } catch (err) {
      throw err;
    }
  };
  public post = async (url: string, data: object, header: object) => {
    const response = await axios.post(url, data, { headers: this.setHeaders(header) });
    return response.data;
  };
}
const http = new Http();
export default http;
