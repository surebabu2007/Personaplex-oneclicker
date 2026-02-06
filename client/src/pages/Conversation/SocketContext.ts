import { createContext, useContext } from "react";
import { type SocketStatus, type WSMessage } from "../../protocol/types";

type SocketContextType = {
  socketStatus: SocketStatus;
  socket: WebSocket | null;
  sendMessage: (message: WSMessage) => void;
};

export const SocketContext = createContext<SocketContextType>({
  socketStatus: "disconnected",
  socket: null,
  sendMessage: () => {},
});

export const useSocketContext = () => {
  return useContext(SocketContext);
};
