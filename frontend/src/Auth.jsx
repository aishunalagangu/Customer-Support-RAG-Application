import { useState } from "react";
import {
  Eye,
  EyeOff,
  Bot,
  Mail,
  Lock,
  User,
  LogIn,
  UserPlus,
} from "lucide-react";

import "./Auth.css";

const API_URL = "http://127.0.0.1:8000";

function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = isLogin ? "/login" : "/register";

      const body = isLogin
        ? {
            email: email,
            password: password,
          }
        : {
            name: name,
            email: email,
            password: password,
          };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      if (isLogin) {
        localStorage.setItem(
          "customer_support_user",
          JSON.stringify(data.user)
        );

        onLogin(data.user);
      } else {
        setSuccess("Registration successful. You can now login.");

        setName("");
        setEmail("");
        setPassword("");

        setIsLogin(true);
      }
    } catch (error) {
      console.error("Authentication error:", error);

      setError(
        error.message || "Unable to connect to the server."
      );
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsLogin((previous) => !previous);

    setError("");
    setSuccess("");

    setName("");
    setEmail("");
    setPassword("");

    setShowPassword(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-card">

        <div className="auth-brand">
          <div className="auth-brand-icon">
            <Bot size={30} />
          </div>

          <h1>Customer Support AI</h1>

          <p>
            AI-powered customer support assistant
          </p>
        </div>

        <div className="auth-title">
          <h2>
            {isLogin ? "Welcome Back" : "Create Account"}
          </h2>

          <p>
            {isLogin
              ? "Login to continue to your support assistant"
              : "Create your account to get started"}
          </p>
        </div>

        {error && (
          <div className="auth-message error">
            {error}
          </div>
        )}

        {success && (
          <div className="auth-message success">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          {!isLogin && (
            <div className="auth-input-group">
              <label>Full Name</label>

              <div className="auth-input-wrapper">
                <User size={18} />

                <input
                  type="text"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  required
                />
              </div>
            </div>
          )}

          <div className="auth-input-group">
            <label>Email</label>

            <div className="auth-input-wrapper">
              <Mail size={18} />

              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                required
              />
            </div>
          </div>

          <div className="auth-input-group">
            <label>Password</label>

            <div className="auth-input-wrapper">
              <Lock size={18} />

              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword((previous) => !previous)
                }
              >
                {showPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading ? (
              "Please wait..."
            ) : isLogin ? (
              <>
                <LogIn size={18} />
                Login
              </>
            ) : (
              <>
                <UserPlus size={18} />
                Create Account
              </>
            )}
          </button>

        </form>

        <div className="auth-switch">
          <span>
            {isLogin
              ? "Don't have an account?"
              : "Already have an account?"}
          </span>

          <button
            type="button"
            onClick={switchMode}
          >
            {isLogin
              ? "Create Account"
              : "Login"}
          </button>
        </div>

      </div>
    </div>
  );
}

export default Auth;