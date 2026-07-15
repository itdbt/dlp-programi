import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor - attach token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('dlp_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle 401
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('dlp_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// AUTH
const login = (formData) => client.post('/auth/login', formData, {
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
})
const getMe = () => client.get('/auth/me')
const updateProfile = (data) => client.put('/auth/me', data)
const changePassword = (data) => client.put('/auth/me/password', data)
const getUsers = (params) => client.get('/auth/users', { params })
const createUser = (data) => client.post('/auth/users', data)
const updateUser = (id, data) => client.put(`/auth/users/${id}`, data)
const deleteUser = (id) => client.delete(`/auth/users/${id}`)

// DASHBOARD
const getDashboardStats = () => client.get('/dashboard/stats')
const getDashboardHealth = () => client.get('/dashboard/health')

// POLICIES
const listPolicies = (params) => client.get('/policies', { params })
const createPolicy = (data) => client.post('/policies', data)
const getPolicy = (id) => client.get(`/policies/${id}`)
const updatePolicy = (id, data) => client.put(`/policies/${id}`, data)
const removePolicy = (id) => client.delete(`/policies/${id}`)
const togglePolicy = (id) => client.post(`/policies/${id}/toggle`)

// INCIDENTS
const listIncidents = (params) => client.get('/incidents', { params })
const createIncident = (data) => client.post('/incidents', data)
const getIncident = (id) => client.get(`/incidents/${id}`)
const updateIncident = (id, data) => client.put(`/incidents/${id}`, data)
const changeIncidentStatus = (id, status) => client.post(`/incidents/${id}/status`, { status })
const assignIncident = (id, userId) => client.post(`/incidents/${id}/assign`, { user_id: userId })
const addComment = (id, comment) => client.post(`/incidents/${id}/comments`, { comment })
const getIncidentSummary = () => client.get('/incidents/summary')

// SCANS
const listScans = (params) => client.get('/scans', { params })
const startLocalScan = (data) => client.post('/scans/local', data)
const startGoogleDriveScan = (data) => client.post('/scans/google-drive', data)
const startOneDriveScan = (data) => client.post('/scans/onedrive', data)
const startSharePointScan = (data) => client.post('/scans/sharepoint', data)
const startGmailScan = (data) => client.post('/scans/gmail', data)
const startOutlookScan = (data) => client.post('/scans/outlook', data)
const getScan = (id) => client.get(`/scans/${id}`)
const getScanResults = (id, params) => client.get(`/scans/${id}/results`, { params })
const removeScan = (id) => client.delete(`/scans/${id}`)
const getPatterns = () => client.get('/scans/patterns')

// REPORTS
const getIncidentReport = (params) => client.get('/reports/incidents', { params })
const getScanReport = (params) => client.get('/reports/scans', { params })
const getComplianceReport = (params) => client.get('/reports/compliance', { params })
const getRiskMatrix = (params) => client.get('/reports/risk-matrix', { params })
const getDataTypesReport = (params) => client.get('/reports/data-types', { params })
const exportIncidentsCSV = (params) => client.get('/reports/incidents/export', { params, responseType: 'blob' })
const exportScansCSV = (params) => client.get('/reports/scans/export', { params, responseType: 'blob' })

// INTEGRATIONS
const listIntegrations = () => client.get('/integrations')
const configureGoogle = (data) => client.post('/integrations/google', data)
const configureOffice365 = (data) => client.post('/integrations/office365', data)
const configureSMTP = (data) => client.post('/integrations/smtp', data)
const getIntegration = (type) => client.get(`/integrations/${type}`)
const updateIntegration = (type, data) => client.put(`/integrations/${type}`, data)
const removeIntegration = (type) => client.delete(`/integrations/${type}`)
const testIntegration = (type) => client.post(`/integrations/${type}/test`)
const syncIntegration = (type) => client.post(`/integrations/${type}/sync`)

// NOTIFICATIONS
const getNotificationRules = () => client.get('/notifications/rules')
const createNotificationRule = (data) => client.post('/notifications/rules', data)
const updateNotificationRule = (id, data) => client.put(`/notifications/rules/${id}`, data)
const deleteNotificationRule = (id) => client.delete(`/notifications/rules/${id}`)
const getNotificationLogs = (params) => client.get('/notifications/logs', { params })
const sendTestNotification = (data) => client.post('/notifications/test', data)

// SETTINGS
const getAllSettings = () => client.get('/settings')
const updateSettings = (data) => client.put('/settings', data)
const getAuditLogs = (params) => client.get('/settings/audit-logs', { params })
const clearLogs = () => client.post('/settings/clear-logs')
const getSystemInfo = () => client.get('/settings/system-info')

export const api = {
  auth: {
    login,
    getMe,
    updateProfile,
    changePassword,
    getUsers,
    createUser,
    updateUser,
    deleteUser
  },
  dashboard: {
    getStats: getDashboardStats,
    getHealth: getDashboardHealth
  },
  policies: {
    list: listPolicies,
    create: createPolicy,
    get: getPolicy,
    update: updatePolicy,
    remove: removePolicy,
    toggle: togglePolicy
  },
  incidents: {
    list: listIncidents,
    create: createIncident,
    get: getIncident,
    update: updateIncident,
    changeStatus: changeIncidentStatus,
    assign: assignIncident,
    addComment,
    getSummary: getIncidentSummary
  },
  scans: {
    list: listScans,
    startLocal: startLocalScan,
    startGoogleDrive: startGoogleDriveScan,
    startOneDrive: startOneDriveScan,
    startSharePoint: startSharePointScan,
    startGmail: startGmailScan,
    startOutlook: startOutlookScan,
    get: getScan,
    getResults: getScanResults,
    remove: removeScan,
    getPatterns
  },
  reports: {
    getIncidents: getIncidentReport,
    getScans: getScanReport,
    getCompliance: getComplianceReport,
    getRiskMatrix,
    getDataTypes: getDataTypesReport,
    exportIncidents: exportIncidentsCSV,
    exportScans: exportScansCSV
  },
  integrations: {
    list: listIntegrations,
    configureGoogle,
    configureOffice365,
    configureSMTP,
    get: getIntegration,
    update: updateIntegration,
    remove: removeIntegration,
    test: testIntegration,
    sync: syncIntegration
  },
  notifications: {
    getRules: getNotificationRules,
    createRule: createNotificationRule,
    updateRule: updateNotificationRule,
    deleteRule: deleteNotificationRule,
    getLogs: getNotificationLogs,
    sendTest: sendTestNotification
  },
  settings: {
    getAll: getAllSettings,
    update: updateSettings,
    getAuditLogs,
    clearLogs,
    getSystemInfo
  }
}

export default client
