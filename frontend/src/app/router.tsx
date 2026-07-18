import { createBrowserRouter, Navigate } from "react-router-dom";
import { RootLayout } from "@/app/root-layout";
import { AppShell } from "@/components/layout/app-shell";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { LoginPage } from "@/features/auth/pages/login-page";
import { RegisterPage } from "@/features/auth/pages/register-page";
import { DashboardPage } from "@/features/dashboard/pages/dashboard-page";
import { ProjectsListPage } from "@/features/projects/pages/projects-list-page";
import { NewProjectPage } from "@/features/projects/pages/new-project-page";
import { ProjectDetailPage } from "@/features/projects/pages/project-detail-page";

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppShell />,
            children: [
              { path: "/dashboard", element: <DashboardPage /> },
              { path: "/projects", element: <ProjectsListPage /> },
              { path: "/projects/new", element: <NewProjectPage /> },
              { path: "/projects/:projectId", element: <ProjectDetailPage /> },
            ],
          },
        ],
      },
      { path: "/", element: <Navigate to="/dashboard" replace /> },
      { path: "*", element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);
