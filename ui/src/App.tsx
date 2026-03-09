import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Members from "./pages/Members";
import Funds from "./pages/Funds";
import Properties from "./pages/Properties";
import BalanceSheet from "./pages/BalanceSheet";
import CommandCenter from "./pages/CommandCenter";
import Profile from "./pages/Profile";
import Chat from "./pages/Chat";
import Import from "./pages/Import";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Dashboard />} />
            <Route path="/funds" element={<Funds />} />
            <Route path="/properties" element={<Properties />} />
            <Route path="/command-center" element={<CommandCenter />} />
            <Route path="/balance-sheet" element={<BalanceSheet />} />
            <Route path="/members" element={<Members />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/import" element={<Import />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
