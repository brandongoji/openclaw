import { LitElement } from "lit";
import { customElement, state } from "lit/decorators.js";
import type { EventLogEntry } from "./app-events.ts";
import type { AppViewState } from "./app-view-state.ts";
import type { DevicePairingList } from "./controllers/devices.ts";
import type { ExecApprovalRequest } from "./controllers/exec-approval.ts";
import type { ExecApprovalsFile, ExecApprovalsSnapshot } from "./controllers/exec-approvals.ts";
import type { SkillMessage } from "./controllers/skills.ts";
import type { GatewayBrowserClient, GatewayHelloOk } from "./gateway.ts";
import type { Tab } from "./navigation.ts";
import type { ResolvedTheme, ThemeMode } from "./theme.ts";
import type {
  AgentsListResult,
  AgentsFilesListResult,
  AgentIdentityResult,
  ConfigSnapshot,
  ConfigUiHints,
  CronJob,
  CronRunLogEntry,
  CronStatus,
  HealthSnapshot,
  LogEntry,
  LogLevel,
  PresenceEntry,
  ChannelsStatusSnapshot,
  SessionsListResult,
  SkillStatusReport,
  StatusSummary,
  NostrProfile,
} from "./types.ts";
import type { NostrProfileFormState } from "./views/channels.nostr-profile-form.ts";
import {
  handleChannelConfigReload as handleChannelConfigReloadInternal,
  handleChannelConfigSave as handleChannelConfigSaveInternal,
  handleNostrProfileCancel as handleNostrProfileCancelInternal,
  handleNostrProfileEdit as handleNostrProfileEditInternal,
  handleNostrProfileFieldChange as handleNostrProfileFieldChangeInternal,
  handleNostrProfileImport as handleNostrProfileImportInternal,
  handleNostrProfileSave as handleNostrProfileSaveInternal,
  handleNostrProfileToggleAdvanced as handleNostrProfileToggleAdvancedInternal,
  handleWhatsAppLogout as handleWhatsAppLogoutInternal,
  handleWhatsAppStart as handleWhatsAppStartInternal,
  handleWhatsAppWait as handleWhatsAppWaitInternal,
} from "./app-channels.ts";
import {
  handleAbortChat as handleAbortChatInternal,
  handleSendChat as handleSendChatInternal,
  removeQueuedMessage as removeQueuedMessageInternal,
} from "./app-chat.ts";
import { DEFAULT_CRON_FORM, DEFAULT_LOG_LEVEL_FILTERS } from "./app-defaults.ts";
import { connectGateway as connectGatewayInternal } from "./app-gateway.ts";
import {
  handleConnected,
  handleDisconnected,
  handleFirstUpdated,
  handleUpdated,
} from "./app-lifecycle.ts";
import { renderApp } from "./app-render.ts";
import {
  exportLogs as exportLogsInternal,
  handleChatScroll as handleChatScrollInternal,
  handleLogsScroll as handleLogsScrollInternal,
  resetChatScroll as resetChatScrollInternal,
  scheduleChatScroll as scheduleChatScrollInternal,
} from "./app-scroll.ts";
import {
  applySettings as applySettingsInternal,
  loadCron as loadCronInternal,
  loadOverview as loadOverviewInternal,
  setTab as setTabInternal,
  setTheme as setThemeInternal,
  onPopState as onPopStateInternal,
} from "./app-settings.ts";
import {
  resetToolStream as resetToolStreamInternal,
  type ToolStreamEntry,
  type CompactionStatus,
} from "./app-tool-stream.ts";
import { resolveInjectedAssistantIdentity } from "./assistant-identity.ts";
import { loadAssistantIdentity as loadAssistantIdentityInternal } from "./controllers/assistant-identity.ts";
import { loadSettings, type UiSettings } from "./storage.ts";
import { type ChatAttachment, type ChatQueueItem, type CronFormState } from "./ui-types.ts";

declare global {
  interface Window {
    __OPENCLAW_CONTROL_UI_BASE_PATH__?: string;
  }
}

const injectedAssistantIdentity = resolveInjectedAssistantIdentity();

