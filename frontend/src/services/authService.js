import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8001/api/v1/auth"
});

export const loginUser = async (email, password) => {
  const res = await API.post("/login", {
    email,
    password
  });

  return res.data;
};

export const registerUser = async (data) => {
  const res = await API.post("/register", data);
  return res.data;
};