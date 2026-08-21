import api from "./api";

export const aiApi = {
  // Send chat message with streaming response
  chat: async (message) => {
    const response = await fetch('/api/v1/patient/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      },
      body: JSON.stringify({ message })
    });
    return response;
  },

  // Transcribe voice note
  transcribeVoice: async (audioFile) => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    
    return api.post('/patient/ai/voice-chat', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Generate conversation summary
  generateSummary: async (conversationId) => {
    return api.post('/patient/ai/summary', { conversation_id: conversationId });
  },

  // Get patient timeline
  getTimeline: async () => {
    return api.get('/patient/timeline');
  },

  // Get patient AI summary (for doctors)
  getPatientSummary: async (patientPublicId) => {
    return api.get(`/staff/doctor/patient-summary/${patientPublicId}`);
  },

  // Discharge patient
  dischargePatient: async (patientPublicId, dischargeNotes) => {
    return api.post('/staff/doctor/discharge', {
      patient_public_id: patientPublicId,
      discharge_notes: dischargeNotes
    });
  }
};