function resolveOnboardingMode(): boolean {
  if (!window.location.search) {
    return false;
  }
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("onboarding");
  if (!raw) {
    return false;
  }
  const normalized = raw.trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
}

function encodeWavPcm16Mono(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i += 1) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const s = Math.max(-1, Math.min(1, samples[i] ?? 0));
    const int16 = s < 0 ? s * 0x8000 : s * 0x7fff;
    view.setInt16(offset, int16, true);
    offset += 2;
  }

  return buffer;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    const slice = bytes.subarray(i, i + chunk);
    binary += String.fromCharCode(...slice);
  }
  return btoa(binary);
}

type MicCaptureSession = {
  stop: () => Promise<void>;
  cancel: () => Promise<void>;
  takeChunkBase64: (minSamples?: number, force?: boolean) => string | null;
};

async function startMicWavCapture(): Promise<MicCaptureSession> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("microphone API unavailable in this browser context");
  }

  let stream: MediaStream;
  try {
    const micPromise = navigator.mediaDevices.getUserMedia({ audio: true });
    const timeoutPromise = new Promise<never>((_, reject) => {
      window.setTimeout(() => reject(new Error("microphone request timed out")), 8000);
    });
    stream = await Promise.race([micPromise, timeoutPromise]);
  } catch (err) {
    const e = err as { name?: string; message?: string };
    throw new Error(`mic permission/capture failed (${e?.name ?? "unknown"}: ${e?.message ?? String(err)})`);
  }

  const audioContext = new AudioContext({ sampleRate: 16000 });
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  const chunks: Float32Array[] = [];
  let totalSamples = 0;
  let consumedSamples = 0;
  let finalized = false;

  const mergeChunks = () => {
    const merged = new Float32Array(totalSamples);
    let at = 0;
    for (const c of chunks) {
      merged.set(c, at);
      at += c.length;
    }
    return merged;
  };

  const takeChunkBase64 = (minSamples = 10_000, force = false): string | null => {
    const available = totalSamples - consumedSamples;
    if (!force && available < minSamples) {
      return null;
    }
    if (available <= 0) {
      return null;
    }

    const merged = mergeChunks();
    const next = merged.subarray(consumedSamples);
    if (next.length <= 0) {
      return null;
    }
    consumedSamples = merged.length;

    const wav = encodeWavPcm16Mono(next, 16000);
    return arrayBufferToBase64(wav);
  };

  processor.onaudioprocess = (event: AudioProcessingEvent) => {
    if (finalized) {
      return;
    }
    const input = event.inputBuffer.getChannelData(0);
    const next = new Float32Array(input);
    chunks.push(next);
    totalSamples += next.length;
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  const finalize = async (): Promise<void> => {
    if (finalized) {
      return;
    }
    finalized = true;

    try {
      processor.disconnect();
      source.disconnect();
    } catch {
      // best-effort cleanup
    }
    stream.getTracks().forEach((t) => t.stop());
    await audioContext.close();
  };

  return {
    stop: () => finalize(),
    cancel: () => finalize(),
    takeChunkBase64,
  };
}

@customElement("openclaw-app")
export class OpenClawApp extends LitElement {
  @state() settings: UiSettings = loadSettings();
  @state() password = "";
  @state() tab: Tab = "chat";
  @state() onboarding = resolveOnboardingMode();
  @state() connected = false;
  @state() theme: ThemeMode = this.settings.theme ?? "system";
  @state() themeResolved: ResolvedTheme = "dark";
  @state() hello: GatewayHelloOk | null = null;
  @state() lastError: string | null = null;
  @state() eventLog: EventLogEntry[] = [];
  private eventLogBuffer: EventLogEntry[] = [];
  private toolStreamSyncTimer: number | null = null;
  private sidebarCloseTimer: number | null = null;

  @state() assistantName = injectedAssistantIdentity.name;
  @state() assistantAvatar = injectedAssistantIdentity.avatar;
  @state() assistantAgentId = injectedAssistantIdentity.agentId ?? null;

