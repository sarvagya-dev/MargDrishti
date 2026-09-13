import { createContext, useContext, useMemo, useState } from "react";
import { getCases } from "@/services/api";
import { updateCaseStatus, createCase } from "@/services/api";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [caseList, setCaseList] = useState(() => [...getCases()]);
  const [driverAlertState, setDriverAlertState] = useState("CLEAR");

  const value = useMemo(
    () => ({
      cases: caseList,
      driverAlertState,
      addCase: (hotspotId) => {
        const created = createCase(hotspotId);
        setCaseList((prev) => [...prev, created]);
        return created;
      },
      updateCase: (caseId, status) => {
        updateCaseStatus(caseId, status);
        setCaseList((prev) => prev.map((c) => (c.id === caseId ? { ...c, status } : c)));
      },
      setDriverAlert: (state) => setDriverAlertState(state),
    }),
    [caseList, driverAlertState],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
