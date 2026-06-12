const DEMO_BOOT_VERSION = "demo-ready-20260611";
console.log("DEMO_APP_JS_LOADED", DEMO_BOOT_VERSION);

const state = {
  equipment: [],
  spares: [],
  history: [],
  demoQueries: [],
  alerts: [],
  roleNotifications: [],
  liveMonitor: null,
  intelligence: null,
  knowledgeSources: null,
  agentic: null,
  agentMetrics: null,
  enterprise: null,
  assetMaster: [],
  operationsCenter: null,
  plantCommandCenter: null,
  plantDigitalTwin: null,
  aiPipeline: null,
  incidentReplay: null,
  reportCatalog: [],
  dependencyGraph: null,
  twinSelectedAssetId: "",
  telemetryTimer: null,
  telemetrySnapshot: {},
  streamAlerts: [],
  previousInvestigations: {},
  lastAssistantText: "",
  selectionRequestId: 0,
  chatHistory: [],
  chatThreads: {},
  workOrder: null,
  selectedEquipmentId: "",
  selectedAsset: null,
  investigationStatus: "NOT_STARTED",
  investigationAssetId: "",
  investigationError: "",
  selectedFinancialImpact: null,
  assetFilterArea: "",
  report: null,
  systemReady: false,
  aiModelReady: false,
  modelStatus: null,
  modelHealth: null,
  backendAvailable: true,
  aiStatus: "",
  startupStartedAt: Date.now(),
  preloadStatus: null,
  startupHealth: null,
  preloadTimer: null,
  lastStartupHealthPollAt: 0,
  investigationProgressTimer: null,
  aiReadyLogged: false,
};

const STARTUP_GRACE_SECONDS = 60;
const STARTUP_POLL_MS = 7000;
const READY_POLL_MS = 30000;
const STARTUP_HEALTH_READY_POLL_MS = 60000;
const DISPLAY_EMPTY = "\u2014";
const INVESTIGATION_STATES = Object.freeze({
  NOT_STARTED: "NOT_STARTED",
  RUNNING: "RUNNING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
});

const els = {
  moduleNav: document.querySelector("#moduleNav"),
  equipmentList: document.querySelector("#equipmentList"),
  equipmentSelect: document.querySelector("#equipmentSelect"),
  globalSearch: document.querySelector("#globalSearch"),
  globalSearchResults: document.querySelector("#globalSearchResults"),
  queryInput: document.querySelector("#queryInput"),
  analyzeButton: document.querySelector("#analyzeButton"),
  runDemoButton: document.querySelector("#runDemoButton"),
  clearButton: document.querySelector("#clearButton"),
  feedbackInput: document.querySelector("#feedbackInput"),
  feedbackButton: document.querySelector("#feedbackButton"),
  refreshLiveButton: document.querySelector("#refreshLiveButton"),
  refreshIntelButton: document.querySelector("#refreshIntelButton"),
  ingestButton: document.querySelector("#ingestButton"),
  chatButton: document.querySelector("#chatButton"),
  whatIfButton: document.querySelector("#whatIfButton"),
  workOrderButton: document.querySelector("#workOrderButton"),
  workOrderSaveButton: document.querySelector("#workOrderSaveButton"),
  workOrderJsonButton: document.querySelector("#workOrderJsonButton"),
  workOrderPdfButton: document.querySelector("#workOrderPdfButton"),
  workOrderStatus: document.querySelector("#workOrderStatus"),
  handoverPdfButton: document.querySelector("#handoverPdfButton"),
  procurementButton: document.querySelector("#procurementButton"),
  reliabilityButton: document.querySelector("#reliabilityButton"),
  executiveReportButton: document.querySelector("#executiveReportButton"),
  executiveReportPdfButton: document.querySelector("#executiveReportPdfButton"),
  knowledgeButton: document.querySelector("#knowledgeButton"),
  scenarioTemperature: document.querySelector("#scenarioTemperature"),
  scenarioVibration: document.querySelector("#scenarioVibration"),
  scenarioCurrent: document.querySelector("#scenarioCurrent"),
  scenarioHydraulic: document.querySelector("#scenarioHydraulic"),
  knowledgeInput: document.querySelector("#knowledgeInput"),
  ingestType: document.querySelector("#ingestType"),
  ingestContent: document.querySelector("#ingestContent"),
  chatInput: document.querySelector("#chatInput"),
  statusStrip: document.querySelector("#statusStrip"),
  assetName: document.querySelector("#assetName"),
  assetAlert: document.querySelector("#assetAlert"),
  riskLevel: document.querySelector("#riskLevel"),
  riskScore: document.querySelector("#riskScore"),
  rulHours: document.querySelector("#rulHours"),
  healthIndex: document.querySelector("#healthIndex"),
  urgencyPill: document.querySelector("#urgencyPill"),
  diagnosisContent: document.querySelector("#diagnosisContent"),
  recommendationsList: document.querySelector("#recommendationsList"),
  traceabilityList: document.querySelector("#traceabilityList"),
  alertList: document.querySelector("#alertList"),
  sparesList: document.querySelector("#sparesList"),
  inventoryKpis: document.querySelector("#inventoryKpis"),
  inventoryRiskAlert: document.querySelector("#inventoryRiskAlert"),
  inventorySearch: document.querySelector("#inventorySearch"),
  inventoryStockFilter: document.querySelector("#inventoryStockFilter"),
  inventoryTypeFilter: document.querySelector("#inventoryTypeFilter"),
  inventorySort: document.querySelector("#inventorySort"),
  liveMonitor: document.querySelector("#liveMonitor"),
  roleNotifications: document.querySelector("#roleNotifications"),
  executiveSummary: document.querySelector("#executiveSummary"),
  plantCommandKpis: document.querySelector("#plantCommandKpis"),
  plantHealthOverview: document.querySelector("#plantHealthOverview"),
  plantHealthPill: document.querySelector("#plantHealthPill"),
  sectorHeatmap: document.querySelector("#sectorHeatmap"),
  clearSectorFilterButton: document.querySelector("#clearSectorFilterButton"),
  criticalAssetList: document.querySelector("#criticalAssetList"),
  maintenanceFeed: document.querySelector("#maintenanceFeed"),
  predictiveTimeline: document.querySelector("#predictiveTimeline"),
  digitalTwin: document.querySelector("#digitalTwin"),
  twinStage: document.querySelector("#twinStage"),
  maintenancePlan: document.querySelector("#maintenancePlan"),
  workOrderView: document.querySelector("#workOrderView"),
  knowledgeResults: document.querySelector("#knowledgeResults"),
  knowledgeCenter: document.querySelector("#knowledgeCenter"),
  knowledgeStats: document.querySelector("#knowledgeStats"),
  ingestedInputs: document.querySelector("#ingestedInputs"),
  sensorEventRepository: document.querySelector("#sensorEventRepository"),
  chatWindow: document.querySelector("#chatWindow"),
  copilotStatus: document.querySelector("#copilotStatus"),
  activeAssetChip: document.querySelector("#activeAssetChip"),
  executiveAiSummary: document.querySelector("#executiveAiSummary"),
  llmProvider: document.querySelector("#llmProvider"),
  aiConfidencePill: document.querySelector("#aiConfidencePill"),
  executiveDecisionSummary: document.querySelector("#executiveDecisionSummary"),
  agentMetrics: document.querySelector("#agentMetrics"),
  agentExecution: document.querySelector("#investigationTimeline"),
  reasoningTrace: document.querySelector("#reasoningTrace"),
  managementDashboard: document.querySelector("#managementDashboard"),
  shiftHandover: document.querySelector("#shiftHandover"),
  criticalityMatrix: document.querySelector("#criticalityMatrix"),
  costImpact: document.querySelector("#costImpact"),
  budgetDashboard: document.querySelector("#budgetDashboard"),
  budgetTrend: document.querySelector("#budgetTrend"),
  maintenanceKpis: document.querySelector("#maintenanceKpis"),
  rcaWorkspace: document.querySelector("#rcaWorkspace"),
  failureTimeline: document.querySelector("#failureTimeline"),
  operationButton: document.querySelector("#operationButton"),
  operationStrategy: document.querySelector("#operationStrategy"),
  operationSimulator: document.querySelector("#operationSimulator"),
  procurementAssistant: document.querySelector("#procurementAssistant"),
  teamWorkload: document.querySelector("#teamWorkload"),
  auditTrail: document.querySelector("#auditTrail"),
  mobileFieldMode: document.querySelector("#mobileFieldMode"),
  copilotPrompts: document.querySelector("#copilotPrompts"),
  incidentReplay: document.querySelector("#incidentReplay"),
  reliabilityAssessment: document.querySelector("#reliabilityAssessment"),
  executiveReportPreview: document.querySelector("#executiveReportPreview"),
  executiveDashboardView: document.querySelector("#executiveDashboardView"),
  operationsCenterKpis: document.querySelector("#operationsCenterKpis"),
  plantDigitalTwin: document.querySelector("#plantDigitalTwin"),
  twinAssetPanel: document.querySelector("#twinAssetPanel"),
  aiPipeline: document.querySelector("#aiPipeline"),
  pipelineTotal: document.querySelector("#pipelineTotal"),
  reportTypeSelect: document.querySelector("#reportTypeSelect"),
  reportPdfButton: document.querySelector("#reportPdfButton"),
  reportExcelButton: document.querySelector("#reportExcelButton"),
  reportJsonButton: document.querySelector("#reportJsonButton"),
  enterpriseReportPreview: document.querySelector("#enterpriseReportPreview"),
  predictiveAnalytics: document.querySelector("#predictiveAnalytics"),
  predictionConfidence: document.querySelector("#predictionConfidence"),
  dependencyGraph: document.querySelector("#dependencyGraph"),
  liveTelemetry: document.querySelector("#liveTelemetry"),
  streamAlerts: document.querySelector("#streamAlerts"),
  streamStatus: document.querySelector("#streamStatus"),
  voiceListenButton: document.querySelector("#voiceListenButton"),
  voiceSpeakButton: document.querySelector("#voiceSpeakButton"),
  voiceStatus: document.querySelector("#voiceStatus"),
  selectedAssetProfile: document.querySelector("#selectedAssetProfile"),
  performanceHealth: document.querySelector("#performanceHealth"),
  modelDiagnostics: document.querySelector("#modelDiagnostics"),
  providerStatus: document.querySelector("#providerStatus"),
  failureProbabilityPill: document.querySelector("#failureProbabilityPill"),
  failureProbabilityWidget: document.querySelector("#failureProbabilityWidget"),
  maintenanceCalendar: document.querySelector("#maintenanceCalendar"),
  spareRecommendations: document.querySelector("#spareRecommendations"),
  failureStageTimeline: document.querySelector("#failureStageTimeline"),
  assetRelationshipView: document.querySelector("#assetRelationshipView"),
};

let backendOnline = true;
let activeChatRequest = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  console.log("API_RAW_RESPONSE", { path, status: response.status, ok: response.ok, data });
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg || item.detail || JSON.stringify(item)).join("; ")
      : data.detail;
    throw new Error(data.error || detail || data.message || `Request failed (${response.status})`);
  }
  return data;
}

