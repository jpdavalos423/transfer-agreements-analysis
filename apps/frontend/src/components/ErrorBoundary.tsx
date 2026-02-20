import React from "react";
import { Link } from "react-router-dom";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error): void {
    // Keep logging local for debugging without changing API behavior.
    // eslint-disable-next-line no-console
    console.error("React render error boundary caught:", error);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <main className="container">
          <section className="panel panel-error" role="alert" aria-live="assertive">
            <h1>Something went wrong</h1>
            <p>We hit an unexpected UI error. You can retry or go back to setup.</p>
            <div className="pathway-actions">
              <button type="button" onClick={this.handleReset}>
                Retry UI
              </button>
              <Link to="/">Back to form</Link>
            </div>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
