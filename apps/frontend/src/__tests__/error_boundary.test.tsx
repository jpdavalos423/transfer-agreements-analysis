import React from "react";
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen } from "@testing-library/react";

import { ErrorBoundary } from "../components/ErrorBoundary";

function ThrowOnRender(): never {
  throw new Error("forced render crash");
}

describe("ErrorBoundary", () => {
  it("renders fallback UI when a child throws", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <MemoryRouter>
        <ErrorBoundary>
          <ThrowOnRender />
        </ErrorBoundary>
      </MemoryRouter>,
    );

    expect(screen.getByText("Something went wrong")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Retry UI" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to form" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Retry UI" }));
    expect(screen.getByText("Something went wrong")).toBeTruthy();

    consoleSpy.mockRestore();
  });
});
