import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { PathwayPage } from "./components/PathwayPage";
import { SetupPage } from "./components/SetupPage";

export default function App() {
  return (
    <Router>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<SetupPage />} />
          <Route path="/pathway" element={<PathwayPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ErrorBoundary>
    </Router>
  );
}
