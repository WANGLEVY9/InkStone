import axios from "axios";

const client = axios.create({
    baseURL: (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_BASE_URL || "/api/v1",
    timeout: 15000,
});

export default client;
