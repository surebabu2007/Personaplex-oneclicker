import moshiProcessorUrl from "../../audio-processor.ts?worker&url";
import { FC, useEffect, useState, useCallback, useRef, MutableRefObject } from "react";
import eruda from "eruda";
import { useSearchParams } from "react-router-dom";
import { Conversation } from "../Conversation/Conversation";
import { Button } from "../../components/Button/Button";
import { useModelParams } from "../Conversation/hooks/useModelParams";
import { env } from "../../env";
import { prewarmDecoderWorker } from "../../decoder/decoderWorker";

const VOICE_OPTIONS = [
  "NATF0.pt", "NATF1.pt", "NATF2.pt", "NATF3.pt",
  "NATM0.pt", "NATM1.pt", "NATM2.pt", "NATM3.pt",
  "VARF0.pt", "VARF1.pt", "VARF2.pt", "VARF3.pt", "VARF4.pt",
  "VARM0.pt", "VARM1.pt", "VARM2.pt", "VARM3.pt", "VARM4.pt",
];

const TEXT_PROMPT_PRESETS = [
  {
    label: "Assistant (default)",
    text: "You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.",
  },
  {
    label: "Medical office (service)",
    text: "You work for Dr. Jones's medical office, and you are receiving calls to record information for new patients. Information: Record full name, date of birth, any medication allergies, tobacco smoking history, alcohol consumption history, and any prior medical conditions. Assure the patient that this information will be confidential, if they ask.",
  },
  {
    label: "Bank (service)",
    text: "You work for First Neuron Bank which is a bank and your name is Alexis Kim. Information: The customer's transaction for $1,200 at Home Depot was declined. Verify customer identity. The transaction was flagged due to unusual location (transaction attempted in Miami, FL; customer normally transacts in Seattle, WA).",
  },
  {
    label: "Astronaut (fun)",
    text: "You enjoy having a good conversation. Have a technical discussion about fixing a reactor core on a spaceship to Mars. You are an astronaut on a Mars mission. Your name is Alex. You are already dealing with a reactor core meltdown on a Mars mission. Several ship systems are failing, and continued instability will lead to catastrophic failure. You explain what is happening and you urgently ask for help thinking through how to stabilize the reactor.",
  },
];

interface HomepageProps {
  showMicrophoneAccessMessage: boolean;
  hasMicrophoneAccess: boolean;
  startConnection: () => Promise<void>;
  textPrompt: string;
  setTextPrompt: (value: string) => void;
  voicePrompt: string;
  setVoicePrompt: (value: string) => void;
}

