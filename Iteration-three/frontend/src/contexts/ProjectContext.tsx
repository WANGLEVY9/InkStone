import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import type { Project } from '@/types';

interface ProjectContextType {
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
  loading: boolean;
}

const ProjectContext = createContext<ProjectContextType>({
  currentProject: null,
  setCurrentProject: () => {},
  loading: false,
});

export const useProjectContext = () => useContext(ProjectContext);

export const ProjectProvider = ({ children }: { children: ReactNode }) => {
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [loading] = useState(false);

  return (
    <ProjectContext.Provider value={{ currentProject, setCurrentProject, loading }}>
      {children}
    </ProjectContext.Provider>
  );
};

// Auto-loads project data for project routes
export const ProjectLoader = ({ children }: { children: ReactNode }) => {
  const { id } = useParams<{ id: string }>();
  const { currentProject, setCurrentProject } = useProjectContext();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    if (currentProject?.id === id) return;

    setLoading(true);
    projectsApi.get(id).then(res => {
      setCurrentProject(res.data);
      setLoading(false);
    }).catch(() => {
      setCurrentProject(null);
      setLoading(false);
    });
  }, [id, currentProject?.id]);

  // Clear project when navigating away from project routes
  useEffect(() => {
    return () => { setCurrentProject(null); };
  }, []);

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}>加载中...</div>;

  return <>{children}</>;
};
