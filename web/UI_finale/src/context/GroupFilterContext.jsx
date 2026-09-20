import { createContext, useContext, useMemo, useState } from 'react';

const GroupFilterContext = createContext(null);

export function GroupFilterProvider({ children }) {
  const [selectedGroupId, setSelectedGroupId] = useState(null);

  const value = useMemo(
    () => ({
      selectedGroupId,
      toggleGroup: (id) => setSelectedGroupId((cur) => (cur === id ? null : id)),
    }),
    [selectedGroupId],
  );

  return <GroupFilterContext.Provider value={value}>{children}</GroupFilterContext.Provider>;
}

export function useGroupFilter() {
  const ctx = useContext(GroupFilterContext);
  if (!ctx) throw new Error('useGroupFilter must be used within a GroupFilterProvider');
  return ctx;
}
