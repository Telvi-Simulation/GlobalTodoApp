import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OnboardingForm from "../../src/components/OnboardingForm";
import * as api from "../../src/api/onboard";

jest.mock("../../src/api/onboard");

const mockedSubmit = api.submitOnboarding as jest.MockedFunction<typeof api.submitOnboarding>;

describe("OnboardingForm", () => {
  const defaultProps = {
    userId: "11111111-1111-1111-1111-111111111111",
    tenantId: "22222222-2222-2222-2222-222222222222",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders all required fields and submit button", () => {
    render(<OnboardingForm {...defaultProps} />);
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Initial Site Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Consent to Marketing/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Accept Terms/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit/i })).toBeInTheDocument();
  });

  test("validates required fields and consent_terms checkbox before submit", async () => {
    render(<OnboardingForm {...defaultProps} />);
    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    expect(await screen.findByText(/Full Name is required/i)).toBeInTheDocument();
    expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/Initial Site Name is required/i)).toBeInTheDocument();
    expect(screen.getByText(/You must accept terms/i)).toBeInTheDocument();
    expect(mockedSubmit).not.toHaveBeenCalled();
  });

  test("shows validation error on invalid email format", async () => {
    render(<OnboardingForm {...defaultProps} />);
    userEvent.type(screen.getByLabelText(/Full Name/i), "Test User");
    userEvent.type(screen.getByLabelText(/Email/i), "invalid-email");
    userEvent.type(screen.getByLabelText(/Initial Site Name/i), "My Site");
    userEvent.click(screen.getByLabelText(/Accept Terms/i));
    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    expect(await screen.findByText(/Invalid email address/i)).toBeInTheDocument();
    expect(mockedSubmit).not.toHaveBeenCalled();
  });

  test("submits valid form data and handles success response", async () => {
    mockedSubmit.mockResolvedValueOnce({ onboarding_id: "abc-123", message: "Success" });

    render(<OnboardingForm {...defaultProps} />);
    userEvent.type(screen.getByLabelText(/Full Name/i), "Test User");
    userEvent.type(screen.getByLabelText(/Email/i), "test@example.com");
    userEvent.type(screen.getByLabelText(/Initial Site Name/i), "My Palette Site");
    userEvent.click(screen.getByLabelText(/Consent to Marketing/i));
    userEvent.click(screen.getByLabelText(/Accept Terms/i));

    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    await waitFor(() => expect(mockedSubmit).toHaveBeenCalledTimes(1));
    expect(mockedSubmit).toHaveBeenCalledWith({
      user_id: defaultProps.userId,
      tenant_id: defaultProps.tenantId,
      full_name: "Test User",
      email: "test@example.com",
      initial_site_name: "My Palette Site",
      consent_marketing: true,
      consent_terms: true,
    });

    expect(await screen.findByText(/Onboarding successful/i)).toBeInTheDocument();
  });

  test("shows server error message on 400/403/500 responses", async () => {
    mockedSubmit.mockRejectedValueOnce({ response: { status: 400, data: { error: "Validation failed" } } });

    render(<OnboardingForm {...defaultProps} />);
    userEvent.type(screen.getByLabelText(/Full Name/i), "Test User");
    userEvent.type(screen.getByLabelText(/Email/i), "test@example.com");
    userEvent.type(screen.getByLabelText(/Initial Site Name/i), "My Palette Site");
    userEvent.click(screen.getByLabelText(/Accept Terms/i));

    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    expect(await screen.findByText(/Validation failed/i)).toBeInTheDocument();

    mockedSubmit.mockRejectedValueOnce({ response: { status: 403, data: { error: "Unauthorized user_id" } } });

    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    expect(await screen.findByText(/Unauthorized user_id/i)).toBeInTheDocument();

    mockedSubmit.mockRejectedValueOnce({ response: { status: 500, data: { error: "Internal server error" } } });

    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    expect(await screen.findByText(/Internal server error/i)).toBeInTheDocument();
  });
});
