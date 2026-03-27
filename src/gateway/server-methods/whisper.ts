import { existsSync, promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { GatewayRequestHandlers } from "./types.js";
import { ErrorCodes, errorShape } from "../protocol/index.js";

const execFileAsync = promisify(execFile);

function isBase64(v: string): boolean {
  return /^[A-Za-z0-9+/]+={0,2}$/.test(v) && v.length % 4 === 0;
}

export const whisperHandlers: GatewayRequestHandlers = {
  "whisper.transcribe": async ({ respond, params }) => {
    const p = (params ?? {}) as {
      audioBase64?: unknown;
      model?: unknown;
      language?: unknown;
      maxSeconds?: unknown;
    };

    const audioBase64 = typeof p.audioBase64 === "string" ? p.audioBase64.trim() : "";
    const modelRaw = typeof p.model === "string" ? p.model.trim().toLowerCase() : "base";
    const model = ["tiny", "base", "small", "medium", "large", "large-v3"].includes(modelRaw)
      ? modelRaw
      : "base";
    const language = typeof p.language === "string" && p.language.trim() ? p.language.trim() : "en";
    const modelDefaultMaxSeconds: Record<string, number> = {
      tiny: 120,
      base: 180,
      small: 300,
      medium: 600,
      large: 1200,
      "large-v3": 1200,
    };
    const requestedMaxSeconds =
      typeof p.maxSeconds === "number" && Number.isFinite(p.maxSeconds) ? Math.floor(p.maxSeconds) : undefined;
    const maxSeconds = Math.max(
      5,
      Math.min(1800, requestedMaxSeconds ?? modelDefaultMaxSeconds[model] ?? 180),
    );

    if (!audioBase64) {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "audioBase64 required"));
      return;
    }
    if (!isBase64(audioBase64)) {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "invalid base64 audio payload"));
      return;
    }

    const bytes = Buffer.from(audioBase64, "base64");
    if (bytes.length === 0 || bytes.length > 20_000_000) {
      respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "audio payload too large (max 20MB)"));
      return;
    }

    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "openclaw-whisper-"));
    const wavPath = path.join(tmpDir, "input.wav");

    const entryPath = process.argv[1] ? path.resolve(process.argv[1]) : "";
    const repoFromEntry = entryPath ? path.resolve(path.dirname(entryPath), "..") : "";
    const candidateScriptPaths = [
      path.resolve(repoFromEntry, "skills", "openai-whisper", "scripts", "transcribe_wav.py"),
      path.resolve(process.cwd(), "skills", "openai-whisper", "scripts", "transcribe_wav.py"),
    ].filter(Boolean);
    const scriptPath = candidateScriptPaths.find((p) => existsSync(p));

    if (!scriptPath) {
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.UNAVAILABLE, `whisper script missing; checked: ${candidateScriptPaths.join(", ")}`),
      );
      await fs.rm(tmpDir, { recursive: true, force: true }).catch(() => undefined);
      return;
    }

    try {
      await fs.writeFile(wavPath, bytes);
      const { stdout, stderr } = await execFileAsync(
        "python",
        [scriptPath, "--input", wavPath, "--model", model, "--language", language],
        { timeout: maxSeconds * 1000, windowsHide: true, maxBuffer: 64 * 1024 * 1024 },
      );

      const text = (stdout ?? "").trim();
      respond(true, { ok: true, text, model, language, stderr: (stderr ?? "").trim() || undefined });
    } catch (err) {
      const rawMessage = err instanceof Error ? err.message : String(err);
      const message = rawMessage.length > 2000 ? `${rawMessage.slice(0, 2000)}…` : rawMessage;
      const hint = /checksum does not match|re-downloading the file/i.test(rawMessage)
        ? " Whisper model cache is being refreshed; large models may need several minutes on first retry."
        : /timed out|timeout/i.test(rawMessage)
          ? " Whisper timed out; try again or use a smaller model while large finishes warming up."
          : "";
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.UNAVAILABLE, `local whisper transcribe failed: ${message}${hint}`),
      );
    } finally {
      await fs.rm(tmpDir, { recursive: true, force: true }).catch(() => undefined);
    }
  },
};