  @state() sessionKey = this.settings.sessionKey;
  @state() chatLoading = false;
  @state() chatSending = false;
  @state() chatMessage = "";
  @state() moonshineModel:
    | "tiny"
    | "base"
    | "whisper-tiny"
    | "whisper-base"
    | "whisper-small"
    | "whisper-large"
    | "parakeet-v2" = "whisper-tiny";
  @state() moonshineBusy = false;
  @state() moonshineRecording = false;
  private moonshineCapture: MicCaptureSession | null = null;
  private moonshineLiveTimer: number | null = null;
  private moonshineLiveInFlight = false;
  private moonshineSessionToken = 0;
  private moonshineLastChunkNorm = "";
  private moonshineRepeatCount = 0;
  @state() chatMessages: unknown[] = [];
  @state() chatToolMessages: unknown[] = [];
  @state() chatStream: string | null = null;
  @state() chatStreamStartedAt: number | null = null;
  @state() chatRunId: string | null = null;
  @state() compactionStatus: CompactionStatus | null = null;
  @state() chatAvatarUrl: string | null = null;
  @state() chatThinkingLevel: string | null = null;
  @state() chatQueue: ChatQueueItem[] = [];
  @state() chatAttachments: ChatAttachment[] = [];
  @state() chatManualRefreshInFlight = false;
  // Sidebar state for tool output viewing
  @state() sidebarOpen = false;
  @state() sidebarContent: string | null = null;
  @state() sidebarError: string | null = null;
  @state() splitRatio = this.settings.splitRatio;

  @state() nodesLoading = false;
  @state() nodes: Array<Record<string, unknown>> = [];
  @state() devicesLoading = false;
  @state() devicesError: string | null = null;
  @state() devicesList: DevicePairingList | null = null;
  @state() execApprovalsLoading = false;
  @state() execApprovalsSaving = false;
  @state() execApprovalsDirty = false;
  @state() execApprovalsSnapshot: ExecApprovalsSnapshot | null = null;
  @state() execApprovalsForm: ExecApprovalsFile | null = null;
  @state() execApprovalsSelectedAgent: string | null = null;
  @state() execApprovalsTarget: "gateway" | "node" = "gateway";
  @state() execApprovalsTargetNodeId: string | null = null;
  @state() execApprovalQueue: ExecApprovalRequest[] = [];
  @state() execApprovalBusy = false;
  @state() execApprovalError: string | null = null;
  @state() pendingGatewayUrl: string | null = null;

  @state() configLoading = false;
  @state() configRaw = "{\n}\n";
  @state() configRawOriginal = "";
  @state() configValid: boolean | null = null;
  @state() configIssues: unknown[] = [];
  @state() configSaving = false;
  @state() configApplying = false;
  @state() updateRunning = false;
  @state() applySessionKey = this.settings.lastActiveSessionKey;
  @state() configSnapshot: ConfigSnapshot | null = null;
  @state() configSchema: unknown = null;
  @state() configSchemaVersion: string | null = null;
  @state() configSchemaLoading = false;
  @state() configUiHints: ConfigUiHints = {};
  @state() configForm: Record<string, unknown> | null = null;
  @state() configFormOriginal: Record<string, unknown> | null = null;
  @state() configFormDirty = false;
  @state() configFormMode: "form" | "raw" = "form";
  @state() configSearchQuery = "";
  @state() configActiveSection: string | null = null;
  @state() configActiveSubsection: string | null = null;

  @state() channelsLoading = false;
  @state() channelsSnapshot: ChannelsStatusSnapshot | null = null;
  @state() channelsError: string | null = null;
  @state() channelsLastSuccess: number | null = null;
  @state() whatsappLoginMessage: string | null = null;
  @state() whatsappLoginQrDataUrl: string | null = null;
  @state() whatsappLoginConnected: boolean | null = null;
  @state() whatsappBusy = false;
  @state() nostrProfileFormState: NostrProfileFormState | null = null;
  @state() nostrProfileAccountId: string | null = null;

  @state() presenceLoading = false;
  @state() presenceEntries: PresenceEntry[] = [];
  @state() presenceError: string | null = null;
  @state() presenceStatus: string | null = null;

