import type { GatewayRequestHandlers } from "./types.js";
import { ErrorCodes, errorShape } from "../protocol/index.js";

function isBase64(v: string): boolean {
  return /^[A-Za-z0-9+/]+={0,2}$/.test(v) && v.length % 4 === 0;
}

export const whisperHandlers: GatewayRequestHandlers = {
  "whisper.transcribe": async ({ respond, params }) => {
    const p = (params ?? {}) as {
      audioBase64?: unknown;
      model?: unknown;
      language?: unknown;
      prompt?: unknown;
    };

    const apiKey = process.env.OPENAI_API_KEY?.trim() || "";
    if (!apiKey) {
      respond(false, undefined, errorShape(ErrorCodes.UNAVAILABLE, "OPENAI_API_KEY is not set"));
      return;
    }

    const audioBase64 = typeof p.audioBase64 === "string" ? p.audioBase64.trim() : "";
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
      respond(
        false,
        undefined,
        errorShape(ErrorCodes.INVALID_REQUEST, "audio payload too large (max 20MB)"),
      );
      return;
    }

    const model = typeof p.model === "string" && p.model.trim() ? p.model.trim() : "whisper-1";
    const language = typeof p.language === "string" && p.language.trim() ? p.language.trim() : "en";
    const prompt = typeof p.prompt === "string" && p.prompt.trim() ? p.prompt.trim() : undefined;

    try {
      const form = new FormData();
      form.append("model", model);
      form.append("language", language);
      if (prompt) {
        form.append("prompt", prompt);
      }
      form.append("response_format", "json");
      form.append("file", new Blob([bytes], { type: "audio/wav" }), "input.wav");

      const res = await fetch("https://api.openai.com/v1/audio/transcriptions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
        body: form,
      });

      const textBody = await res.text();
      if (!res.ok) {
        respond(
          false,
          undefined,
          errorShape(
            ErrorCodes.UNAVAILABLE,
            `whisper transcribe failed (${res.status}): ${textBody.slice(0, 500)}`,
          ),
        );
        return;
      }

      let parsed: { text?: string } = {};
      try {
        parsed = JSON.parse(textBody) as { text?: string };
      } catch {
        // ignore parse errors; will fallback to raw body
      }

      const text = (parsed.text ?? "").trim() || textBody.trim();
      respond(true, { ok: true, text, model, language });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      respond(false, undefined, errorShape(ErrorCodes.UNAVAILABLE, `whisper transcribe failed: ${message}`));
    }
  },
};