const Homepage = ({
  startConnection,
  showMicrophoneAccessMessage,
  hasMicrophoneAccess,
  textPrompt,
  setTextPrompt,
  voicePrompt,
  setVoicePrompt,
}: HomepageProps) => {
  const setupProgress = hasMicrophoneAccess ? 70 : 30;
  const setupLabel = hasMicrophoneAccess
    ? "Mic Ready"
    : showMicrophoneAccessMessage
      ? "Mic Blocked"
      : "Ready";
  return (
    <div className="ppx-shell">
      <div className="ppx-ambient" />
      <div className="ppx-card ppx-card--wide">
        <div className="ppx-header">
          <div className="ppx-title">PersonaPlex</div>
          <div className="ppx-tagline">Simplified &amp; one-click install by SurAiverse</div>
          <div className="ppx-subtag">Based on NVIDIA PersonaPlex 7B</div>
        </div>

        <div className="ppx-progress">
          <div className="ppx-progress-row">
            <span>Setup</span>
            <span>{setupLabel}</span>
          </div>
          <div className="ppx-progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={setupProgress}>
            <div className="ppx-progress-bar" style={{ width: `${setupProgress}%` }} />
          </div>
          <div className="ppx-progress-steps">
            <span className="active">Ready</span>
            <span className={hasMicrophoneAccess ? "active" : ""}>Mic Ready</span>
            <span>Connect</span>
          </div>
        </div>

        <div className="ppx-divider" />

        <div className="flex flex-col gap-6">
          <div className="ppx-panel">
            <label htmlFor="text-prompt" className="block text-left text-sm uppercase tracking-[0.18em] text-[#6e5d3b] mb-3">
              Text Prompt
            </label>
            <div className="ppx-field mb-3">
              <span className="text-[0.7rem] uppercase tracking-[0.2em] text-[#8a7a5a] block mb-2">Examples</span>
              <div className="flex flex-wrap gap-2 justify-center">
                {TEXT_PROMPT_PRESETS.map((preset) => (
                  <button
                    key={preset.label}
                    onClick={() => setTextPrompt(preset.text)}
                    className="px-3 py-1 text-xs bg-white/80 hover:bg-white text-[#5f5136] rounded-full border border-[#d3c3a4] transition-colors"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              id="text-prompt"
              name="text-prompt"
              value={textPrompt}
              onChange={(e) => setTextPrompt(e.target.value)}
              className="ppx-field w-full h-32 min-h-[90px] max-h-72 resize-y"
              placeholder="Enter your text prompt..."
              maxLength={1000}
            />
            <div className="text-right text-xs text-[#7b6a4a] mt-2">
              {textPrompt.length}/1000
            </div>
          </div>

          <div className="ppx-panel">
            <label htmlFor="voice-prompt" className="block text-left text-sm uppercase tracking-[0.18em] text-[#6e5d3b] mb-3">
              Voice
            </label>
            <select
              id="voice-prompt"
              name="voice-prompt"
              value={voicePrompt}
              onChange={(e) => setVoicePrompt(e.target.value)}
              className="ppx-field w-full"
            >
              {VOICE_OPTIONS.map((voice) => (
                <option key={voice} value={voice}>
                  {voice
                    .replace('.pt', '')
                    .replace(/^NAT/, 'NATURAL_')
                    .replace(/^VAR/, 'VARIETY_')}
                </option>
              ))}
            </select>
          </div>

          {showMicrophoneAccessMessage && (
            <p className="text-center text-red-600">Please enable your microphone before proceeding</p>
          )}

          <div className="flex flex-col items-center gap-3">
            <Button onClick={async () => await startConnection()}>Connect</Button>
            <span className="ppx-pill">Immersive voice session</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export const Queue:FC = () => {
  const theme = "light" as const;  // Always use light theme
  const [searchParams] = useSearchParams();
  const overrideWorkerAddr = searchParams.get("worker_addr");
  const [hasMicrophoneAccess, setHasMicrophoneAccess] = useState<boolean>(false);
  const [showMicrophoneAccessMessage, setShowMicrophoneAccessMessage] = useState<boolean>(false);
  const modelParams = useModelParams();

  const audioContext = useRef<AudioContext | null>(null);
  const worklet = useRef<AudioWorkletNode | null>(null);
  
  // enable eruda in development
  useEffect(() => {
    if(env.VITE_ENV === "development") {
      eruda.init();
    }
    () => {
      if(env.VITE_ENV === "development") {
        eruda.destroy();
      }
    };
  }, []);

  const getMicrophoneAccess = useCallback(async () => {
    try {
      await window.navigator.mediaDevices.getUserMedia({ audio: true });
      setHasMicrophoneAccess(true);
      return true;
    } catch(e) {
      console.error(e);
      setShowMicrophoneAccessMessage(true);
      setHasMicrophoneAccess(false);
    }
    return false;
}, [setHasMicrophoneAccess, setShowMicrophoneAccessMessage]);

  const startProcessor = useCallback(async () => {
    if(!audioContext.current) {
      audioContext.current = new AudioContext();
      // Prewarm decoder worker as soon as we have audio context
      // This gives WASM time to load while user grants mic access
      prewarmDecoderWorker(audioContext.current.sampleRate);
    }
    if(worklet.current) {
      return;
    }
    let ctx = audioContext.current;
    ctx.resume();
    try {
      worklet.current = new AudioWorkletNode(ctx, 'moshi-processor');
    } catch (err) {
      await ctx.audioWorklet.addModule(moshiProcessorUrl);
      worklet.current = new AudioWorkletNode(ctx, 'moshi-processor');
    }
    worklet.current.connect(ctx.destination);
  }, [audioContext, worklet]);

  const startConnection = useCallback(async() => {
      await startProcessor();
      const hasAccess = await getMicrophoneAccess();
      if (hasAccess) {
      // Values are already set in modelParams, they get passed to Conversation
    }
  }, [startProcessor, getMicrophoneAccess]);

  return (
    <>
      {(hasMicrophoneAccess && audioContext.current && worklet.current) ? (
        <Conversation
        workerAddr={overrideWorkerAddr ?? ""}
        audioContext={audioContext as MutableRefObject<AudioContext|null>}
        worklet={worklet as MutableRefObject<AudioWorkletNode|null>}
        theme={theme}
        startConnection={startConnection}
        {...modelParams}
        />
      ) : (
        <Homepage
          startConnection={startConnection}
          showMicrophoneAccessMessage={showMicrophoneAccessMessage}
          hasMicrophoneAccess={hasMicrophoneAccess}
          textPrompt={modelParams.textPrompt}
          setTextPrompt={modelParams.setTextPrompt}
          voicePrompt={modelParams.voicePrompt}
          setVoicePrompt={modelParams.setVoicePrompt}
        />
      )}
    </>
  );
};
