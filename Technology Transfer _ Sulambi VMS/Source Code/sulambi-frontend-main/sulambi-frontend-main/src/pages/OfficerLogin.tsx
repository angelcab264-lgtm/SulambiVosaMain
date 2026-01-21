import { Box, IconButton, Typography } from "@mui/material";
import FlexBox from "../components/FlexBox";
import SulambiLogo from "../components/Icons/SulambiLogo";
import CustomInput from "../components/Inputs/CustomInput";
import CustomButton from "../components/Buttons/CustomButton";

import LoginIcon from "@mui/icons-material/Login";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import RemoveRedEyeIcon from "@mui/icons-material/RemoveRedEye";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";

import { useContext, useEffect, useState } from "react";
import { login } from "../api/auth";
import { MembershipType, SessionResponse } from "../interface/types";
import { useNavigate } from "react-router-dom";
import { AccountDetailsContext } from "../contexts/AccountDetailsProvider";
import { SnackbarContext } from "../contexts/SnackbarProvider";
import { getImagePath } from "../utils/imagePath";

interface LoginResponse {
  message: string;
  session?: SessionResponse;
  memberData?: MembershipType;
}

const OfficerLogin = () => {
  const [showError, setShowError] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [showPass, setShowPass] = useState(false);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const { setAccountDetails } = useContext(AccountDetailsContext);
  const { showSnackbarMessage } = useContext(SnackbarContext);

  const navigate = useNavigate();

  // When opening the login page, clear any stale auth data instead of forcing redirect.
  // This prevents being auto-redirected back into a previous account when you explicitly
  // want to switch users.
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      console.log("[FRONTEND_LOGIN] Clearing stale token on login page load");
    }
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("accountType");
    localStorage.removeItem("membershipCache");
  }, []);

  const loginButtonAction = async () => {
    console.log('[FRONTEND_LOGIN] ========================================');
    console.log('[FRONTEND_LOGIN] Login attempt started');
    console.log('[FRONTEND_LOGIN] Username:', username);
    console.log('[FRONTEND_LOGIN] Password:', '*'.repeat(password.length));
    
    try {
      console.log('[FRONTEND_LOGIN] Making API request to /auth/login...');
      const loginResponse = await login(username, password);
      console.log('[FRONTEND_LOGIN] ✅ API response received');
      console.log('[FRONTEND_LOGIN] Status:', loginResponse.status);
      console.log('[FRONTEND_LOGIN] Response data:', loginResponse.data);
      
      const loginResponseData: LoginResponse = loginResponse.data;

      // save session token
      if (loginResponseData.session) {
        console.log('[FRONTEND_LOGIN] ✅ Session data received');
        console.log('[FRONTEND_LOGIN] Account Type:', loginResponseData.session.accountType);
        const token = loginResponseData.session.token;
        console.log('[FRONTEND_LOGIN] Token:', token ? `${token.substring(0, 20)}...` : 'None');
        
        localStorage.setItem("token", token ?? "");
        localStorage.setItem("username", username);
        console.log('[FRONTEND_LOGIN] Token saved to localStorage');

        // redirect after saving
        switch (loginResponseData.session.accountType) {
          case "admin":
            localStorage.setItem("accountType", "admin");
            setAccountDetails({
              accountType: "admin",
              username: username,
            });
            redirectLoggedIn("/admin/dashboard");
            break;

          case "member":
            localStorage.setItem("accountType", "member");
            setAccountDetails({
              accountType: "member",
              username: username,
            });

            localStorage.setItem(
              "membershipCache",
              JSON.stringify(loginResponseData.memberData)
            );
            showSnackbarMessage("Cached membership user data");
            redirectLoggedIn("/member");
            break;

          case "officer":
            localStorage.setItem("accountType", "officer");
            setAccountDetails({
              accountType: "officer",
              username: username,
            });
            redirectLoggedIn("/officer");
            break;
        }
      } else {
        console.log('[FRONTEND_LOGIN] ❌ No session data in response');
      }
      console.log('[FRONTEND_LOGIN] ========================================');
    } catch (err: any) {
      console.log('[FRONTEND_LOGIN] ❌ ERROR: Login failed');
      console.log('[FRONTEND_LOGIN] Error type:', err?.constructor?.name);
      console.log('[FRONTEND_LOGIN] Error message:', err?.message);
      console.log('[FRONTEND_LOGIN] Error response:', err?.response?.data);
      console.log('[FRONTEND_LOGIN] Error status:', err?.response?.status);
      console.log('[FRONTEND_LOGIN] Full error:', err);
      console.log('[FRONTEND_LOGIN] ========================================');
      
      // Check if it's a network error (server might be off)
      if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error')) {
        console.error('[FRONTEND_LOGIN] 🚨 NETWORK ERROR: Backend server might be offline!');
        showSnackbarMessage("Cannot connect to server. Please check if the backend is running.", "error");
      } else {
        showLoginError();
      }
    }
  };

  const showLoginError = () => {
    setShowError(true);
    setTimeout(() => setShowError(false), 3000);
  };

  const redirectLoggedIn = (redirect: string) => {
    setShowLogin(true);
    setTimeout(() => navigate(redirect), 1000);
  };

  return (
    <div style={{ 
      height: "100vh", 
      width: "100%", 
      display: "flex", 
      justifyContent: "center", 
      alignItems: "center",
      background: "linear-gradient(180deg, #c07f00 0%, #ffdf75 100%)"
    }}>
      <div style={{
        backgroundColor: "white",
        padding: "20px 30px",
        borderRadius: "10px",
        boxShadow: "0 0 15px 1px #533805",
        minWidth: "300px"
      }}>
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <img src={getImagePath("/images/logo.png")} height="70px" width="80px" style={{ borderRadius: "50%" }} />
          <h2 style={{ color: "#475443", margin: "10px 0" }}>Sulambi Log In</h2>
        </div>
        
        <div style={{ marginBottom: "20px" }}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              marginBottom: "10px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              boxSizing: "border-box"
            }}
          />
          <div style={{ position: "relative", marginBottom: "10px" }}>
            <input
              type={showPass ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 40px 10px 10px",
                border: "1px solid #ccc",
                borderRadius: "4px",
                boxSizing: "border-box"
              }}
            />
            <IconButton
              onClick={() => setShowPass(!showPass)}
              edge="end"
              size="small"
              sx={{
                position: "absolute",
                right: "5px",
                top: "50%",
                transform: "translateY(-50%)",
                padding: "5px",
                '&:hover': {
                  bgcolor: 'action.hover'
                }
              }}
            >
              {showPass ? <VisibilityOffIcon /> : <RemoveRedEyeIcon />}
            </IconButton>
          </div>
          
          {showError && (
            <p style={{ color: "red", textAlign: "center", margin: "10px 0" }}>
              Invalid account
            </p>
          )}
          
          {showLogin && (
            <p style={{ color: "green", textAlign: "center", margin: "10px 0" }}>
              Logged In!
            </p>
          )}
        </div>
        
        <div style={{ textAlign: "right" }}>
          <button
            onClick={loginButtonAction}
            style={{
              backgroundColor: "#475443",
              color: "white",
              padding: "8px 20px",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer"
            }}
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};

export default OfficerLogin;