async function apiWithTimeout(path, options = {}, timeoutMs = 15000, controller = new AbortController()) {
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await api(path, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Backend request timed out.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

function setBackendStatus(isOnline, detail = "") {
  backendOnline = Boolean(isOnline);
  state.backendAvailable = backendOnline;
  if (!els.copilotStatus) return;
  const statusLine = els.copilotStatus.querySelector("div:first-child span");
  if (statusLine) {
    statusLine.textContent = backendOnline ? "Backend Online" : "Backend Offline";
    statusLine.className = `connectivity-badge ${backendOnline ? "online" : "offline"}`;
    statusLine.title = detail;
  }
  if (els.providerStatus) {
    els.providerStatus.textContent = backendOnline ? "AI Provider: Groq Online" : "AI Provider: Backend Offline";
  }
}

function backendOfflineMessage(error) {
  const text = error?.message || "";
  return text.includes("timed out") ? "Backend Offline - request timed out." : "Backend Offline";
}

window.addEventListener("offline", () => {
  cancelActiveChatRequest("browser_offline");
  setBackendStatus(false, "Browser reported offline.");
  console.log("BACKEND_UNAVAILABLE", { reason: "browser_offline", timestamp: new Date().toISOString() });
});

window.addEventListener("online", () => {
  setBackendStatus(true);
});

function createRequestId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function cancelActiveChatRequest(reason = "cancelled") {
  if (!activeChatRequest) return;
  activeChatRequest.streamCancelled = true;
  activeChatRequest.cancelReason = reason;
  if (!activeChatRequest.controller.signal.aborted) {
    activeChatRequest.controller.abort();
  }
}

function isActiveChatRequest(requestId) {
  return Boolean(
    activeChatRequest &&
    activeChatRequest.id === requestId &&
    !activeChatRequest.streamCancelled &&
    !activeChatRequest.controller.signal.aborted
  );
}

async function verifyBackendForStream(requestId) {
  if (!isActiveChatRequest(requestId)) return false;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 650);
  try {
    const response = await fetch("/api/preload-status", { signal: controller.signal });
    let data = {};
    try {
      data = await response.clone().json();
    } catch {
      data = {};
    }
    console.log("API_RAW_RESPONSE", { path: "/api/preload-status", status: response.status, ok: response.ok, data });
    return response.ok && isActiveChatRequest(requestId);
  } catch {
    console.log("BACKEND_UNAVAILABLE", { requestId, stage: "stream_heartbeat" });
    setBackendStatus(false, "Backend unavailable during response stream.");
    if (activeChatRequest?.id === requestId) {
      activeChatRequest.streamCancelled = true;
      activeChatRequest.cancelReason = "backend_unavailable";
    }
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

function safeValue(value, fallback = DISPLAY_EMPTY) {
  if (value === undefined || value === null) return fallback;
  if (typeof value === "number" && Number.isNaN(value)) return fallback;
  if (value === "") return fallback;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return fallback;
    if (/^(undefined|null|nan)$/i.test(trimmed)) return fallback;
    return value
      .replace(/\bundefined\b/gi, fallback)
      .replace(/\bnull\b/gi, fallback)
      .replace(/\bNaN\b/g, fallback);
  }
  return value;
}

function safe(value, fallback = DISPLAY_EMPTY) {
  return safeValue(value, fallback);
}

function safeNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function isMissingValue(value) {
  if (value === undefined || value === null) return true;
  if (typeof value === "number" && Number.isNaN(value)) return true;
  if (typeof value === "string" && !value.trim()) return true;
  if (typeof value === "string" && /^(undefined|null|nan)$/i.test(value.trim())) return true;
  return false;
}

function logMissingRenderField(scope, field, value) {
  if (!isMissingValue(value)) return false;
  console.error(`Missing ${field}`, { scope, field, value });
  return true;
}

function escapeHtml(value) {
  return String(safeValue(value))
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function firstDefined(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

function normalizeRiskLabel(level, fallback = "low") {
  const value = String(firstDefined(level, fallback, "low")).trim().toLowerCase();
  if (["critical", "high", "medium", "low"].includes(value)) return value;
  if (["watch", "warning", "warn"].includes(value)) return "medium";
  if (["stable", "healthy", "normal", "ok"].includes(value)) return "low";
  return String(fallback || "low").toLowerCase();
}

function classifyRisk(score, fallback = "low") {
  const numeric = Number(score);
  if (Number.isFinite(numeric)) {
    if (numeric >= 90) return "critical";
    if (numeric >= 75) return "high";
    if (numeric >= 50) return "medium";
    return "low";
  }
  return normalizeRiskLabel(fallback);
}

function riskDisplay(level) {
  return normalizeRiskLabel(level).toUpperCase();
}

function selectedReport() {
  const reportAssetId = assetDisplayId(state.report?.equipment || {});
  return state.report && state.selectedEquipmentId && reportAssetId === state.selectedEquipmentId ? state.report : null;
}

function selectedRiskScore() {
  const report = selectedReport();
  const selected = selectedEquipment() || {};
  const master = state.assetMaster.find((asset) => asset.id === state.selectedEquipmentId || asset.equipment_id === state.selectedEquipmentId) || {};
  const twin = selectedTwinAsset() || {};
  return firstDefined(report?.risk?.score, twin.risk_score, master.risk_score, selected.risk_score);
}

function selectedRiskLevel() {
  const report = selectedReport();
  if (report?.risk?.level) return normalizeRiskLabel(report.risk.level);
  const selected = selectedEquipment() || {};
  const master = state.assetMaster.find((asset) => asset.id === state.selectedEquipmentId || asset.equipment_id === state.selectedEquipmentId) || {};
  const twin = selectedTwinAsset() || {};
  return normalizeRiskLabel(firstDefined(twin.risk_level, master.risk_level, selected.risk_level, classifyRisk(selectedRiskScore(), "low")));
}

function setInvestigationStatus(status, equipmentId = state.selectedEquipmentId, error = "") {
  state.investigationStatus = status || INVESTIGATION_STATES.NOT_STARTED;
  state.investigationAssetId = equipmentId || "";
  state.investigationError = error || "";
}

function investigationStatusForSelectedAsset() {
  if (!state.selectedEquipmentId) return INVESTIGATION_STATES.NOT_STARTED;
  if (state.investigationAssetId && state.investigationAssetId !== state.selectedEquipmentId) {
    return INVESTIGATION_STATES.NOT_STARTED;
  }
  return state.investigationStatus || INVESTIGATION_STATES.NOT_STARTED;
}

function payloadMatchesSelectedAsset(payload = {}) {
  if (!state.selectedEquipmentId) return false;
  const payloadAssetId = firstDefined(payload?.asset, payload?.equipment_id, payload?.asset_id, payload?.equipment?.equipment_id, payload?.equipment?.asset_id);
  return !payloadAssetId || payloadAssetId === state.selectedEquipmentId;
}

function normalizeEquipmentRecord(item = {}) {
  const equipmentId = firstDefined(item.equipment_id, item.asset_id, item.assetId, item.id);
  const assetName = firstDefined(item.asset_name, item.equipment_name, item.assetName, item.name, equipmentId);
  const alert = firstDefined(item.anomaly_alert, item.active_alert, item.alert_code, item.alert, item.status, "NORMAL_WATCH");
  const riskScore = firstDefined(item.risk_score, item.risk?.score);
  const riskLevel = firstDefined(item.risk_level, item.risk?.level, item.risk)
    ? normalizeRiskLabel(firstDefined(item.risk_level, item.risk?.level, item.risk))
    : classifyRisk(riskScore, "low");
  return {
    ...item,
    equipment_id: equipmentId || "",
    asset_id: equipmentId || "",
    equipment_name: assetName || "",
    asset_name: assetName || "",
    anomaly_alert: alert || "NORMAL_WATCH",
    risk_level: riskLevel,
  };
}

function normalizeReport(report = {}) {
  if (!report?.equipment) return report;
  const normalizedRisk = {
    ...(report.risk || {}),
    level: report?.risk?.level ? normalizeRiskLabel(report.risk.level) : classifyRisk(report?.risk?.score, "low"),
  };
  return {
    ...report,
    equipment: normalizeEquipmentRecord(report.equipment),
    risk: normalizedRisk,
  };
}

function normalizePlantDigitalTwinPayload(data) {
  if (!data?.zones) return data;
  return {
    ...data,
    zones: data.zones.map((zone) => ({
      ...zone,
      assets: (zone.assets || []).map(normalizeEquipmentRecord),
    })),
  };
}

function assetDisplayName(item = {}) {
  return firstDefined(item.asset_name, item.equipment_name, item.assetName, item.name, item.equipment_id, item.id, "-");
}

function assetDisplayId(item = {}) {
  return firstDefined(item.equipment_id, item.asset_id, item.assetId, item.id, "-");
}

function assetDisplayAlert(item = {}) {
  return firstDefined(item.anomaly_alert, item.active_alert, item.alert_code, item.alert, item.status, "NORMAL_WATCH");
}

function msValue(source = {}, ...keys) {
  for (const key of keys) {
    const value = source?.[key];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return null;
}

function formatMs(value) {
  if (value === undefined || value === null || value === "") return "n/a";
  const number = Number(value);
  return Number.isFinite(number) ? `${number.toFixed(1)} ms` : "n/a";
}

function riskClass(level) {
  return `risk-${normalizeRiskLabel(level)}`;
}

function pillClass(level) {
  return `pill ${normalizeRiskLabel(level)}`;
}

function money(value) {
  const number = safeNumber(value, 0);
  if (number >= 100000) {
    return `₹${(number / 100000).toFixed(1)} L`;
  }
  return `₹${number.toLocaleString("en-IN")}`;
}

function formatKpiValue(item) {
  return item?.money ? money(item.value) : item?.value;
}

function inStartupGracePeriod() {
  return Date.now() - state.startupStartedAt < STARTUP_GRACE_SECONDS * 1000;
}

function logStatusTransition(nextStatus) {
  if (state.aiStatus === nextStatus) return;
  state.aiStatus = nextStatus;
  if (nextStatus === "ready") console.log("STATUS_READY", { timestamp: new Date().toISOString() });
  if (nextStatus === "initializing") console.log("STATUS_INITIALIZING", { timestamp: new Date().toISOString() });
  if (nextStatus === "offline") console.log("STATUS_OFFLINE", { timestamp: new Date().toISOString() });
}

function aiStatusLabel(isReady = state.systemReady) {
  if (!state.backendAvailable) return "Backend Offline";
  return isReady ? "AI Ready" : "AI Initializing";
}

function removeStartupBlocker() {
  document.querySelectorAll([
    "#startupOverlay",
    ".startup-overlay",
    ".startup-gate",
    ".startup-screen",
    ".ai-warmup-screen",
    ".ai-loading-screen",
    ".model-warmup-screen",
    ".warmup-overlay",
    ".preload-overlay",
    ".loading-overlay",
    "[data-warmup-overlay]",
    "[data-startup-overlay]",
  ].join(", ")).forEach((element) => {
    element.remove();
  });
  document.body.classList.remove("startup-blocked", "ai-warmup-active", "warmup-active", "preload-blocked", "loading-blocked");
  document.documentElement.classList.add("dashboard-visible");
  document.body.classList.add("dashboard-visible");
  const shell = document.querySelector(".app-shell");
  const workspace = document.querySelector(".workspace");
  if (shell) shell.style.removeProperty("display");
  if (workspace) workspace.style.removeProperty("display");
}

function setBusy(isBusy) {
  const investigationReady = state.systemReady && state.aiModelReady && Boolean(state.selectedEquipmentId);
  els.analyzeButton.disabled = isBusy || !investigationReady;
  els.runDemoButton.disabled = isBusy;
  if (els.whatIfButton) els.whatIfButton.disabled = isBusy;
  els.analyzeButton.textContent = !state.selectedEquipmentId
    ? "Select Asset"
    : !state.systemReady
    ? aiStatusLabel(false)
    : !state.aiModelReady
    ? "AI Engine Initializing"
    : isBusy
        ? "Running Investigation..."
        : "Run Investigation";
  els.analyzeButton.classList.toggle("is-loading", Boolean(isBusy));
}

function setAiActionAvailability(isReady, modelReady = state.aiModelReady) {
  state.systemReady = Boolean(isReady);
  state.aiModelReady = Boolean(modelReady);
  const unavailableLabel = state.systemReady && !state.aiModelReady ? "AI Engine Initializing" : aiStatusLabel(false);
  const assetSelected = Boolean(state.selectedEquipmentId);
  const gatedButtons = [
    els.chatButton,
    els.executiveReportButton,
    els.executiveReportPdfButton,
    els.procurementButton,
    els.reliabilityButton,
    els.workOrderButton,
    els.reportPdfButton,
    els.reportExcelButton,
    els.reportJsonButton,
  ].filter(Boolean);
  gatedButtons.forEach((button) => {
    button.disabled = !state.systemReady || !state.aiModelReady;
    button.title = state.systemReady && state.aiModelReady ? "" : unavailableLabel;
  });
  if (els.analyzeButton) {
    els.analyzeButton.disabled = !state.systemReady || !state.aiModelReady || !assetSelected;
    els.analyzeButton.title = !assetSelected
      ? "Select an asset to start investigation."
      : !state.systemReady
      ? unavailableLabel
      : !state.aiModelReady
      ? "Embedding and reranker models are loading in the background."
      : "";
    els.analyzeButton.textContent = !assetSelected
      ? "Select Asset"
      : !state.systemReady
      ? unavailableLabel
      : !state.aiModelReady
      ? "AI Engine Initializing"
      : "Run Investigation";
  }
  if (els.chatButton) {
    els.chatButton.textContent = state.systemReady && state.aiModelReady ? "Send" : unavailableLabel;
  }
}

function combinedAiStatus(preload = {}, startup = {}) {
  const background = startup.background_status || {};
  const completed = Boolean(firstDefined(preload.completed, background.completed, startup.preload_completed));
  const embeddingLoaded = Boolean(firstDefined(preload.embedding_loaded, startup.embedding_loaded, background.embedding_loaded));
  const rerankerLoaded = Boolean(firstDefined(preload.reranker_loaded, startup.reranker_loaded, background.reranker_loaded));
  const vectorStoreLoaded = Boolean(firstDefined(preload.vector_store_loaded, startup.vector_store_loaded, background.vector_store_loaded));
  const workflowLoaded = Boolean(firstDefined(preload.workflow_loaded, startup.workflow_loaded, background.workflow_loaded));
  const ready = vectorStoreLoaded && workflowLoaded;
  const modelWarmup = preload.model_warmup || startup.model_warmup || background.model_warmup || {};
  const aiModelReady = Boolean(
    firstDefined(preload.ai_model_ready, startup.ai_model_ready, modelWarmup.ai_model_ready, embeddingLoaded && rerankerLoaded)
  );
  const completedSteps = [vectorStoreLoaded, workflowLoaded].filter(Boolean).length;
  return {
    ...background,
    ...startup,
    ...preload,
    completed,
    embedding_loaded: embeddingLoaded,
    reranker_loaded: rerankerLoaded,
    embedding_warming: Boolean(firstDefined(preload.embedding_warming, startup.embedding_warming, modelWarmup.embedding_warming)),
    reranker_warming: Boolean(firstDefined(preload.reranker_warming, startup.reranker_warming, modelWarmup.reranker_warming)),
    ai_model_ready: aiModelReady,
    model_warmup: modelWarmup,
    vector_store_loaded: vectorStoreLoaded,
    workflow_loaded: workflowLoaded,
    system_ready: ready,
    ready_steps_completed: completedSteps,
    ready_steps_total: 2,
    ready_progress_percent: ready ? 100 : Number(firstDefined(preload.ready_progress_percent, background.ready_progress_percent, Math.round((completedSteps / 2) * 100), 0)),
  };
}

async function refreshPreloadStatus(options = {}) {
  removeStartupBlocker();
  const forceStartupHealth = Boolean(options.forceStartupHealth);
  const shouldPollStartupHealth = forceStartupHealth
    || !state.systemReady
    || Date.now() - state.lastStartupHealthPollAt >= STARTUP_HEALTH_READY_POLL_MS;
  const shouldPollModelStatus = false;
  const [preloadResult, startupResult, modelResult] = await Promise.allSettled([
    apiWithTimeout("/api/preload-status", {}, 15000),
    shouldPollStartupHealth ? apiWithTimeout("/api/startup-health", {}, 15000) : Promise.resolve({ skipped: true }),
    shouldPollModelStatus ? apiWithTimeout("/api/model-status", {}, 15000) : Promise.resolve({ skipped: true }),
  ]);
  const preload = preloadResult.status === "fulfilled" ? preloadResult.value : {};
  const startupHealthSkipped = startupResult.status === "fulfilled" && startupResult.value?.skipped;
  const startup = startupResult.status === "fulfilled" && !startupHealthSkipped ? startupResult.value : (state.startupHealth || {});
  const modelStatusSkipped = modelResult.status === "fulfilled" && modelResult.value?.skipped;
  const modelStatus = modelResult.status === "fulfilled" && !modelStatusSkipped ? modelResult.value : (state.modelStatus || {});
  if (startupResult.status === "fulfilled" && !startupHealthSkipped) {
    state.lastStartupHealthPollAt = Date.now();
  }
  const backendReachable = preloadResult.status === "fulfilled"
    || (startupResult.status === "fulfilled" && !startupHealthSkipped)
    || (modelResult.status === "fulfilled" && !modelStatusSkipped);
  if (!backendReachable && inStartupGracePeriod()) {
    setBackendStatus(true, "Health endpoints are still starting.");
    const ready = state.systemReady;
    setAiActionAvailability(ready);
    logStatusTransition(ready ? "ready" : "initializing");
    renderPreloadProgress({ ...(state.preloadStatus || {}), system_ready: ready, ready_progress_percent: state.systemReady ? 100 : state.preloadStatus?.ready_progress_percent || 0 });
    return;
  }
  if (!backendReachable) {
    const error = preloadResult.reason || startupResult.reason || new Error("Backend Offline");
    setBackendStatus(false, error.message);
    setAiActionAvailability(false);
    logStatusTransition("offline");
    renderPreloadProgress({ system_ready: false, error: "Backend Offline", ready_progress_percent: 0 });
    return;
  }
  try {
    console.log("PRELOAD_STATUS_RECEIVED", preload);
    if (!startupHealthSkipped) console.log("STARTUP_HEALTH_RECEIVED", startup);
    if (modelResult.status === "fulfilled" && !modelStatusSkipped) console.log("MODEL_STATUS_RECEIVED", modelStatus);
    const status = combinedAiStatus({ ...preload, ...modelStatus }, startup);
    console.log("Warmup gate source", {
      gateCondition: "dashboard_ready_requires_vector_store_and_workflow_only",
      vector_store_loaded: status.vector_store_loaded,
      workflow_loaded: status.workflow_loaded,
      system_ready: status.system_ready,
      embedding_loaded: status.embedding_loaded,
      reranker_loaded: status.reranker_loaded,
      ai_model_ready: status.ai_model_ready,
      model_warmup_running: Boolean(status.model_warmup?.running),
    });
    state.preloadStatus = status;
    state.startupHealth = startup;
    state.modelStatus = modelStatus;
    setBackendStatus(true);
    const ready = state.systemReady || Boolean(status.vector_store_loaded && status.workflow_loaded);
    const modelReady = Boolean(status.ai_model_ready);
    setAiActionAvailability(ready, modelReady);
    logStatusTransition(ready ? "ready" : "initializing");
    renderPreloadProgress(status);
    if (ready && !state.aiReadyLogged) {
      state.aiReadyLogged = true;
      console.log("AI_ENGINE_READY", status);
    }
  } catch (error) {
    setBackendStatus(false, error.message);
    setAiActionAvailability(false);
    logStatusTransition("offline");
    renderPreloadProgress({ system_ready: false, error: "Backend Offline", ready_progress_percent: 0 });
  }
}

function renderPreloadProgress(status = state.preloadStatus) {
  if (!status) return;
  removeStartupBlocker();
  console.log("Warmup gate source", {
    gateCondition: "fullscreen_warmup_disabled_badge_only",
    vector_store_loaded: Boolean(status.vector_store_loaded),
    workflow_loaded: Boolean(status.workflow_loaded),
    system_ready: Boolean(state.systemReady || status.system_ready),
    embedding_loaded: Boolean(status.embedding_loaded),
    reranker_loaded: Boolean(status.reranker_loaded),
    ai_model_ready: Boolean(status.ai_model_ready),
    model_warmup_running: Boolean(status.model_warmup?.running),
  });
  if (els.statusStrip) {
    renderStatus(state.alerts || []);
  }
  if (els.copilotStatus) {
    els.copilotStatus.dataset.ready = state.systemReady ? "true" : "false";
    const sourceTitle = els.copilotStatus.querySelector(".source-title");
    if (sourceTitle) {
      sourceTitle.textContent = state.aiModelReady ? "Knowledge Sources Connected" : "AI Engine Initializing";
    }
  }
  renderModelWarningBanner(status);
}

function modelFallbackActive(source = state.modelHealth || state.preloadStatus || {}) {
  return Boolean(source.fallback_active || source.embedding_fallback_active || source.reranker_fallback_active);
}

function semanticRetrievalDisabled(source = state.modelHealth || state.preloadStatus || {}) {
  if (source.embedding_warming || source.reranker_warming || source.ai_model_ready === false) return false;
  const embeddingUnavailable = !Boolean(source.embedding_loaded || source.embedding_real_model_loaded);
  const rerankerUnavailable = !Boolean(source.reranker_loaded || source.reranker_real_model_loaded);
  return embeddingUnavailable && rerankerUnavailable;
}

function activeRetrievalMode(source = state.modelHealth || state.preloadStatus || {}) {
  if (source.retrieval_mode) return source.retrieval_mode;
  if (source.embedding_real_model_loaded && source.reranker_real_model_loaded) return "Hybrid RAG";
  if (source.embedding_loaded || source.embedding_real_model_loaded) return "Semantic RAG";
  if (modelFallbackActive(source)) return "Lexical Fallback";
  if (source.embedding_warming || source.reranker_warming || source.ai_model_ready === false) return "AI Engine Initializing";
  return semanticRetrievalDisabled(source) ? "Semantic Retrieval Disabled" : "Initializing";
}

function ensureModelWarningBanner() {
  let banner = document.querySelector("#modelWarningBanner");
  if (banner) return banner;
  banner = document.createElement("div");
  banner.id = "modelWarningBanner";
  banner.className = "model-warning-banner";
  const workspace = document.querySelector(".workspace");
  const topbar = document.querySelector(".topbar");
  if (workspace && topbar) {
    topbar.insertAdjacentElement("afterend", banner);
  } else {
    document.body.prepend(banner);
  }
  return banner;
}

function renderModelWarningBanner(source = state.modelHealth || state.preloadStatus || {}) {
  const banner = ensureModelWarningBanner();
  if (!semanticRetrievalDisabled(source)) {
    banner.classList.add("hidden");
    banner.innerHTML = "";
    return;
  }
  banner.classList.remove("hidden");
  const reasons = [source.embedding_fallback_reason, source.reranker_fallback_reason].filter(Boolean);
  banner.innerHTML = `
    <strong>Semantic AI retrieval disabled</strong>
    <span>Active mode: ${escapeHtml(activeRetrievalMode(source))}</span>
    <small>${escapeHtml(reasons.join(" | ") || "Embedding or reranker model is unavailable.")}</small>
  `;
}

function renderNoInvestigationState(noAsset = !state.selectedEquipmentId) {
  const contextPreview = noAsset ? "" : renderAssetContextPreview();
  if (els.queryInput) {
    els.queryInput.value = "";
    els.queryInput.placeholder = noAsset
      ? "No investigation active. Select an asset and click Run Investigation, or ask a maintenance question."
      : "No investigation active. Click Run Investigation to generate an asset-specific brief.";
  }
  if (els.assetName) els.assetName.textContent = noAsset ? "Select Asset" : assetDisplayName(selectedEquipment());
  if (els.assetAlert) els.assetAlert.textContent = noAsset ? "No asset selected" : `${assetDisplayId(selectedEquipment())} - ${assetDisplayAlert(selectedEquipment())}`;
  if (els.riskLevel) {
    els.riskLevel.textContent = "—";
    els.riskLevel.className = "";
  }
  if (els.riskScore) els.riskScore.textContent = noAsset ? "Awaiting asset selection" : "Awaiting investigation";
  if (els.rulHours) els.rulHours.textContent = "—";
  if (els.healthIndex) els.healthIndex.textContent = "—";
  if (els.urgencyPill) {
    els.urgencyPill.textContent = noAsset ? "Select Asset" : "Ready";
    els.urgencyPill.className = "pill";
  }
  if (els.diagnosisContent) {
    els.diagnosisContent.innerHTML = `
      <div class="empty-state compact">
        ${noAsset ? "No investigation active. Select an asset to begin." : "Asset context loaded. Run Investigation to generate diagnosis, root cause, ROI, and recommendations."}
      </div>
      ${contextPreview}
    `;
  }
  if (els.recommendationsList) {
    els.recommendationsList.innerHTML = `<li>${noAsset ? "No recommendations generated." : "Run Investigation to generate recommendations."}</li>`;
  }
  if (els.traceabilityList) {
    els.traceabilityList.innerHTML = `<div class="empty-state compact">Evidence will appear after investigation.</div>`;
  }
  if (els.executiveDecisionSummary) {
    els.executiveDecisionSummary.innerHTML = `<div class="empty-state compact">No executive recommendation generated.</div>`;
  }
  if (els.executiveAiSummary) {
    els.executiveAiSummary.textContent = noAsset
      ? "No investigation active. Select an asset and click Run Investigation or ask a maintenance question."
      : "Asset selected. Run an investigation to generate the executive maintenance recommendation.";
  }
  if (els.costImpact) {
    els.costImpact.innerHTML = `<div class="empty-state compact">ROI analysis will appear after investigation.</div>`;
  }
  if (els.agentExecution) {
    els.agentExecution.innerHTML = `<div class="empty-state compact">No investigation active. LangGraph execution timeline will appear during Run Investigation.</div>`;
  }
  if (els.reasoningTrace) {
    els.reasoningTrace.innerHTML = `<div class="empty-state compact">Reasoning and evidence will appear after investigation.</div>`;
  }
  if (els.aiConfidencePill) {
    els.aiConfidencePill.textContent = "AI Confidence";
    els.aiConfidencePill.className = "pill";
  }
  if (noAsset) {
    renderAssetIntelligenceWidgets(null);
  }
  renderActiveAssetChip();
}

function renderAssetContextPreview() {
  const asset = selectedTwinAsset() || {};
  const context = activeAssetContext();
  const prediction = asset?.id ? predictionForAsset(asset) : null;
  const failureProbability = failureProbabilityForContext();
  const maintenance = (asset.maintenance_history || []).slice(0, 3);
  const agentHistory = (state.aiPipeline?.steps || state.aiPipeline?.stages || []).slice(0, 4);
  const sensor = context.sensor_snapshot || {};
  const sensorBars = Object.entries(sensor).slice(0, 6).map(([key, value]) => {
    const width = Math.max(8, Math.min(100, safeNumber(value, 0)));
    return `<div><span>${escapeHtml(key)}</span><b>${escapeHtml(safe(value))}</b><i style="width:${width}%"></i></div>`;
  }).join("");
  return `
    <div class="asset-context-preview">
      ${kpiCard("Asset Risk Trend", safe(prediction?.trend || context.risk_level), "Existing digital twin trend")}
      ${kpiCard("Failure Probability", `${safe(failureProbability)}%`, "Estimated from current health")}
      ${kpiCard("RUL Gauge", safe(context.rul_days), safe(context.remaining_useful_life))}
      ${kpiCard("Current Alert", safe(context.current_alert), "Active asset alert")}
      <div class="context-preview-wide">
        <strong>Sensor Snapshot</strong>
        <div class="twin-analytics">${sensorBars || `<div><span>No sensor snapshot</span><b>—</b><i style="width:0%"></i></div>`}</div>
      </div>
      <div class="context-preview-wide">
        <strong>Maintenance Schedule</strong>
        ${(maintenance.length ? maintenance : [{ date: "—", action: "No maintenance schedule loaded" }]).map((item) => `<p class="mini-record">${escapeHtml(safe(item.date || item.timestamp))} - ${escapeHtml(safe(item.action || item.finding || item.summary))}</p>`).join("")}
      </div>
      <div class="context-preview-wide">
        <strong>Agent Execution History</strong>
        ${(agentHistory.length ? agentHistory : [{ name: "No previous agent execution", status: "—", latency_ms: "—" }]).map((item) => `<p class="mini-record">${escapeHtml(safe(item.name || item.stage))} - ${escapeHtml(safe(item.status))} - ${escapeHtml(safe(item.latency_ms))} ms</p>`).join("")}
      </div>
    </div>
  `;
}

function nextStatusPollDelay() {
  if (!state.systemReady) return STARTUP_POLL_MS;
  return READY_POLL_MS;
}

function schedulePreloadStatusPoll(delayMs = nextStatusPollDelay()) {
  if (state.preloadTimer) {
    clearTimeout(state.preloadTimer);
    state.preloadTimer = null;
  }
  state.preloadTimer = setTimeout(async () => {
    state.preloadTimer = null;
    await refreshPreloadStatus();
    schedulePreloadStatusPoll();
  }, delayMs);
}

async function pollStatusNow(reason, options = {}) {
  console.log("STATUS_POLL_IMMEDIATE", { reason, timestamp: new Date().toISOString() });
  if (state.preloadTimer) {
    clearTimeout(state.preloadTimer);
    state.preloadTimer = null;
  }
  await refreshPreloadStatus(options);
  schedulePreloadStatusPoll();
}

async function startPreloadStatusPolling() {
  removeStartupBlocker();
  if (state.preloadTimer) {
    clearTimeout(state.preloadTimer);
    state.preloadTimer = null;
  }
  logStatusTransition("initializing");
  await refreshPreloadStatus({ forceStartupHealth: true });
  schedulePreloadStatusPoll();
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2800);
}

function on(element, eventName, handler) {
  if (element) {
    element.addEventListener(eventName, handler);
  }
}

function switchModule(moduleName) {
  document.querySelectorAll(".module-view").forEach((view) => {
    view.classList.toggle("active", view.dataset.module === moduleName);
  });
  if (els.moduleNav) {
    els.moduleNav.querySelectorAll("button").forEach((button) => {
      button.classList.toggle("active", button.dataset.module === moduleName);
    });
  }
  if (moduleName === "settings") {
    renderPerformanceHealth();
  }
  if (moduleName === "incident-replay") {
    refreshIncidentReplay("module_open");
  }
  if (moduleName === "executive-dashboard") {
    renderExecutiveDashboardView();
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function selectedEquipment() {
  if (!state.selectedEquipmentId) return null;
  return state.equipment.find((item) => item.equipment_id === state.selectedEquipmentId) || null;
}

function selectedAssetData(equipmentId = state.selectedEquipmentId) {
  if (!equipmentId) return null;
  const equipment = state.equipment.find((item) => item.equipment_id === equipmentId) || {};
  const master = state.assetMaster.find((asset) => asset.id === equipmentId || asset.equipment_id === equipmentId) || {};
  const twinAssets = state.plantDigitalTwin?.zones?.flatMap((zone) => zone.assets || []) || [];
  const twin = twinAssets.find((asset) => asset.id === equipmentId) || {};
  const report = state.report?.equipment && assetDisplayId(state.report.equipment) === equipmentId ? state.report : null;
  const spares = (state.spares || []).filter((item) => item.equipment_id === equipmentId || item.asset_id === equipmentId);
  const history = (state.history || []).filter((item) => item.equipment_id === equipmentId || item.asset_id === equipmentId);
  const sensorSnapshot = {
    ...(twin.sensor_snapshot || {}),
    ...(state.telemetrySnapshot[equipmentId] || {}),
    temperature: firstDefined(twin.sensor_snapshot?.temperature, state.telemetrySnapshot[equipmentId]?.temperature, equipment.temperature_c, equipment.temperature),
    vibration: firstDefined(twin.sensor_snapshot?.vibration, state.telemetrySnapshot[equipmentId]?.vibration, equipment.vibration_mm_s, equipment.vibration),
    pressure: firstDefined(twin.sensor_snapshot?.pressure, state.telemetrySnapshot[equipmentId]?.pressure, equipment.hydraulic_pressure_bar, equipment.pressure),
    current: firstDefined(twin.sensor_snapshot?.current, state.telemetrySnapshot[equipmentId]?.current, equipment.motor_current_a, equipment.current),
    oil_quality: firstDefined(twin.sensor_snapshot?.oil_quality, state.telemetrySnapshot[equipmentId]?.oil_quality, equipment.oil_quality),
    flow: firstDefined(twin.sensor_snapshot?.flow, state.telemetrySnapshot[equipmentId]?.flow, equipment.flow),
  };
  const merged = normalizeEquipmentRecord({
    ...master,
    ...equipment,
    equipment_id: equipmentId,
    id: equipmentId,
    name: firstDefined(twin.name, master.name, equipment.asset_name, equipment.equipment_name),
    equipment_name: firstDefined(twin.name, master.name, equipment.asset_name, equipment.equipment_name),
    asset_name: firstDefined(twin.name, master.name, equipment.asset_name, equipment.equipment_name),
    area: firstDefined(twin.area, master.area, equipment.area),
    type: firstDefined(twin.type, master.type, equipment.type),
    health_score: firstDefined(twin.health_score, master.health_score, equipment.health_score, report?.prediction?.health_index),
    risk_level: normalizeRiskLabel(firstDefined(report?.risk?.level, twin.risk_level, master.risk_level, equipment.risk_level, classifyRisk(firstDefined(report?.risk?.score, twin.risk_score, master.risk_score, equipment.risk_score), "low"))),
    status: firstDefined(twin.status, master.status, equipment.status),
    current_alert: firstDefined(twin.current_alert, master.active_alert, equipment.anomaly_alert, report?.equipment?.active_alert),
    sensor_snapshot: sensorSnapshot,
    maintenance_history: twin.maintenance_history || master.maintenance_history || [],
    recent_failures: twin.recent_failures || history || [],
    work_orders: twin.work_orders || [],
    spares,
    failure_modes: master.failure_modes || report?.diagnosis?.asset_failure_modes || [],
    relationships: firstDefined(twin.relationships, master.relationships, equipment.relationships, []),
    report,
  });
  return merged;
}

function clampNumber(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

function matchingAssetByName(name) {
  const needle = String(name || "").toLowerCase();
  const assets = [
    ...(state.assetMaster || []),
    ...(state.equipment || []),
    ...(state.plantDigitalTwin?.zones?.flatMap((zone) => zone.assets || []) || []),
  ];
  return assets.find((asset) => {
    const text = `${asset.name || ""} ${asset.asset_name || ""} ${asset.equipment_name || ""} ${asset.type || ""}`.toLowerCase();
    return text.includes(needle) || needle.includes(String(asset.type || "").toLowerCase());
  });
}

function relationshipChainForAsset(asset) {
  const type = String(asset?.type || asset?.name || "").toLowerCase();
  const selectedName = assetDisplayName(asset);
  if (type.includes("drive motor") || type.includes("motor")) {
    return [
      { name: selectedName, dependency_type: "Selected Asset" },
      { name: "Gearbox", dependency_type: "Downstream Drive Train" },
      { name: "Coupling", dependency_type: "Mechanical Coupling" },
      { name: "Mill Stand", dependency_type: "Production Consumer" },
    ];
  }
  if (type.includes("gearbox")) {
    return [
      { name: "Drive Motor", dependency_type: "Upstream Prime Mover" },
      { name: selectedName, dependency_type: "Selected Asset" },
      { name: "Coupling", dependency_type: "Downstream Coupling" },
      { name: "Mill Stand", dependency_type: "Production Consumer" },
    ];
  }
  if (type.includes("hydraulic")) {
    return [
      { name: "Hydraulic Tank", dependency_type: "Fluid Source" },
      { name: selectedName, dependency_type: "Selected Asset" },
      { name: "Pressure Valve", dependency_type: "Control Element" },
      { name: "Actuator", dependency_type: "Downstream Load" },
    ];
  }
  if (type.includes("conveyor")) {
    return [
      { name: selectedName, dependency_type: "Selected Asset" },
      { name: "Drive Pulley", dependency_type: "Torque Transfer" },
      { name: "Belt", dependency_type: "Material Flow" },
      { name: "Downstream Chute", dependency_type: "Production Consumer" },
    ];
  }
  return [
    { name: "Upstream Feed", dependency_type: "Upstream Asset" },
    { name: selectedName, dependency_type: "Selected Asset" },
    { name: "Control System", dependency_type: "Control Dependency" },
    { name: "Downstream Process", dependency_type: "Production Consumer" },
  ];
}

function normalizeRelationshipNode(item, index, asset = state.selectedAsset) {
  const match = matchingAssetByName(item.name || item.asset_name || item.node_name);
  const isSelected = item.dependency_type === "Selected Asset" || item.id === asset?.equipment_id || item.name === assetDisplayName(asset);
  const nodeAsset = isSelected ? asset : match || {};
  return {
    id: firstDefined(item.id, item.equipment_id, nodeAsset.id, nodeAsset.equipment_id, `${asset?.equipment_id || "asset"}-rel-${index}`),
    name: firstDefined(item.name, item.asset_name, item.node_name, nodeAsset.name, nodeAsset.asset_name, nodeAsset.equipment_name),
    health: firstDefined(item.health, item.health_score, nodeAsset.health_score, isSelected ? asset?.health_score : "—"),
    risk: classifyRisk(firstDefined(item.risk_score, nodeAsset.risk_score), firstDefined(item.risk, item.risk_level, nodeAsset.risk_level, isSelected ? asset?.risk_level : "medium")),
    dependency_type: firstDefined(item.dependency_type, item.relationship, item.status, isSelected ? "Selected Asset" : "Dependency"),
    isSelected,
  };
}

function buildAssetRelationshipView(asset = state.selectedAsset) {
  if (!asset?.equipment_id) return null;
  const sourceRelationships = Array.isArray(asset.relationships) && asset.relationships.length
    ? asset.relationships
    : relationshipChainForAsset(asset);
  const nodes = sourceRelationships.map((item, index) => normalizeRelationshipNode(item, index, asset));
  const selectedNode = nodes.find((node) => node.isSelected) || normalizeRelationshipNode({ name: assetDisplayName(asset), dependency_type: "Selected Asset" }, 0, asset);
  const edges = nodes.slice(0, -1).map((node, index) => ({
    source: node.id,
    target: nodes[index + 1].id,
    relationship: nodes[index + 1].dependency_type,
  }));
  return {
    root: assetDisplayName(asset),
    nodes,
    edges,
    relationships: nodes,
    children: nodes.filter((node) => node.id !== selectedNode.id).map((node) => ({
      name: node.name,
      status: node.dependency_type,
      health: node.health,
      risk: node.risk,
      dependency_type: node.dependency_type,
    })),
  };
}

function buildSelectedAssetIntelligence(asset = state.selectedAsset) {
  if (!asset?.equipment_id) return null;
  const health = safeNumber(asset.health_score, 75);
  const risk = String(asset.risk_level || "medium").toLowerCase();
  const history = asset.recent_failures || [];
  const maintenance = asset.maintenance_history || [];
  const spares = asset.spares || [];
  const riskOffset = { critical: 32, high: 22, medium: 12, low: 4 }[risk] || 10;
  const failurePercent = Number((clampNumber((100 - health) * 0.75 + riskOffset + history.length * 1.6, 4, 97)).toFixed(1));
  const probability = {
    percent: failurePercent,
    level: failurePercent < 30 ? "low" : failurePercent < 70 ? "medium" : "high",
    confidence: Math.round(clampNumber(68 + history.length * 1.8 + maintenance.length * 1.2 + Object.keys(asset.sensor_snapshot || {}).length * 2, 58, 96)),
    drivers: {
      health_score: health,
      failure_history_records: history.length,
      maintenance_records: maintenance.length,
      spare_parts: spares.length,
    },
  };
  const rulHours = safeNumber(firstDefined(asset.rul_hours, asset.report?.prediction?.estimated_remaining_useful_life_hours), Math.max(0, Math.round((safeNumber(asset.rated_hours, 50000) - safeNumber(asset.running_hours, 49000)) * (health / 100))));
  const openWorkOrder = (asset.work_orders || []).find((item) => ["Open", "Assigned"].includes(item.status));
  const assetProfile = {
    asset_id: asset.equipment_id,
    asset_name: assetDisplayName(asset),
    area: asset.area,
    sector: asset.area,
    manufacturer: asset.manufacturer || "Tata Steel OEM Cell",
    commission_date: asset.commission_date || "—",
    operating_hours: firstDefined(asset.running_hours, asset.operating_hours),
    criticality: asset.criticality || asset.risk_level,
    current_failure_mode: (asset.failure_modes || [asset.current_alert || asset.anomaly_alert || "watch"])[0],
    failure_probability: probability.percent,
    rul_hours: rulHours,
    health_score: health,
    last_maintenance_date: firstDefined(asset.last_maintenance, maintenance[0]?.date),
    next_planned_maintenance: firstDefined(openWorkOrder?.created_at, asset.next_planned_maintenance, "Not scheduled"),
    asset_icon: asset.type || "Industrial Asset",
  };
  const maintenanceCalendar = [
    { window: "Today", items: [`Inspect ${assetDisplayName(asset)} if risk trend worsens`, `${(asset.work_orders || []).filter((item) => item.status === "Open").length} open work order(s)`] },
    { window: "7 Days", items: [`Review RUL forecast: ${safe(rulHours)} h`, `${history.slice(0, 5).length} recent failure reference(s)`] },
    { window: "30 Days", items: [`Planned PM after ${maintenance[0]?.action || "condition review"}`, "Spare min-max review"] },
    { window: "90 Days", items: ["Reliability review", "Long-term component replacement planning"] },
  ];
  const spareRecommendations = spares
    .slice()
    .sort((a, b) => safeNumber(firstDefined(a.current_stock, a.available_qty), 0) - safeNumber(firstDefined(b.current_stock, b.available_qty), 0))
    .slice(0, 4)
    .map((item) => {
      const stock = safeNumber(firstDefined(item.current_stock, item.available_qty), 0);
      const minStock = safeNumber(firstDefined(item.min_stock, 1), 1);
      const leadTime = safeNumber(item.lead_time_days, 0);
      return {
        part: firstDefined(item.part_name, item.part),
        quantity: Math.max(1, minStock - stock + 1),
        stock,
        lead_time_days: leadTime,
        availability: stock > 0 ? "In Stock" : "Stockout",
        risk_if_unavailable: probability.percent >= 70 || leadTime >= 14 ? "High" : "Medium",
      };
    });
  if (!spareRecommendations.length) {
    const fallbackParts = (asset.failure_modes || [asset.current_alert || "critical component"])
      .slice(0, 3)
      .map((mode) => String(mode).replace(/_/g, " ").replace(/\bfailure\b/gi, "").trim())
      .filter(Boolean);
    (fallbackParts.length ? fallbackParts : ["inspection kit", "sensor kit"]).forEach((part) => {
      spareRecommendations.push({
        part,
        quantity: probability.percent >= 70 ? 2 : 1,
        stock: "—",
        lead_time_days: "—",
        availability: "Review Required",
        risk_if_unavailable: probability.percent >= 70 ? "High" : "Medium",
      });
    });
  }
  const currentStage = probability.percent < 20 ? "Normal" : probability.percent < 45 ? "Watch" : probability.percent < 70 ? "Warning" : "Critical";
  const failureTimeline = ["Normal", "Watch", "Warning", "Critical", "Predicted Failure"].map((stage) => ({
    stage,
    active: stage === currentStage || (stage === "Predicted Failure" && probability.percent >= 88),
  }));
  return {
    asset_profile: assetProfile,
    failure_probability: probability,
    maintenance_calendar: maintenanceCalendar,
    spare_recommendations: spareRecommendations,
    failure_timeline: failureTimeline,
    relationship_view: buildAssetRelationshipView(asset),
  };
}

function updateSelectedAssetState(equipmentId = state.selectedEquipmentId, overrides = {}) {
  state.selectedAsset = equipmentId ? selectedAssetData(equipmentId) : null;
  if (state.selectedAsset) {
    const override = overrides.asset_intelligence;
    const overrideAssetId = firstDefined(override?.asset_profile?.asset_id, override?.asset_profile?.equipment_id);
    const overrideMatches = override && (!overrideAssetId || overrideAssetId === equipmentId);
    state.selectedAsset.asset_intelligence = overrideMatches ? override : buildSelectedAssetIntelligence(state.selectedAsset);
  }
  return state.selectedAsset;
}

function dispatchAssetSelected(reason = "selection") {
  window.dispatchEvent(new CustomEvent("maintenance-asset-selected", {
    detail: {
      reason,
      equipment_id: state.selectedEquipmentId,
      asset: state.selectedAsset,
    },
  }));
}

function selectEquipment(equipmentId, updateQuery = false, refreshContext = false) {
  const previousEquipmentId = state.selectedEquipmentId;
  if (!equipmentId) {
    state.selectedEquipmentId = "";
    state.twinSelectedAssetId = "";
    state.selectedAsset = null;
    state.report = null;
    state.incidentReplay = null;
    state.workOrder = null;
    state.agentic = null;
    state.selectedFinancialImpact = null;
    setInvestigationStatus(INVESTIGATION_STATES.NOT_STARTED, "");
    if (els.equipmentSelect) els.equipmentSelect.value = "";
    if (els.queryInput) els.queryInput.value = "";
    state.chatHistory = [];
    renderEquipment();
    renderNoInvestigationState(true);
    renderAgentic(null);
    renderWorkOrder(state.workOrder);
    renderExecutiveDashboardView();
    renderIncidentReplay();
    renderChat();
    setAiActionAvailability(state.systemReady, state.aiModelReady);
    dispatchAssetSelected("cleared");
    pollStatusNow("asset_change");
    return;
  }
  state.selectedEquipmentId = equipmentId;
  state.twinSelectedAssetId = equipmentId;
  state.incidentReplay = null;
  if (previousEquipmentId !== equipmentId) {
    state.report = null;
    state.workOrder = null;
    state.agentic = null;
    state.selectedFinancialImpact = null;
    setInvestigationStatus(INVESTIGATION_STATES.NOT_STARTED, equipmentId);
  }
  updateSelectedAssetState(equipmentId);
  els.equipmentSelect.value = equipmentId;
  if (previousEquipmentId && previousEquipmentId !== equipmentId) {
    cancelActiveChatRequest("asset_changed");
    state.chatThreads[previousEquipmentId] = state.chatHistory.filter((item) => item.role !== "assistant").slice(-20);
    saveCopilotMemory({}, previousEquipmentId);
    state.chatHistory = [];
    loadCopilotMemory(equipmentId);
    renderChat();
  }
  if (updateQuery) {
    els.queryInput.value = buildLocalInvestigationBrief();
  }
  renderEquipment();
  renderActiveAssetChip();
  renderSelectedAsset();
  renderSpares();
  renderWorkOrder(state.workOrder);
  renderScenarioInputs();
  renderLiveMonitor();
  renderDigitalTwin();
  renderPlantDigitalTwin();
    renderPredictiveAnalytics();
    renderDependencyGraph();
    renderLiveTelemetry();
    renderNoInvestigationState(false);
  renderAgentic(null);
  renderExecutiveDashboardView();
  renderIncidentReplay();
  dispatchAssetSelected("selected");
  setAiActionAvailability(state.systemReady, state.aiModelReady);
  if (refreshContext) {
    refreshSelectedAssetContext(updateQuery);
  }
  pollStatusNow("asset_change");
}

function buildLocalInvestigationBrief() {
  const item = selectedEquipment();
  if (!item) return "";
  const equipmentId = assetDisplayId(item);
  const equipmentName = assetDisplayName(item);
  const alert = assetDisplayAlert(item);
  const breaches = [
    Number(item.vibration_mm_s) >= 4.5 ? `vibration ${item.vibration_mm_s} mm/s` : "",
    Number(item.temperature_c) >= 75 ? `temperature ${item.temperature_c} C` : "",
    Number(item.hydraulic_pressure_bar) <= 120 ? `hydraulic pressure ${item.hydraulic_pressure_bar} bar` : "",
    Number(item.oil_pressure_bar) <= 2.8 ? `oil pressure ${item.oil_pressure_bar} bar` : "",
    Number(item.motor_current_a) >= 320 ? `motor current ${item.motor_current_a} A` : "",
  ].filter(Boolean).join(", ") || "current readings inside warning band";
  const master = state.assetMaster.find((asset) => asset.id === equipmentId || asset.equipment_id === equipmentId);
  const modes = master?.failure_modes?.slice(0, 3).join(", ") || alert;
  return `Investigate ${equipmentName} (${equipmentId}). Active alert: ${alert}. Sensor anomalies: ${breaches}. Known failure modes: ${modes}. Generate asset-specific diagnosis, RUL, business impact, root cause, maintenance action, and spare strategy.`;
}

async function refreshSelectedAssetContext(updateBrief = true) {
  const requestId = ++state.selectionRequestId;
  renderAssetContextSkeleton();
  try {
    const data = await api(`/api/asset-context?equipment_id=${encodeURIComponent(state.selectedEquipmentId)}`);
    if (requestId !== state.selectionRequestId) return;
    if (updateBrief && data.investigation_brief) {
      els.queryInput.value = data.investigation_brief;
    }
    if (data.report) data.report = normalizeReport(data.report);
    renderReport(data.report);
    renderExecutiveDecision(data.executive_decision_summary);
    renderCostImpact(data.failure_cost_impact);
    renderExecutiveDashboardView(data.executive_decision_summary);
    state.workOrder = data.work_order || state.workOrder;
    renderWorkOrder(state.workOrder);
    if (els.aiConfidencePill) {
      const confidence = calculateUiConfidence(data.report);
      els.aiConfidencePill.textContent = `AI Confidence ${confidence}%`;
      els.aiConfidencePill.className = pillClass(confidence >= 84 ? "low" : "medium");
    }
    updateSelectedAssetState(state.selectedEquipmentId, { asset_intelligence: data.asset_intelligence });
    renderIncidentReplay();
    dispatchAssetSelected("asset_context_loaded");
  } catch (error) {
    showToast(error.message);
  }
}

function renderAssetContextSkeleton() {
  const skeleton = `
    <div class="skeleton-card">
      <i></i>
      <strong></strong>
      <span></span>
    </div>
    <div class="skeleton-card">
      <i></i>
      <strong></strong>
      <span></span>
    </div>
  `;
  if (els.costImpact) els.costImpact.innerHTML = skeleton;
  if (els.executiveDecisionSummary) els.executiveDecisionSummary.innerHTML = `<div class="decision-grid">${skeleton}</div>`;
}

function calculateUiConfidence(report) {
  const breaches = report?.diagnosis?.condition_breaches?.length || 0;
  const modes = report?.diagnosis?.asset_failure_modes?.length || 0;
  const trace = report?.traceability?.length || 0;
  return Math.min(96, 66 + breaches * 5 + modes * 3 + trace * 2);
}

function renderAssetIntelligenceWidgets(data = state.selectedAsset?.asset_intelligence || null) {
  const selectedAsset = state.selectedAsset || updateSelectedAssetState();
  const dataAssetId = firstDefined(data?.asset_profile?.asset_id, data?.asset_profile?.equipment_id);
  const selectedAssetId = selectedAsset?.equipment_id;
  const scopedData = dataAssetId && selectedAssetId && dataAssetId !== selectedAssetId ? null : data;
  const intelligence = scopedData || selectedAsset?.asset_intelligence || (selectedAsset ? buildSelectedAssetIntelligence(selectedAsset) : null);
  if (selectedAsset && intelligence && !selectedAsset.asset_intelligence) {
    selectedAsset.asset_intelligence = intelligence;
  }
  if (!selectedAsset) {
    renderSelectedAssetProfile(null);
    renderFailureProbability(null);
    renderMaintenanceCalendar([]);
    renderSpareRecommendations([]);
    renderFailureStageTimeline([]);
    renderAssetRelationshipView(null);
    return;
  }
  renderSelectedAssetProfile(intelligence?.asset_profile);
  renderFailureProbability(intelligence?.failure_probability);
  renderMaintenanceCalendar(intelligence?.maintenance_calendar || []);
  renderSpareRecommendations(intelligence?.spare_recommendations || []);
  renderFailureStageTimeline(intelligence?.failure_timeline || []);
  renderAssetRelationshipView(intelligence?.relationship_view);
}

function renderSelectedAssetProfile(profile) {
  if (!els.selectedAssetProfile) return;
  if (!profile) {
    els.selectedAssetProfile.innerHTML = state.selectedAsset
      ? emptyState(`No profile fields available for ${assetDisplayName(state.selectedAsset)}.`)
      : emptyState("Select an asset to view the digital twin source record.");
    return;
  }
  const rows = [
    ["Asset ID", profile?.asset_id],
    ["Asset Name", profile?.asset_name],
    ["Area", profile?.area],
    ["Sector", profile?.sector],
    ["Manufacturer", profile?.manufacturer],
    ["Commission Date", profile?.commission_date],
    ["Operating Hours", profile?.operating_hours],
    ["Criticality", profile?.criticality],
    ["Current Failure Mode", profile?.current_failure_mode],
    ["Failure Probability", `${safeValue(profile?.failure_probability, 0)}%`],
    ["RUL", `${safeValue(profile?.rul_hours, 0)} h`],
    ["Health Score", `${safeValue(profile?.health_score, 0)}%`],
    ["Last Maintenance", profile?.last_maintenance_date],
    ["Next Planned Maintenance", profile?.next_planned_maintenance],
    ["Asset Icon", profile?.asset_icon],
  ];
  els.selectedAssetProfile.innerHTML = rows.map(([label, value]) => kpiCard(label, value, "Asset-specific source record")).join("");
}

function renderFailureProbability(probability) {
  if (!els.failureProbabilityWidget) return;
  if (!probability) {
    if (els.failureProbabilityPill) {
      els.failureProbabilityPill.textContent = "Probability";
      els.failureProbabilityPill.className = "pill";
    }
    els.failureProbabilityWidget.innerHTML = state.selectedAsset
      ? emptyState(`Failure probability inputs are not available for ${assetDisplayName(state.selectedAsset)}.`)
      : emptyState("Select an asset to calculate failure probability.");
    return;
  }
  const level = probability.level === "high" ? "critical" : probability.level === "medium" ? "medium" : "low";
  if (els.failureProbabilityPill) {
    els.failureProbabilityPill.textContent = `${safeValue(probability.percent, 0)}% ${safeValue(probability.level)}`;
    els.failureProbabilityPill.className = pillClass(level);
  }
  els.failureProbabilityWidget.innerHTML = `
    <div class="probability-gauge ${escapeHtml(level)}" style="--prob:${safeNumber(probability.percent)}">
      <strong>${escapeHtml(safeValue(probability?.percent, 0))}%</strong>
      <span>${escapeHtml(safeValue(probability?.level))} probability</span>
    </div>
    <div class="probability-drivers">
      ${Object.entries(probability?.drivers || {}).map(([key, value]) => `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
      ${kpiCard("Confidence", `${safeValue(probability?.confidence, 0)}%`, "Source-data confidence")}
    </div>
  `;
}

function renderMaintenanceCalendar(rows) {
  if (!els.maintenanceCalendar) return;
  if (!rows?.length) {
    els.maintenanceCalendar.innerHTML = emptyState(state.selectedAsset
      ? `No maintenance calendar records for ${assetDisplayName(state.selectedAsset)}.`
      : "Select an asset to view the maintenance calendar.");
    return;
  }
  els.maintenanceCalendar.innerHTML = rows.map((row) => `
    <div class="calendar-window">
      <strong>${escapeHtml(row.window)}</strong>
      <ul>${(row.items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `).join("");
}

function renderSpareRecommendations(rows) {
  if (!els.spareRecommendations) return;
  const items = rows || [];
  els.spareRecommendations.innerHTML = items.length ? items.map((row) => `
    <div class="spare-rec">
      <strong>${escapeHtml(row?.part)}</strong>
      <p>Qty ${escapeHtml(row?.quantity)} / Stock ${escapeHtml(row?.stock)} / Lead ${escapeHtml(row?.lead_time_days)} days</p>
      <span>${escapeHtml(row?.availability)} / Risk if unavailable: ${escapeHtml(row?.risk_if_unavailable)}</span>
    </div>
  `).join("") : emptyState(state.selectedAsset
    ? `No spare recommendation records for ${assetDisplayName(state.selectedAsset)}.`
    : "Select an asset to view spare recommendations.");
}

function renderFailureStageTimeline(rows) {
  if (!els.failureStageTimeline) return;
  if (!rows?.length) {
    els.failureStageTimeline.innerHTML = emptyState(state.selectedAsset
      ? `No failure progression timeline is available for ${assetDisplayName(state.selectedAsset)}.`
      : "Select an asset to view failure progression.");
    return;
  }
  els.failureStageTimeline.innerHTML = rows.map((row) => `
    <div class="failure-stage ${row.active ? "active" : ""}">
      <span></span>
      <strong>${escapeHtml(row?.stage)}</strong>
    </div>
  `).join("");
}

function renderAssetRelationshipView(view) {
  if (!els.assetRelationshipView) return;
  const sourceView = view || buildAssetRelationshipView(state.selectedAsset);
  const relationships = sourceView?.relationships
    || sourceView?.nodes
    || (sourceView?.children ? [{ name: sourceView.root || assetDisplayName(state.selectedAsset), dependency_type: "Selected Asset" }, ...sourceView.children] : []);
  console.log("selectedAsset.relationships", state.selectedAsset?.relationships || relationships);
  if (!sourceView || !relationships.length) {
    els.assetRelationshipView.innerHTML = emptyState(state.selectedAsset
      ? `No asset relationship view is available for ${assetDisplayName(state.selectedAsset)}.`
      : "Select an asset to view asset relationships.");
    return;
  }
  const nodes = relationships.map((item, index) => normalizeRelationshipNode(item, index, state.selectedAsset));
  const edges = sourceView.edges || nodes.slice(0, -1).map((node, index) => ({
    source: node.id,
    target: nodes[index + 1].id,
    relationship: nodes[index + 1].dependency_type,
  }));
  els.assetRelationshipView.innerHTML = `
    <div class="relationship-root">${escapeHtml(sourceView.root || assetDisplayName(state.selectedAsset))}</div>
    <div class="network-canvas relationship-graph">
      ${nodes.map((node, index) => {
        const x = nodes.length === 1 ? 50 : 12 + (index / Math.max(1, nodes.length - 1)) * 76;
        const y = index % 2 === 0 ? 42 : 60;
        return `
          <button class="network-node relationship-node ${node.isSelected ? "active" : ""}" type="button"
            data-asset="${escapeHtml(node.id)}"
            style="left:${x}%;top:${y}%;--risk:${riskColor(node.risk)}">
            <strong>${escapeHtml(node.name)}</strong>
            <b>Health ${escapeHtml(percentLabel(node.health))}</b>
            <span>${escapeHtml(String(node.risk).toUpperCase())}</span>
            <small>${escapeHtml(node.dependency_type)}</small>
          </button>
        `;
      }).join("")}
    </div>
    <div class="dependency-list">
      ${edges.length ? edges.map((edge) => {
        const source = nodes.find((node) => node.id === edge.source);
        const target = nodes.find((node) => node.id === edge.target);
        return `<div class="trace-item"><strong>${escapeHtml(source?.name || edge.source)} -> ${escapeHtml(target?.name || edge.target)}</strong><p>${escapeHtml(edge.relationship || target?.dependency_type || "Dependency")}</p></div>`;
      }).join("") : emptyState("Relationship graph has one node and no linked dependency edges.")}
    </div>
  `;
  els.assetRelationshipView.querySelectorAll(".network-node").forEach((button) => {
    button.addEventListener("click", () => {
      const assetId = button.dataset.asset;
      if (state.equipment.some((item) => item.equipment_id === assetId)) {
        selectEquipment(assetId, false);
      }
    });
  });
}

function renderEquipment() {
  const filtered = state.assetFilterArea
    ? state.equipment.filter((item) => {
        const master = state.assetMaster.find((asset) => asset.id === item.equipment_id);
        return master?.area === state.assetFilterArea;
      })
    : state.equipment;
  els.equipmentList.innerHTML = filtered
    .map((item) => {
      const active = item.equipment_id === state.selectedEquipmentId ? "active" : "";
      const equipmentId = assetDisplayId(item);
      const equipmentName = assetDisplayName(item);
      const alert = assetDisplayAlert(item);
      const risk = normalizeRiskLabel(firstDefined(item.risk_level, item.risk?.level, item.risk, classifyRisk(firstDefined(item.risk_score, item.risk?.score), "low")));
      return `
        <button class="equipment-button ${active} equipment-risk-${escapeHtml(risk)}" type="button" data-equipment="${escapeHtml(equipmentId)}">
          <strong><span class="equipment-risk-dot"></span>${escapeHtml(equipmentId)}</strong>
          <span>${escapeHtml(equipmentName)}</span>
          <span class="equipment-meta"><em>${escapeHtml(riskDisplay(risk))}</em>${escapeHtml(alert)}</span>
        </button>
      `;
    })
    .join("");

  els.equipmentList.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => selectEquipment(button.dataset.equipment));
  });

  els.equipmentSelect.innerHTML = [
    `<option value="">Select Asset</option>`,
    ...state.equipment
      .map((item) => `<option value="${escapeHtml(assetDisplayId(item))}">${escapeHtml(assetDisplayId(item))} - ${escapeHtml(assetDisplayName(item))}</option>`),
  ]
    .join("");
  els.equipmentSelect.value = state.selectedEquipmentId;
}

function renderStatus(alerts) {
  const critical = alerts.filter((item) => item.risk_level === "critical").length;
  const high = alerts.filter((item) => item.risk_level === "high").length;
  const roles = state.roleNotifications.length;
  const label = aiStatusLabel(state.systemReady);
  const progress = state.systemReady ? 100 : Number(state.preloadStatus?.ready_progress_percent || 0);
  const backendOnline = Boolean(state.backendAvailable);
  const vectorReady = Boolean(state.systemReady || state.preloadStatus?.vector_store_loaded);
  const workflowReady = Boolean(state.systemReady || state.preloadStatus?.workflow_loaded);
  const modelsReady = Boolean(state.aiModelReady);
  const retrievalMode = activeRetrievalMode(state.modelHealth || state.preloadStatus || {});
  const fallback = modelFallbackActive(state.modelHealth || state.preloadStatus || {});
  const disabled = semanticRetrievalDisabled(state.modelHealth || state.preloadStatus || {});
  const documentCount = firstDefined(
    state.preloadStatus?.vector_store?.document_count,
    state.preloadStatus?.document_count,
    state.preloadStatus?.vector_count,
    657
  );
  els.statusStrip.innerHTML = `
    <span class="pill critical">${critical} Critical</span>
    <span class="pill high">${high} High</span>
    <span class="pill">${roles} Role Alerts</span>
    <span class="live-status ${state.systemReady ? "online" : "loading"}"><i></i>${escapeHtml(state.systemReady ? "AI READY" : label.toUpperCase())}</span>
    <span class="live-status ${vectorReady ? "online" : "loading"}"><i></i>${vectorReady ? "KNOWLEDGE BASE CONNECTED" : "KNOWLEDGE BASE LOADING"}</span>
    <span class="live-status ${modelsReady ? "online" : "loading"}"><i></i>${modelsReady ? "PREDICTIVE MODELS ACTIVE" : "PREDICTIVE MODELS LOADING"}</span>
    <span class="live-status ${disabled || fallback ? "warning" : modelsReady ? "online" : "loading"}"><i></i>${escapeHtml(retrievalMode.toUpperCase())}</span>
    <span class="live-status ${backendOnline ? "online" : "loading"}"><i></i>${backendOnline ? "REAL-TIME MONITORING ONLINE" : "REAL-TIME MONITORING PENDING"}</span>
    <span class="live-status indexed ${vectorReady ? "online" : "loading"}"><i></i>${escapeHtml(documentCount)} Documents Indexed</span>
    <span class="preload-progress"><i style="width:${Math.max(4, Math.min(100, progress))}%"></i></span>
  `;
}

async function renderPerformanceHealth() {
  if (!els.performanceHealth) return;
  try {
    const [performanceResult, startupResult, systemResult, modelResult] = await Promise.allSettled([
      apiWithTimeout("/api/performance-health", {}, 15000),
      apiWithTimeout("/api/startup-health", {}, 15000),
      apiWithTimeout("/api/system-health", {}, 15000),
      apiWithTimeout("/api/model-health", {}, 15000),
    ]);
    if (performanceResult.status !== "fulfilled") throw performanceResult.reason;
    if (startupResult.status !== "fulfilled") console.warn("STARTUP_HEALTH_REQUEST_FAILED", startupResult.reason?.message || startupResult.reason);
    if (systemResult.status !== "fulfilled") console.warn("SYSTEM_HEALTH_REQUEST_FAILED", systemResult.reason?.message || systemResult.reason);
    const data = performanceResult.value;
    const startup = startupResult.status === "fulfilled" ? startupResult.value : {};
    const system = systemResult.status === "fulfilled" ? systemResult.value : {};
    const modelHealth = modelResult.status === "fulfilled" ? modelResult.value : {};
    if (modelResult.status === "fulfilled") {
      state.modelHealth = modelHealth;
      renderModelWarningBanner(modelHealth);
      renderModelDiagnostics(modelHealth);
    }
    const items = [
      ["Startup", formatMs(msValue(data, "startup_ms", "startup_time_ms") ?? msValue(startup, "startup_time_ms", "startup_ms")), "Process uptime and startup diagnostic"],
      ["Retrieval", formatMs(msValue(data, "retrieval_ms", "retrieval_time")), activeRetrievalMode(modelHealth || data)],
      ["Rerank", formatMs(msValue(data, "rerank_ms", "rerank_time", "reranking_time_ms")), "Cross-encoder/lexical rerank"],
      ["LLM", formatMs(msValue(data, "llm_ms", "llm_time", "latency_ms")), "Groq or fallback response"],
      ["Workflow", formatMs(msValue(data, "workflow_ms", "workflow_time")), data.workflow_engine || "workflow"],
      ["Total", formatMs(msValue(data, "total_request_ms", "total_response_time", "total_time")), "Latest request"],
      ["System Ready", firstDefined(data.system_ready, startup.system_ready) ? "Yes" : "No", `Preload ${firstDefined(data.ready_progress_percent, startup.background_status?.ready_progress_percent, 0)}%`],
      ["Cache Hit Rate", `${Math.round(Number(data.cache_hit_rate || 0) * 100)}%`, "Investigation cache"],
      ["Tokens", Number(firstDefined(data.total_tokens, data.token_count, 0)), `Vectors ${firstDefined(system.vector_count, system.vectors, "-")}`],
    ];
    els.performanceHealth.innerHTML = items.map(([label, value, help]) => kpiCard(label, value, help)).join("");
  } catch (error) {
    els.performanceHealth.innerHTML = `<div class="empty-state compact">Backend Offline</div>`;
  }
}

function renderModelDiagnostics(modelHealth = state.modelHealth || {}) {
  if (!els.modelDiagnostics) return;
  const fallback = modelFallbackActive(modelHealth);
  const disabled = semanticRetrievalDisabled(modelHealth);
  const cards = [
    ["Embedding Model Status", modelHealth.embedding_real_model_loaded ? "Loaded" : modelHealth.embedding_loaded ? "Fallback" : "Not Loaded", modelHealth.embedding_fallback_reason || "all-MiniLM-L6-v2"],
    ["Reranker Status", modelHealth.reranker_real_model_loaded ? "Loaded" : modelHealth.reranker_loaded ? "Fallback" : "Not Loaded", modelHealth.reranker_fallback_reason || "cross-encoder/ms-marco-MiniLM-L-6-v2"],
    ["Cache Location", modelHealth.cache_directory || modelHealth.model_cache_directory || "—", modelHealth.model_mode || "offline"],
    ["Fallback Active", fallback ? "Yes" : "No", disabled ? "Semantic AI retrieval disabled" : "Semantic AI retrieval active"],
    ["Active Retrieval Mode", activeRetrievalMode(modelHealth), "Semantic / Hybrid / Lexical"],
  ];
  els.modelDiagnostics.innerHTML = `
    <div class="panel-heading compact-heading">
      <div>
        <h3>Startup Diagnostics</h3>
        <p>AI model readiness, cache validation, and active retrieval mode.</p>
      </div>
      <span class="pill ${disabled || fallback ? "high" : "low"}">${disabled ? "Semantic Disabled" : fallback ? "Fallback Active" : "Semantic Active"}</span>
    </div>
    <div class="kpi-grid">
      ${cards.map(([label, value, help]) => kpiCard(label, safe(value), safe(help))).join("")}
    </div>
  `;
}

function renderAgentic(agentic = state.agentic) {
  if (!agentic) {
    renderAgentMetrics(state.agentMetrics);
    els.agentExecution.innerHTML = `<div class="empty-state compact">Run an investigation to generate the maintenance timeline.</div>`;
    els.reasoningTrace.innerHTML = `<div class="empty-state compact">Evidence and reasoning will appear after investigation.</div>`;
    return;
  }
  state.agentic = agentic;
  els.executiveAiSummary.textContent = agentic.executive_ai_summary;
  els.llmProvider.textContent = "Maintenance Wizard Intelligence Engine";
  els.aiConfidencePill.textContent = `AI Confidence ${agentic.ai_confidence.score}%`;
  els.aiConfidencePill.className = pillClass(agentic.ai_confidence.score >= 85 ? "low" : "medium");
  renderAgentMetrics(agentic.agent_metrics);
  renderAgentExecution(agentic.agent_execution);
  renderReasoningTrace(agentic.reasoning_trace);
}

function renderAgentMetrics(metrics = state.agentMetrics) {
  if (!metrics) return;
  state.agentMetrics = metrics;
  if (!els.agentMetrics) return;
  const cards = [
    ["Workflow Success Rate", `${metrics.agent_success_rate}%`],
    ["Diagnosis Confidence", `${metrics.average_diagnosis_confidence}%`],
    ["Knowledge Match Accuracy", `${metrics.knowledge_retrieval_accuracy}%`],
    ["Work Orders Generated", metrics.work_orders_generated],
    ["Historical Match Rate", `${metrics.historical_match_rate}%`],
  ];
  els.agentMetrics.innerHTML = cards
    .map(([label, value]) => `
      <div class="agent-metric-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
      </div>
    `)
    .join("");
}

function renderEnterprise(data = state.enterprise) {
  if (!data) return;
  state.enterprise = data;
  if (!state.selectedEquipmentId) {
    state.incidentReplay = data.incident_replay || state.incidentReplay;
  }
  renderExecutiveDecision(data.executive_decision_summary);
  renderCostImpact(data.failure_cost_impact);
  renderIncidentReplay(data.incident_replay);
  renderShiftHandover(data.shift_handover);
  renderProcurement(data.procurement_recommendations);
  renderReliabilityAssessment(data.maintenance_kpis);
  renderExecutiveDashboardView(data.executive_decision_summary);
  renderExecutiveReportPreview(data);
  renderCopilotPrompts();
  renderOperationsCenter();
  renderPipeline();
}

function renderExecutiveDecision(data) {
  if (!els.executiveDecisionSummary) return;
  if (!data) {
    els.executiveDecisionSummary.innerHTML = emptyState("Run an investigation to generate the executive decision summary.");
    return;
  }
  const approvals = Array.isArray(data.required_approvals) ? data.required_approvals : [];
  els.executiveDecisionSummary.innerHTML = `
    <div class="decision-grid">
      ${kpiCard("Top Plant Risk", data?.current_top_plant_risk, data?.asset)}
      ${kpiCard("Production Impact", data?.expected_production_impact, "Expected operational exposure")}
      ${kpiCard("Maintenance Strategy", data?.recommended_maintenance_strategy, "Recommended decision")}
      ${kpiCard("Downtime Avoided", data?.estimated_downtime_avoided, "Avoided if action is approved")}
      ${kpiCard("Cost Avoided", money(data?.estimated_cost_avoided_inr), "Estimated avoided loss")}
      ${kpiCard("Required Approvals", approvals.join(", ") || "Not Available", "Decision owners")}
    </div>
  `;
  renderRoiDecisionCard(els.executiveDecisionSummary, data?.failure_cost_impact || state.enterprise?.failure_cost_impact);
}

function kpiCard(label, value, help = "") {
  value = safeValue(value);
  help = safeValue(help);
  const labelSlug = String(label || "metric").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "metric";
  const riskValue = ["critical", "high", "medium", "low"].includes(String(value).toLowerCase())
    ? ` risk-${String(value).toLowerCase()}`
    : "";
  const seed = trendSeed(label, value);
  const delta = seed % 2 === 0 ? `+${(seed % 9) + 1}%` : `-${(seed % 7) + 1}%`;
  const deltaClass = delta.startsWith("+") ? "positive" : "negative";
  const count = countAnimationMeta(value);
  const countAttrs = count
    ? ` data-count-target="${escapeHtml(count.target)}" data-count-prefix="${escapeHtml(count.prefix)}" data-count-suffix="${escapeHtml(count.suffix)}" data-count-decimals="${escapeHtml(count.decimals)}" data-count-final="${escapeHtml(value)}"`
    : "";
  const bars = [0, 1, 2, 3, 4].map((index) => {
    const height = 22 + ((seed + index * 17) % 54);
    return `<i style="height:${height}%"></i>`;
  }).join("");
  return `
    <div class="kpi-card kpi-card-${escapeHtml(labelSlug)}${escapeHtml(riskValue)}">
      <span>${escapeHtml(label)}</span>
      <strong${countAttrs}>${escapeHtml(value)}</strong>
      <div class="kpi-micro-row">
        <em class="${deltaClass}">${escapeHtml(delta)}</em>
        <div class="kpi-sparkline" aria-hidden="true">${bars}</div>
      </div>
      <small>${escapeHtml(help)}</small>
    </div>
  `;
}

function trendSeed(label, value) {
  return String(`${safeValue(label)}:${safeValue(value)}`)
    .split("")
    .reduce((total, char) => total + char.charCodeAt(0), 0);
}

function countAnimationMeta(value) {
  const text = String(safeValue(value, ""));
  const match = text.match(/-?[\d,]+(?:\.\d+)?/);
  if (!match) return null;
  const target = Number(match[0].replaceAll(",", ""));
  if (!Number.isFinite(target)) return null;
  const decimals = match[0].includes(".") ? match[0].split(".").pop().length : 0;
  return {
    target,
    decimals: Math.min(decimals, 2),
    prefix: text.slice(0, match.index),
    suffix: text.slice((match.index || 0) + match[0].length),
  };
}

function renderManagementDashboard(data) {
  els.managementDashboard.innerHTML = [
    kpiCard("Plant Health Score", `${data.plant_health_score}%`, "Management readiness indicator"),
    kpiCard("Critical Assets", data.critical_assets, "Assets needing immediate decision"),
    kpiCard("Predicted Failures", data.predicted_failures, "Next risk window"),
    kpiCard("Risk Exposure", money(data.risk_exposure_inr), "Production and repair exposure"),
    kpiCard("Downtime Exposure", `${data.downtime_exposure_hours} h`, "Expected production exposure"),
    kpiCard("Readiness", `${data.maintenance_readiness_percent || data.plant_health_score}%`, "Maintenance execution readiness"),
    kpiCard("Spare Risks", data.spare_risks || "-", "Inventory blockers"),
    kpiCard("Monthly Cost Impact", money(data.monthly_cost_impact_inr), `Top bottleneck ${data.top_bottleneck || "-"}`),
  ].join("");
  if (data.executive_summary) {
    els.managementDashboard.insertAdjacentHTML("beforeend", `<div class="executive-note">${escapeHtml(data.executive_summary)}</div>`);
  }
}

function renderShiftHandover(data) {
  if (!data || !els.shiftHandover) return;
  const shortages = data.spare_shortages.slice(0, 4).map((item) => `${item.part} (${item.lead_time_days}d)`).join(", ");
  const jobList = (items) => items.map((item) => `<li>${escapeHtml(item.job)} - ${escapeHtml(item.owner)} - ${escapeHtml(item.status)}</li>`).join("");
  els.shiftHandover.innerHTML = `
    <div class="handover-summary">${escapeHtml(data.summary)}</div>
    <div class="handover-grid">
      ${kpiCard("Shift", data.shift, "Handover period")}
      ${kpiCard("Open Critical Alerts", data.open_critical_alerts.length, "Requires next-shift watch")}
      ${kpiCard("Spare Shortages", data.spare_shortages.length, shortages || "No blocker")}
    </div>
    <h4>Completed Jobs</h4>
    <ul>${jobList(data.completed_jobs || [])}</ul>
    <h4>Pending Jobs</h4>
    <ul>${jobList(data.pending_jobs || [])}</ul>
    <h4>Safety Notes</h4>
    <ul>${data.safety_observations.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <h4>Next Shift Recommendations</h4>
    <ul>${(data.next_shift_recommendations || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <h4>AI Generated Handover Summary</h4>
    <p>${escapeHtml(data.summary)}</p>
  `;
}

function renderSelectedAssetExecutiveDashboardView(data) {
  if (!els.executiveDashboardView) return;
  const selectedContext = activeAssetContext();
  const selectedAssetId = selectedContext.asset_id;
  const hasSelectedAsset = selectedAssetId && selectedAssetId !== DISPLAY_EMPTY && selectedContext.asset_name !== "No asset selected";
  const lifecycleState = investigationStatusForSelectedAsset();
  const riskLevel = selectedRiskLevel();
  const riskScore = selectedRiskScore();
  const selectedImpact = selectedAssetFinancialImpact();
  const selectedRoi = roiInputFromCostImpact(selectedImpact);
  const effectiveData = data || {
    current_top_plant_risk: hasSelectedAsset ? selectedContext.asset_name : "No asset selected",
    asset: selectedAssetId,
    expected_production_impact: hasSelectedAsset ? `${riskDisplay(riskLevel)} risk exposure` : "Select asset to calculate exposure",
    recommended_maintenance_strategy: hasSelectedAsset ? selectedExecutiveRecommendation({}, lifecycleState) : "Select asset for decision",
    estimated_downtime_avoided: safe(state.report?.prediction?.rul_label, DISPLAY_EMPTY),
    estimated_cost_avoided_inr: selectedRoi.savings,
    required_approvals: ["Maintenance Lead", "Production Supervisor"],
  };
  effectiveData.recommended_maintenance_strategy = selectedExecutiveRecommendation(effectiveData, lifecycleState);
  effectiveData.expected_production_impact = hasSelectedAsset
    ? `${riskDisplay(riskLevel)} risk with ${safe(state.report?.priority?.urgency, lifecycleState === INVESTIGATION_STATES.COMPLETED ? "active" : "pending investigation")} urgency`
    : effectiveData.expected_production_impact;
  const approvals = Array.isArray(effectiveData.required_approvals) ? effectiveData.required_approvals : [];
  const assetsMonitored = (state.assetMaster?.length || state.equipment?.length || 0);
  const criticalAssets = (state.assetMaster || state.equipment || []).filter((asset) => normalizeRiskLabel(firstDefined(asset.risk_level, asset.risk?.level, asset.risk, classifyRisk(firstDefined(asset.risk_score, asset.risk?.score), "low"))) === "critical").length;
  const financialExposure = firstDefined(selectedImpact.business_exposure_inr, selectedImpact.total_risk_exposure_inr, selectedImpact.total_business_impact_inr, selectedImpact.production_loss_inr, 0);
  const recommendedActions = uniqueNonEmpty([effectiveData.recommended_maintenance_strategy, ...(selectedReport()?.recommendations || [])])
    .filter((item) => lifecycleState === INVESTIGATION_STATES.NOT_STARTED || !isGenericInvestigationAction(item));
  const enterpriseDecision = state.enterprise?.executive_decision_summary || {};
  const enterpriseImpact = state.enterprise?.failure_cost_impact || {};
  const plantTopAssetId = firstDefined(enterpriseDecision.asset, enterpriseImpact.equipment_id, enterpriseImpact.asset_id);
  const plantTopAsset = plantTopAssetId ? selectedAssetData(plantTopAssetId) : null;
  const plantTopName = plantTopAsset ? assetDisplayName(plantTopAsset) : safe(enterpriseDecision.current_top_plant_risk, "Plant risk leader");
  const selectedDataSummary = payloadMatchesSelectedAsset(effectiveData) ? effectiveData.ai_executive_summary : "";
  const executiveSummary = state.agentic?.executive_ai_summary
    || selectedDataSummary
    || (hasSelectedAsset
      ? `${safe(selectedContext.asset_name)} requires ${safe(effectiveData.recommended_maintenance_strategy, "maintenance decision")} based on selected-asset risk, health, and business exposure.`
      : "Select an asset in Command Center, then run investigation to generate the executive decision.");

  els.executiveDashboardView.innerHTML = `
    <section class="executive-decision-center">
      <div class="executive-decision-title">
        <span>Executive Decision Center - Selected Asset</span>
        <strong>${escapeHtml(hasSelectedAsset ? selectedContext.asset_name : "No asset selected")}</strong>
        <div class="executive-asset-meta">
          <b class="asset-status-chip ${riskClass(riskLevel)}">${escapeHtml(riskDisplay(riskLevel))}</b>
          <b>Score ${escapeHtml(safe(riskScore))}</b>
          <b>Health ${escapeHtml(percentLabel(selectedContext.health_score))}</b>
          <b>RUL ${escapeHtml(selectedContext.rul_days)}</b>
        </div>
        <p>${escapeHtml(executiveSummary)}</p>
      </div>
      <div class="executive-impact-grid">
        ${kpiCard("Assets Monitored", assetsMonitored, "Connected asset master records")}
        ${kpiCard("Critical Assets", criticalAssets, "Assets requiring immediate attention")}
        ${kpiCard("Selected Asset Exposure", money(financialExposure), "Current selected-asset business exposure")}
        ${kpiCard("Recommended Actions", recommendedActions.length, safe(recommendedActions[0], "No action selected"))}
      </div>
      <div class="top-risk-asset-card ${normalizeRiskLabel(riskLevel) === "critical" ? "critical-glow" : ""}">
        <span>SELECTED ASSET DECISION</span>
        <strong>${escapeHtml(hasSelectedAsset ? selectedContext.asset_name : "Select asset in Command Center")}</strong>
        <p>${escapeHtml(selectedContext.asset_id)} / ${escapeHtml(selectedContext.current_alert)} / Health ${escapeHtml(percentLabel(selectedContext.health_score))}</p>
        <div class="top-risk-detail-grid">
          ${kpiCard("Risk Score", safe(riskScore), "Current selected-asset score")}
          ${kpiCard("Potential Loss", money(selectedRoi.potentialFailureCost), "Selected asset failure progression exposure")}
          ${kpiCard("Expected Savings", money(selectedRoi.savings), "Failure cost minus shutdown cost")}
          ${kpiCard("Recommended Action", safe(recommendedActions[0]), "AI maintenance decision")}
        </div>
        <b class="asset-status-chip ${riskClass(riskLevel)}">${escapeHtml(riskDisplay(riskLevel))}</b>
      </div>
    </section>
    <div class="decision-grid executive-hierarchy-grid">
      ${kpiCard("Selected Asset", selectedContext.asset_name, selectedContext.asset_id)}
      ${kpiCard("Production Impact", effectiveData.expected_production_impact, "Expected exposure")}
      ${kpiCard("Strategy", effectiveData.recommended_maintenance_strategy, "Recommended action")}
      ${kpiCard("Downtime Avoided", effectiveData.estimated_downtime_avoided, "If approved")}
      ${kpiCard("Cost Avoided", money(effectiveData.estimated_cost_avoided_inr), "Estimated")}
      ${kpiCard("Approvals", approvals.join(", ") || "Not Available", "Required")}
    </div>
    <section class="enterprise-risk-summary">
      <div class="panel-heading compact-heading">
        <h3>Enterprise Risk Summary</h3>
        <span class="pill">Plant-Wide Context</span>
      </div>
      <div class="decision-grid executive-hierarchy-grid">
        ${kpiCard("Top Enterprise Risk", plantTopName, safe(enterpriseDecision.asset, plantTopAssetId || "Portfolio"))}
        ${kpiCard("Plant Exposure", money(firstDefined(enterpriseImpact.total_risk_exposure_inr, enterpriseImpact.total_business_impact_inr, enterpriseImpact.production_loss_inr, 0)), "Enterprise-level risk")}
        ${kpiCard("Enterprise Strategy", safe(enterpriseDecision.recommended_maintenance_strategy, "Review plant risk ranking"), "Portfolio action")}
      </div>
    </section>
  `;
  renderRoiDecisionCard(els.executiveDashboardView, selectedImpact);
}

function renderExecutiveDashboardView(data) {
  renderSelectedAssetExecutiveDashboardView(data);
}

function renderOperationsCenter(data = state.operationsCenter) {
  if (!els.operationsCenterKpis) return;
  if (!data) {
    els.operationsCenterKpis.innerHTML = emptyState("Executive operations KPIs are loading.");
    return;
  }
  state.operationsCenter = data;
  els.operationsCenterKpis.innerHTML = (data.kpis || [])
    .map((item) => kpiCard(item.label, formatKpiValue(item), item.help))
    .join("");
  els.operationsCenterKpis.insertAdjacentHTML("beforeend", `
    <div class="ops-drilldown">
      <strong>Plant-to-Asset Drill Down</strong>
      <div>
        ${(data.top_risks || []).length ? (data.top_risks || []).slice(0, 6).map((asset) => `
          <button type="button" data-asset="${escapeHtml(asset.id)}">
            <span class="${pillClass(asset.risk_level)}">${escapeHtml(asset.risk_level)}</span>
            <b>${escapeHtml(asset.name)}</b>
            <small>${escapeHtml(asset.area)} / health ${escapeHtml(asset.health_score)}%</small>
          </button>
        `).join("") : emptyState("No active top-risk drill-down records.")}
      </div>
    </div>
  `);
  els.operationsCenterKpis.querySelectorAll(".ops-drilldown button").forEach((button) => {
    button.addEventListener("click", () => {
      selectEquipment(button.dataset.asset, false);
      switchModule("asset-intelligence");
    });
  });
}

function renderPipeline(data = state.aiPipeline) {
  if (!els.aiPipeline) return;
  if (!data || !(data.stages || []).length) {
    if (els.pipelineTotal) els.pipelineTotal.textContent = "Awaiting Run";
    els.aiPipeline.innerHTML = emptyState("Run an investigation to view AI pipeline execution.");
    return;
  }
  state.aiPipeline = data;
  const totalSeconds = ((data.total_processing_ms || 0) / 1000).toFixed(2);
  if (els.pipelineTotal) els.pipelineTotal.textContent = `Total ${totalSeconds} sec`;
  els.aiPipeline.innerHTML = (data.stages || [])
    .map((stage) => `
      <div class="pipeline-step">
        <div>
          <strong>${escapeHtml(stage.name)}</strong>
          <span>${escapeHtml(stage.status)}</span>
        </div>
        <b>${escapeHtml(stage.latency_ms)} ms</b>
        <small>${escapeHtml(String(stage.completed_at || "").split("T").pop())}</small>
      </div>
    `)
    .join("");
}

function animateNumber(element, value) {
  const meta = countAnimationMeta(value);
  const numeric = Number(meta?.target ?? value);
  if (!Number.isFinite(numeric)) {
    element.textContent = value;
    return;
  }
  const start = 0;
  const duration = 850;
  const started = performance.now();
  const prefix = meta?.prefix || "";
  const suffix = meta?.suffix || "";
  const decimals = Number(meta?.decimals || 0);
  function frame(now) {
    const progress = Math.min(1, (now - started) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + (numeric - start) * eased;
    element.textContent = `${prefix}${current.toLocaleString("en-IN", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(frame);
    } else if (element.dataset.countFinal) {
      element.textContent = element.dataset.countFinal;
    }
  }
  requestAnimationFrame(frame);
}

function animateKpiCounters(root = document) {
  const nodes = root.querySelectorAll("[data-count-target]:not([data-count-animated]), [data-counter]:not([data-count-animated])");
  nodes.forEach((node) => {
    node.dataset.countAnimated = "true";
    animateNumber(node, node.dataset.countFinal || node.dataset.counter || node.dataset.countTarget);
  });
}

function sanitizeInvalidDisplayText(root = document.body) {
  if (!root) return;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const invalidPattern = /\b(undefined|null|NaN)\b/g;
  const replacements = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (invalidPattern.test(node.nodeValue || "")) {
      replacements.push(node);
    }
    invalidPattern.lastIndex = 0;
  }
  replacements.forEach((node) => {
    node.nodeValue = String(node.nodeValue || "").replace(invalidPattern, "—");
  });
}

function emptyState(message = "No data available.") {
  return `
    <div class="empty-state compact enterprise-empty-state">
      <span></span>
      <strong>Awaiting Context</strong>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function hasRenderableContent(element) {
  if (!element) return false;
  const text = String(element.textContent || "").trim();
  return Boolean(text || element.querySelector("svg, canvas, button, input, textarea, select, .kpi-card, .command-kpi-card, .financial-impact-card"));
}

function renderEmptyIfNeeded(element, message) {
  if (!element) return;
  if (!hasRenderableContent(element)) {
    element.innerHTML = emptyState(message);
  }
}

function auditDashboardCards(root = document.body) {
  if (!root) return;
  sanitizeInvalidDisplayText(root);
  root.querySelectorAll(".kpi-card, .command-kpi-card, .financial-impact-card, .metric-tile, .telemetry-card, .curve-card").forEach((card) => {
    card.classList.add("safe-card");
  });
  const panels = new Set([...root.querySelectorAll(".panel")]);
  if (root.matches?.(".panel")) panels.add(root);
  const closestPanel = root.closest?.(".panel");
  if (closestPanel) panels.add(closestPanel);
  panels.forEach((panel) => {
    const content = Array.from(panel.children).filter((child) => !child.classList.contains("panel-heading"));
    const hasContent = content.some(hasRenderableContent);
    panel.classList.toggle("is-empty-panel", !hasContent);
  });
}

function renderDashboardPlaceholders() {
  renderEmptyIfNeeded(els.executiveSummary, "Executive KPI data will appear after dashboard data loads.");
  renderEmptyIfNeeded(els.costImpact, "Run an investigation to generate Business Impact Analysis.");
  renderEmptyIfNeeded(els.plantCommandKpis, "Plant command KPIs are loading.");
  renderEmptyIfNeeded(els.plantHealthOverview, "Plant health overview is loading.");
  renderEmptyIfNeeded(els.sectorHeatmap, "Sector heatmap data is loading.");
  renderEmptyIfNeeded(els.criticalAssetList, "No critical assets currently require attention.");
  renderEmptyIfNeeded(els.maintenanceFeed, "No recent maintenance log entries available.");
  renderEmptyIfNeeded(els.predictiveTimeline, "No predictive maintenance timeline available.");
  renderEmptyIfNeeded(els.aiPipeline, "Run an investigation to view AI pipeline execution.");
  renderEmptyIfNeeded(els.liveTelemetry, "Select an asset to start real-time sensor streaming.");
  renderEmptyIfNeeded(els.selectedAssetProfile, "Select an asset to view the asset profile.");
  renderEmptyIfNeeded(els.failureProbabilityWidget, "Select an asset to view failure probability.");
  renderEmptyIfNeeded(els.maintenanceCalendar, "Select an asset to view the maintenance calendar.");
  renderEmptyIfNeeded(els.spareRecommendations, "Select an asset to view spare part recommendations.");
  renderEmptyIfNeeded(els.failureStageTimeline, "Select an asset to view failure progression.");
  renderEmptyIfNeeded(els.assetRelationshipView, "Select an asset to view asset relationships.");
  auditDashboardCards();
}

function renderPlantCommandCenter(data = state.plantCommandCenter) {
  if (!data) {
    renderEmptyIfNeeded(els.plantCommandKpis, "Plant command KPIs are loading.");
    renderEmptyIfNeeded(els.plantHealthOverview, "Plant health overview is loading.");
    renderEmptyIfNeeded(els.sectorHeatmap, "Sector heatmap data is loading.");
    renderEmptyIfNeeded(els.criticalAssetList, "Critical asset list is loading.");
    renderEmptyIfNeeded(els.maintenanceFeed, "Recent maintenance logs are loading.");
    renderEmptyIfNeeded(els.predictiveTimeline, "Predictive timeline is loading.");
    return;
  }
  state.plantCommandCenter = data;
  if (els.plantCommandKpis) {
    const summary = assetStatusSummary();
    const assetCards = [
      ["Total Assets", summary.total],
      ["Healthy Assets", summary.healthy],
      ["Warning Assets", summary.warning],
      ["Critical Assets", summary.critical],
    ];
    els.plantCommandKpis.innerHTML = `
      ${assetCards.map(([label, value]) => `
        <div class="command-kpi-card asset-summary-card ${label.includes("Critical") ? "critical-summary" : ""}">
          <span>${escapeHtml(label)}</span>
          <strong data-counter="${escapeHtml(value)}">0</strong>
        </div>
      `).join("")}
      ${(data.kpis || []).map((item) => `
        <div class="command-kpi-card">
          <span>${escapeHtml(item.label)}</span>
          <strong data-counter="${escapeHtml(item.value)}">0</strong>
        </div>
      `).join("")}
    `;
    els.plantCommandKpis.querySelectorAll("[data-counter]").forEach((node) => animateNumber(node, node.dataset.counter));
  }
  renderPlantHealth(data.plant_health);
  renderSectorHeatmap(data.sector_heatmap || []);
  renderCriticalAssets(data.critical_assets || []);
  renderMaintenanceFeed(data.maintenance_feed || []);
  renderPredictiveTimeline(data.predictive_timeline || []);
}

function assetStatusSummary() {
  const assets = state.assetMaster.length ? state.assetMaster : state.equipment;
  return assets.reduce((summary, asset) => {
    const risk = String(asset.risk_level || "").toLowerCase();
    const health = Number(asset.health_score ?? asset.health_index ?? 100);
    summary.total += 1;
    if (risk === "critical" || health < 70) {
      summary.critical += 1;
    } else if (risk === "high" || risk === "medium" || (health >= 70 && health < 90)) {
      summary.warning += 1;
    } else {
      summary.healthy += 1;
    }
    return summary;
  }, { total: 0, healthy: 0, warning: 0, critical: 0 });
}

function renderPlantHealth(health) {
  if (!els.plantHealthOverview) return;
  if (!health) {
    if (els.plantHealthPill) els.plantHealthPill.textContent = "Health";
    els.plantHealthOverview.innerHTML = emptyState("Plant health overview is loading.");
    return;
  }
  if (els.plantHealthPill) els.plantHealthPill.textContent = `${health.score}% Plant Health`;
  const distribution = health.distribution || {};
  const trend = health.trend_7_days || [];
  const points = trend.map((item, index) => {
    const x = (index / Math.max(1, trend.length - 1)) * 100;
    const y = 50 - (Number(item.score) / 100) * 44;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  els.plantHealthOverview.innerHTML = `
    <div class="health-gauge" style="--score:${Number(health.score)}">
      <strong>${escapeHtml(health.score)}%</strong>
      <span>Weighted Plant Health</span>
    </div>
    <div class="health-distribution">
      ${Object.entries(distribution).map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
      ${kpiCard("Maintenance Required", health.maintenance_required, "Assets requiring maintenance")}
    </div>
    <div class="trend-panel">
      <strong>7-Day Health Trend</strong>
      <svg viewBox="0 0 100 54" preserveAspectRatio="none"><polyline points="${points}" /></svg>
    </div>
  `;
}

function renderSectorHeatmap(rows) {
  if (!els.sectorHeatmap) return;
  if (!rows?.length) {
    els.sectorHeatmap.innerHTML = emptyState("No sector risk data available.");
    return;
  }
  els.sectorHeatmap.innerHTML = rows.map((sector) => `
    <button class="sector-tile ${escapeHtml(sector.risk_level)}" type="button" data-area="${escapeHtml(sector.area)}">
      <strong>${escapeHtml(sector.sector)}</strong>
      <span>${escapeHtml(sector.health)}% health</span>
      <small>${escapeHtml(sector.asset_count)} assets / ${escapeHtml(sector.active_alerts)} alerts</small>
      <b>${escapeHtml(sector.risk_level)}</b>
    </button>
  `).join("");
  els.sectorHeatmap.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.assetFilterArea = button.dataset.area;
      renderEquipment();
      const first = state.equipment.find((item) => state.assetMaster.find((asset) => asset.id === item.equipment_id)?.area === state.assetFilterArea);
      if (first) selectEquipment(first.equipment_id);
      showToast(`Filtered assets: ${button.textContent.trim().split(/\s+/).slice(0, 3).join(" ")}`);
    });
  });
}

function renderCriticalAssets(rows) {
  if (!els.criticalAssetList) return;
  if (!rows?.length) {
    els.criticalAssetList.innerHTML = emptyState("No critical assets currently require attention.");
    return;
  }
  els.criticalAssetList.innerHTML = rows.map((asset, index) => `
    <button class="critical-row ${asset.risk_level === "critical" ? "is-critical" : ""}" type="button" data-asset="${escapeHtml(asset.id)}">
      <span>${index + 1}</span>
      <div><strong>${escapeHtml(asset.name)}</strong><small>${escapeHtml(asset.area)} / ${escapeHtml(asset.active_alert)}</small></div>
      <b>${escapeHtml(asset.health_score)}%</b>
      <em>${escapeHtml(asset.risk_score)}</em>
    </button>
  `).join("");
  els.criticalAssetList.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => selectEquipment(button.dataset.asset));
  });
}

function renderMaintenanceFeed(rows) {
  if (!els.maintenanceFeed) return;
  if (!rows?.length) {
    els.maintenanceFeed.innerHTML = emptyState("No recent maintenance log entries available.");
    return;
  }
  els.maintenanceFeed.innerHTML = rows.map((row) => `
    <div class="feed-row">
      <strong>${escapeHtml(row.asset_name)}</strong>
      <span>${escapeHtml(row.action)} / ${escapeHtml(row.technician)}</span>
      <small>${escapeHtml(row.date)} / downtime ${escapeHtml(row.duration_hours)} h</small>
    </div>
  `).join("");
}

function renderPredictiveTimeline(rows) {
  if (!els.predictiveTimeline) return;
  if (!rows?.length) {
    els.predictiveTimeline.innerHTML = emptyState("No predictive maintenance timeline available.");
    return;
  }
  els.predictiveTimeline.innerHTML = rows.map((row) => `
    <div class="timeline-window">
      <strong>${escapeHtml(row.window)}</strong>
      <span>${escapeHtml(row.date)}</span>
      <p>Predicted failures: ${escapeHtml((row.predicted_failures || []).map((item) => `${item.asset} (${item.mode})`).join(", ") || "none")}</p>
      <p>Planned shutdowns: ${escapeHtml((row.planned_shutdowns || []).map((item) => `${item.work_order} ${item.asset}`).join(", ") || "none")}</p>
      <small>${escapeHtml(row.maintenance_schedules)} maintenance schedules</small>
    </div>
  `).join("");
}

function riskColor(level) {
  return {
    critical: "#d92d20",
    high: "#f97316",
    medium: "#eab308",
    low: "#22c55e",
  }[String(level || "low").toLowerCase()] || "#22c55e";
}

function renderPlantDigitalTwin(data = state.plantDigitalTwin) {
  if (!els.plantDigitalTwin || !els.twinAssetPanel) return;
  if (!data) {
    els.plantDigitalTwin.innerHTML = emptyState("Digital Twin layout is loading.");
    els.twinAssetPanel.innerHTML = emptyState("Select an asset on the Digital Twin to load asset context.");
    return;
  }
  state.plantDigitalTwin = data;
  const zones = data.zones || [];
  const assets = zones.flatMap((zone) => zone.assets || []);
  const selected = state.twinSelectedAssetId ? assets.find((asset) => asset.id === state.twinSelectedAssetId) : null;
  if (window.MaintenanceDigitalTwin?.render) {
    const rendered = window.MaintenanceDigitalTwin.render(els.plantDigitalTwin, data, (assetId) => {
      state.twinSelectedAssetId = assetId;
      const matching = state.equipment.find((item) => item.equipment_id === assetId);
      if (matching) selectEquipment(matching.equipment_id, false);
      renderPlantDigitalTwin();
      renderPredictiveAnalytics();
      renderDependencyGraph();
    });
    if (rendered) {
      renderTwinAssetPanel(selected);
      renderPredictiveAnalytics();
      renderDependencyGraph();
      return;
    }
  }
  els.plantDigitalTwin.innerHTML = `
    <div class="plant-floor">
      ${zones.map((zone) => `
        <button class="plant-zone" type="button" style="left:${zone.x}%;top:${zone.y}%">
          <strong>${escapeHtml(zone.name)}</strong>
          <span>${escapeHtml(zone.health_score)}% health</span>
        </button>
        ${(zone.assets || []).map((asset) => `
          <button class="asset-node ${asset.id === selected?.id ? "active" : ""} ${healthZoneClass(asset.health_score)} ${asset.risk_level === "critical" ? "critical-node" : ""}" type="button"
            data-asset="${escapeHtml(asset.id)}"
            data-health="${escapeHtml(asset.health_score)}"
            style="left:${asset.x}%;top:${asset.y}%;--risk:${riskColor(asset.risk_level)}"
            title="${escapeHtml(asset.name)}">
            <span></span>
          </button>
        `).join("")}
      `).join("")}
    </div>
  `;
  els.plantDigitalTwin.querySelectorAll(".asset-node").forEach((button) => {
    button.addEventListener("click", () => {
      state.twinSelectedAssetId = button.dataset.asset;
      const matching = state.equipment.find((item) => item.equipment_id === state.twinSelectedAssetId);
      if (matching) selectEquipment(matching.equipment_id, false);
      renderPlantDigitalTwin();
    });
  });
  renderTwinAssetPanel(selected);
  renderPredictiveAnalytics();
  renderDependencyGraph();
}

function renderTwinAssetPanel(asset) {
  if (!els.twinAssetPanel) return;
  if (!asset) {
    els.twinAssetPanel.innerHTML = `<div class="empty-state compact">Select an asset on the Digital Twin to load asset context.</div>`;
    return;
  }
  const sensor = asset.sensor_snapshot || {};
  const failures = (asset.recent_failures || []).slice(0, 3);
  const maintenance = (asset.maintenance_history || []).slice(0, 4);
  const workOrders = (asset.work_orders || []).slice(0, 4);
  const analytics = digitalTwinHealthAnalytics(asset);
  els.twinAssetPanel.innerHTML = `
    <div class="twin-panel-head">
      <span class="${pillClass(asset.risk_level)}">${escapeHtml(asset.risk_level)}</span>
      <strong>${escapeHtml(asset.name)}</strong>
      <p>${escapeHtml(asset.id)} / ${escapeHtml(asset.area)} / ${escapeHtml(asset.type)}</p>
    </div>
    <div class="enterprise-kpis">
      ${kpiCard("Health Score", `${asset.health_score}%`, asset.status)}
      ${kpiCard("Remaining Useful Life", `${asset.rul_hours} h`, `Rated ${asset.rated_hours} h`)}
      ${kpiCard("Last Maintenance", asset.last_maintenance, `MTBF ${asset.mtbf} h`)}
      ${kpiCard("Open Work Orders", asset.open_work_orders, `MTTR ${asset.mttr} h`)}
    </div>
    <h4>Sensor Snapshot</h4>
    <div class="sensor-chip-row">
      ${["temperature", "vibration", "pressure", "flow", "oil_quality", "current"].map((key) => `<span>${escapeHtml(key)}: ${escapeHtml(sensor[key] ?? "-")}</span>`).join("")}
    </div>
    <h4>Digital Twin Health Analytics</h4>
    <div class="twin-analytics">
      ${Object.entries(analytics).map(([label, value]) => `
        <div><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}%</b><i style="width:${safeNumber(value)}%"></i></div>
      `).join("")}
    </div>
    <h4>Recent Failures</h4>
    ${failures.length ? failures.map((item) => `<p class="mini-record">${escapeHtml(item.record_id)} - ${escapeHtml(item.failure_mode)} - ${escapeHtml(item.severity)}</p>`).join("") : `<p class="mini-record">No recent failure records.</p>`}
    <h4>Maintenance History</h4>
    ${maintenance.length ? maintenance.map((item) => `<p class="mini-record">${escapeHtml(item.date)} - ${escapeHtml(item.action)} - ${escapeHtml(item.finding)}</p>`).join("") : `<p class="mini-record">No maintenance history available.</p>`}
    <h4>Work Orders</h4>
    ${workOrders.length ? workOrders.map((item) => `<p class="mini-record">${escapeHtml(item.work_order_id)} - ${escapeHtml(item.priority)} - ${escapeHtml(item.status)}</p>`).join("") : `<p class="mini-record">No recent work orders.</p>`}
  `;
}

function healthZoneClass(value) {
  const health = safeNumber(value, 0);
  if (health >= 90) return "health-green";
  if (health >= 70) return "health-yellow";
  return "health-red";
}

function healthFromHigh(value, warn, trip) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 86;
  if (numeric <= warn) return 100;
  if (numeric >= trip) return 18;
  return Math.round(100 - ((numeric - warn) / (trip - warn)) * 70);
}

function healthFromLow(value, warn, trip) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 86;
  if (numeric >= warn) return 100;
  if (numeric <= trip) return 18;
  return Math.round(100 - ((warn - numeric) / (warn - trip)) * 70);
}

function digitalTwinHealthAnalytics(asset) {
  const sensor = asset?.sensor_snapshot || {};
  const typeText = `${asset?.type || ""} ${asset?.name || ""}`.toLowerCase();
  const mechanical = healthFromHigh(Number(sensor.vibration || 2), typeText.includes("gearbox") ? 4.2 : 4.8, 7.1);
  const electrical = healthFromHigh(Number(sensor.current || 160), typeText.includes("motor") || typeText.includes("transformer") ? 340 : 380, 430);
  const hydraulic = healthFromLow(Number(sensor.pressure || 125), typeText.includes("hydraulic") ? 118 : 100, 82);
  const thermal = healthFromHigh(Number(sensor.temperature || 60), typeText.includes("motor") || typeText.includes("transformer") ? 78 : 84, 96);
  const process = Math.round((healthFromLow(Number(sensor.flow || 160), 100, 70) + healthFromLow(Number(sensor.oil_quality || 80), 62, 38)) / 2);
  return { mechanical, electrical, hydraulic, thermal, process };
}

function selectedTwinAsset() {
  const assets = state.plantDigitalTwin?.zones?.flatMap((zone) => zone.assets || []) || [];
  if (!state.twinSelectedAssetId && !state.selectedEquipmentId) return null;
  return assets.find((asset) => asset.id === state.twinSelectedAssetId) || assets.find((asset) => asset.id === state.selectedEquipmentId) || null;
}

function activeAssetContext() {
  if (!state.selectedEquipmentId) {
    return {
      asset_id: "—",
      asset_name: "No asset selected",
      health_score: "—",
      risk_level: "—",
      remaining_useful_life: "—",
      rul_days: "—",
      current_alert: "—",
      sensor_snapshot: {},
      maintenance_history_summary: "—",
      failure_modes: [],
    };
  }
  const selected = selectedEquipment() || {};
  const twin = selectedTwinAsset() || {};
  const master = state.assetMaster.find((asset) => asset.id === state.selectedEquipmentId || asset.equipment_id === state.selectedEquipmentId) || {};
  const report = state.report?.equipment && assetDisplayId(state.report.equipment) === state.selectedEquipmentId ? state.report : null;
  const riskLevel = normalizeRiskLabel(firstDefined(report?.risk?.level, twin.risk_level, master.risk_level, selected.risk_level, classifyRisk(firstDefined(report?.risk?.score, twin.risk_score, master.risk_score, selected.risk_score), "low")));
  const sensor = {
    ...(twin.sensor_snapshot || {}),
    ...(state.telemetrySnapshot[state.selectedEquipmentId] || {}),
  };
  const maintenanceRows = twin.maintenance_history || master.maintenance_history || [];
  const historySummary = maintenanceRows.length
    ? maintenanceRows.slice(0, 3).map((row) => `${row.date || row.timestamp || ""} ${row.action || row.finding || row.summary || ""}`.trim()).join("; ")
    : "No recent maintenance history loaded in current view";
  return {
    asset_id: safe(state.selectedEquipmentId || assetDisplayId(selected)),
    asset_name: safe(assetDisplayName({ ...master, ...selected, name: twin.name || master.name || selected.equipment_name })),
    health_score: safe(firstDefined(twin.health_score, master.health_score, report?.prediction?.health_index, selected.health_score)),
    risk_level: riskDisplay(riskLevel),
    remaining_useful_life: safe(firstDefined(twin.rul_hours ? `${twin.rul_hours}h` : "", master.rul_hours ? `${master.rul_hours}h` : "", report?.prediction?.rul_label)),
    rul_days: safe(rulDaysLabel(firstDefined(twin.rul_hours, master.rul_hours, report?.prediction?.estimated_remaining_useful_life_hours, selected.rul_hours))),
    current_alert: safe(firstDefined(twin.current_alert, master.active_alert, master.anomaly_alert, selected.anomaly_alert, report?.equipment?.active_alert, assetDisplayAlert(selected))),
    sensor_snapshot: sensor,
    maintenance_history_summary: safe(historySummary),
    failure_modes: master.failure_modes || report?.diagnosis?.asset_failure_modes || [],
  };
}

function rulDaysLabel(hours) {
  const value = safeNumber(hours, NaN);
  if (!Number.isFinite(value)) return "—";
  return `${Math.max(0, Math.round(value / 24))} days`;
}

function percentLabel(value) {
  const display = safe(value);
  return display === "—" ? display : `${display}%`;
}

function assetContextPrompt(context = activeAssetContext()) {
  const sensor = context.sensor_snapshot || {};
  const sensorLines = Object.entries(sensor)
    .slice(0, 8)
    .map(([key, value]) => `${key}: ${safe(value)}`)
    .join("\n");
  const latestSummary = state.report
    ? [
        `Fault: ${safe(state.report?.diagnosis?.probable_fault)}`,
        `Risk: ${safe(state.report?.risk?.level)} ${safe(state.report?.risk?.score)}`,
        `Action: ${safe((state.report?.recommendations || [])[0])}`,
      ].join(" | ")
    : "No completed investigation in current session";
  return [
    "Asset Context:",
    `Asset ID: ${safe(context.asset_id)}`,
    `Asset Name: ${safe(context.asset_name)}`,
    `Health Score: ${percentLabel(context.health_score)}`,
    `Risk Level: ${safe(context.risk_level)}`,
    `RUL: ${safe(context.remaining_useful_life)} (${safe(context.rul_days)})`,
    `Current Alert: ${safe(context.current_alert)}`,
    sensorLines,
    `Maintenance History Summary: ${safe(context.maintenance_history_summary)}`,
    `Known Failure Modes: ${(context.failure_modes || []).map((item) => safe(item)).join(", ") || "not specified"}`,
    `Latest Investigation Summary: ${latestSummary}`,
  ].filter(Boolean).join("\n");
}

function renderActiveAssetChip() {
  if (!els.activeAssetChip) return;
  const context = activeAssetContext();
  if (!state.selectedEquipmentId) {
    els.activeAssetChip.className = "active-asset-chip";
    els.activeAssetChip.innerHTML = `
      <div class="active-asset-main">
        <span>Maintenance Copilot</span>
        <strong>No investigation active</strong>
        <small>Select an asset and click Run Investigation or ask a maintenance question.</small>
      </div>
      <em>Asset-Aware Mode Waiting</em>
    `;
    return;
  }
  const riskLevel = normalizeRiskLabel(context.risk_level);
  els.activeAssetChip.className = `active-asset-chip active-asset-${riskLevel}`;
  els.activeAssetChip.innerHTML = `
    <div class="active-asset-main">
      <span>ACTIVE ASSET</span>
      <strong>${escapeHtml(context.asset_name)}</strong>
      <small>${escapeHtml(context.asset_id)}</small>
    </div>
    <div class="active-asset-metrics">
      <b class="asset-status-chip ${riskClass(context.risk_level)}">Risk ${escapeHtml(riskDisplay(context.risk_level))}</b>
      <b>Health ${escapeHtml(percentLabel(context.health_score))}</b>
      <b>RUL ${escapeHtml(context.rul_days)}</b>
      <b>Alert ${escapeHtml(context.current_alert)}</b>
    </div>
    <em>Asset-Aware Mode Enabled</em>
  `;
}

function roiInputFromCostImpact(data = state.enterprise?.failure_cost_impact || {}) {
  const productionLoss = safeNumber(data?.production_loss_inr, 0);
  const downtimeCost = safeNumber(data?.downtime_cost_inr, 0);
  const repairCost = safeNumber(data?.repair_cost_inr, 0);
  const potentialFailureCost = safeNumber(firstDefined(data?.potential_failure_cost_inr, data?.failure_event_consequence_inr, productionLoss + downtimeCost + repairCost), 0);
  const shutdownCost = Math.max(1, Math.round(safeNumber(firstDefined(data?.shutdown_cost_inr, data?.controlled_shutdown_cost_inr, data?.planned_shutdown_cost_inr, potentialFailureCost * 0.075, 1200000), 1200000)));
  const savings = safeNumber(firstDefined(data?.expected_savings_inr, Math.max(0, potentialFailureCost - shutdownCost)), 0);
  const roi = safeNumber(firstDefined(data?.roi_percent, shutdownCost > 0 ? Math.round((savings / shutdownCost) * 100) : 0), 0);
  const riskLevel = riskDisplay(classifyRisk(selectedRiskScore(), state.report?.risk?.level || state.enterprise?.executive_decision_summary?.risk_level || "high"));
  const confidence = calculateUiConfidence(state.report) || 92;
  const failureProbability = failureProbabilityForContext();
  return {
    recommendedAction: riskLevel === "CRITICAL" ? "Controlled Shutdown" : "Controlled Shutdown Within 7 Days",
    shutdownCost,
    potentialFailureCost,
    savings,
    roi,
    riskLevel,
    confidence,
    failureProbability,
    businessImpact: safeNumber(firstDefined(data?.business_exposure_inr, data?.total_risk_exposure_inr, potentialFailureCost), potentialFailureCost),
  };
}

function isGenericInvestigationAction(value) {
  const text = String(value || "").trim().toLowerCase();
  return !text
    || text === DISPLAY_EMPTY
    || text.includes("run asset investigation")
    || text.includes("select asset")
    || text.includes("no action selected")
    || text.includes("review plant risk ranking");
}

function uniqueNonEmpty(items) {
  const seen = new Set();
  return (items || []).filter((item) => {
    const value = safeValue(item, "");
    if (!value) return false;
    const key = String(value).trim().toLowerCase();
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function heuristicRecommendationForSelectedAsset(riskLevel = selectedRiskLevel()) {
  const report = selectedReport() || {};
  const context = activeAssetContext();
  const text = [
    report?.diagnosis?.probable_fault,
    ...(report?.diagnosis?.probable_root_causes || []),
    context.current_alert,
    ...(context.failure_modes || []),
    context.asset_name,
  ].join(" ").toLowerCase();

  if (normalizeRiskLabel(riskLevel) === "critical") return "Controlled shutdown within 24 hours";
  if (text.includes("oil") || text.includes("lubric")) return "Replace contaminated lubricant";
  if (text.includes("gearbox") || text.includes("gear")) return "Schedule gearbox overhaul";
  if (text.includes("bearing") || text.includes("vibration")) return "Perform bearing inspection";
  if (text.includes("hydraulic") || text.includes("pressure") || text.includes("seal")) return "Inspect hydraulic leakage and replace seal kit";
  if (normalizeRiskLabel(riskLevel) === "high") return "Restrict operation to 70% load";
  return "Schedule condition-based maintenance intervention";
}

function selectedExecutiveRecommendation(data = {}, status = investigationStatusForSelectedAsset()) {
  if (!state.selectedEquipmentId) return "Select asset for decision";
  if (status === INVESTIGATION_STATES.NOT_STARTED) return "Run Investigation";
  if (status === INVESTIGATION_STATES.RUNNING) return "Investigation In Progress";
  if (status === INVESTIGATION_STATES.FAILED) return "Retry Investigation";

  const report = selectedReport() || {};
  const dataMatchesSelection = payloadMatchesSelectedAsset(data);
  const candidates = uniqueNonEmpty([
    dataMatchesSelection ? data?.recommended_maintenance_strategy : "",
    dataMatchesSelection ? data?.recommended_action : "",
    dataMatchesSelection ? data?.maintenance_recommendation : "",
    ...(report?.recommendations || []),
    report?.first_action,
    report?.priority?.first_action,
    state.agentic?.maintenance_plan?.summary,
    state.agentic?.planner?.recommended_action,
    state.agentic?.executive_decision?.recommended_action,
  ]).filter((item) => !isGenericInvestigationAction(item));

  return candidates[0] || heuristicRecommendationForSelectedAsset(selectedRiskLevel());
}

function selectedAssetFinancialImpact() {
  const reportAssetId = assetDisplayId(state.report?.equipment || {});
  const selectedId = state.selectedEquipmentId;
  const selectedImpactAssetId = firstDefined(state.selectedFinancialImpact?.equipment_id, state.selectedFinancialImpact?.asset_id);
  if (state.selectedFinancialImpact && selectedImpactAssetId === selectedId) {
    return state.selectedFinancialImpact;
  }
  const reportMatchesSelection = state.report && (!selectedId || reportAssetId === selectedId);
  if (reportMatchesSelection) {
    return financialImpactFromReport(state.report);
  }
  const enterpriseImpact = state.enterprise?.failure_cost_impact || {};
  const enterpriseAssetId = firstDefined(enterpriseImpact.equipment_id, enterpriseImpact.asset_id);
  if (selectedId && enterpriseAssetId && enterpriseAssetId !== selectedId) {
    const context = activeAssetContext();
    const healthPenalty = Math.max(0, 100 - safeNumber(context.health_score, 75));
    const riskMultiplier = { CRITICAL: 2.2, HIGH: 1.55, MEDIUM: 1, LOW: 0.55 }[String(context.risk_level || "").toUpperCase()] || 1;
    const productionLoss = Math.round((550000 + healthPenalty * 42000) * riskMultiplier);
    const downtimeCost = Math.round((260000 + failureProbabilityForContext() * 18000) * riskMultiplier);
    const repairCost = Math.round((380000 + healthPenalty * 21000) * riskMultiplier);
    const inventoryCost = Math.round(repairCost * 0.35);
    const potentialFailureCost = productionLoss + downtimeCost + repairCost;
    const businessExposure = potentialFailureCost + inventoryCost + Math.round(productionLoss * 0.18);
    const shutdownCost = Math.max(120000, Math.round(downtimeCost * 0.38 + repairCost * 0.28));
    const expectedSavings = Math.max(0, potentialFailureCost - shutdownCost);
    return {
      equipment_id: selectedId,
      production_loss_inr: productionLoss,
      downtime_cost_inr: downtimeCost,
      repair_cost_inr: repairCost,
      inventory_cost_inr: inventoryCost,
      estimated_downtime_hours: Math.max(2, Math.round(14 - safeNumber(context.health_score, 75) / 10)),
      total_risk_exposure_inr: businessExposure,
      business_exposure_inr: businessExposure,
      failure_event_consequence_inr: potentialFailureCost,
      potential_failure_cost_inr: potentialFailureCost,
      controlled_shutdown_cost_inr: shutdownCost,
      shutdown_cost_inr: shutdownCost,
      expected_savings_inr: expectedSavings,
      roi_percent: shutdownCost > 0 ? Math.round((expectedSavings / shutdownCost) * 100) : 0,
    };
  }
  return enterpriseImpact;
}

function failureProbabilityForContext() {
  const context = activeAssetContext();
  const health = Number(context.health_score);
  if (!Number.isFinite(health)) return 32;
  return Math.max(12, Math.min(88, Math.round((100 - health) * 1.25)));
}

function renderRoiDecisionCard(target, data = state.enterprise?.failure_cost_impact || {}) {
  if (!target) return;
  const roi = roiInputFromCostImpact(data);
  target.insertAdjacentHTML("beforeend", `
    <section class="roi-decision-card">
      <div class="roi-decision-head">
        <span>Executive Decision Impact</span>
        <strong>${escapeHtml(roi.recommendedAction)}</strong>
        <div>
          <b class="risk-badge">${escapeHtml(roi.riskLevel)}</b>
          <b class="roi-badge">${escapeHtml(roi.roi)}% ROI</b>
          <b class="savings-badge">${money(roi.savings)} Savings</b>
        </div>
      </div>
      <div class="roi-decision-grid">
        ${kpiCard("Failure Probability", `${roi.failureProbability}%`, "Asset-specific failure risk")}
        ${kpiCard("Shutdown Cost", money(roi.shutdownCost), "Controlled intervention estimate")}
        ${kpiCard("Potential Failure Cost", money(roi.potentialFailureCost), "If failure is allowed to progress")}
        ${kpiCard("Potential Savings", money(roi.savings), "Failure cost minus shutdown cost")}
        ${kpiCard("ROI", `${roi.roi}%`, "Savings divided by shutdown cost")}
        ${kpiCard("Confidence", `${roi.confidence}%`, "Decision confidence")}
      </div>
    </section>
  `);
}

function metricSeries(asset, metric) {
  const rows = asset?.sensor_history || [];
  return rows.map((row) => Number(row[metric])).filter((value) => Number.isFinite(value));
}

function trendDirection(values, highBad = true) {
  if (values.length < 4) return "stable";
  const first = values.slice(0, Math.ceil(values.length / 3)).reduce((a, b) => a + b, 0) / Math.ceil(values.length / 3);
  const lastValues = values.slice(-Math.ceil(values.length / 3));
  const last = lastValues.reduce((a, b) => a + b, 0) / lastValues.length;
  const delta = last - first;
  if (Math.abs(delta) < Math.max(0.2, Math.abs(first) * 0.02)) return "stable";
  return highBad ? (delta > 0 ? "degrading" : "improving") : (delta < 0 ? "degrading" : "improving");
}

function predictionForAsset(asset) {
  if (!asset) return null;
  const vibration = metricSeries(asset, "vibration");
  const temperature = metricSeries(asset, "temperature");
  const pressure = metricSeries(asset, "pressure");
  const oil = metricSeries(asset, "oil_quality");
  const severity = {
    critical: 0.45,
    high: 0.7,
    medium: 1.15,
    low: 1.8,
  }[asset.risk_level] || 1.1;
  const rul = Math.max(4, Math.round(Number(asset.rul_hours || 100) * severity));
  const predictionDate = new Date(Date.now() + rul * 60 * 60 * 1000);
  const badSignals = [
    trendDirection(vibration) === "degrading",
    trendDirection(temperature) === "degrading",
    trendDirection(pressure, false) === "degrading",
    trendDirection(oil, false) === "degrading",
  ].filter(Boolean).length;
  const confidence = Math.min(96, 68 + badSignals * 6 + (asset.failure_reports || []).length * 2);
  return { rul, predictionDate, confidence, badSignals };
}

function sparkline(values, metric, highBad = true) {
  if (!values.length) return `<div class="empty-state compact">No ${escapeHtml(metric)} history.</div>`;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const points = values.map((value, index) => {
    const x = (index / Math.max(1, values.length - 1)) * 100;
    const y = 48 - ((value - min) / range) * 42;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const trend = trendDirection(values, highBad);
  return `
    <div class="curve-card ${trend}">
      <div class="curve-head"><strong>${escapeHtml(metric)}</strong><span>${escapeHtml(trend)}</span></div>
      <svg viewBox="0 0 100 54" preserveAspectRatio="none">
        <polyline points="${points}" />
      </svg>
      <small>Range ${min.toFixed(1)} to ${max.toFixed(1)}</small>
    </div>
  `;
}

function renderPredictiveAnalytics() {
  if (!els.predictiveAnalytics) return;
  const asset = selectedTwinAsset();
  const prediction = predictionForAsset(asset);
  if (!asset || !prediction) {
    els.predictiveAnalytics.innerHTML = `<div class="empty-state compact">Select an asset in the digital twin to view prediction curves.</div>`;
    return;
  }
  if (els.predictionConfidence) els.predictionConfidence.textContent = `${prediction.confidence}% Confidence`;
  els.predictiveAnalytics.innerHTML = `
    ${kpiCard("Failure Prediction Date", prediction.predictionDate.toLocaleString(), asset.risk_level)}
    ${kpiCard("RUL Forecast", `${prediction.rul} h`, "Remaining useful life forecast")}
    ${kpiCard("Confidence Score", `${prediction.confidence}%`, `${prediction.badSignals} degrading trend signals`)}
    ${kpiCard("Trend Analysis", prediction.badSignals >= 2 ? "Degrading" : "Watch", "Vibration, temperature, pressure, oil quality")}
    <div class="curve-grid">
      ${sparkline(metricSeries(asset, "vibration"), "vibration")}
      ${sparkline(metricSeries(asset, "temperature"), "temperature")}
      ${sparkline(metricSeries(asset, "pressure"), "pressure", false)}
      ${sparkline(metricSeries(asset, "oil_quality"), "oil quality", false)}
    </div>
  `;
}

function renderDependencyGraph(data = state.dependencyGraph) {
  if (!els.dependencyGraph) return;
  if (!data) {
    els.dependencyGraph.innerHTML = emptyState("Dependency graph data is loading.");
    return;
  }
  state.dependencyGraph = data;
  const assetId = state.twinSelectedAssetId || state.selectedEquipmentId;
  if (!assetId) {
    els.dependencyGraph.innerHTML = emptyState("Select an asset to view upstream, downstream, and cascading failure risk.");
    return;
  }
  let nodes = data.nodes || [];
  let edges = data.edges || [];
  let relatedEdges = edges.filter((edge) => edge.source === assetId || edge.target === assetId);
  const relatedIds = new Set([assetId, ...relatedEdges.flatMap((edge) => [edge.source, edge.target])]);
  let relatedNodes = nodes.filter((node) => relatedIds.has(node.id));
  let selected = nodes.find((node) => node.id === assetId);
  if (!relatedNodes.length || !relatedEdges.length) {
    const asset = state.selectedAsset || selectedAssetData(assetId) || {};
    relatedNodes = [
      { id: "plant", name: "Tata Steel Plant", area: "Plant", risk_level: "low", health_score: 92 },
      { id: `area-${safe(asset.area, "area")}`, name: safe(asset.area, "Production Area"), area: "Area", risk_level: asset.risk_level || "medium", health_score: asset.health_score || 80 },
      { id: `line-${assetId}`, name: `${safe(asset.area, "Production")} Line`, area: safe(asset.area), risk_level: asset.risk_level || "medium", health_score: asset.health_score || 80 },
      { id: assetId, name: assetDisplayName(asset), area: safe(asset.area), risk_level: asset.risk_level || "medium", health_score: asset.health_score || 80 },
      { id: `subsystem-${assetId}`, name: safe(asset.type, "Subsystem"), area: safe(asset.area), risk_level: asset.risk_level || "medium", health_score: asset.health_score || 80 },
    ];
    relatedEdges = relatedNodes.slice(0, -1).map((node, index) => ({
      source: node.id,
      target: relatedNodes[index + 1].id,
      relationship: ["Plant", "Area", "Line", "Asset"][index] || "Dependency",
      cascading_failure_risk: index >= 2 ? failureProbabilityForContext() : 12 + index * 8,
    }));
    nodes = relatedNodes;
    selected = relatedNodes.find((node) => node.id === assetId);
  }
  const maxRisk = Math.max(0, ...relatedEdges.map((edge) => Number(edge.cascading_failure_risk || 0)));
  els.dependencyGraph.innerHTML = `
    <div class="dependency-summary">
      ${kpiCard("Selected Asset", selected?.name || assetId, selected?.area || "-")}
      ${kpiCard("Upstream Assets", relatedEdges.filter((edge) => edge.target === assetId).length, "Production dependencies")}
      ${kpiCard("Downstream Assets", relatedEdges.filter((edge) => edge.source === assetId).length, "Impacted assets")}
      ${kpiCard("Cascading Risk", `${maxRisk}%`, "Highest relationship risk")}
    </div>
    <div class="network-canvas">
      ${relatedNodes.map((node, index) => {
        const angle = (index / Math.max(1, relatedNodes.length)) * Math.PI * 2;
        const radius = node.id === assetId ? 0 : 38;
        const x = 50 + Math.cos(angle) * radius;
        const y = 50 + Math.sin(angle) * radius;
        return `<button class="network-node ${node.id === assetId ? "active" : ""}" data-asset="${escapeHtml(node.id)}" style="left:${x}%;top:${y}%;--risk:${riskColor(node.risk_level)}"><strong>${escapeHtml(node.name)}</strong><b>Health ${escapeHtml(percentLabel(node.health_score))}</b><span>${escapeHtml(node.risk_level || "watch")}</span><small>${escapeHtml(node.area)}</small></button>`;
      }).join("")}
    </div>
    <div class="dependency-list">
      ${relatedEdges.length ? relatedEdges.map((edge) => {
        const source = nodes.find((node) => node.id === edge.source);
        const target = nodes.find((node) => node.id === edge.target);
        return `<div class="trace-item"><strong>${escapeHtml(source?.name || edge.source)} -> ${escapeHtml(target?.name || edge.target)}</strong><p>${escapeHtml(edge.relationship)} / cascading failure risk ${escapeHtml(edge.cascading_failure_risk)}%</p></div>`;
      }).join("") : `<div class="empty-state compact">No direct dependency records for this asset.</div>`}
    </div>
  `;
  els.dependencyGraph.querySelectorAll(".network-node").forEach((button) => {
    button.addEventListener("click", () => {
      state.twinSelectedAssetId = button.dataset.asset;
      if (state.equipment.some((item) => item.equipment_id === button.dataset.asset)) {
        selectEquipment(button.dataset.asset, false);
      }
      renderPlantDigitalTwin();
    });
  });
}

function initializeTelemetrySnapshot() {
  const assets = state.plantDigitalTwin?.zones?.flatMap((zone) => zone.assets || []) || [];
  state.telemetrySnapshot = {};
  assets.forEach((asset) => {
    state.telemetrySnapshot[asset.id] = { ...(asset.sensor_snapshot || {}) };
  });
}

function updateTelemetry() {
  const assets = state.plantDigitalTwin?.zones?.flatMap((zone) => zone.assets || []) || [];
  assets.forEach((asset) => {
    const current = state.telemetrySnapshot[asset.id] || { ...(asset.sensor_snapshot || {}) };
    const riskMultiplier = asset.risk_level === "critical" ? 1.7 : asset.risk_level === "high" ? 1.25 : 0.7;
    current.temperature = Number((Number(current.temperature || 60) + (Math.random() - 0.35) * riskMultiplier).toFixed(1));
    current.vibration = Number(Math.max(0.6, Number(current.vibration || 2.2) + (Math.random() - 0.35) * 0.18 * riskMultiplier).toFixed(2));
    current.pressure = Number(Math.max(45, Number(current.pressure || 120) + (Math.random() - 0.58) * 2.5 * riskMultiplier).toFixed(1));
    current.flow = Number(Math.max(40, Number(current.flow || 150) + (Math.random() - 0.5) * 5).toFixed(1));
    current.current = Number(Math.max(20, Number(current.current || 180) + (Math.random() - 0.35) * 4 * riskMultiplier).toFixed(1));
    current.oil_quality = Number(Math.max(10, Number(current.oil_quality || 70) + (Math.random() - 0.56) * 1.1 * riskMultiplier).toFixed(1));
    state.telemetrySnapshot[asset.id] = current;
  });
  renderLiveTelemetry();
}

function renderLiveTelemetry() {
  if (!els.liveTelemetry) return;
  const asset = selectedTwinAsset();
  if (!asset) {
    els.liveTelemetry.innerHTML = emptyState("Select an asset to start real-time sensor streaming.");
    if (els.streamAlerts) {
      els.streamAlerts.innerHTML = emptyState("No active stream selected.");
    }
    return;
  }
  const snapshot = state.telemetrySnapshot[asset.id] || asset.sensor_snapshot || {};
  const checks = [
    ["temperature", snapshot.temperature, 82, "high"],
    ["vibration", snapshot.vibration, 5.2, "high"],
    ["pressure", snapshot.pressure, 95, "low"],
    ["current", snapshot.current, 370, "high"],
    ["oil_quality", snapshot.oil_quality, 55, "low"],
    ["flow", snapshot.flow, 95, "low"],
  ];
  const alerts = checks.filter(([, value, limit, mode]) => mode === "high" ? Number(value) >= limit : Number(value) <= limit);
  state.streamAlerts = alerts.map(([metric, value, limit, mode]) => ({
    metric,
    value,
    limit,
    message: `${metric} ${mode === "high" ? "above" : "below"} threshold on ${asset.name}`,
  }));
  els.liveTelemetry.innerHTML = checks.map(([metric, value, limit, mode]) => {
    const breached = mode === "high" ? Number(value) >= limit : Number(value) <= limit;
    return `
      <div class="telemetry-card ${breached ? "breached" : ""}">
        <span>${escapeHtml(metric)}</span>
        <strong>${escapeHtml(value ?? "-")}</strong>
        <small>Limit ${escapeHtml(mode === "high" ? "<= " : ">= ")}${escapeHtml(limit)}</small>
      </div>
    `;
  }).join("");
  if (els.streamAlerts) {
    els.streamAlerts.innerHTML = state.streamAlerts.length
      ? state.streamAlerts.map((alert) => `<div class="alert-item"><div><strong>${escapeHtml(alert.metric)}</strong><p>${escapeHtml(alert.message)} / value ${escapeHtml(alert.value)} / limit ${escapeHtml(alert.limit)}</p></div><span class="pill critical">Alert</span></div>`).join("")
      : `<div class="empty-state compact">No streaming threshold breach for selected asset.</div>`;
  }
}

function startTelemetry() {
  if (state.telemetryTimer) clearInterval(state.telemetryTimer);
  initializeTelemetrySnapshot();
  updateTelemetry();
  state.telemetryTimer = setInterval(updateTelemetry, 4000);
}

function renderReportCatalog() {
  if (!els.reportTypeSelect) return;
  els.reportTypeSelect.innerHTML = state.reportCatalog
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`)
    .join("");
  renderEnterpriseReportPreview();
}

function renderEnterpriseReportPreview() {
  if (!els.enterpriseReportPreview) return;
  const selected = state.reportCatalog.find((item) => item.id === els.reportTypeSelect?.value) || state.reportCatalog[0];
  const kpis = state.operationsCenter?.kpis || [];
  const decision = state.enterprise?.executive_decision_summary || {};
  const impact = state.enterprise?.failure_cost_impact || {};
  const selectedRecommendation = selectedExecutiveRecommendation(decision, investigationStatusForSelectedAsset());
  els.enterpriseReportPreview.innerHTML = `
    <div class="report-summary-preview compact-report-preview">
      <div class="report-summary-main">
        <span>Executive Summary Preview</span>
        <strong>${escapeHtml(selected?.name || "Enterprise Report")}</strong>
        <p>Export-ready report for plant leadership, reliability engineering, maintenance planning, and stores review.</p>
      </div>
      <div class="report-summary-grid">
        ${kpiCard("Risk Level", riskDisplay(selectedRiskLevel()), activeAssetContext().asset_id || "Plant level")}
        ${kpiCard("Financial Impact", money(impact.total_risk_exposure_inr || impact.production_loss_inr), "Estimated exposure")}
        ${kpiCard("Recommended Action", selectedRecommendation || "Approve maintenance action", "Decision")}
        ${kpiCard("Generated Timestamp", new Date().toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }), kpis.slice(0, 3).map((item) => item.label).join(", "))}
      </div>
    </div>
  `;
}

function exportEnterpriseReport(format) {
  const reportType = els.reportTypeSelect?.value || "executive_summary";
  window.location.href = `/api/report-export?type=${encodeURIComponent(reportType)}&format=${encodeURIComponent(format)}`;
}

function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    if (els.voiceStatus) els.voiceStatus.textContent = "Speech recognition is not supported in this browser.";
    showToast("Speech recognition is not supported in this browser.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  if (els.voiceStatus) els.voiceStatus.textContent = "Listening...";
  recognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript || "";
    els.chatInput.value = transcript;
    if (els.voiceStatus) els.voiceStatus.textContent = `Heard: ${transcript}`;
    sendChat();
  };
  recognition.onerror = () => {
    if (els.voiceStatus) els.voiceStatus.textContent = "Voice input failed. Try again.";
  };
  recognition.onend = () => {
    if (els.voiceStatus && els.voiceStatus.textContent === "Listening...") {
      els.voiceStatus.textContent = "Voice assistant ready";
    }
  };
  recognition.start();
}

function speakLastResponse() {
  if (!("speechSynthesis" in window)) {
    showToast("Text-to-speech is not supported in this browser.");
    return;
  }
  const text = state.lastAssistantText || state.chatHistory.slice().reverse().find((item) => item.role === "assistant")?.content || "";
  if (!text) {
    showToast("No assistant response to speak yet.");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-IN";
  utterance.rate = 0.95;
  utterance.pitch = 1;
  if (els.voiceStatus) els.voiceStatus.textContent = "Speaking response...";
  utterance.onend = () => {
    if (els.voiceStatus) els.voiceStatus.textContent = "Voice assistant ready";
  };
  window.speechSynthesis.speak(utterance);
}

function searchCorpus() {
  const twinAssets = state.plantDigitalTwin?.zones?.flatMap((zone) => zone.assets || []) || [];
  const failures = twinAssets.flatMap((asset) =>
    (asset.recent_failures || []).map((failure) => ({
      kind: "Failure Mode",
      id: failure.record_id,
      title: failure.failure_mode,
      detail: `${failure.asset_name || failure.equipment_id} / ${failure.severity}`,
      assetId: failure.equipment_id,
    }))
  );
  const logs = twinAssets.flatMap((asset) =>
    (asset.maintenance_history || []).map((log) => ({
      kind: "Maintenance Log",
      id: log.log_id,
      title: log.action,
      detail: `${log.asset_name} / ${log.finding} / ${log.technician}`,
      assetId: log.equipment_id,
    }))
  );
  const orders = twinAssets.flatMap((asset) =>
    (asset.work_orders || []).map((order) => ({
      kind: "Work Order",
      id: order.work_order_id,
      title: order.priority,
      detail: `${order.asset_name} / ${order.status} / ${order.assigned_team}`,
      assetId: order.equipment_id,
    }))
  );
  const spares = (state.operationsCenter ? state.assetMaster : []).flatMap(() => []);
  return [
    ...state.assetMaster.map((asset) => ({
      kind: "Asset",
      id: asset.id,
      title: asset.name,
      detail: `${asset.area} / ${asset.type} / ${asset.risk_level}`,
      assetId: asset.id,
    })),
    ...failures,
    ...logs,
    ...orders,
    ...state.spares.map((spare) => ({
      kind: "Spare",
      id: spare.equipment_id,
      title: spare.part,
      detail: `Stock ${spare.available_qty} / Lead ${spare.lead_time_days} days`,
      assetId: spare.equipment_id,
    })),
    ...spares,
  ];
}

function renderGlobalSearch() {
  if (!els.globalSearch || !els.globalSearchResults) return;
  const query = els.globalSearch.value.trim().toLowerCase();
  if (!query) {
    els.globalSearchResults.innerHTML = "";
    renderEquipment();
    return;
  }
  const matches = searchCorpus()
    .filter((item) => `${item.kind} ${item.id} ${item.title} ${item.detail}`.toLowerCase().includes(query))
    .slice(0, 8);
  els.globalSearchResults.innerHTML = matches.length
    ? matches.map((item) => `
      <button type="button" data-asset="${escapeHtml(item.assetId)}">
        <strong>${escapeHtml(item.kind)} / ${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.detail)}</span>
      </button>
    `).join("")
    : `<div class="empty-state compact">No matching asset, failure, or spare found.</div>`;
  els.globalSearchResults.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const assetId = button.dataset.asset;
      if (state.equipment.some((item) => item.equipment_id === assetId)) {
        selectEquipment(assetId);
      }
      state.twinSelectedAssetId = assetId;
      switchModule("asset-intelligence");
      renderPlantDigitalTwin();
    });
  });
  renderEquipment();
}

function renderCriticalityMatrix(rows) {
  els.criticalityMatrix.innerHTML = `
    <table><thead><tr><th>Equipment</th><th>Production</th><th>Safety</th><th>Cost</th><th>Score</th><th>Class</th></tr></thead>
    <tbody>${rows.map((row) => `
      <tr><td>${escapeHtml(row.equipment_id)}</td><td>${row.production_impact}</td><td>${row.safety_impact}</td><td>${row.maintenance_cost}</td><td>${row.criticality_score}</td><td>${escapeHtml(row.criticality)}</td></tr>
    `).join("")}</tbody></table>
  `;
}

function renderCostImpact(data) {
  if (!els.costImpact) return;
  if (!data) {
    els.costImpact.innerHTML = emptyState("Run an investigation to generate Business Impact Analysis.");
    return;
  }
  const asset = selectedEquipment() || {};
  const cause = assetDisplayName(asset) || data?.equipment_id || "Selected asset";
  const outage = `${safeValue(firstDefined(data?.estimated_downtime_hours, data?.downtime_hours), 0)} Hours`;
  const totalExposure = firstDefined(data?.total_risk_exposure_inr, data?.total_business_impact_inr, 0);
  els.costImpact.innerHTML = [
    financialImpactCard("Production Loss", money(data?.production_loss_inr), cause, outage, "High", "large"),
    financialImpactCard("Downtime Cost", money(data?.downtime_cost_inr), cause, outage, "High", "large"),
    financialImpactCard("Risk Exposure", money(totalExposure), cause, outage, "High", "large"),
    financialImpactCard("Inventory Cost", money(data?.inventory_cost_inr), cause, outage, "Medium", "medium"),
    financialImpactCard("Repair Cost", money(data?.repair_cost_inr), cause, outage, "Medium", "medium"),
    financialImpactCard("Estimated Downtime", `${safeValue(data?.estimated_downtime_hours, 0)} h`, data?.equipment_id, outage, "Watch", "small"),
  ].join("");
  const scenarios = data?.scenario_comparison || [];
  if (scenarios.length) {
    const max = Math.max(...scenarios.map((item) => Number(item.risk_exposure_inr || 1)));
    els.costImpact.insertAdjacentHTML("beforeend", `
      <div class="impact-bars">
        ${scenarios.map((item) => `
          <div>
            <span>${escapeHtml(item?.scenario)}</span>
            <strong>${money(item?.risk_exposure_inr)} / ${escapeHtml(item?.downtime_hours)} h</strong>
            <div class="bar-track"><i style="width:${Math.max(8, (safeNumber(item?.risk_exposure_inr, 0) / max) * 100)}%"></i></div>
          </div>
        `).join("")}
      </div>
    `);
  }
  renderRoiDecisionCard(els.costImpact, data);
}

function financialImpactCard(label, value, cause, outage, impact, size = "medium") {
  const count = countAnimationMeta(value);
  const countAttrs = count
    ? ` data-count-target="${escapeHtml(count.target)}" data-count-prefix="${escapeHtml(count.prefix)}" data-count-suffix="${escapeHtml(count.suffix)}" data-count-decimals="${escapeHtml(count.decimals)}" data-count-final="${escapeHtml(value)}"`
    : "";
  const causeClass = /^[A-Z0-9-]{8,}$/.test(String(cause || "")) ? "equipment-id" : "asset-name";
  return `
    <article class="financial-impact-card business-impact-card ${escapeHtml(size)} ${impact === "High" ? "high-impact" : ""}">
      <span>${escapeHtml(label)}</span>
      <strong${countAttrs}>${escapeHtml(value)}</strong>
      <dl>
        <div class="impact-row"><dt class="impact-label">Cause</dt><dd class="impact-value cause-value impact-cause ${causeClass}">${escapeHtml(cause)}</dd></div>
        <div class="impact-row"><dt class="impact-label">Estimated Outage</dt><dd class="impact-value">${escapeHtml(outage)}</dd></div>
        <div class="impact-row"><dt class="impact-label">Business Impact</dt><dd class="impact-value impact-cause">${escapeHtml(impact)}</dd></div>
      </dl>
    </article>
  `;
}

function buildIncidentReplayFromState() {
  const context = activeAssetContext();
  const assetId = context.asset_id === DISPLAY_EMPTY ? "" : context.asset_id;
  const selectedHistory = (state.history || []).filter((item) => !assetId || item.equipment_id === assetId || item.asset_id === assetId);
  const history = selectedHistory.length ? selectedHistory : (state.history || []);
  const primary = history[0] || {};
  const fault = firstDefined(primary.fault, primary.failure_mode, primary.alert_code, context.current_alert, "Historical reliability event");
  const risk = context.risk_level === DISPLAY_EMPTY ? firstDefined(primary.severity, primary.risk_level, "medium") : context.risk_level;
  return {
    incident_name: `${safe(context.asset_name, "Plant Asset")} - ${safe(fault, "Incident Replay")}`,
    risk_level: normalizeRiskLabel(risk || classifyRisk(firstDefined(primary.risk_score, selectedRiskScore()), "low")),
    timeline: [
      { time: "09:10", event: safe(primary.symptoms || primary.summary || "Abnormal operating condition observed") },
      { time: "09:25", event: safe(primary.failure_progression || "Condition trend reviewed against historical records") },
      { time: "09:40", event: `Alert context linked to ${safe(context.current_alert, "active asset watch")}` },
      { time: "10:05", event: safe(primary.production_impact || "Production impact assessed by operations team") },
      { time: "10:20", event: safe(primary.action || primary.corrective_action || "Corrective action and lessons captured") },
    ],
    failure_progression: safe(primary.failure_progression || primary.root_cause || `${safe(fault)} progressed from abnormal condition to maintenance decision.`),
    production_impact: safe(primary.production_impact || "Previous incident records and investigation history are available for replay."),
    corrective_actions_taken: [
      safe(primary.action || primary.corrective_action || "Reviewed failure history and active sensor evidence"),
      safe(primary.recommendation || "Prepared maintenance action and ownership path"),
    ],
    lessons_learned: [
      "Review similar failures before approving maintenance windows",
      "Connect incident evidence to spare and work-order planning",
    ],
  };
}

function renderIncidentReplay(data = state.incidentReplay || state.enterprise?.incident_replay || buildIncidentReplayFromState()) {
  if (!els.incidentReplay) return;
  if (!data) {
    els.incidentReplay.innerHTML = emptyState("Incident replay records are loading.");
    return;
  }
  state.incidentReplay = data;
  console.log("INCIDENT_REPLAY_RENDER", {
    source: data === state.enterprise?.incident_replay ? "enterprise_payload" : state.incidentReplay === data ? "state" : "local_history",
    incident_name: data.incident_name,
    timeline_count: Array.isArray(data.timeline) ? data.timeline.length : 0,
  });
  const timeline = Array.isArray(data.timeline) ? data.timeline : [];
  const correctiveActions = Array.isArray(data.corrective_actions_taken) ? data.corrective_actions_taken : [];
  const lessons = Array.isArray(data.lessons_learned) ? data.lessons_learned : [];
  els.incidentReplay.innerHTML = `
    <div class="incident-header">
      <div>
        <span>Incident</span>
        <strong>${escapeHtml(data.incident_name)}</strong>
      </div>
      <span class="${pillClass(data.risk_level)}">${escapeHtml(riskDisplay(data.risk_level))}</span>
    </div>
    <div class="incident-summary">
      ${kpiCard("Production Impact", data.production_impact, "Historical operational effect")}
      ${kpiCard("Failure Progression", data.failure_progression, "Observed degradation path")}
    </div>
    <div class="incident-timeline">
      ${timeline.map((item, index) => `
        <div class="timeline-item incident-event">
          <div class="incident-event-marker"><b>${escapeHtml(String(index + 1).padStart(2, "0"))}</b><span>${escapeHtml(item.time)}</span></div>
          <p>${escapeHtml(item.event)}</p>
        </div>
      `).join("")}
    </div>
    <h4>Corrective Actions Taken</h4>
    <ul>${correctiveActions.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>Not Available</li>"}</ul>
    <h4>Lessons Learned</h4>
    <ul>${lessons.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>Not Available</li>"}</ul>
  `;
}

async function refreshIncidentReplay(reason = "manual") {
  if (!els.incidentReplay) return;
  const equipmentId = state.selectedEquipmentId;
  const endpoint = equipmentId
    ? `/api/incident-replay?equipment_id=${encodeURIComponent(equipmentId)}`
    : "/api/incident-replay";
  console.log("INCIDENT_REPLAY_REQUEST_SENT", { endpoint, reason, equipment_id: equipmentId || null });
  try {
    const payload = await apiWithTimeout(endpoint, {}, 12000);
    console.log("INCIDENT_REPLAY_RESPONSE_RECEIVED", payload);
    state.incidentReplay = payload.incident_replay || payload;
    renderIncidentReplay(state.incidentReplay);
  } catch (error) {
    console.warn("INCIDENT_REPLAY_REQUEST_FAILED", { endpoint, error: error.message });
    renderIncidentReplay(buildIncidentReplayFromState());
  }
}

function renderBudgetDashboard(data) {
  els.budgetDashboard.innerHTML = [
    kpiCard("Monthly Spend", money(data.monthly_maintenance_spend_inr), "Current month"),
    kpiCard("Emergency Repairs", money(data.emergency_repairs_inr), "Unplanned work"),
    kpiCard("Planned Maintenance", money(data.planned_maintenance_inr), "Scheduled work"),
    kpiCard("Cost Avoidance", money(data.cost_avoidance_inr), "Prevented downtime"),
    kpiCard("Inventory Value", money(data.inventory_value_inr), "Stores value"),
  ].join("");
  els.budgetTrend.innerHTML = data.trend.map((item) => `<span style="height:${item.spend * 2}px" title="${item.month}"></span>`).join("");
}

function renderMaintenanceKpis(data) {
  if (!els.maintenanceKpis) return;
  els.maintenanceKpis.innerHTML = [
    kpiCard("MTBF", `${data.mtbf_hours} h`, "Mean time between failures"),
    kpiCard("MTTR", `${data.mttr_hours} h`, "Mean time to repair"),
    kpiCard("Availability", `${data.availability_percent}%`, "Asset availability"),
    kpiCard("OEE Impact", `${data.oee_impact_percent}%`, "Production efficiency impact"),
    kpiCard("Compliance", `${data.maintenance_compliance_percent}%`, "PM compliance"),
    kpiCard("WO Completion", `${data.work_order_completion_rate_percent}%`, "Closed within planned window"),
    kpiCard("Emergency Repairs", `${data.emergency_repair_ratio_percent}%`, `Planned vs unplanned ${data.planned_vs_unplanned_ratio}`),
    kpiCard("PM Success", `${data.preventive_maintenance_success_percent}%`, "Preventive work preventing repeat failures"),
  ].join("");
}

function renderReliabilityAssessment(data) {
  if (!data || !els.reliabilityAssessment) return;
  els.reliabilityAssessment.innerHTML = [
    kpiCard("MTBF", `${data.mtbf_hours} h`, "Mean time between failures"),
    kpiCard("MTTR", `${data.mttr_hours} h`, "Mean time to repair"),
    kpiCard("Failure Frequency", data.breakdown_frequency, "Recent breakdown count"),
    kpiCard("Recurring Failure Index", `${Math.max(12, data.breakdown_frequency * 9)}%`, "Repeat-failure signal"),
    kpiCard("Maintenance Compliance", `${data.maintenance_compliance_percent}%`, "PM completion"),
    kpiCard("Recommended Actions", "Stabilize recurring modes", "Review PM interval, spares, and inspection checklist"),
  ].join("");
}

function renderRcaWorkspace(data) {
  const fiveWhy = Array.isArray(data.five_why) ? data.five_why : [];
  const fishbone = data.fishbone && typeof data.fishbone === "object" ? data.fishbone : {};
  els.rcaWorkspace.innerHTML = `
    <div class="source-group"><strong>${escapeHtml(data.problem)}</strong><p>Probable RCA: ${escapeHtml(data.probable_rca)}</p></div>
    <h4>5 Why Analysis</h4>
    <ol>${fiveWhy.map((item) => `<li>${escapeHtml(item.answer)}</li>`).join("") || "<li>Not Available</li>"}</ol>
    <h4>Fishbone Categories</h4>
    <div class="fishbone-grid">${Object.entries(fishbone).map(([key, value]) => `<div><strong>${escapeHtml(key)}</strong><p>${escapeHtml(value)}</p></div>`).join("") || "<div><strong>N/A</strong><p>Not Available</p></div>"}</div>
  `;
}

function renderFailureTimeline(items) {
  els.failureTimeline.innerHTML = items.map((item) => `
    <div class="timeline-item"><strong>${escapeHtml(item.period)}</strong><p>${escapeHtml(item.event)}</p><small>${escapeHtml(item.impact)}</small></div>
  `).join("");
}

function renderOperationCards(items) {
  els.operationSimulator.innerHTML = items.map((item) => kpiCard(
    item.strategy,
    item.risk,
    `${money(item.estimated_cost_inr)} - ${escapeHtml(item.downtime_hours)} h - ${item.production_impact}. ${item.recommendation || ""}`
  )).join("");
}

async function simulateOperation() {
  try {
    const data = await api("/api/operation-simulator", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: state.selectedEquipmentId,
        strategy: els.operationStrategy.value,
      }),
    });
    renderOperationCards([data.simulation]);
    showToast("Operation impact simulated.");
  } catch (error) {
    showToast(error.message);
  }
}

function renderProcurement(items) {
  if (!els.procurementAssistant) return;
  els.procurementAssistant.innerHTML = items.length ? items.map((item) => `
    <div class="spare-item">
      <strong>${escapeHtml(item.part)}</strong>
      <p>Asset ${escapeHtml(item.equipment_id)} / Current stock ${item.current_qty} / Lead time ${item.lead_time_days} days</p>
      <p>Recommended quantity ${item.suggested_order_qty} / Priority ${escapeHtml(item.risk_if_delayed)} / Approval route: Maintenance Lead -> Stores -> Plant Manager</p>
      <p>Business impact: delayed procurement may extend downtime and restrict production recovery.</p>
    </div>
  `).join("") : `<div class="empty-state compact">No procurement blockers detected for the selected risk set.</div>`;
}

function renderExecutiveReportPreview(data) {
  if (!data || !els.executiveReportPreview) return;
  const decision = data?.executive_decision_summary || {};
  const impact = data?.failure_cost_impact || {};
  const generatedAt = new Date().toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
  const riskLevel = state.report?.risk?.level || "High";
  els.executiveReportPreview.innerHTML = `
    <div class="report-summary-preview">
      <div class="report-summary-main">
        <span>Executive Summary Preview</span>
        <strong>${escapeHtml(decision?.current_top_plant_risk || "Plant maintenance risk")}</strong>
        <p>${escapeHtml(decision?.recommended_maintenance_strategy || "Review current maintenance strategy and approve recommended intervention.")}</p>
      </div>
      <div class="report-summary-grid">
        ${kpiCard("Risk Level", riskLevel, decision?.asset || "Selected asset")}
        ${kpiCard("Financial Impact", money(firstDefined(impact?.total_risk_exposure_inr, impact?.total_business_impact_inr, impact?.production_loss_inr, 0)), "Production and maintenance exposure")}
        ${kpiCard("Recommended Action", decision?.recommended_maintenance_strategy || "Approve intervention", "Leadership decision")}
        ${kpiCard("Generated Timestamp", generatedAt, "Report preview time")}
      </div>
    </div>
  `;
  renderRoiDecisionCard(els.executiveReportPreview, data?.failure_cost_impact);
}

function renderTeamWorkload(rows) {
  els.teamWorkload.innerHTML = `
    <table><thead><tr><th>Engineer</th><th>Tasks</th><th>Open WO</th><th>Critical</th><th>Completion</th></tr></thead>
    <tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.engineer)}</td><td>${row.assigned_tasks}</td><td>${row.open_work_orders}</td><td>${row.critical_jobs}</td><td>${row.completion_rate}%</td></tr>`).join("")}</tbody></table>
  `;
}

function renderAuditTrail(rows) {
  els.auditTrail.innerHTML = rows.slice().reverse().map((row) => `
    <div class="audit-item"><strong>${escapeHtml(row.timestamp)}</strong><p>${escapeHtml(row.user)} ${escapeHtml(row.action)} - ${escapeHtml(row.equipment_id)} - ${escapeHtml(row.decision)}</p></div>
  `).join("");
}

function renderMobileFieldMode(data) {
  const fieldActions = Array.isArray(data.field_actions) ? data.field_actions : [];
  els.mobileFieldMode.innerHTML = `
    ${kpiCard("Equipment QR", data.equipment_qr, data.active_work_order_status)}
    <ul>${fieldActions.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>Not Available</li>"}</ul>
  `;
}

function renderCopilotPrompts() {
  const prompts = [
    "Generate Shutdown Recommendation",
    "Generate Maintenance Plan",
    "Generate Procurement Request",
    "Generate Shift Handover",
    "Generate Executive Report",
    "Generate Root Cause Analysis",
    "Generate Inspection Checklist",
    "Generate Reliability Assessment",
  ];
  if (!els.copilotPrompts) return;
  els.copilotPrompts.innerHTML = prompts.map((item) => `<button class="small-button copilot-prompt" type="button">${escapeHtml(item)}</button>`).join("");
  els.copilotPrompts.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.textContent || "";
      if (action.includes("Procurement")) switchModule("inventory-spares");
      if (action.includes("Handover") || action.includes("Maintenance Plan")) switchModule("maintenance-planning");
      if (action.includes("Executive Report")) switchModule("reports");
      if (action.includes("Reliability")) switchModule("asset-intelligence");
      if (action.includes("Root Cause") || action.includes("Inspection")) switchModule("asset-intelligence");
      sendChat(action);
    });
  });
}

function renderAgentExecution(execution) {
  if (!els.agentExecution) return;
  const steps = execution || [];
  const timeline = [
    ["Retriever Agent", steps[0], "Asset context, manuals, SOPs, and live condition evidence retrieved"],
    ["Diagnosis Agent", steps[1], "Probable fault and sensor breach pattern evaluated"],
    ["Root Cause Agent", steps[3], "Likely root causes ranked against evidence and failure history"],
    ["Maintenance Planner Agent", steps[6], "Inspection sequence and corrective maintenance plan prepared"],
    ["Inventory Agent", steps[5], "Spare availability, lead time, and procurement risk checked"],
    ["Executive Agent", steps[7], "Decision brief, priority, owner, and approvals prepared"],
  ];
  els.agentExecution.innerHTML = timeline
    .map(([label, source, detail], index) => `
      <div class="timeline-step investigation-step">
        <div class="timeline-step-head">
          <strong><span class="step-check" aria-hidden="true">&#10003;</span>${escapeHtml(label)}</strong>
          <span class="pill low">${escapeHtml(source?.status || "completed")}</span>
        </div>
        <div class="progress-track"><span style="width:${Math.round(((index + 1) / timeline.length) * 100)}%"></span></div>
        <p>${escapeHtml(detail)}</p>
        <small>${escapeHtml(timeOnly(source?.completed_at))} / duration ${escapeHtml(stepDuration(source))}</small>
      </div>
    `)
    .join("");
}

function investigationProgressStages() {
  return [
    "Investigation Started",
    "Retriever Agent",
    "Diagnosis Agent",
    "Root Cause Agent",
    "Maintenance Planner Agent",
    "Inventory Agent",
    "Executive Agent",
    "Investigation Complete",
  ];
}

function renderInvestigationProgress(activeIndex = 0, complete = false, startedAt = null) {
  if (!els.agentExecution) return;
  const stages = investigationProgressStages();
  const elapsed = startedAt ? `${((performance.now() - startedAt) / 1000).toFixed(1)}s` : "—";
  els.agentExecution.innerHTML = `
    <div class="investigation-progress-card">
      <div class="investigation-progress-head">
        <span>AI Investigation Progress</span>
        <strong>${complete ? "Investigation Complete" : stages[Math.min(activeIndex, stages.length - 1)]}</strong>
        <small>Execution duration ${escapeHtml(elapsed)}</small>
      </div>
      <div class="investigation-progress-list">
        ${stages.map((stage, index) => {
          const done = complete || index < activeIndex;
          const active = !complete && index === activeIndex;
          return `
            <div class="${done ? "done" : ""} ${active ? "active" : ""}">
              <b>${done ? "✓" : active ? "•" : ""}</b>
              <span>${escapeHtml(stage)}</span>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function startInvestigationProgress() {
  if (state.investigationProgressTimer) {
    clearInterval(state.investigationProgressTimer);
    state.investigationProgressTimer = null;
  }
  let activeIndex = 0;
  const startedAt = performance.now();
  renderInvestigationProgress(activeIndex, false, startedAt);
  state.investigationProgressTimer = setInterval(() => {
    activeIndex = Math.min(activeIndex + 1, investigationProgressStages().length - 2);
    renderInvestigationProgress(activeIndex, false, startedAt);
  }, 700);
  return {
    complete() {
      if (state.investigationProgressTimer) clearInterval(state.investigationProgressTimer);
      state.investigationProgressTimer = null;
      renderInvestigationProgress(investigationProgressStages().length - 1, true, startedAt);
    },
    fail() {
      if (state.investigationProgressTimer) clearInterval(state.investigationProgressTimer);
      state.investigationProgressTimer = null;
    },
  };
}

function timeOnly(value) {
  return value ? String(value).split("T").pop() : "-";
}

function stepDuration(step) {
  if (!step?.started_at || !step?.completed_at) return "<1s";
  const started = new Date(step.started_at);
  const completed = new Date(step.completed_at);
  const ms = Math.max(0, completed - started);
  return ms < 1000 ? "<1s" : `${(ms / 1000).toFixed(1)}s`;
}

function renderReasoningTrace(trace) {
  if (!trace || !els.reasoningTrace) return;
  const retrieved = trace.retrieved_context || [];
  const sensor = trace.observed_evidence || [];
  const manuals = retrieved.filter((item) => item.toLowerCase().includes("manual"));
  const sops = retrieved.filter((item) => item.toLowerCase().includes("sop"));
  const history = retrieved.filter((item) => item.toLowerCase().includes("history") || item.toLowerCase().includes("fh-"));
  const group = (title, items) => `
    <div class="reasoning-group">
      <strong>${escapeHtml(title)}</strong>
      <ul>${(items.length ? items : ["No direct evidence recorded for this category."]).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
  els.reasoningTrace.innerHTML = `
    <div class="evidence-grid">
      ${group("Manual References", manuals)}
      ${group("SOP References", sops)}
      ${group("Historical Failures", history)}
      ${group("Sensor Evidence", sensor)}
    </div>
    ${group("Reasoning Summary", trace.reasoning || [])}
    <div class="reasoning-confidence">
      <strong>Diagnosis Confidence</strong>
      <span>${escapeHtml(trace.diagnosis_confidence)}%</span>
    </div>
  `;
}

function renderSelectedAsset() {
  const item = selectedEquipment();
  if (!item) return;
  els.assetName.textContent = assetDisplayName(item);
  els.assetAlert.textContent = `${assetDisplayId(item)} - ${assetDisplayAlert(item)}`;
}

function renderScenarioInputs() {
  const item = selectedEquipment();
  if (!item) return;
  if (!els.scenarioTemperature || !els.scenarioVibration || !els.scenarioCurrent || !els.scenarioHydraulic) return;
  els.scenarioTemperature.value = item.temperature_c;
  els.scenarioVibration.value = item.vibration_mm_s;
  els.scenarioCurrent.value = item.motor_current_a;
  els.scenarioHydraulic.value = item.hydraulic_pressure_bar;
}

function sparePartName(item = {}) {
  return firstDefined(item.part, item.part_name, item.name, item.part_id, "Unknown Spare");
}

function sparePartId(item = {}) {
  return firstDefined(item.part_id, item.spare_id, item.item_code, item.part_no, item.part_number, "SPARE");
}

function spareStock(item = {}) {
  return safeNumber(firstDefined(item.current_stock, item.available_qty, item.stock, item.qty), 0);
}

function spareMinStock(item = {}) {
  return safeNumber(firstDefined(item.min_stock, item.reorder_level, 2), 2);
}

function spareLeadTime(item = {}) {
  return safeNumber(item.lead_time_days, 0);
}

function spareCost(item = {}) {
  const estimated = firstDefined(item.estimated_cost_inr, item.unit_cost_inr, item.unit_cost, item.cost_inr);
  if (estimated !== undefined) return safeNumber(estimated, 0);
  const lead = spareLeadTime(item);
  const name = String(sparePartName(item)).toLowerCase();
  if (name.includes("bearing")) return 85000;
  if (name.includes("gear") || name.includes("mandrel")) return 185000;
  if (name.includes("motor") || name.includes("winding")) return 250000;
  return Math.max(12000, lead * 2400);
}

function spareAsset(item = {}) {
  const equipmentId = firstDefined(item.equipment_id, item.asset_id);
  return state.assetMaster.find((asset) => asset.equipment_id === equipmentId || asset.id === equipmentId)
    || state.equipment.find((asset) => asset.equipment_id === equipmentId || asset.id === equipmentId)
    || { equipment_id: equipmentId, asset_name: item.asset_name || equipmentId, type: "Plant Asset" };
}

function spareStatus(item = {}) {
  const stock = spareStock(item);
  const minStock = spareMinStock(item);
  if (stock <= 0) return "out";
  if (stock <= minStock || stock <= 2) return "low";
  return "in";
}

function spareStatusLabel(status, stock) {
  if (status === "out") return "OUT OF STOCK";
  if (status === "low") return `LOW STOCK (${stock})`;
  return `IN STOCK (${stock})`;
}

function renderInventoryTypeOptions() {
  if (!els.inventoryTypeFilter) return;
  const selected = els.inventoryTypeFilter.value || "all";
  const types = Array.from(new Set((state.spares || []).map((item) => spareAsset(item).type || spareAsset(item).area || "Plant Asset"))).sort();
  els.inventoryTypeFilter.innerHTML = [
    `<option value="all">All Asset Types</option>`,
    ...types.map((type) => `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`),
  ].join("");
  els.inventoryTypeFilter.value = types.includes(selected) ? selected : "all";
}

function renderSpares() {
  if (!els.sparesList) return;
  const query = String(els.inventorySearch?.value || "").toLowerCase().trim();
  const stockFilter = els.inventoryStockFilter?.value || "all";
  const typeFilter = els.inventoryTypeFilter?.value || "all";
  const sortBy = els.inventorySort?.value || "default";
  const spares = (state.spares || []).map((item, index) => {
    const asset = spareAsset(item);
    const stock = spareStock(item);
    const leadTime = spareLeadTime(item);
    const cost = spareCost(item);
    const status = spareStatus(item);
    const health = safeNumber(firstDefined(asset.health_score, asset.health, 72), 72);
    const riskScore = (status === "out" ? 45 : status === "low" ? 25 : 8) + Math.min(30, leadTime / 2) + Math.max(0, 70 - health) / 2;
    return { ...item, _index: index, _asset: asset, _stock: stock, _leadTime: leadTime, _cost: cost, _status: status, _health: health, _riskScore: riskScore };
  });

  const totalValue = spares.reduce((sum, item) => sum + item._cost * Math.max(1, item._stock), 0);
  const outCount = spares.filter((item) => item._status === "out").length;
  const lowCount = spares.filter((item) => item._status === "low").length;

  if (els.inventoryKpis) {
    els.inventoryKpis.innerHTML = [
      kpiCard("Cataloged Spares", spares.length, "Parts tracked in stores"),
      kpiCard("Out of Stock Spares", outCount, "Immediate procurement blockers"),
      kpiCard("Low Stock Spares", lowCount, "Below minimum or watch threshold"),
      kpiCard("On-Hand Value", money(totalValue), "Estimated inventory value"),
    ].join("");
  }

  const blockers = spares
    .filter((item) => item._status !== "in" || item._leadTime >= 30)
    .sort((a, b) => b._riskScore - a._riskScore)
    .slice(0, 3);
  if (els.inventoryRiskAlert) {
    const exposure = blockers.reduce((sum, item) => sum + item._cost + item._leadTime * 10000, 0);
    els.inventoryRiskAlert.innerHTML = blockers.length ? `
      <div class="risk-alert-icon">!</div>
      <div class="risk-alert-content">
        <span>Critical Spares Shortage Risk Alert</span>
        <strong>Production Downtime Risk Exposure: ${money(exposure)}</strong>
        <p>There are ${escapeHtml(blockers.length)} degraded or critical plant assets missing matching spare parts. Production losses accumulate daily during parts lead-time.</p>
        <div class="inventory-risk-table">
          <div class="inventory-risk-head"><b>Degraded Asset</b><b>Health</b><b>Missing Spare Part</b><b>Lead Time</b><b>Risk Valuation</b><b>Action</b></div>
          ${blockers.map((item) => `
            <div class="inventory-risk-row">
              <b>${escapeHtml(assetDisplayName(item._asset))}<small>${escapeHtml(assetDisplayId(item._asset))}</small></b>
              <span class="stock-badge critical">${escapeHtml(item._health.toFixed(1))}%</span>
              <b>${escapeHtml(sparePartName(item))}<small>${escapeHtml(sparePartId(item))} / ${money(item._cost)}</small></b>
              <strong>${escapeHtml(item._leadTime)} Days</strong>
              <strong>${money(item._cost + item._leadTime * 10000)}</strong>
              <button class="small-button danger-button" type="button">Expedite PO</button>
            </div>
          `).join("")}
        </div>
      </div>
    ` : `<div class="empty-state compact">No critical spare exposure detected.</div>`;
  }

  let filtered = spares.filter((item) => {
    const haystack = [
      sparePartName(item),
      sparePartId(item),
      assetDisplayName(item._asset),
      assetDisplayId(item._asset),
      item.criticality,
      item._asset.type,
      item._asset.area,
    ].join(" ").toLowerCase();
    if (query && !haystack.includes(query)) return false;
    if (stockFilter !== "all" && item._status !== stockFilter) return false;
    const type = item._asset.type || item._asset.area || "Plant Asset";
    if (typeFilter !== "all" && type !== typeFilter) return false;
    return true;
  });

  if (sortBy === "risk") filtered.sort((a, b) => b._riskScore - a._riskScore);
  if (sortBy === "lead") filtered.sort((a, b) => b._leadTime - a._leadTime);
  if (sortBy === "stock") filtered.sort((a, b) => a._stock - b._stock);
  if (sortBy === "value") filtered.sort((a, b) => b._cost - a._cost);

  els.sparesList.innerHTML = filtered.length ? filtered
    .slice(0, 60)
    .map((item) => {
      const statusClass = item._status === "out" ? "critical" : item._status === "low" ? "medium" : "low";
      return `
        <div class="spare-catalog-card spare-item">
          <div class="spare-card-head">
            <span>${escapeHtml(item._asset.type || item._asset.area || "Plant Asset")}</span>
            <strong>${escapeHtml(sparePartName(item))}</strong>
            <small>Part No: ${escapeHtml(sparePartId(item))}</small>
          </div>
          <div class="spare-card-body">
            <p><span>Stock Level:</span><b class="stock-badge ${statusClass}">${escapeHtml(spareStatusLabel(item._status, item._stock))}</b></p>
            <p><span>Unit Cost:</span><b>${money(item._cost)}</b></p>
            <p><span>Standard Lead Time:</span><b>${escapeHtml(item._leadTime)} Days</b></p>
            <p><span>Linked Asset:</span><b>${escapeHtml(assetDisplayName(item._asset))}</b></p>
          </div>
          <button class="spare-po-button ${item._status === "out" ? "active" : ""}" type="button">+ 1-Click Purchase Order</button>
        </div>
      `;
    })
    .join("") : `<div class="empty-state compact">No spare parts match the current filters.</div>`;
}

function renderAlerts(alerts) {
  state.alerts = alerts;
  if (!els.alertList) return;
  els.alertList.innerHTML = alerts
    .map((raw) => {
      const item = normalizeEquipmentRecord(raw);
      return `
      <div class="alert-item">
        <div>
          <strong>${escapeHtml(assetDisplayName(item))}</strong>
          <p>${escapeHtml(assetDisplayId(item))} - Score ${escapeHtml(item.risk_score)}</p>
        </div>
        <span class="${pillClass(item.risk_level)}">${escapeHtml(item.risk_level)}</span>
      </div>
    `;
    })
    .join("");
}

function renderRoleNotifications(items = state.roleNotifications) {
  state.roleNotifications = items;
  if (!els.roleNotifications) return;
  els.roleNotifications.innerHTML = items
    .slice(0, 10)
    .map((item) => `
      <div class="role-item">
        <div>
          <strong>${escapeHtml(item.role)}</strong>
          <p>${escapeHtml(item.message)}</p>
        </div>
        <span class="${pillClass(item.priority)}">${escapeHtml(item.priority)}</span>
      </div>
    `)
    .join("");
}

function renderKnowledgeCenter(data = state.knowledgeSources) {
  if (!data) return;
  const groups = [
    ["Indexed Manuals", data.knowledge_documentation_inputs.filter((item) => item.name.includes("Manual") || item.name.includes("manual"))],
    ["SOP Repository", data.knowledge_documentation_inputs.filter((item) => item.name.includes("SOP"))],
    ["Historical Failure Records", data.knowledge_documentation_inputs.filter((item) => item.name.includes("Historical"))],
    ["Sensor Event Repository", data.condition_monitoring_inputs],
    ["Work Order History", [{ name: "Saved work orders", records: "live", status: "available" }]],
    ["Spare Inventory Knowledge Base", data.knowledge_documentation_inputs.filter((item) => item.name.includes("Spare"))],
  ];
  const totalDocs = groups.reduce((sum, [, items]) => sum + items.reduce((inner, item) => inner + Number(item.records === "live" ? 1 : item.records || 0), 0), 0);
  const chunks = Math.max(276, totalDocs * 34 + (data.ingested_runtime_inputs || []).length * 3);
  if (els.knowledgeStats) {
    els.knowledgeStats.innerHTML = [
      kpiCard("Documents Ingested", totalDocs || groups.length, "Enterprise knowledge sources"),
      kpiCard("Text Chunks Created", chunks, "Searchable RAG segments"),
      kpiCard("Vector Embeddings", "Active", "Semantic retrieval enabled"),
      kpiCard("Last Index Refresh", "2 min ago", "Live indexing status"),
    ].join("");
  }
  els.knowledgeCenter.innerHTML = groups
    .map(([title, items], index) => {
      const count = items.reduce((sum, item) => sum + Number(item.records === "live" ? 1 : item.records || 0), 0);
      const confidence = Math.max(82, 96 - index * 2);
      return `
      <div class="knowledge-card enterprise-knowledge-card">
        <div class="knowledge-card-title">
          <strong>${escapeHtml(title)}</strong>
          <span>${confidence}%</span>
        </div>
        <div class="knowledge-meta">
          <span>${escapeHtml(count || items.length)} documents</span>
          <span>Indexed</span>
          <span>${confidence}% retrieval confidence</span>
        </div>
        ${items.length ? items.map((item) => `
          <p>${escapeHtml(item.name)} - ${escapeHtml(item.records)} records - ${escapeHtml(item.status || "indexed")}</p>
        `).join("") : "<p>No indexed records available.</p>"}
      </div>
    `;
    })
    .join("");
  renderIngestedInputs(data.ingested_runtime_inputs || []);
  renderSensorEventRepository(data.ingested_runtime_inputs || []);
}

function renderIngestedInputs(items) {
  els.ingestedInputs.innerHTML = items.length
    ? items.slice().reverse().map((item) => `
      <div class="trace-item">
        <strong>${escapeHtml(item.input_type)} / ${escapeHtml(item.equipment_id)} / ${escapeHtml(item.record_id)}</strong>
        <p>${escapeHtml(item.content)}</p>
      </div>
    `).join("")
    : `<div class="empty-state compact">Runtime inputs will appear here after ingestion.</div>`;
}

function renderSensorEventRepository(items) {
  const events = items.filter((item) => ["sensor_summary", "anomaly_alert", "process_indicator", "fault_message"].includes(item.input_type));
  els.sensorEventRepository.innerHTML = events.length
    ? events.slice().reverse().map((item) => `
      <div class="trace-item">
        <strong>${escapeHtml(item.input_type)} / ${escapeHtml(item.equipment_id)} / ${escapeHtml(item.record_id)}</strong>
        <p>${escapeHtml(item.content)}</p>
      </div>
    `).join("")
    : `<div class="empty-state compact">Sensor events and runtime alerts will appear here after ingestion.</div>`;
}

function renderChat() {
  if (!els.chatWindow) return;
  const asset = selectedEquipment();
  els.chatWindow.innerHTML = state.chatHistory.length
    ? state.chatHistory.map((item) => renderChatMessage(item)).join("")
    : `<div class="empty-state compact">New conversation for ${escapeHtml(assetDisplayId(asset || {}))}. Ask a follow-up question or choose a quick action.</div>`;
  els.chatWindow.scrollTop = els.chatWindow.scrollHeight;
}

function memoryKey(assetId = state.selectedEquipmentId) {
  return `maintenance-wizard-memory-${assetId}`;
}

function loadCopilotMemory(assetId = state.selectedEquipmentId) {
  try {
    const saved = JSON.parse(localStorage.getItem(memoryKey(assetId)) || "{}");
    state.previousInvestigations[assetId] = saved;
    state.chatHistory = Array.isArray(saved.messages)
      ? saved.messages.filter((item) => item.role !== "assistant").slice(-20)
      : [];
    state.lastAssistantText = "";
  } catch {
    state.chatHistory = [];
    state.lastAssistantText = "";
  }
}

function saveCopilotMemory(extra = {}, assetId = state.selectedEquipmentId) {
  const existing = state.previousInvestigations[assetId] || {};
  const payload = {
    ...existing,
    ...extra,
    selected_asset: assetId,
    messages: state.chatHistory.filter((item) => item.role !== "assistant").slice(-20),
    updated_at: new Date().toISOString(),
  };
  state.previousInvestigations[assetId] = payload;
  try {
    localStorage.setItem(memoryKey(assetId), JSON.stringify(payload));
  } catch {
    return;
  }
}

function renderChatMessage(item) {
  const speaker = item.role === "user" ? "Engineer" : "Maintenance Wizard AI";
  const status = item.status === "processing" ? `<div class="typing-indicator">${escapeHtml(item.content)}</div>` : "";
  const typing = item.status === "typing" ? `<div class="typing-indicator">Maintenance Wizard AI is typing...</div>` : "";
  const timing = item.timing ? renderTimingStrip(item.timing) : "";
  const initials = item.role === "user" ? "ME" : "AI";
  const timestamp = item.timestamp || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return `
    <div class="chat-turn ${escapeHtml(item.role)}">
      <div class="chat-avatar" aria-hidden="true">${escapeHtml(initials)}</div>
      <div class="chat-message-body">
        <div class="chat-meta">
          <strong>${escapeHtml(speaker)}</strong>
          <span>${escapeHtml(timestamp)}</span>
        </div>
        ${status || `<p>${escapeHtml(item.content)}</p>`}
        ${typing}
        ${timing}
        ${item.card ? renderResponseCard(item.card) : ""}
        ${item.evidence ? renderEvidenceBlock(item.evidence) : ""}
      </div>
    </div>
  `;
}

function renderTimingStrip(timing = {}) {
  const items = [
    ["Retrieval", msValue(timing, "retrieval_ms", "retrieval_time")],
    ["Rerank", msValue(timing, "rerank_ms", "rerank_time", "reranking_time_ms")],
    ["LLM", msValue(timing, "llm_ms", "llm_time", "latency_ms")],
    ["Total", msValue(timing, "total_ms", "total_request_ms", "workflow_ms", "workflow_time")],
  ];
  return `
    <div class="timing-strip">
      ${items.map(([label, value]) => `<span>${escapeHtml(label)} <b>${formatMs(value)}</b></span>`).join("")}
    </div>
  `;
}

function renderInitialSkeletons() {
  const skeletonCards = (count = 4) => Array.from({ length: count }, () => `
    <div class="skeleton-card">
      <i></i>
      <strong></strong>
      <span></span>
    </div>
  `).join("");
  if (els.executiveSummary) els.executiveSummary.innerHTML = skeletonCards(5);
  if (els.plantCommandKpis) els.plantCommandKpis.innerHTML = skeletonCards(6);
  if (els.costImpact) els.costImpact.innerHTML = skeletonCards(4);
  if (els.digitalTwin) els.digitalTwin.innerHTML = `
    <div class="skeleton-twin">
      <i></i>
      <span></span>
      <span></span>
      <span></span>
    </div>
  `;
  if (els.agentExecution) {
    els.agentExecution.innerHTML = `
      <div class="skeleton-timeline">
        ${["Retrieval", "Diagnosis", "RCA", "Planning", "Inventory", "Executive Summary"].map((label) => `
          <div><b>${escapeHtml(label)}</b><span></span></div>
        `).join("")}
      </div>
    `;
  }
}

function nowStamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function messageId() {
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function streamAssistantMessage(requestId, message, fullText, card, evidence) {
  const request = activeChatRequest;
  if (!request || request.id !== requestId || !request.backendSucceeded || request.streamCancelled) {
    console.log("STREAM_CANCELLED", { requestId, reason: request?.cancelReason || "inactive_request" });
    return false;
  }
  console.log("STREAM_STARTED", { requestId, timestamp: new Date().toISOString() });
  message.status = "typing";
  message.content = "";
  message.card = null;
  message.evidence = null;
  renderChat();
  const chunks = String(fullText || "")
    .split(/(\n+)/)
    .filter((chunk) => chunk.length);
  for (const chunk of chunks) {
    if (!isActiveChatRequest(requestId) || !request.backendSucceeded || !(await verifyBackendForStream(requestId))) {
      message.status = "cancelled";
      message.content = "Backend Offline";
      message.card = null;
      message.evidence = null;
      console.log("BACKEND_UNAVAILABLE", { requestId, stage: "stream_chunk" });
      renderChat();
      return false;
    }
    message.content += chunk;
    renderChat();
    await Promise.resolve();
  }
  if (!isActiveChatRequest(requestId)) {
    console.log("STREAM_CANCELLED", { requestId, reason: "superseded" });
    return false;
  }
  message.status = "complete";
  message.card = card;
  message.evidence = evidence;
  state.lastAssistantText = fullText;
  console.log("STREAM_COMPLETED", { requestId, timestamp: new Date().toISOString() });
  renderChat();
  return true;
}

function buildEvidence(traceability = []) {
  const evidence = { manuals: [], history: [], sops: [] };
  traceability.forEach((item) => {
    const source = `${item.source || ""} ${item.title || ""}`.toLowerCase();
    if (source.includes("manual")) evidence.manuals.push(item.title);
    if (source.includes("history") || source.includes("fh-")) evidence.history.push(item.title);
    if (source.includes("sop")) evidence.sops.push(item.title);
  });
  return {
    manuals: [...new Set(evidence.manuals)].slice(0, 2),
    history: [...new Set(evidence.history)].slice(0, 3),
    sops: [...new Set(evidence.sops)].slice(0, 2),
  };
}

function structuredActionType(message) {
  const text = String(message).toLowerCase();
  if (text.includes("shutdown")) return "Shutdown Recommendation";
  if (text.includes("maintenance plan")) return "Maintenance Plan";
  if (text.includes("procurement")) return "Procurement Request";
  if (text.includes("handover")) return "Shift Handover";
  if (text.includes("executive report")) return "Executive Report";
  if (text.includes("root cause")) return "Root Cause Analysis";
  if (text.includes("inspection")) return "Inspection Checklist";
  if (text.includes("reliability")) return "Reliability Assessment";
  return "";
}

function actionSpecialist(type) {
  return {
    "Shutdown Recommendation": "Operations Supervisor",
    "Maintenance Plan": "Maintenance Planner",
    "Procurement Request": "Procurement Specialist",
    "Shift Handover": "Shift Coordinator",
    "Executive Report": "Executive Advisor",
    "Root Cause Analysis": "Root Cause Investigator",
    "Inspection Checklist": "Field Technician Lead",
    "Reliability Assessment": "Reliability Engineer",
  }[type] || "Maintenance Copilot";
}

function actionPrompt(type, message, asset) {
  const prompts = {
    "Shutdown Recommendation": "Act as an operations supervisor. Decide whether the asset can continue running, maximum safe runtime, shutdown triggers, escalation timeline, and recommended operating mode.",
    "Maintenance Plan": "Act as a maintenance planner. Build an execution plan with task list, resources, technician assignments, duration estimates, planned schedule, and safety requirements.",
    "Procurement Request": "Act as a procurement specialist. Identify required spare parts, quantities, stock, lead time, vendor recommendation, priority, and estimated cost.",
    "Shift Handover": "Act as a shift coordinator. Generate open critical assets, completed actions, pending actions, spare risks, safety concerns, and next shift recommendations.",
    "Executive Report": "Act as an executive advisor. Summarize financial impact, production impact, risk exposure, downtime estimate, business recommendation, and leadership decision.",
    "Root Cause Analysis": "Act as a root cause investigator. Produce 5 Why analysis, fishbone categories, contributing factors, historical comparison, confidence, and corrective actions.",
    "Inspection Checklist": "Act as a field technician lead. Produce inspection steps, measurement points, pass/fail criteria, safety checks, and required tools.",
    "Reliability Assessment": "Act as a reliability engineer. Assess asset health score, MTBF, MTTR, failure probability, remaining useful life, reliability trend, and reliability actions.",
  };
  return `${prompts[type] || "Act as an industrial maintenance copilot."}\n${assetContextPrompt()}\n\nUser Question:\n${message}\nSelected asset: ${assetDisplayId(asset || {})} - ${assetDisplayName(asset || {})}`;
}

function selectedSparesForReport(report) {
  const equipmentId = report?.equipment?.equipment_id || state.selectedEquipmentId;
  return state.spares.filter((item) => item.equipment_id === equipmentId);
}

function blockedSparesForReport(report) {
  return selectedSparesForReport(report).filter((item) => Number(item.available_qty) <= 0 || Number(item.lead_time_days) >= 14);
}

function breachLabels(report) {
  return (report?.diagnosis?.condition_breaches || []).map((item) => `${safeValue(item?.metric)} ${safeValue(item?.value)} (${safeValue(item?.level)})`);
}

function estimateCostForSpare(spare) {
  const base = String(spare.part || "").toLowerCase().includes("mandrel") ? 320000 : String(spare.part || "").toLowerCase().includes("bearing") ? 90000 : 65000;
  return base * Math.max(1, Number(spare.available_qty) <= 0 ? 2 : 1);
}

function buildResponseCard(type, report) {
  if (!type || !report) return null;
  report = normalizeReport(report);
  const riskLevel = safeValue(report?.risk?.level, "medium");
  const asset = `${assetDisplayId(report?.equipment)} - ${assetDisplayName(report?.equipment)}`;
  const risk = `${riskLevel} / score ${safeValue(report?.risk?.score, 0)}`;
  const actions = (report?.recommendations || []).slice(0, 5);
  const causes = report?.diagnosis?.probable_root_causes || [];
  const breaches = breachLabels(report);
  const blockedSpares = blockedSparesForReport(report);
  const approvals = riskLevel === "critical"
    ? ["Maintenance Lead", "Production Supervisor", "Safety Officer"]
    : ["Maintenance Lead", "Shift Supervisor"];
  const confidence = Math.min(96, 78 + causes.length * 4 + breaches.length * 3);
  const common = { title: type, specialist: actionSpecialist(type), asset, approvals, confidence, roi: roiInputFromCostImpact(selectedAssetFinancialImpact()) };

  if (type === "Shutdown Recommendation") {
    const roi = common.roi;
    return {
      ...common,
      variant: "shutdown",
      kpis: [
        ["Can Continue Running", riskLevel === "critical" ? "No" : "Restricted", "Based on current risk and threshold breaches"],
        ["Maximum Safe Runtime", riskLevel === "critical" ? "0-2 h" : "4-8 h", "Before stop-window decision"],
        ["Operating Mode", riskLevel === "critical" ? "Controlled shutdown" : "Restricted operation", "Production supervisor decision"],
        ["Shutdown Cost", money(roi.shutdownCost), "Controlled intervention estimate"],
        ["Potential Failure Cost", money(roi.potentialFailureCost), "Failure progression exposure"],
        ["Expected Savings", money(roi.savings), "Avoided loss after shutdown cost"],
        ["ROI", `${roi.roi}%`, "Financial return on shutdown decision"],
      ],
      sections: [
        ["Shutdown Trigger Conditions", breaches.length ? breaches : ["Any repeat trip alarm", "Rapid increase in vibration/current", "Pressure below operating band"]],
        ["Risk Escalation Timeline", ["Immediate: restrict operation", "+2 h: shutdown if trend persists", "+4 h: production impact likely without intervention"]],
        ["Decision Summary", [`${assetDisplayName(report?.equipment)} should ${riskLevel === "critical" ? "not continue normal operation" : "continue only under restriction"}. ${actions[0] || "Escalate to maintenance review."}`]],
      ],
    };
  }

  if (type === "Maintenance Plan") {
    return {
      ...common,
      variant: "maintenance",
      kpis: [
        ["Duration Estimate", riskLevel === "critical" ? "6 h" : "4 h", "Planned execution window"],
        ["Technicians", riskLevel === "critical" ? "5" : "3", "Mechanical, electrical, and safety coverage"],
        ["Safety Level", riskLevel === "critical" ? "High-energy isolation" : "Standard isolation", "Permit requirement"],
      ],
      sections: [
        ["Task List", actions],
        ["Technician Assignments", ["Mechanical lead: root-cause inspection", "Electrical technician: sensor and PLC validation", "Safety officer: isolation and permit control"]],
        ["Planned Schedule", ["T+0: approve stop window", "T+1 h: isolate and inspect", "T+3 h: replace/adjust component", "T+5 h: restart validation"]],
      ],
    };
  }

  if (type === "Procurement Request") {
    const parts = blockedSpares.length ? blockedSpares : selectedSparesForReport(report).slice(0, 2);
    return {
      ...common,
      variant: "procurement",
      kpis: [
        ["Parts Required", parts.length, "Spare lines for purchasing"],
        ["Highest Lead Time", `${Math.max(...parts.map((item) => Number(item.lead_time_days || 0)), 0)} days`, "Procurement exposure"],
        ["Estimated Cost", money(parts.reduce((sum, item) => sum + estimateCostForSpare(item), 0)), "Budgetary estimate"],
      ],
      sections: [
        ["Required Parts", parts.map((item) => `${item.part}: qty ${Number(item.available_qty) <= 0 ? 2 : 1}, stock ${item.available_qty}, lead ${item.lead_time_days} days`)],
        ["Vendor Recommendation", parts.map((item) => `${item.part}: approved OEM or emergency local equivalent if lead time exceeds 14 days`)],
        ["Approval Route", ["Maintenance Lead -> Stores Controller -> Procurement Owner -> Plant Manager"]],
      ],
    };
  }

  if (type === "Root Cause Analysis") {
    return {
      ...common,
      variant: "rca",
      kpis: [
        ["Confidence", `${Math.min(94, 72 + causes.length * 7 + breaches.length * 3)}%`, "Based on evidence match"],
        ["Contributing Factors", causes.length + breaches.length, "Detected investigation factors"],
        ["Historical Match", (report?.traceability || []).filter((item) => String(item?.source).includes("history")).length, "Related cases"],
      ],
      sections: [
        ["5 Why Analysis", [
          `Why 1: ${assetDisplayAlert(report?.equipment)} was triggered.`,
          `Why 2: ${breaches[0] || "condition indicator"} moved outside normal range.`,
          `Why 3: ${causes[0] || "component degradation"} is the most likely degradation mode.`,
          "Why 4: preventive action did not remove the recurring failure path.",
          "Why 5: inspection interval, spare readiness, or operating stress needs correction.",
        ]],
        ["Fishbone Categories", ["Machine: component wear or leakage", "Method: inspection interval and SOP adherence", "Material: spare availability", "Measurement: sensor validation", "Environment: hot rolling duty cycle"]],
        ["Corrective Actions", actions],
      ],
    };
  }

  if (type === "Executive Report") {
    return {
      ...common,
      variant: "executive",
      kpis: [
        ["Financial Impact", riskLevel === "critical" ? "High" : "Moderate", "Cost exposure"],
        ["Production Impact", report?.priority?.urgency, "Operating impact"],
        ["Downtime Estimate", riskLevel === "critical" ? "6 h" : "4 h", "Planning estimate"],
      ],
      sections: [
        ["Executive Summary", [`${assetDisplayName(report?.equipment)} has ${risk} from ${safeValue(report?.diagnosis?.probable_fault)}.`]],
        ["Business Recommendation", [actions[0] || "Approve maintenance intervention.", blockedSpares.length ? "Approve spare escalation due to procurement risk." : "Proceed with planned maintenance resources."]],
        ["Risk Exposure", [`Condition drivers: ${breaches.join(", ") || "condition degradation"}`, `Spare blockers: ${blockedSpares.map((item) => item.part).join(", ") || "none"}`]],
      ],
    };
  }

  if (type === "Reliability Assessment") {
    const health = safeNumber(report?.prediction?.health_index, 0);
    return {
      ...common,
      variant: "reliability",
      kpis: [
        ["Asset Health Score", `${health}%`, "Digital health index"],
        ["MTBF", "428 h", "Fleet benchmark"],
        ["MTTR", riskLevel === "critical" ? "6.2 h" : "4.8 h", "Expected repair time"],
        ["Failure Probability", riskLevel === "critical" ? "High" : "Medium", "Next risk window"],
      ],
      sections: [
        ["Remaining Useful Life", [report?.prediction?.rul_label || `${safeValue(report?.prediction?.estimated_remaining_useful_life_hours, 0)} h`, report?.prediction?.rul_explanation || report?.prediction?.method]],
        ["Reliability Trend", [health < 40 ? "Degrading rapidly" : health < 65 ? "Degraded and watchlisted" : "Stable with monitoring"]],
        ["Recommended Reliability Actions", ["Review PM interval", "Validate recurring failure modes", "Update spare min-max levels", "Add focused inspection route"]],
      ],
    };
  }

  if (type === "Inspection Checklist") {
    return {
      ...common,
      variant: "inspection",
      kpis: [
        ["Inspection Route", "Field execution", "Technician checklist"],
        ["Measurement Points", Math.max(3, breaches.length + 2), "Readings to verify"],
        ["Permit", riskLevel === "critical" ? "Required" : "Review", "Safety prerequisite"],
      ],
      sections: [
        ["Inspection Steps", ["Verify local gauge/sensor reading", "Inspect suspected component for leakage/wear", "Check alignment, lubrication, pressure, and electrical trend", "Record photos and actual measurements"]],
        ["Measurement Points", breaches.length ? breaches : ["Vibration", "Hydraulic pressure", "Motor current", "Temperature"]],
        ["Pass/Fail Criteria", ["Pass: readings return below warning limits for 30 minutes", "Fail: repeat alarm, abnormal noise, pressure loss, or visible component damage"]],
        ["Required Tools", ["Thermal scanner", "Vibration meter", "Pressure gauge", "Lockout/tagout kit", "Inspection camera"]],
      ],
    };
  }

  return {
    ...common,
    variant: "general",
    kpis: [["Risk", risk, "Current risk classification"]],
    sections: [["Recommended Actions", actions]],
  };
}

function buildAssistantText(message, data) {
  const report = normalizeReport(data?.report || state.report || {});
  const context = activeAssetContext();
  const reportAssetId = assetDisplayId(report?.equipment);
  const reportAssetName = assetDisplayName(report?.equipment);
  const asset = `${safe(context.asset_id, reportAssetId)} ${safe(context.asset_name, reportAssetName)}`;
  const activeAlert = safe(context.current_alert, assetDisplayAlert(report?.equipment));
  const causes = (report?.diagnosis?.probable_root_causes || []).join(", ") || "field confirmation pending";
  const firstAction = (report?.recommendations || [])[0] || "Escalate to maintenance review.";
  const assistantText = data?.turn?.assistant || data?.message || data?.response || data?.content || data?.answer || firstAction;
  const type = structuredActionType(message);
  const specialist = actionSpecialist(type);
  if (type) {
    return (
      `${specialist} workflow for ${asset}.\n` +
      `Purpose: ${type} using selected asset context only.\n` +
      `Selected asset context: health ${safe(context.health_score)}%, risk ${safe(context.risk_level)}, RUL ${safe(context.rul_days)}, alert ${activeAlert}.\n` +
      `Risk basis: ${safeValue(report?.risk?.level)} risk, score ${safeValue(report?.risk?.score, 0)}, active alert ${activeAlert}.\n` +
      `Primary decision: ${firstAction}`
    );
  }
  return (
    `For selected asset ${asset}, Maintenance Wizard reviewed the active alert ${activeAlert}, health ${safe(context.health_score)}%, risk ${safe(context.risk_level)}, RUL ${safe(context.rul_days)}, current condition data, historical failures, SOP context, and spare constraints.\n` +
    `${assistantText}\n` +
    `Most likely causes: ${causes}.\n` +
    `Recommended next step: ${firstAction}`
  );
}

function buildMemoryContext() {
  const memory = state.previousInvestigations[state.selectedEquipmentId] || {};
  return {
    selected_asset: state.selectedEquipmentId,
    previous_investigation: memory.previous_investigation || state.report?.diagnosis?.probable_fault || "",
    generated_reports: memory.generated_reports || [],
    root_causes_discussed: memory.root_causes_discussed || [],
  };
}

function renderResponseCard(card) {
  return `
    <div class="response-card ${escapeHtml(card.variant || "general")}">
      <div class="response-card-head">
        <div>
          <strong>${escapeHtml(card.title)}</strong>
          <p>${escapeHtml(card.specialist)} / ${escapeHtml(card.asset)}</p>
        </div>
        <div class="response-badges">
          <span class="pill low">Generated</span>
          <span class="confidence-badge">${escapeHtml(card.confidence || 88)}% Confidence</span>
        </div>
      </div>
      <div class="response-kpis">
        ${(card.kpis || []).map(([label, value, help]) => kpiCard(label, value, help)).join("")}
      </div>
      ${card.roi ? `
        <div class="response-roi-strip">
          <span class="roi-badge">${escapeHtml(card.roi.roi)}% ROI</span>
          <span class="savings-badge">${money(card.roi.savings)} Savings</span>
          <span>Shutdown ${money(card.roi.shutdownCost)}</span>
          <span>Failure ${money(card.roi.potentialFailureCost)}</span>
        </div>
      ` : ""}
      ${(card.sections || []).map(([title, items]) => `
        <div class="response-section">
          <span>${escapeHtml(title)}</span>
          <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      `).join("")}
      <div class="response-section approval-section">
        <span>Approvals Required</span>
        <p>${escapeHtml(card.approvals.join(", "))}</p>
      </div>
    </div>
  `;
}

function renderEvidenceBlock(evidence) {
  return `
    <div class="evidence-used">
      <strong>Evidence Used</strong>
      <p>Manual: ${escapeHtml(evidence.manuals.join(", ") || "Relevant asset manual")}</p>
      <p>Historical Failures: ${escapeHtml(evidence.history.join(", ") || "No close match")}</p>
      <p>SOP: ${escapeHtml(evidence.sops.join(", ") || "Relevant maintenance SOP")}</p>
    </div>
  `;
}

function metricLabel(metric) {
  return {
    temperature_c: "Temp C",
    vibration_mm_s: "Vibration",
    motor_current_a: "Current",
    hydraulic_pressure_bar: "Hydraulic",
  }[metric] || metric;
}

function renderLiveMonitor() {
  if (!state.liveMonitor || !els.liveMonitor) return;
  const asset = state.liveMonitor.assets.find((item) => item.equipment_id === state.selectedEquipmentId);
  if (!asset) return;
  const latest = asset.points[asset.points.length - 1];
  els.liveMonitor.innerHTML = state.liveMonitor.metrics
    .map((metric) => {
      const values = asset.points.map((point) => Number(point[metric]));
      const min = Math.min(...values);
      const max = Math.max(...values);
      const latestValue = Number(latest[metric]);
      const range = max - min || 1;
      const bars = values
        .map((value) => {
          const height = 22 + ((value - min) / range) * 58;
          return `<span style="height:${height.toFixed(1)}%"></span>`;
        })
        .join("");
      return `
        <div class="trend-card">
          <div class="trend-heading">
            <strong>${escapeHtml(metricLabel(metric))}</strong>
            <small>${escapeHtml(latestValue)}</small>
          </div>
          <div class="spark-bars">${bars}</div>
          <p>Range ${min.toFixed(1)} to ${max.toFixed(1)}</p>
        </div>
      `;
    })
    .join("");
}

function renderExecutiveSummary() {
  if (!els.executiveSummary) return;
  if (state.operationsCenter?.kpis?.length) {
    els.executiveSummary.innerHTML = state.operationsCenter.kpis
      .slice(0, 10)
      .map((item) => kpiCard(item.label, formatKpiValue(item), item.help))
      .join("");
    return;
  }
  if (!state.intelligence) return;
  const summary = state.intelligence.executive_summary;
  const top = summary.top_bottleneck || {};
  const items = [
    ["Plant Availability", `${Math.max(0, 100 - summary.critical_assets * 3.2).toFixed(1)}%`, "Estimated operating availability"],
    ["Critical Assets", summary.critical_assets, "Assets requiring immediate action"],
    ["Downtime Exposure", `${summary.downtime_exposure_minutes} min`, "Risk-weighted exposure estimate"],
    ["Spare Blockers", summary.spare_blockers, "Parts with zero stock or long lead"],
    ["Top Bottleneck", top.equipment_id || "-", top.equipment_name || "No active bottleneck"],
  ];
  els.executiveSummary.innerHTML = items
    .map(([label, value, help]) => `
      <div class="kpi-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        <small>${escapeHtml(help)}</small>
      </div>
    `)
    .join("");
}

function renderDigitalTwin() {
  if (!els.digitalTwin || !els.twinStage) return;
  if (!state.intelligence) {
    els.twinStage.textContent = "Pending";
    els.twinStage.className = "pill";
    els.digitalTwin.innerHTML = emptyState("Digital Twin health data is loading.");
    return;
  }
  if (!state.selectedEquipmentId) {
    els.twinStage.textContent = "Select Asset";
    els.twinStage.className = "pill";
    els.digitalTwin.innerHTML = `<div class="empty-state compact">Select an asset to view digital twin health.</div>`;
    return;
  }
  const twin = state.intelligence.digital_twins.find((item) => item.equipment_id === state.selectedEquipmentId);
  if (!twin) {
    els.digitalTwin.innerHTML = emptyState("No Digital Twin health record found for the selected asset.");
    return;
  }
  els.twinStage.textContent = twin.degradation_stage;
  els.twinStage.className = pillClass(twin.overall_health < 40 ? "critical" : twin.overall_health < 65 ? "high" : "low");
  const components = Object.entries(twin.components)
    .map(([name, value]) => `
      <div class="health-row">
        <div>
          <strong>${escapeHtml(name)}</strong>
          <span>${escapeHtml(value)}%</span>
        </div>
        <div class="health-bar"><span style="width:${safeNumber(value)}%"></span></div>
      </div>
    `)
    .join("");
  els.digitalTwin.innerHTML = `
    <div class="twin-score">
      <strong>${escapeHtml(twin.overall_health)}%</strong>
      <span>${escapeHtml(twin.equipment_name)}</span>
    </div>
    ${components}
  `;
}

function renderMaintenancePlan() {
  if (!state.intelligence || !els.maintenancePlan) return;
  els.maintenancePlan.innerHTML = state.intelligence.maintenance_plan
    .map((item) => {
      const spares = item.required_spares.length
        ? item.required_spares.map((spare) => `${spare.part} (${spare.lead_time_days}d)`).join(", ")
        : "No blocking spares";
      return `
        <div class="plan-item">
          <span class="${pillClass(item.risk_level)}">P${escapeHtml(item.priority)} ${escapeHtml(item.risk_level)}</span>
          <div>
            <strong>${escapeHtml(assetDisplayName(normalizeEquipmentRecord(item)))}</strong>
            <p>${escapeHtml(item.recommended_window)} - ${escapeHtml(item.estimated_duration_minutes)} min - ${escapeHtml(item.status)}</p>
            <p>${escapeHtml(spares)}</p>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderWorkOrder(order) {
  if (!order) {
    els.workOrderView.innerHTML = `<div class="empty-state compact">Generate a work order after selecting an asset or running an investigation.</div>`;
    if (els.workOrderStatus) els.workOrderStatus.value = "Open";
    return;
  }
  if (els.workOrderStatus) els.workOrderStatus.value = order.status || "Open";
  const tasks = (order.tasks || []).slice(0, 6).map((item) => `<li>${escapeHtml(item.task)}</li>`).join("");
  const requiredParts = order.required_parts || order.required_spares || [];
  const spares = requiredParts.length ? requiredParts.map((item) => `
    <div class="wo-line">
      <strong>${escapeHtml(item.part)}</strong>
      <span>Qty ${escapeHtml(item.available_qty)} / Lead ${escapeHtml(item.lead_time_days)} days / ${escapeHtml(item.criticality || "standard")}</span>
    </div>
  `).join("") : `<div class="wo-line"><strong>No blocking spares</strong><span>Stores can support this work order.</span></div>`;
  const skills = order.required_skills ? order.required_skills.join(", ") : "maintenance safety";
  els.workOrderView.innerHTML = `
    <div class="work-order-head">
      <div>
        <span>Work Order</span>
        <strong>${escapeHtml(order.work_order_id)}</strong>
      </div>
      <span class="${pillClass(order.priority)}">${escapeHtml(order.priority)}</span>
    </div>
    <div class="lifecycle-row">${(order.lifecycle || []).map((item) => `<span class="${item === order.status ? "active" : ""}">${escapeHtml(item)}</span>`).join("")}</div>
    <div class="wo-grid">
      ${kpiCard("Assigned Team", order.assigned_team || "-", order.owner_role || "Maintenance owner")}
      ${kpiCard("Required Skills", skills, "Crew capability")}
      ${kpiCard("Safety Permit", order.safety_permit || "-", order.safety_classification || "standard maintenance")}
      ${kpiCard("Estimated Downtime", `${order.shutdown_duration_hours || "-"} h`, `${order.estimated_duration_minutes || "-"} min task duration`)}
      ${kpiCard("Estimated Repair Cost", money(order.estimated_cost_inr), "Labour and material")}
      ${kpiCard("Approval", order.approval_role || "-", "Required before execution")}
    </div>
    <div class="wo-detail">
      <div>
        <h4>Asset and Problem</h4>
        <p>${escapeHtml(order.asset || order.equipment_id)} - ${escapeHtml(order.equipment_name || "-")}</p>
        <p>${escapeHtml(order.problem || "-")}</p>
        <p>Likely root cause: ${escapeHtml(order.root_cause || "Pending field confirmation")}</p>
      </div>
      <div>
        <h4>Required Spares</h4>
        ${spares}
      </div>
    </div>
    <h4>Execution Tasks</h4>
    <ol>${tasks}</ol>
  `;
}

function renderReport(report) {
  if (!report) return;
  report = normalizeReport(report);
  state.report = report;
  const riskLevel = classifyRisk(report?.risk?.score, report?.risk?.level);
  els.assetName.textContent = assetDisplayName(report?.equipment);
  els.assetAlert.textContent = `${assetDisplayId(report?.equipment)} - ${assetDisplayAlert(report?.equipment)}`;
  els.riskLevel.textContent = riskDisplay(riskLevel);
  els.riskLevel.className = riskClass(riskLevel);
  els.riskScore.textContent = `Score ${safeValue(report?.risk?.score, 0)} - ${safeValue(report?.priority?.urgency)}`;
  els.rulHours.textContent = report?.prediction?.rul_label || `${safeValue(report?.prediction?.estimated_remaining_useful_life_hours, 0)} h`;
  els.healthIndex.textContent = `Health index ${safeValue(report?.prediction?.health_index, 0)} - ${safeValue(report?.prediction?.rul_explanation, "estimated from condition data")}`;
  els.urgencyPill.textContent = safeValue(report?.priority?.urgency);
  els.urgencyPill.className = pillClass(riskLevel);

  const causes = (report?.diagnosis?.probable_root_causes || []).map((item) => escapeHtml(item)).join("<br>") || "Not Available";
  const breaches = report?.diagnosis?.condition_breaches || [];
  const breachRows = breaches.length
    ? breaches.map((item) => `
        <tr>
          <td>${escapeHtml(item?.metric)}</td>
          <td>${escapeHtml(item?.value)}</td>
          <td>${escapeHtml(item?.level)}</td>
          <td>${escapeHtml(item?.limit)}</td>
        </tr>
      `).join("")
    : `<tr><td colspan="4">No active threshold breach</td></tr>`;

  els.diagnosisContent.className = "";
  els.diagnosisContent.innerHTML = `
    <div class="diagnosis-grid">
      <div class="info-block">
        <span>Probable Fault</span>
        <strong>${escapeHtml(report?.diagnosis?.probable_fault)}</strong>
      </div>
      <div class="info-block">
        <span>Root Cause Candidates</span>
        <strong>${causes}</strong>
      </div>
      <div class="info-block">
        <span>Risk Drivers</span>
        <strong>Condition ${escapeHtml(report?.risk?.drivers?.condition_score)} - History ${escapeHtml(report?.risk?.drivers?.historical_severity_score)} - Spares ${escapeHtml(report?.risk?.drivers?.spares_penalty)}</strong>
      </div>
      <div class="info-block">
        <span>RUL Method</span>
        <strong>${escapeHtml(report?.prediction?.method)}</strong>
      </div>
    </div>
    <table class="breach-table">
      <thead>
        <tr><th>Metric</th><th>Value</th><th>Level</th><th>Limit</th></tr>
      </thead>
      <tbody>${breachRows}</tbody>
    </table>
  `;
  renderRoiDecisionCard(els.diagnosisContent, financialImpactFromReport(report));

  els.recommendationsList.innerHTML = (report?.recommendations || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("") || `<li>Not Available</li>`;

  els.traceabilityList.innerHTML = (report?.traceability || [])
    .map((item) => `
      <div class="trace-item">
        <strong>${escapeHtml(item?.source)} / ${escapeHtml(item?.title)}</strong>
        <p>${escapeHtml(item?.detail)}</p>
      </div>
    `)
    .join("") || `<div class="empty-state compact">No traceability records available.</div>`;
}

function executiveDecisionFromReport(report = {}) {
  const equipment = report?.equipment || selectedEquipment() || {};
  const riskLevel = riskDisplay(classifyRisk(report?.risk?.score, report?.risk?.level || "high"));
  const primaryAction = (report?.recommendations || [])[0] || "Review maintenance recommendation";
  const approvals = riskLevel === "CRITICAL"
    ? ["Maintenance Head", "Production Head", "Safety Officer"]
    : ["Maintenance Lead", "Production Supervisor"];
  return {
    current_top_plant_risk: assetDisplayName(equipment),
    asset: assetDisplayId(equipment),
    expected_production_impact: `${safeValue(riskLevel)} risk with ${safeValue(report?.priority?.urgency, "active")} urgency`,
    recommended_maintenance_strategy: primaryAction,
    estimated_downtime_avoided: report?.prediction?.rul_label || `${safeValue(report?.prediction?.estimated_remaining_useful_life_hours, 0)} h RUL`,
    estimated_cost_avoided_inr: 0,
    required_approvals: approvals,
  };
}

function financialImpactFromReport(report = {}) {
  const equipment = report?.equipment || selectedEquipment() || {};
  const riskScore = safeNumber(report?.risk?.score, 0);
  const downtimeHours = Math.max(1, Math.round((100 - Math.min(95, riskScore)) / 8) + 4);
  const baseCost = Math.max(500000, Math.round(riskScore * 85000));
  const productionLoss = baseCost * 3;
  const downtimeCost = baseCost;
  const repairCost = Math.round(baseCost * 0.7);
  const inventoryCost = Math.round(baseCost * 0.35);
  const potentialFailureCost = productionLoss + downtimeCost + repairCost;
  const businessExposure = potentialFailureCost + inventoryCost + Math.round(productionLoss * 0.18);
  const shutdownCost = Math.max(120000, Math.round(downtimeCost * 0.38 + repairCost * 0.28));
  const expectedSavings = Math.max(0, potentialFailureCost - shutdownCost);
  return {
    equipment_id: assetDisplayId(equipment),
    production_loss_inr: productionLoss,
    downtime_cost_inr: downtimeCost,
    repair_cost_inr: repairCost,
    inventory_cost_inr: inventoryCost,
    estimated_downtime_hours: downtimeHours,
    total_risk_exposure_inr: businessExposure,
    business_exposure_inr: businessExposure,
    failure_event_consequence_inr: potentialFailureCost,
    potential_failure_cost_inr: potentialFailureCost,
    controlled_shutdown_cost_inr: shutdownCost,
    shutdown_cost_inr: shutdownCost,
    expected_savings_inr: expectedSavings,
    roi_percent: shutdownCost > 0 ? Math.round((expectedSavings / shutdownCost) * 100) : 0,
  };
}

function latestEnterpriseSlice(path, fallback) {
  return path.reduce((source, key) => source?.[key], state.enterprise) || fallback;
}

function renderTargetedInvestigationPanels(analyzeResponse = {}) {
  const report = analyzeResponse?.report ? normalizeReport(analyzeResponse.report) : null;
  const executiveSummary = analyzeResponse?.executive_summary
    || analyzeResponse?.executive_decision_summary
    || analyzeResponse?.enterprise?.executive_decision_summary
    || latestEnterpriseSlice(["executive_decision_summary"], null)
    || executiveDecisionFromReport(report);
  const financialImpact = analyzeResponse?.financial_impact
    || analyzeResponse?.failure_cost_impact
    || analyzeResponse?.enterprise?.failure_cost_impact
    || latestEnterpriseSlice(["failure_cost_impact"], null)
    || financialImpactFromReport(report);
  state.selectedFinancialImpact = financialImpact;
  const assetIntelligence = analyzeResponse?.asset_intelligence
    || analyzeResponse?.enterprise?.asset_intelligence
    || latestEnterpriseSlice(["asset_intelligence"], null);

  logMissingRenderField("analyzeResponse", "report", report);
  logMissingRenderField("analyzeResponse", "executive_summary", executiveSummary);
  logMissingRenderField("analyzeResponse", "financialImpact", financialImpact);
  if (!assetIntelligence) {
    console.warn("Missing optional asset_intelligence", { scope: "analyzeResponse", response: analyzeResponse });
  }
  if (report?.equipment) {
    const equipmentId = assetDisplayId(report.equipment);
    if (equipmentId) {
      state.selectedEquipmentId = equipmentId;
      state.twinSelectedAssetId = equipmentId;
      setInvestigationStatus(INVESTIGATION_STATES.COMPLETED, equipmentId);
    }
  }
  updateSelectedAssetState(state.selectedEquipmentId, { asset_intelligence: assetIntelligence || undefined });

  renderReport(report);
  renderAgentic(analyzeResponse?.agentic);
  renderExecutiveDecision({ ...executiveSummary, failure_cost_impact: financialImpact });
  renderCostImpact(financialImpact);
  renderExecutiveDashboardView(executiveSummary);
  renderAssetIntelligenceWidgets(assetIntelligence);
  renderDependencyGraph();
  dispatchAssetSelected("investigation_rendered");
  renderActiveAssetChip();
}

async function analyze() {
  if (!state.selectedEquipmentId) {
    showToast("Select an asset before running investigation.");
    renderNoInvestigationState(true);
    setAiActionAvailability(state.systemReady, state.aiModelReady);
    return;
  }
  if (!state.systemReady) {
    showToast("AI Engine Initializing...");
    return;
  }
  if (!els.queryInput.value.trim()) {
    els.queryInput.value = buildLocalInvestigationBrief();
  }
  const query = els.queryInput.value.trim();
  if (!query) {
    showToast("Enter a maintenance query first.");
    return;
  }
  setBusy(true);
  setInvestigationStatus(INVESTIGATION_STATES.RUNNING, state.selectedEquipmentId);
  renderExecutiveDashboardView();
  const progress = startInvestigationProgress();
  try {
    const data = await api("/api/analyze", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: els.equipmentSelect.value,
        query,
      }),
    });
    data.report = normalizeReport(data.report);
    progress.complete();
    const renderStarted = performance.now();
    console.log("INVESTIGATION_RENDER_START", {
      equipment_id: assetDisplayId(data?.report?.equipment),
      timestamp: new Date().toISOString(),
    });
    const analyzedEquipmentId = assetDisplayId(data?.report?.equipment);
    state.selectedEquipmentId = analyzedEquipmentId;
    state.twinSelectedAssetId = analyzedEquipmentId;
    if (els.equipmentSelect && analyzedEquipmentId) {
      els.equipmentSelect.value = analyzedEquipmentId;
    }
    state.workOrder = data?.work_order || state.workOrder;
    setInvestigationStatus(INVESTIGATION_STATES.COMPLETED, analyzedEquipmentId);
    renderTargetedInvestigationPanels(data);
    console.log("INVESTIGATION_RENDER_COMPLETE", {
      equipment_id: assetDisplayId(data?.report?.equipment),
      render_ms: Number((performance.now() - renderStarted).toFixed(1)),
      timestamp: new Date().toISOString(),
    });
    showToast("Analysis complete.");
  } catch (error) {
    setInvestigationStatus(INVESTIGATION_STATES.FAILED, state.selectedEquipmentId, error.message);
    renderExecutiveDashboardView();
    progress.fail();
    showToast(error.message);
  } finally {
    setBusy(false);
    pollStatusNow("run_investigation");
  }
}

function renderFinancialRefresh() {
  renderExecutiveSummary();
  renderExecutiveDashboardView(state.enterprise?.executive_decision_summary);
  renderCostImpact(state.enterprise?.failure_cost_impact);
  renderAssetIntelligenceWidgets(state.enterprise?.asset_intelligence || state.report?.asset_intelligence);
}

async function runDemo() {
  setBusy(true);
  try {
    switchModule("command-center");
    els.agentExecution.innerHTML = [
      "Initializing plant incident",
      "Running investigation",
      "Retrieving evidence",
      "Building work order",
      "Preparing executive view",
    ].map((step, index) => `
      <div class="timeline-step">
        <div class="timeline-step-head"><strong>${escapeHtml(step)}</strong><span class="pill low">running</span></div>
        <div class="progress-track"><span style="width:${(index + 1) * 20}%"></span></div>
      </div>
    `).join("");
    await sleep(800);
    const data = await api("/api/plant-incident-demo", { method: "POST", body: "{}" });
    await sleep(2500);
    data.report = normalizeReport(data.report);
    selectEquipment(assetDisplayId(data.report.equipment), false);
    renderReport(data.report);
    renderAgentic(data.agentic);
    state.workOrder = data.work_order;
    renderWorkOrder(state.workOrder);
    renderEnterprise(data.enterprise);
    const [operations, command, twin, pipeline, dependency] = await Promise.all([
      api("/api/operations-center"),
      api("/api/plant-command-center"),
      api("/api/digital-twin"),
      api("/api/ai-pipeline"),
      api("/api/dependency-graph"),
    ]);
    state.operationsCenter = operations;
    state.plantCommandCenter = command;
    state.plantDigitalTwin = twin;
    state.aiPipeline = pipeline;
    state.dependencyGraph = dependency;
    state.twinSelectedAssetId = assetDisplayId(data.report.equipment);
    renderExecutiveSummary();
    renderOperationsCenter();
    renderPlantCommandCenter();
    renderPlantDigitalTwin();
    renderPipeline();
    renderPredictiveAnalytics();
    renderDependencyGraph();
    startTelemetry();
    renderAlerts(data.alerts);
    renderStatus(data.alerts);
    showToast("Asset alert and executive summary generated.");
    await sleep(900);
    switchModule("asset-intelligence");
    showToast("Diagnosis and evidence reviewed.");
    await sleep(900);
    switchModule("work-orders");
    showToast("Work order generated.");
    await sleep(900);
    switchModule("inventory-spares");
    showToast("Spare risk and procurement request reviewed.");
    await sleep(900);
    switchModule("reports");
    showToast("Executive report ready for plant leadership.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

async function runWhatIf() {
  setBusy(true);
  try {
    const data = await api("/api/what-if", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: state.selectedEquipmentId,
        overrides: {
          temperature_c: els.scenarioTemperature.value,
          vibration_mm_s: els.scenarioVibration.value,
          motor_current_a: els.scenarioCurrent.value,
          hydraulic_pressure_bar: els.scenarioHydraulic.value,
        },
      }),
    });
    renderReport(data.report);
    renderAlerts(data.alerts);
    renderRoleNotifications(data.role_notifications);
    renderStatus(data.alerts);
    showToast("What-if scenario evaluated.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

async function refreshLive() {
  try {
    const data = await api("/api/live");
    state.liveMonitor = data;
    renderLiveMonitor();
    showToast("Live monitor refreshed.");
  } catch (error) {
    showToast(error.message);
  }
}

async function refreshIntelligence() {
  try {
    const [data, operations, command, twin, pipeline, dependency] = await Promise.all([
      api("/api/intelligence"),
      api("/api/operations-center"),
      api("/api/plant-command-center"),
      api("/api/digital-twin"),
      api("/api/ai-pipeline"),
      api("/api/dependency-graph"),
    ]);
    state.intelligence = data;
    state.operationsCenter = operations;
    state.plantCommandCenter = command;
    state.plantDigitalTwin = twin;
    state.aiPipeline = pipeline;
    state.dependencyGraph = dependency;
    renderExecutiveSummary();
    renderDigitalTwin();
    renderMaintenancePlan();
    renderOperationsCenter();
    renderPlantCommandCenter();
    renderPlantDigitalTwin();
    renderPipeline();
    renderPredictiveAnalytics();
    renderDependencyGraph();
    startTelemetry();
    showToast("Decision intelligence refreshed.");
  } catch (error) {
    showToast(error.message);
  }
}

async function refreshKnowledgeCenter() {
  try {
    const sources = await api("/api/knowledge-center");
    state.knowledgeSources = sources;
    renderKnowledgeCenter();
    showToast("Knowledge center refreshed.");
  } catch (error) {
    showToast(error.message);
  }
}

async function ingestInput() {
  const content = els.ingestContent.value.trim();
  if (!content) {
    showToast("Paste an input record before ingesting.");
    return;
  }
  try {
    const data = await api("/api/ingest", {
      method: "POST",
      body: JSON.stringify({
        input_type: els.ingestType.value,
        equipment_id: state.selectedEquipmentId,
        content,
      }),
    });
    state.knowledgeSources = data.knowledge_center;
    els.ingestContent.value = "";
    renderKnowledgeCenter();
    showToast(`Input captured as ${data.ingested.record_id}.`);
  } catch (error) {
    showToast(error.message);
  }
}

async function sendChat(overrideMessage = "") {
  if (!state.selectedEquipmentId) {
    showToast("Select an asset before asking the maintenance copilot.");
    renderNoInvestigationState(true);
    return;
  }
  if (!state.systemReady) {
    showToast("AI Engine Initializing...");
    return;
  }
  const message = String(overrideMessage || els.chatInput.value || "").trim();
  if (!message) {
    showToast("Enter a follow-up question.");
    return;
  }
  if (els.queryInput && !els.queryInput.value.trim()) {
    els.queryInput.value = buildLocalInvestigationBrief();
  }
  cancelActiveChatRequest("new_request");
  const requestId = createRequestId();
  const controller = new AbortController();
  activeChatRequest = {
    id: requestId,
    controller,
    backendSucceeded: false,
    streamCancelled: false,
    createdAt: Date.now(),
  };
  state.lastAssistantText = "";
  const asset = selectedEquipment();
  const history = state.chatHistory
    .filter((item) => item.status !== "processing")
    .slice(-20)
    .map((item) => ({ role: item.role, content: item.content }));
  const memoryContext = buildMemoryContext();
  state.chatHistory.push({
    id: messageId(),
    role: "user",
    content: message,
    timestamp: nowStamp(),
    asset_id: state.selectedEquipmentId,
  });
  const processingMessage = {
    id: messageId(),
    role: "assistant",
    content: "Retrieving Knowledge",
    timestamp: nowStamp(),
    status: "processing",
    asset_id: state.selectedEquipmentId,
  };
  state.chatHistory.push(processingMessage);
  const thinkingStages = [
    "Retrieving Knowledge",
    "Analyzing Asset",
    "Root Cause Analysis",
    "Planning Maintenance",
    "Generating Executive Summary",
  ];
  let thinkingIndex = 0;
  const thinkingTimer = setInterval(() => {
    if (!isActiveChatRequest(requestId)) {
      clearInterval(thinkingTimer);
      return;
    }
    thinkingIndex = Math.min(thinkingIndex + 1, thinkingStages.length - 1);
    processingMessage.content = thinkingStages[thinkingIndex];
    renderChat();
  }, 650);
  state.chatHistory = state.chatHistory.slice(-20);
  renderChat();
  els.chatInput.value = "";
  try {
    console.log("CHAT_REQUEST_SENT", {
      requestId,
      equipment_id: state.selectedEquipmentId,
      message_length: message.length,
      timestamp: new Date().toISOString(),
    });
    const actionType = structuredActionType(message);
    const data = await apiWithTimeout("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: state.selectedEquipmentId,
        message: `${actionPrompt(actionType, message, asset)}\nMemory: ${JSON.stringify(memoryContext)}`,
        history,
      }),
    }, 15000, controller);
    if (!isActiveChatRequest(requestId)) {
      clearInterval(thinkingTimer);
      console.log("STREAM_CANCELLED", { requestId, reason: "stale_response" });
      return;
    }
    clearInterval(thinkingTimer);
    state.chatHistory = state.chatHistory.filter((item) => item.id !== processingMessage.id);
    activeChatRequest.backendSucceeded = true;
    console.log("CHAT_RESPONSE_RECEIVED", {
      requestId,
      equipment_id: data?.report?.equipment?.equipment_id || state.selectedEquipmentId,
      risk_level: data?.report?.risk?.level,
      timestamp: new Date().toISOString(),
    });
    setBackendStatus(true);
    data.report = normalizeReport(data.report);
    const chatReportAssetId = assetDisplayId(data?.report?.equipment || {});
    if (chatReportAssetId && chatReportAssetId === state.selectedEquipmentId) {
      setInvestigationStatus(INVESTIGATION_STATES.COMPLETED, chatReportAssetId);
      state.selectedFinancialImpact = data?.financial_impact || data?.failure_cost_impact || financialImpactFromReport(data.report);
    }
    const responseText = buildAssistantText(message, data);
    const card = buildResponseCard(actionType, data.report);
    const evidence = buildEvidence(data.report.traceability);
    const assistantMessage = {
      id: messageId(),
      role: "assistant",
      content: responseText,
      timestamp: nowStamp(),
      status: "complete",
      asset_id: assetDisplayId(data.report.equipment),
      timing: data.timing,
      card,
      evidence,
    };
    state.chatHistory.push(assistantMessage);
    const streamed = await streamAssistantMessage(requestId, assistantMessage, responseText, card, evidence);
    if (!streamed) {
      state.chatHistory = state.chatHistory.filter((item) => item.id !== assistantMessage.id);
      renderChat();
      return;
    }
    state.chatHistory = state.chatHistory.slice(-20);
    state.chatThreads[state.selectedEquipmentId] = state.chatHistory.filter((item) => item.role !== "assistant").slice(-20);
    saveCopilotMemory({
      previous_investigation: data?.report?.diagnosis?.probable_fault,
      generated_reports: [
        ...(memoryContext.generated_reports || []),
        actionType || "Follow-up Chat",
      ].slice(-10),
      root_causes_discussed: [
        ...(memoryContext.root_causes_discussed || []),
        ...(data?.report?.diagnosis?.probable_root_causes || []),
      ].slice(-12),
    });
    renderReport(data?.report);
    renderExecutiveDashboardView();
    showToast("Maintenance Wizard response generated.");
  } catch (error) {
    clearInterval(thinkingTimer);
    console.log("CHAT_REQUEST_FAILED", {
      requestId,
      equipment_id: state.selectedEquipmentId,
      error: error.message,
      timestamp: new Date().toISOString(),
    });
    console.log("BACKEND_UNAVAILABLE", { requestId, error: error.message });
    if (activeChatRequest?.id === requestId) {
      activeChatRequest.streamCancelled = true;
      activeChatRequest.cancelReason = "backend_unavailable";
    }
    state.lastAssistantText = "";
    state.chatHistory = state.chatHistory.filter((item) => item.status !== "typing" && item.status !== "processing");
    setBackendStatus(false, error.message);
    renderChat();
    showToast(backendOfflineMessage(error));
  } finally {
    if (activeChatRequest?.id === requestId) {
      activeChatRequest = null;
    }
    pollStatusNow("copilot_request");
  }
}

async function generateWorkOrder() {
  if (!state.systemReady) {
    showToast("AI Engine Initializing...");
    return;
  }
  setBusy(true);
  try {
    const data = await api("/api/work-order", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: state.selectedEquipmentId,
        query: els.queryInput.value.trim(),
      }),
    });
    state.workOrder = data.work_order;
    renderWorkOrder(state.workOrder);
    showToast("Work order generated.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

async function saveWorkOrder() {
  if (!state.workOrder) {
    showToast("Generate a work order first.");
    return;
  }
  try {
    const data = await api("/api/save-work-order", {
      method: "POST",
      body: JSON.stringify({
        work_order: state.workOrder,
        status: els.workOrderStatus.value,
      }),
    });
    state.workOrder = data.work_order;
    renderWorkOrder(state.workOrder);
    showToast("Work order saved to audit record.");
  } catch (error) {
    showToast(error.message);
  }
}

function exportWorkOrderJson() {
  if (!state.workOrder) {
    showToast("Generate a work order first.");
    return;
  }
  downloadJson(`${state.workOrder.work_order_id || "work_order"}.json`, state.workOrder);
}

function downloadWorkOrderPdf() {
  window.location.href = "/api/work-order-pdf";
}

function downloadHandoverPdf() {
  window.location.href = "/api/shift-handover-pdf";
}

function downloadExecutiveReportPdf() {
  if (!state.systemReady) {
    showToast("AI Engine Initializing...");
    return;
  }
  window.location.href = "/api/executive-report-pdf";
}

function generateProcurementRequest() {
  if (!state.systemReady) {
    showToast("AI Engine Initializing...");
    return;
  }
  renderProcurement(state.enterprise?.procurement_recommendations || []);
  switchModule("inventory-spares");
  showToast("Procurement request generated.");
}

function generateReliabilityAssessment() {
  if (!state.systemReady) {
    showToast("AI Engine Initializing...");
    return;
  }
  renderReliabilityAssessment(state.enterprise?.maintenance_kpis || {});
  switchModule("asset-intelligence");
  showToast("Reliability assessment generated.");
}

async function searchKnowledge() {
  const query = els.knowledgeInput.value.trim() || els.queryInput.value.trim();
  if (!query) {
    showToast("Enter a knowledge search query.");
    return;
  }
  try {
    const data = await api("/api/knowledge-search", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: state.selectedEquipmentId,
        query,
      }),
    });
    els.knowledgeResults.innerHTML = data.results
      .map((item) => `
        <div class="trace-item">
          <strong>${escapeHtml(item.source)} / ${escapeHtml(item.title)} / score ${escapeHtml(item.score)}</strong>
          <p>${escapeHtml(item.detail)}</p>
        </div>
      `)
      .join("");
    showToast("Knowledge search complete.");
  } catch (error) {
    showToast(error.message);
  }
}

async function saveFeedback() {
  const feedback = els.feedbackInput.value.trim();
  if (!feedback) {
    showToast("Enter feedback before saving.");
    return;
  }
  try {
    await api("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        equipment_id: state.selectedEquipmentId,
        feedback,
      }),
    });
    els.feedbackInput.value = "";
    showToast("Feedback saved.");
  } catch (error) {
    showToast(error.message);
  }
}

async function init() {
  renderInitialSkeletons();
  let data;
  try {
    data = await apiWithTimeout("/api/bootstrap", {}, 15000);
    setBackendStatus(true);
  } catch (error) {
    console.error("BOOTSTRAP_REQUEST_FAILED", { error: error.message, timestamp: new Date().toISOString() });
    setBackendStatus(false, error.message);
    showToast(backendOfflineMessage(error));
    return;
  }
  setAiActionAvailability(false);
  startPreloadStatusPolling();
  state.equipment = (data.equipment || []).map(normalizeEquipmentRecord);
  state.assetMaster = (data.equipment_master || []).map(normalizeEquipmentRecord);
  state.spares = data.spares || [];
  state.history = data.history || [];
  state.demoQueries = data.demo_queries || [];
  state.alerts = (data.alerts || []).map((item) => ({
    ...item,
    risk_level: normalizeRiskLabel(firstDefined(item.risk_level, item.risk?.level, item.risk, classifyRisk(firstDefined(item.risk_score, item.score, item.risk?.score), "low"))),
  }));
  state.roleNotifications = data.role_notifications || [];
  state.liveMonitor = data.live_monitor;
  state.intelligence = data.intelligence;
  state.knowledgeSources = data.knowledge_center;
  state.agentMetrics = data.agent_metrics;
  state.enterprise = data.enterprise;
  state.incidentReplay = data.enterprise?.incident_replay || null;
  state.operationsCenter = data.operations_center;
  state.plantCommandCenter = data.plant_command_center;
  state.plantDigitalTwin = normalizePlantDigitalTwinPayload(data.plant_digital_twin);
  state.aiPipeline = data.ai_pipeline;
  state.reportCatalog = data.report_catalog || [];
  state.dependencyGraph = data.dependency_graph;
  state.selectedEquipmentId = "";
  state.twinSelectedAssetId = "";
  state.report = null;
  state.chatHistory = [];
  renderEquipment();
  renderInventoryTypeOptions();
  renderActiveAssetChip();
  renderSelectedAsset();
  renderSpares();
  renderAlerts(state.alerts);
  renderRoleNotifications(data.role_notifications);
  renderStatus(state.alerts);
  renderScenarioInputs();
  renderLiveMonitor();
  renderExecutiveSummary();
  renderOperationsCenter();
  renderPlantCommandCenter();
  renderDigitalTwin();
  renderPlantDigitalTwin();
  renderPredictiveAnalytics();
  renderDependencyGraph();
  startTelemetry();
  renderPipeline();
  renderMaintenancePlan();
  renderWorkOrder(null);
  renderKnowledgeCenter();
  renderChat();
  renderAgentic(null);
  renderExecutiveDashboardView(state.enterprise?.executive_decision_summary);
  renderIncidentReplay(state.enterprise?.incident_replay);
  renderReportCatalog();
  renderPerformanceHealth();
  renderNoInvestigationState(true);
  renderDashboardPlaceholders();
  setAiActionAvailability(state.systemReady, state.aiModelReady);
}

on(els.analyzeButton, "click", analyze);
on(els.runDemoButton, "click", runDemo);
on(els.feedbackButton, "click", saveFeedback);
on(els.refreshLiveButton, "click", refreshLive);
on(els.refreshIntelButton, "click", refreshIntelligence);
on(els.ingestButton, "click", ingestInput);
on(els.chatButton, "click", sendChat);
on(els.operationButton, "click", simulateOperation);
on(els.whatIfButton, "click", runWhatIf);
on(els.workOrderButton, "click", generateWorkOrder);
on(els.workOrderSaveButton, "click", saveWorkOrder);
on(els.workOrderJsonButton, "click", exportWorkOrderJson);
on(els.workOrderPdfButton, "click", downloadWorkOrderPdf);
on(els.handoverPdfButton, "click", downloadHandoverPdf);
on(els.procurementButton, "click", generateProcurementRequest);
on(els.reliabilityButton, "click", generateReliabilityAssessment);
on(els.executiveReportButton, "click", downloadExecutiveReportPdf);
on(els.executiveReportPdfButton, "click", downloadExecutiveReportPdf);
on(els.knowledgeButton, "click", searchKnowledge);
on(els.globalSearch, "input", renderGlobalSearch);
on(els.inventorySearch, "input", renderSpares);
on(els.inventoryStockFilter, "change", renderSpares);
on(els.inventoryTypeFilter, "change", renderSpares);
on(els.inventorySort, "change", renderSpares);
on(els.reportTypeSelect, "change", renderEnterpriseReportPreview);
on(els.reportPdfButton, "click", () => exportEnterpriseReport("pdf"));
on(els.reportExcelButton, "click", () => exportEnterpriseReport("excel"));
on(els.reportJsonButton, "click", () => exportEnterpriseReport("json"));
on(els.voiceListenButton, "click", startVoiceInput);
on(els.voiceSpeakButton, "click", speakLastResponse);
on(els.clearSectorFilterButton, "click", () => {
  state.assetFilterArea = "";
  renderEquipment();
  showToast("Showing all assets.");
});
window.addEventListener("maintenance-digital-twin-ready", () => renderPlantDigitalTwin());
window.addEventListener("maintenance-asset-selected", () => {
  renderAssetIntelligenceWidgets();
  renderDependencyGraph();
  renderExecutiveDashboardView();
  renderIncidentReplay();
  auditDashboardCards(document.body);
});
on(els.clearButton, "click", () => {
  els.queryInput.value = "";
  els.queryInput.focus();
});
on(els.equipmentSelect, "change", () => selectEquipment(els.equipmentSelect.value));
on(els.workOrderStatus, "change", () => {
  if (state.workOrder) {
    state.workOrder.status = els.workOrderStatus.value;
    renderWorkOrder(state.workOrder);
  }
});
if (els.moduleNav) {
  els.moduleNav.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => switchModule(button.dataset.module));
  });
}

const kpiCounterObserver = new MutationObserver((records) => {
  records.forEach((record) => {
    record.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        animateKpiCounters(node);
        sanitizeInvalidDisplayText(node);
        auditDashboardCards(node);
      }
    });
  });
});
kpiCounterObserver.observe(document.body, { childList: true, subtree: true });
animateKpiCounters();
sanitizeInvalidDisplayText();
renderDashboardPlaceholders();

init().catch((error) => showToast(error.message));
