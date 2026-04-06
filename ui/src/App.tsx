import { useState, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

type StepStatus = "waiting" | "running" | "done" | "failed";
type Phase = "preflight" | "idle" | "building" | "done" | "error";

type Step = { id: number; label: string; status: StepStatus };

const STEPS: Step[] = [
  { id: 0, label: "Grounding in live web data",    status: "waiting" },
  { id: 1, label: "Compressing intent",             status: "waiting" },
  { id: 2, label: "Generating interface mock",      status: "waiting" },
  { id: 3, label: "Parsing features",               status: "waiting" },
  { id: 4, label: "Mapping dependencies",           status: "waiting" },
  { id: 5, label: "Generating tasks + validation",  status: "waiting" },
  { id: 6, label: "Writing software",               status: "waiting" },
];

export default function App() {
  const [prompt, setPrompt]           = useState("");
  const [phase, setPhase]             = useState<Phase>("preflight");
  const [steps, setSteps]             = useState<Step[]>(STEPS);
  const [outputPath, setOutputPath]   = useState("");
  const [errorMsg, setErrorMsg]       = useState("");
  const [preflightLog, setPreflightLog] = useState("Checking Ollama + Gemma 4...");
  const textareaRef                   = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    invoke<string>("preflight_check")
      .then(log => { setPreflightLog(log); setPhase("idle"); })
      .catch(e  => { setPreflightLog(String(e)); setPhase("error"); });
  }, []);

  useEffect(() => {
    if (phase === "idle") textareaRef.current?.focus();
  }, [phase]);

  const mark = (id: number, status: StepStatus) =>
    setSteps(prev => prev.map(s => s.id === id ? { ...s, status } : s));

  const handleBuild = async () => {
    if (!prompt.trim()) return;
    setPhase("building");
    setSteps(STEPS.map(s => ({ ...s, status: "waiting" })));
    setErrorMsg("");

    for (let i = 0; i <= 6; i++) {
      mark(i, "running");
      try {
        await invoke("run_step", { step: i, prompt });
        mark(i, "done");
      } catch (e) {
        mark(i, "failed");
        setErrorMsg(String(e));
        setPhase("error");
        return;
      }
    }

    try {
      const path = await invoke<string>("get_output_path");
      setOutputPath(path);
    } catch { setOutputPath("./output"); }
    setPhase("done");
  };

  const reset = () => {
    setPhase("idle");
    setPrompt("");
    setOutputPath("");
    setErrorMsg("");
    setSteps(STEPS.map(s => ({ ...s, status: "waiting" })));
  };

  return (
    <div className="app">

      {phase === "preflight" && (
        <div className="composer">
          <div className="wordmark">local-ai-v5</div>
          <pre className="preflight-log">{preflightLog}</pre>
        </div>
      )}

      {phase === "idle" && (
        <div className="composer">
          <div className="wordmark">local-ai-v5</div>
          <p className="tagline">Describe what you want to build.</p>
          <textarea
            ref={textareaRef}
            className="input"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="A budget tracker with charts, categories, and CSV export..."
            rows={5}
            onKeyDown={e => { if (e.key === "Enter" && e.metaKey) handleBuild(); }}
          />
          <div className="row">
            <button className="build-btn" onClick={handleBuild} disabled={!prompt.trim()}>
              Build
            </button>
            <span className="hint">⌘↵  ·  Any language  ·  Fully offline</span>
          </div>
        </div>
      )}

      {phase === "building" && (
        <div className="progress">
          <div className="wordmark">local-ai-v5</div>
          <div className="steps">
            {steps.map(s => (
              <div key={s.id} className={`step step--${s.status}`}>
                <span className="dot" />
                <span className="label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {phase === "done" && (
        <div className="done">
          <div className="wordmark">local-ai-v5</div>
          <p className="done-msg">Your software is ready.</p>
          <p className="done-path">{outputPath}</p>
          <div className="done-row">
            <button className="open-btn" onClick={() => invoke("open_output_folder", { path: outputPath })}>
              Open folder
            </button>
            <button className="reset-btn" onClick={reset}>Build something else</button>
          </div>
        </div>
      )}

      {phase === "error" && (
        <div className="done">
          <div className="wordmark">local-ai-v5</div>
          <p className="done-msg">Something went wrong.</p>
          {errorMsg && <pre className="err">{errorMsg.slice(0, 500)}</pre>}
          <button className="reset-btn" onClick={reset}>Try again</button>
        </div>
      )}

    </div>
  );
}
