import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
});

// Request interceptor
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

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
    const response = await api.get('/users/me');
    return response.data;
};

// ==================== Interview ====================

export const createInterview = async (position, jobPostingId = null, scheduledTime = null) => {
    const response = await api.post('/interviews', {
        position,
        job_posting_id: jobPostingId,
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