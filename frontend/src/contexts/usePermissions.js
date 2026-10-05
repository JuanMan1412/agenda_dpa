import { createContext, useContext } from "react";

export const PermissionsContext = createContext(null);

export function usePermissions() {
  const context = useContext(PermissionsContext);
  if (!context) throw new Error("usePermissions debe usarse dentro de PermissionsProvider");
  return context;
}
