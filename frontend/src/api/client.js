import axios from "axios";

export const api = axios.create({
    baseURL: "http://localhost:8000",
});

// ============================================================
// Request interceptor
// ============================================================

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("access_token");

        if (token) {
            config.headers = config.headers || {};
            config.headers.Authorization = `Bearer ${token}`;
        }

        /*
         * IMPORTANT:
         *
         * When sending FormData, do NOT manually set
         * Content-Type.
         *
         * The browser/Axios will automatically generate:
         *
         * multipart/form-data; boundary=...
         *
         * FastAPI needs that boundary to correctly detect
         * the uploaded "file" field.
         */

        if (config.data instanceof FormData) {
            if (config.headers) {
                delete config.headers["Content-Type"];
                delete config.headers["content-type"];
            }
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;