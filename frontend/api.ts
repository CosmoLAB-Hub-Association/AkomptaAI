import axios from 'axios';
import { UserProfile, Transaction, Product, Budget, Notification } from './types';

export const BASE_URL = 'http://127.0.0.1:8000';

const API_URL = `${BASE_URL}/api`;

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Token management
export const setAuthToken = (token: string) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        localStorage.setItem('accessToken', token);
    } else {
        delete api.defaults.headers.common['Authorization'];
        localStorage.removeItem('accessToken');
    }
};

export const setRefreshToken = (token: string) => {
    if (token) {
        localStorage.setItem('refreshToken', token);
    } else {
        localStorage.removeItem('refreshToken');
    }
};

// Initialize token from storage
const storedToken = localStorage.getItem('accessToken');
if (storedToken) {
    setAuthToken(storedToken);
}

// Interceptor for 401 (Token Refresh)
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
                        refresh: refreshToken,
                    });
                    const { access } = response.data;
                    setAuthToken(access);
                    originalRequest.headers['Authorization'] = `Bearer ${access}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // Logout if refresh fails
                    setAuthToken('');
                    setRefreshToken('');
                    window.location.reload(); // Or redirect to login
                }
            }
        }
        return Promise.reject(error);
    }
);

export const auth = {
    register: (data: any) => api.post('/auth/register/', data),
    login: (data: any) => api.post('/auth/login/', data),
    getProfile: () => api.get<UserProfile>('/auth/me/'),
    updateProfile: (data: Partial<UserProfile>) => api.patch<UserProfile>('/auth/me/', data),
    changePassword: (data: any) => api.post('/auth/change-password/', data),
    uploadAvatar: (file: File) => {
        const formData = new FormData();
        formData.append('avatar', file);
        return api.patch<UserProfile>('/auth/me/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    uploadBusinessLogo: (file: File) => {
        const formData = new FormData();
        formData.append('business_logo', file);
        return api.patch<UserProfile>('/auth/me/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
};


export const products = {
    list: (params?: any) => api.get<{ results: Product[] }>('/products/', { params }),
    create: (data: any) => api.post<Product>('/products/', data),
    update: (id: string, data: any) => api.patch<Product>(`/products/${id}/`, data),
    delete: (id: string) => api.delete(`/products/${id}/`),
    export: () => api.get('/products/export/', { responseType: 'blob' }),
};

export const transactions = {
    list: (params?: any) => api.get<{ results: Transaction[] }>('/transactions/', { params }),
    create: (data: any) => api.post<Transaction>('/transactions/', data),
    update: (id: string, data: any) => api.patch<Transaction>(`/transactions/${id}/`, data),
    delete: (id: string) => api.delete(`/transactions/${id}/`),
    summary: () => api.get('/transactions/summary/'),
};

export const budgets = {
    list: () => api.get<{ results: Budget[] }>('/budgets/'),
    create: (data: any) => api.post<Budget>('/budgets/', data),
    update: (id: string, data: any) => api.patch<Budget>(`/budgets/${id}/`, data),
    delete: (id: string) => api.delete(`/budgets/${id}/`),
};

export const ads = {
    list: (params?: any) => api.get('/ads/', { params }),
    create: (data: any) => {
        const isFormData = data instanceof FormData;
        return api.post('/ads/', data, {
            headers: {
                'Content-Type': isFormData ? 'multipart/form-data' : 'application/json',
            },
        });
    },
};

export const notifications = {
    list: () => api.get<{ results: Notification[] }>('/notifications/'),
    markRead: (id: string) => api.patch(`/notifications/${id}/mark_read/`),
    markAllRead: () => api.patch('/notifications/mark_all_read/'),
};

export const support = {
    create: (data: any) => api.post('/support/', data),
    list: () => api.get('/support/'),
};

export const analytics = {
    overview: () => api.get('/analytics/overview/'),
    breakdown: () => api.get('/analytics/breakdown/'),
    kpi: () => api.get('/analytics/kpi/'),
    activity: () => api.get('/analytics/activity/'),
    balanceHistory: () => api.get('/analytics/balance-history/'),
    insights: (context: any) => api.post('/ai-insights/', { context }),
};

export const voice = {
    send: (data: FormData | { text: string }) => {
        const isFormData = data instanceof FormData;
        return api.post('/voice-command/', data, {
            headers: {
                'Content-Type': isFormData ? 'multipart/form-data' : 'application/json',
            },
        });
    },
};

export const reports = {
    syscohadaZip: (year?: number) =>
        api.get('/reports/syscohada/download/', {
            params: year ? { year } : undefined,
            responseType: 'blob',
        }),
};

export default api;
