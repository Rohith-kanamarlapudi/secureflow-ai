import { useState } from "react";
import { api } from "../api/client";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("admin@secureflow.example.com");
  const [password, setPassword] = useState("Admin@12345");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      const { access_token, refresh_token } = response.data;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);

      onLogin();
    } catch (error) {
      console.error("Login error:", error);

      if (error.response) {
        setError(
          error.response.data?.detail || "Login failed"
        );
      } else {
        setError(
          "Unable to connect to the backend."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          SecureFlow AI
        </h1>

        <p className="text-gray-600 mb-6">
          Sign in to your document management dashboard.
        </p>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-100 border border-red-300 text-red-700 rounded-md p-3">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white rounded-md px-4 py-2 hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}