  @state() agentsLoading = false;
  @state() agentsList: AgentsListResult | null = null;
  @state() agentsError: string | null = null;
  @state() agentsSelectedId: string | null = null;
  @state() agentsPanel: "overview" | "files" | "tools" | "skills" | "channels" | "cron" =
    "overview";
  @state() agentFilesLoading = false;
  @state() agentFilesError: string | null = null;
  @state() agentFilesList: AgentsFilesListResult | null = null;
  @state() agentFileContents: Record<string, string> = {};
  @state() agentFileDrafts: Record<string, string> = {};
  @state() agentFileActive: string | null = null;
  @state() agentFileSaving = false;
  @state() agentIdentityLoading = false;
  @state() agentIdentityError: string | null = null;
  @state() agentIdentityById: Record<string, AgentIdentityResult> = {};
  @state() agentSkillsLoading = false;
  @state() agentSkillsError: string | null = null;
  @state() agentSkillsReport: SkillStatusReport | null = null;
  @state() agentSkillsAgentId: string | null = null;

  @state() sessionsLoading = false;
  @state() sessionsResult: SessionsListResult | null = null;
  @state() sessionsError: string | null = null;
  @state() sessionsFilterActive = "";
  @state() sessionsFilterLimit = "120";
  @state() sessionsIncludeGlobal = true;
  @state() sessionsIncludeUnknown = false;

