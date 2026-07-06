import { Component, type ErrorInfo, type ReactNode } from "react";

type PageErrorBoundaryProps = {
  children: ReactNode;
};

type PageErrorBoundaryState = {
  message: string | null;
};

class PageErrorBoundary extends Component<PageErrorBoundaryProps, PageErrorBoundaryState> {
  state: PageErrorBoundaryState = { message: null };

  static getDerivedStateFromError(error: Error): PageErrorBoundaryState {
    return { message: error.message };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(error, errorInfo);
  }

  render() {
    if (this.state.message) {
      return (
        <section className="page">
          <div className="error-banner">
            This page could not be rendered. Check the browser console for details.
            <br />
            <small>{this.state.message}</small>
          </div>
        </section>
      );
    }

    return this.props.children;
  }
}

export default PageErrorBoundary;
