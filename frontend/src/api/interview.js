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

export const register = async (email, username, password, fullName, birthDate, profileImage) => {
    const response = await api.post('/auth/register', {
        email,
        username,
        password,
        full_name: fullName,
        birth_date: birthDate,
        profile_image: profileImage,
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

export const createInterview = async (position, jobPostingId = null, resumeId = null, scheduledTime = null) => {
    const payload = {
        position,
        company_id: jobPostingId,
        resume_id: resumeId,
        scheduled_time: scheduledTime
    };
    console.log('[InterviewAPI] createInterview Payload:', payload);
    const response = await api.post('/interviews', payload);
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

export const triggerNextQuestion = async (interviewId) => {
    const response = await api.post(`/interviews/${interviewId}/trigger-question`);
    return response.data;
};


// ==================== Transcript ====================

export const recognizeAudio = async (audioBlob) => {
    const formData = new FormData();
    formData.append('file', audioBlob);

    // 타임아웃 5분 (모델 로딩 대비)
    const response = await api.post('/stt/recognize', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000
    });
    return response.data;
};


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

    const response = await api.post('/resumes/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data;
};

export const getResume = async (resumeId) => {
    const response = await api.get(`/resumes/${resumeId}`);
    return response.data;
};

export const getResumePdf = async (resumeId) => {
    const response = await api.get(`/api/resumes/${resumeId}/pdf`, {
        responseType: 'blob'
    });
    return response.data; // this is the Blob
};

export const getAllInterviews = async () => {
    const response = await api.get('/interviews');
    return response.data;
};

export const updateUserProfile = async ({ fullName, birthDate, email, phoneNumber, profileImageFile, desiredCompanyTypes, desiredPositions }) => {
    const formData = new FormData();
    if (fullName !== undefined && fullName !== null) formData.append('full_name', fullName);
    if (birthDate !== undefined && birthDate !== null) formData.append('birth_date', birthDate);
    if (email !== undefined && email !== null) formData.append('email', email);
    if (phoneNumber !== undefined && phoneNumber !== null) formData.append('phone_number', phoneNumber);
    if (profileImageFile instanceof File) formData.append('profile_image', profileImageFile);
    if (desiredCompanyTypes !== undefined && desiredCompanyTypes !== null) formData.append('desired_company_types', JSON.stringify(desiredCompanyTypes));
    if (desiredPositions !== undefined && desiredPositions !== null) formData.append('desired_positions', JSON.stringify(desiredPositions));

    const response = await api.patch('/users/me', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const changePassword = async (newPassword) => {
    const response = await api.patch('/auth/password', null, {
        params: { new_password: newPassword }
    });
    return response.data;
};

export const withdrawUser = async () => {
    const response = await api.delete('/auth/withdraw');
    return response.data;
};