  @state() usageLoading = false;
  @state() usageResult: import("./types.js").SessionsUsageResult | null = null;
  @state() usageCostSummary: import("./types.js").CostUsageSummary | null = null;
  @state() usageError: string | null = null;
  @state() usageStartDate = (() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  })();
  @state() usageEndDate = (() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  })();
  @state() usageSelectedSessions: string[] = [];
  @state() usageSelectedDays: string[] = [];
  @state() usageSelectedHours: number[] = [];
  @state() usageChartMode: "tokens" | "cost" = "tokens";
  @state() usageDailyChartMode: "total" | "by-type" = "by-type";
  @state() usageTimeSeriesMode: "cumulative" | "per-turn" = "per-turn";
  @state() usageTimeSeriesBreakdownMode: "total" | "by-type" = "by-type";
  @state() usageTimeSeries: import("./types.js").SessionUsageTimeSeries | null = null;
  @state() usageTimeSeriesLoading = false;
  @state() usageSessionLogs: import("./views/usage.js").SessionLogEntry[] | null = null;
  @state() usageSessionLogsLoading = false;
  @state() usageSessionLogsExpanded = false;
  // Applied query (used to filter the already-loaded sessions list client-side).
  @state() usageQuery = "";
  // Draft query text (updates immediately as the user types; applied via debounce or "Search").
  @state() usageQueryDraft = "";
  @state() usageSessionSort: "tokens" | "cost" | "recent" | "messages" | "errors" = "recent";
  @state() usageSessionSortDir: "desc" | "asc" = "desc";
  @state() usageRecentSessions: string[] = [];
  @state() usageTimeZone: "local" | "utc" = "local";
  @state() usageContextExpanded = false;
  @state() usageHeaderPinned = false;
  @state() usageSessionsTab: "all" | "recent" = "all";
  @state() usageVisibleColumns: string[] = [
    "channel",
    "agent",
    "provider",
    "model",
    "messages",
    "tools",
    "errors",
    "duration",
  ];
  @state() usageLogFilterRoles: import("./views/usage.js").SessionLogRole[] = [];
  @state() usageLogFilterTools: string[] = [];
  @state() usageLogFilterHasTools = false;
  @state() usageLogFilterQuery = "";

  // Non-reactive (don’t trigger renders just for timer bookkeeping).
  usageQueryDebounceTimer: number | null = null;

  @state() cronLoading = false;
  @state() cronJobs: CronJob[] = [];
  @state() cronStatus: CronStatus | null = null;
  @state() cronError: string | null = null;
  @state() cronForm: CronFormState = { ...DEFAULT_CRON_FORM };
  @state() cronRunsJobId: string | null = null;
  @state() cronRuns: CronRunLogEntry[] = [];
  @state() cronBusy = false;

  @state() skillsLoading = false;
  @state() skillsReport: SkillStatusReport | null = null;
  @state() skillsError: string | null = null;
  @state() skillsFilter = "";
  @state() skillEdits: Record<string, string> = {};
  @state() skillsBusyKey: string | null = null;
  @state() skillMessages: Record<string, SkillMessage> = {};

  @state() debugLoading = false;
  @state() debugStatus: StatusSummary | null = null;
  @state() debugHealth: HealthSnapshot | null = null;
  @state() debugModels: unknown[] = [];
  @state() debugHeartbeat: unknown = null;
  @state() debugCallMethod = "";
  @state() debugCallParams = "{}";
  @state() debugCallResult: string | null = null;
  @state() debugCallError: string | null = null;

  @state() logsLoading = false;
  @state() logsError: string | null = null;
  @state() logsFile: string | null = null;
  @state() logsEntries: LogEntry[] = [];
  @state() logsFilterText = "";
  @state() logsLevelFilters: Record<LogLevel, boolean> = {
    ...DEFAULT_LOG_LEVEL_FILTERS,
  };
  @state() logsAutoFollow = true;
  @state() logsTruncated = false;
  @state() logsCursor: number | null = null;
  @state() logsLastFetchAt: number | null = null;
  @state() logsLimit = 500;
  @state() logsMaxBytes = 250_000;
  @state() logsAtBottom = true;

  client: GatewayBrowserClient | null = null;
  private chatScrollFrame: number | null = null;
  private chatScrollTimeout: number | null = null;
  private chatHasAutoScrolled = false;
  private chatUserNearBottom = true;
  @state() chatNewMessagesBelow = false;
  private nodesPollInterval: number | null = null;
  private logsPollInterval: number | null = null;
  private debugPollInterval: number | null = null;
  private logsScrollFrame: number | null = null;
  private toolStreamById = new Map<string, ToolStreamEntry>();
  private toolStreamOrder: string[] = [];
  refreshSessionsAfterChat = new Set<string>();
  basePath = "";
  private popStateHandler = () =>
    onPopStateInternal(this as unknown as Parameters<typeof onPopStateInternal>[0]);
  private themeMedia: MediaQueryList | null = null;
  private themeMediaHandler: ((event: MediaQueryListEvent) => void) | null = null;
  private topbarObserver: ResizeObserver | null = null;

  createRenderRoot() {
    return this;
  }

  connectedCallback() {
    super.connectedCallback();
    handleConnected(this as unknown as Parameters<typeof handleConnected>[0]);
  }

  protected firstUpdated() {
    handleFirstUpdated(this as unknown as Parameters<typeof handleFirstUpdated>[0]);
  }

  disconnectedCallback() {
    handleDisconnected(this as unknown as Parameters<typeof handleDisconnected>[0]);
    super.disconnectedCallback();
  }

  protected updated(changed: Map<PropertyKey, unknown>) {
    handleUpdated(this as unknown as Parameters<typeof handleUpdated>[0], changed);
  }

  connect() {
    connectGatewayInternal(this as unknown as Parameters<typeof connectGatewayInternal>[0]);
  }

  handleChatScroll(event: Event) {
    handleChatScrollInternal(
      this as unknown as Parameters<typeof handleChatScrollInternal>[0],
      event,
    );
  }

  handleLogsScroll(event: Event) {
    handleLogsScrollInternal(
      this as unknown as Parameters<typeof handleLogsScrollInternal>[0],
      event,
    );
  }

  exportLogs(lines: string[], label: string) {
    exportLogsInternal(lines, label);
  }

  resetToolStream() {
    resetToolStreamInternal(this as unknown as Parameters<typeof resetToolStreamInternal>[0]);
  }

  resetChatScroll() {
    resetChatScrollInternal(this as unknown as Parameters<typeof resetChatScrollInternal>[0]);
  }

  scrollToBottom(opts?: { smooth?: boolean }) {
    resetChatScrollInternal(this as unknown as Parameters<typeof resetChatScrollInternal>[0]);
    scheduleChatScrollInternal(
      this as unknown as Parameters<typeof scheduleChatScrollInternal>[0],
      true,
      Boolean(opts?.smooth),
    );
  }

  async loadAssistantIdentity() {
    await loadAssistantIdentityInternal(this);
  }

  applySettings(next: UiSettings) {
    applySettingsInternal(this as unknown as Parameters<typeof applySettingsInternal>[0], next);
  }

  setTab(next: Tab) {
    setTabInternal(this as unknown as Parameters<typeof setTabInternal>[0], next);
  }

  setTheme(next: ThemeMode, context?: Parameters<typeof setThemeInternal>[2]) {
    setThemeInternal(this as unknown as Parameters<typeof setThemeInternal>[0], next, context);
  }

  async loadOverview() {
    await loadOverviewInternal(this as unknown as Parameters<typeof loadOverviewInternal>[0]);
  }

  async loadCron() {
    await loadCronInternal(this as unknown as Parameters<typeof loadCronInternal>[0]);
  }

  async handleAbortChat() {
    await handleAbortChatInternal(this as unknown as Parameters<typeof handleAbortChatInternal>[0]);
  }

  removeQueuedMessage(id: string) {
    removeQueuedMessageInternal(
      this as unknown as Parameters<typeof removeQueuedMessageInternal>[0],
      id,
    );
  }

  async handleSendChat(
    messageOverride?: string,
    opts?: Parameters<typeof handleSendChatInternal>[2],
  ) {
    await handleSendChatInternal(
      this as unknown as Parameters<typeof handleSendChatInternal>[0],
      messageOverride,
      opts,
    );
  }

  private appendMoonshineText(text: string) {
    let trimmed = text.replace(/\s+/g, " ").trim();
    // Remove common junk prefixes from chunked STT (e.g., ". . ." / "..." / "uh uh uh")
    trimmed = trimmed.replace(/^(?:[.\u2026]\s*){2,}/, "");
    trimmed = trimmed.replace(/^\b(\w+)(?:\s+\1){2,}\b\s*/i, "");
    if (!trimmed) {
      return;
    }

    const normalizedChunk = trimmed.toLowerCase().replace(/[\p{P}\p{S}]+/gu, "").trim();
    if (normalizedChunk && normalizedChunk === this.moonshineLastChunkNorm) {
      this.moonshineRepeatCount += 1;
      if (this.moonshineRepeatCount >= 2) {
        return;
      }
    } else {
      this.moonshineLastChunkNorm = normalizedChunk;
      this.moonshineRepeatCount = 0;
    }

    const existing = this.chatMessage.trim();
    if (existing.length > 0) {
      // Skip exact repeat chunk
      if (existing.endsWith(trimmed)) {
        return;
      }
      // Trim overlapping prefix when live chunks repeat boundary words.
      const maxOverlap = Math.min(80, existing.length, trimmed.length);
      for (let i = maxOverlap; i >= 12; i--) {
        if (existing.endsWith(trimmed.slice(0, i))) {
          trimmed = trimmed.slice(i).trimStart();
          break;
        }
      }
      if (!trimmed) {
        return;
      }
    }

    this.chatMessage = existing.length > 0 ? `${existing} ${trimmed}` : trimmed;
  }

  private async transcribeMoonshineChunk(audioBase64: string, token: number, phase: string) {
    if (!this.client || !audioBase64) {
      return;
    }
    this.moonshineBusy = true;
    try {
      const whisperModelMap: Record<string, string> = {
        "whisper-tiny": "tiny",
        "whisper-base": "base",
        "whisper-small": "small",
        "whisper-large": "large",
      };
      const useWhisper = this.moonshineModel.startsWith("whisper-");
      const useParakeet = this.moonshineModel === "parakeet-v2";
      const selectedModel = useWhisper
        ? (whisperModelMap[this.moonshineModel] ?? "base")
        : useParakeet
          ? "nvidia/parakeet-tdt-0.6b-v2"
          : this.moonshineModel;
      const method = useWhisper
        ? "whisper.transcribe"
        : useParakeet
          ? "parakeet.transcribe"
          : "moonshine.transcribe";
      const res = (await this.client.request(method, {
        audioBase64,
        model: selectedModel,
        language: "en",
        maxSeconds: useWhisper || useParakeet ? 600 : 15,
      })) as { text?: string };

      if (token !== this.moonshineSessionToken) {
        return;
      }
      // Hard guard: ignore stale live chunks when transcription is no longer recording.
      if (phase !== "stop" && !this.moonshineRecording) {
        return;
      }

      const text = (res?.text ?? "").trim();
      if (!text) {
        return;
      }
      this.appendMoonshineText(text);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);

      // Compatibility fallback: if gateway doesn't have parakeet yet,
      // transparently fall back to whisper-tiny so STT still works.
      if (this.moonshineModel === "parakeet-v2" && /unknown method:\s*parakeet\.transcribe/i.test(msg)) {
        try {
          const res = (await this.client.request("whisper.transcribe", {
            audioBase64,
            model: "tiny",
            language: "en",
            maxSeconds: 600,
          })) as { text?: string };

          if (token === this.moonshineSessionToken && (phase === "stop" || this.moonshineRecording)) {
            const text = (res?.text ?? "").trim();
            if (text) {
              this.appendMoonshineText(text);
            }
          }

          this.lastError = "Parakeet backend not loaded yet; temporarily using Whisper Tiny.";
          return;
        } catch {
          // fall through to normal error handling
        }
      }

      this.lastError = `Moonshine failed: ${msg}`;
      console.error("moonshine-debug", { model: this.moonshineModel, phase, error: err });
    } finally {
      this.moonshineBusy = false;
    }
  }

  private stopMoonshineLiveTimer() {
    if (this.moonshineLiveTimer != null) {
      window.clearInterval(this.moonshineLiveTimer);
      this.moonshineLiveTimer = null;
    }
  }

  private async handleMoonshineLiveTick(token: number) {
    if (!this.moonshineRecording || this.moonshineLiveInFlight || token !== this.moonshineSessionToken) {
      return;
    }

    // For heavier models (Whisper/Parakeet), defer transcription until stop (final-only).
    if (this.moonshineModel.startsWith("whisper-") || this.moonshineModel === "parakeet-v2") {
      return;
    }

    const capture = this.moonshineCapture;
    if (!capture) {
      return;
    }

    const chunk = capture.takeChunkBase64();
    if (!chunk) {
      return;
    }

    this.moonshineLiveInFlight = true;
    try {
      await this.transcribeMoonshineChunk(chunk, token, "live");
    } finally {
      this.moonshineLiveInFlight = false;
    }
  }

  async handleMoonshinePTTStart() {
    if (!this.connected || !this.client || this.moonshineBusy || this.moonshineRecording) {
      return;
    }
    this.lastError = null;
    this.moonshineRecording = true;
    this.moonshineSessionToken += 1;
    this.moonshineLastChunkNorm = "";
    this.moonshineRepeatCount = 0;
    const token = this.moonshineSessionToken;

    try {
      this.moonshineCapture = await startMicWavCapture();
      this.stopMoonshineLiveTimer();
      this.moonshineLiveTimer = window.setInterval(() => {
        void this.handleMoonshineLiveTick(token);
      }, 1200);
    } catch (err) {
      this.moonshineRecording = false;
      this.moonshineCapture = null;
      const msg = err instanceof Error ? err.message : String(err);
      this.lastError = `Moonshine failed to start: ${msg}`;
      console.error("moonshine-debug", { model: this.moonshineModel, phase: "start", error: err });
    }
  }

  async handleMoonshinePTTStop() {
    if (!this.moonshineRecording) {
      return;
    }

    this.moonshineRecording = false;
    // Show processing state immediately on release for clearer UX.
    this.moonshineBusy = true;
    this.stopMoonshineLiveTimer();

    const capture = this.moonshineCapture;
    this.moonshineCapture = null;
    const token = this.moonshineSessionToken;

    if (!capture) {
      this.moonshineBusy = false;
      return;
    }

    try {
      // Flush any remaining unsent samples after release.
      const tail = capture.takeChunkBase64(1, true);
      await capture.stop();
      if (tail) {
        await this.transcribeMoonshineChunk(tail, token, "stop");
      } else {
        this.moonshineBusy = false;
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      this.lastError = `Moonshine failed: ${msg}`;
      this.moonshineBusy = false;
      console.error("moonshine-debug", { model: this.moonshineModel, phase: "stop", error: err });
    } finally {
      this.moonshineLiveInFlight = false;
      this.moonshineLastChunkNorm = "";
      this.moonshineRepeatCount = 0;
    }
  }

  async handleMoonshinePTTCancel() {
    this.moonshineRecording = false;
    this.stopMoonshineLiveTimer();
    this.moonshineSessionToken += 1;
    this.moonshineLiveInFlight = false;
    this.moonshineLastChunkNorm = "";
    this.moonshineRepeatCount = 0;

    const capture = this.moonshineCapture;
    this.moonshineCapture = null;
    if (!capture) {
      return;
    }
    try {
      await capture.cancel();
    } catch {
      // ignore cancel cleanup errors
    }
  }

  async handleMoonshineTranscribe() {
    if (this.moonshineRecording) {
      await this.handleMoonshinePTTStop();
      return;
    }
    await this.handleMoonshinePTTStart();
  }

  async handleWhatsAppStart(force: boolean) {
    await handleWhatsAppStartInternal(this, force);
  }

  async handleWhatsAppWait() {
    await handleWhatsAppWaitInternal(this);
  }

  async handleWhatsAppLogout() {
    await handleWhatsAppLogoutInternal(this);
  }

  async handleChannelConfigSave() {
    await handleChannelConfigSaveInternal(this);
  }

  async handleChannelConfigReload() {
    await handleChannelConfigReloadInternal(this);
  }

  handleNostrProfileEdit(accountId: string, profile: NostrProfile | null) {
    handleNostrProfileEditInternal(this, accountId, profile);
  }

  handleNostrProfileCancel() {
    handleNostrProfileCancelInternal(this);
  }

  handleNostrProfileFieldChange(field: keyof NostrProfile, value: string) {
    handleNostrProfileFieldChangeInternal(this, field, value);
  }

  async handleNostrProfileSave() {
    await handleNostrProfileSaveInternal(this);
  }

  async handleNostrProfileImport() {
    await handleNostrProfileImportInternal(this);
  }

  handleNostrProfileToggleAdvanced() {
    handleNostrProfileToggleAdvancedInternal(this);
  }

  async handleExecApprovalDecision(decision: "allow-once" | "allow-always" | "deny") {
    const active = this.execApprovalQueue[0];
    if (!active || !this.client || this.execApprovalBusy) {
      return;
    }
    this.execApprovalBusy = true;
    this.execApprovalError = null;
    try {
      await this.client.request("exec.approval.resolve", {
        id: active.id,
        decision,
      });
      this.execApprovalQueue = this.execApprovalQueue.filter((entry) => entry.id !== active.id);
    } catch (err) {
      this.execApprovalError = `Exec approval failed: ${String(err)}`;
    } finally {
      this.execApprovalBusy = false;
    }
  }

  handleGatewayUrlConfirm() {
    const nextGatewayUrl = this.pendingGatewayUrl;
    if (!nextGatewayUrl) {
      return;
    }
    this.pendingGatewayUrl = null;
    applySettingsInternal(this as unknown as Parameters<typeof applySettingsInternal>[0], {
      ...this.settings,
      gatewayUrl: nextGatewayUrl,
    });
    this.connect();
  }

  handleGatewayUrlCancel() {
    this.pendingGatewayUrl = null;
  }

  // Sidebar handlers for tool output viewing
  handleOpenSidebar(content: string) {
    if (this.sidebarCloseTimer != null) {
      window.clearTimeout(this.sidebarCloseTimer);
      this.sidebarCloseTimer = null;
    }
    this.sidebarContent = content;
    this.sidebarError = null;
    this.sidebarOpen = true;
  }

  handleCloseSidebar() {
    this.sidebarOpen = false;
    // Clear content after transition
    if (this.sidebarCloseTimer != null) {
      window.clearTimeout(this.sidebarCloseTimer);
    }
    this.sidebarCloseTimer = window.setTimeout(() => {
      if (this.sidebarOpen) {
        return;
      }
      this.sidebarContent = null;
      this.sidebarError = null;
      this.sidebarCloseTimer = null;
    }, 200);
  }

  handleSplitRatioChange(ratio: number) {
    const newRatio = Math.max(0.4, Math.min(0.7, ratio));
    this.splitRatio = newRatio;
    this.applySettings({ ...this.settings, splitRatio: newRatio });
  }

  render() {
    return renderApp(this as unknown as AppViewState);
  }
}
