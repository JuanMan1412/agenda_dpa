import api from "../../services/api";

export default class Request {
  static get(path, callback) { return api.get(path, { callback }); }
  static post(path, data = {}, callback) { return api.post(path, data, { callback }); }
  static postMultipart(path, data = {}, callback) { return api.post(path, data, { callback }); }
  static put(path, data = {}, callback) { return api.put(path, data, { callback }); }
  static delete(path, callback) { return api.delete(path, { callback }); }
  static patch(path, data = {}, callback) { return api.patch(path, data, { callback }); }
  static download(path) { return api.get(path, { responseType: "blob" }); }
}
