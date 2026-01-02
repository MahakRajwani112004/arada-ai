"use client";

import { createContext, useContext } from "react";

interface CanvasContextValue {
  markUnsaved: () => void;
}

export const CanvasContext = createContext<CanvasContextValue>({
  markUnsaved: () => {},
});

export function useCanvasContext() {
  return useContext(CanvasContext);
}
