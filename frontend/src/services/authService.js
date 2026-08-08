// -----------------------------------------------------------------
// authService.js
//
// All API calls related to authentication and profile management.
// -----------------------------------------------------------------

import api from "./api";

export async function signup(data) {
  const response = await api.post("/auth/signup", data);
  return response.data; // { access_token, token_type, student }
}

export async function login(data) {
  const response = await api.post("/auth/login", data);
  return response.data; // { access_token, token_type, student }
}

export async function getMyProfile() {
  const response = await api.get("/profile/me");
  return response.data;
}

export async function updateMyProfile(data) {
  const response = await api.put("/profile/me", data);
  return response.data;
}
