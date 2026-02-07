import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
});

// Request interceptor
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('[API] Request to:', config.url, '| Token present:', !!token);
    } else {
        console.warn('[API] Request to:', config.url, '| No token found');
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Response interceptor to handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            console.error('[API] 401 Unauthorized - Token may be expired or invalid');
            // Clear invalid token
            localStorage.removeItem('token');
            // Redirect to login if not already on auth page
            if (window.location.pathname !== '/') {
                window.location.href = '/';
            }
        }
        return Promise.reject(error);
    }
);

// ==================== Auth ====================

export const register = async (email, username, password, fullName) => {
    const response = await api.post('/auth/register', {
        email,
        username,
        password,
        full_name: fullName,
        role: 'candidate'
    });
    return response.data;
};

export const login = async (username, password) => {
    // FastAPI OAuth2PasswordRequestForm은 form-data 형식 요구
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/token', formData.toString(), {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
    
    if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
};

export const logout = () => {
    localStorage.removeItem('token');
};

export const getCurrentUser = async () => {
    const response = await api.get('/users/me'); // users 라우터는 별도 분리 예정 또는 main에 유지
    return response.data;
};

// export const getDeepgramToken = async () => {
//     const response = await api.get('/auth/deepgram-token');
//     return response.data.temp_key;
// };
// -> Removed Deepgram Token API

export const recognizeAudio = async (audioBlob) => {
    const formData = new FormData();
    // 파일명은 timestamp 등으로 유니크하게 지정 (백엔드 처리용)
    formData.append('file', audioBlob, `recording_${Date.now()}.webm`);
    
    // Hugging Face Whisper API 엔드포인트 호출
    const response = await api.post('/stt/recognize', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data; // { text: "..." }
};

// ==================== Interview ====================

export const createInterview = async (position, companyId = null, resumeId = null, scheduledTime = null) => {
    const response = await api.post('/interviews', {
        position,
        company_id: companyId,
        resume_id: resumeId,
        scheduled_time: scheduledTime
    });
    return response.data;
};

export const getInterviewQuestions = async (interviewId) => {
    const response = await api.get(`/interviews/${interviewId}/questions`);
    return response.data;
};

export const completeInterview = async (interviewId) => {
    const response = await api.post(`/interviews/${interviewId}/complete`);
    return response.data;
};

// ==================== Transcript ====================

export const createTranscript = async (interviewId, speaker, text, questionId = null) => {
    const response = await api.post('/transcripts', {
        interview_id: interviewId,
        speaker: speaker,
        text: text,
        question_id: questionId
    });
    return response.data;
};

export const getInterviewTranscripts = async (interviewId) => {
    const response = await api.get(`/interviews/${interviewId}/transcripts`);
    return response.data;
};

// ==================== Evaluation ====================

export const getEvaluationReport = async (interviewId) => {
    const response = await api.get(`/interviews/${interviewId}/report`);
    return response.data;
};

// ==================== Resume & Recruiter ====================

export const uploadResume = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/resumes/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data;
};

export const getResume = async (resumeId) => {
    const response = await api.get(`/api/resumes/${resumeId}`);
    return response.data;
};

export const getAllInterviews = async () => {
    const response = await api.get('/interviews');
    return response.data;
};