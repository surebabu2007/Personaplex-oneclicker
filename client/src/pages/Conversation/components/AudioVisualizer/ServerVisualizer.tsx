import { FC, RefObject, useCallback, useEffect, useRef, useState } from "react";
import { clamp } from "../../hooks/audioUtils";
import { useSocketContext } from "../../SocketContext";
import { type ThemeType } from "../../hooks/useSystemTheme";

type AudioVisualizerProps = {
  analyser: AnalyserNode | null;
  parent: RefObject<HTMLElement>;
  theme: ThemeType;
};

const MAX_INTENSITY = 255;

export const ServerVisualizer: FC<AudioVisualizerProps> = ({ analyser, parent, theme }) => {
  const [canvasWidth, setCanvasWidth] = useState( parent.current ? Math.min(parent.current.clientWidth, parent.current.clientHeight) : 0 );
  const requestRef = useRef<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const { socketStatus } = useSocketContext();

  const draw = useCallback((width: number, centerX:number, centerY:number,audioData: Uint8Array, ctx: CanvasRenderingContext2D) => {
    const maxCircleWidth = Math.floor(width * 0.95);
    const averageIntensity = Math.sqrt(
      audioData.reduce((acc, curr) => acc + curr * curr, 0) / audioData.length,
    );
    const intensity = clamp(
      averageIntensity * 1.4,
      averageIntensity,
      MAX_INTENSITY,
    );
    const relIntensity = intensity / MAX_INTENSITY;
    const radius = ((socketStatus === "connected" ? 0.3 + 0.7 * relIntensity : relIntensity) * maxCircleWidth) / 2;
    // Draw a circle with radius based on intensity
    ctx.clearRect( centerX - width /2, centerY - width/2 , width, width);
    ctx.fillStyle = theme === "dark" ? "#000000" : "#fafafa";
    ctx.fillRect(centerX - width / 2, centerY - width / 2, width, width);
    ctx.beginPath();
    ctx.fillStyle = "#4E8800";
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.fill();
    ctx.closePath();

    // Draw an inner circle if we are connected.
    if (socketStatus === "connected") {
      ctx.beginPath();
      ctx.arc(centerX, centerY, maxCircleWidth / 6, 0, 2 * Math.PI);
      ctx.fillStyle = "#76B900";
      ctx.fill();
      ctx.closePath();
    }

    //Draw a circle with max radius
    ctx.beginPath();
    ctx.arc(centerX, centerY, maxCircleWidth / 2, 0, 2 * Math.PI);
    ctx.strokeStyle = theme === "dark" ? "white" : "black";
    ctx.lineWidth = width / 50;
    ctx.stroke();
    ctx.closePath();
  }, [socketStatus]);

  const visualizeData = useCallback(() => {
    const width = parent.current ? Math.min(parent.current.clientWidth, parent.current.clientHeight) : 0;
    if (width !== canvasWidth) {
      setCanvasWidth(width);
    }
    requestRef.current = window.requestAnimationFrame(() => visualizeData());
    if (!canvasRef.current) {
      console.log("Canvas not found");
      return;
    }
    const ctx = canvasRef.current.getContext("2d");
    const audioData = new Uint8Array(140);
    analyser?.getByteFrequencyData(audioData);
    if(!ctx){
      console.log("Canvas context not found");
      return;
    }
    const centerX = width / 2;
    const centerY = width / 2;
    draw(width, centerX, centerY, audioData, ctx);
  }, [analyser, socketStatus, canvasWidth, parent]);


  useEffect(() => {
    if (!analyser) {
      return;
    }
    analyser.smoothingTimeConstant = 0.95;
    visualizeData();
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [visualizeData, analyser]);

  return (
    <canvas
      className="max-h-full max-w-full"
      ref={canvasRef}
      width={canvasWidth}
      height={canvasWidth}
    />
  );
};
