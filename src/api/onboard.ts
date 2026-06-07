import axios from "axios";

export interface OnboardPayload {
  user_id: string;
  tenant_id: string;
  full_name: string;
  email: string;
  initial_site_name: string;
  consent_marketing?: boolean;
  consent_terms: boolean;
}

export interface OnboardResponse {
  onboarding_id: string;
  message: string;
}

export async function submitOnboarding(payload: OnboardPayload): Promise<OnboardResponse> {
  const response = await axios.post<OnboardResponse>("/api/onboard", payload);
  return response.data;
}
