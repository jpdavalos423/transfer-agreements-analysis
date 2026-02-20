import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { PathwayPage } from "../components/PathwayPage";
import type { GeneratePathwayRequest, GeneratePathwayResponse } from "../types";

const REQUEST: GeneratePathwayRequest = {
  college_id: "de_anza",
  target_ucs: ["UCLA"],
  ge_pattern: "IGETC",
  completed_courses: ["MATH 1A"],
};

const SUCCESS_RESPONSE: GeneratePathwayResponse = {
  version: "v1",
  request_id: "req-1",
  plan: [
    {
      term: "Term 1",
      courses: [
        { courseCode: "MATH 1B", units: 5 },
        { courseCode: "IG_1A", units: 3 },
      ],
    },
  ],
  warnings: [],
  meta: {
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "IGETC",
    completed_courses_count: 1,
  },
};

describe("PathwayPage resilience", () => {
  it("shows error state on network failure and recovers on retry with same payload", async () => {
    const requestCalls: GeneratePathwayRequest[] = [];
    let attempts = 0;

    const requestPathway = async (
      payload: GeneratePathwayRequest,
    ): Promise<GeneratePathwayResponse> => {
      requestCalls.push(payload);
      attempts += 1;
      if (attempts === 1) {
        throw new Error("network down");
      }
      return SUCCESS_RESPONSE;
    };

    render(
      <MemoryRouter>
        <PathwayPage
          loadStoredRequest={() => REQUEST}
          requestPathway={requestPathway}
        />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Request Error")).toBeTruthy();
    expect(
      screen.getByText("REQUEST_FAILED: Unable to complete request. Please try again."),
    ).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to form" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Pathway Results")).toBeTruthy();
    expect(screen.getByText("Plan Status")).toBeTruthy();

    await waitFor(() => {
      expect(requestCalls).toEqual([REQUEST, REQUEST]);
    });
  });
});
