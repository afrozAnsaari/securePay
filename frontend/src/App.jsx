import { useState, useEffect } from "react";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./context/useAuth";
import { Layout } from "./components/layout/Layout";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Dashboard } from "./pages/Dashboard";
import { Accounts } from "./pages/Accounts";
import { SendMoney } from "./pages/SendMoney";
import { Transactions } from "./pages/Transactions";
import { TransactionDetails } from "./pages/TransactionDetails";
import { Spinner } from "./components/common/Feedback";

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentRoute, setCurrentRoute] = useState("dashboard");
  const [selectedTxId, setSelectedTxId] = useState(null);

  // Sync hash routing with window.location.hash
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#", "").trim();
      if (hash) {
        if (hash.startsWith("transaction/")) {
          const id = hash.replace("transaction/", "");
          setSelectedTxId(id);
          setCurrentRoute("transaction-detail");
        } else {
          setCurrentRoute(hash);
        }
      }
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const navigate = (route, param = null) => {
    if (route === "transaction-detail" && param) {
      setSelectedTxId(param);
      window.location.hash = `transaction/${param}`;
      setCurrentRoute("transaction-detail");
      return;
    }
    setSelectedTxId(null);
    window.location.hash = route;
    setCurrentRoute(route);
  };

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#0a1128",
        }}
      >
        <Spinner size="lg" text="Starting SecurePay..." />
      </div>
    );
  }

  // Unauthenticated routing
  if (!isAuthenticated) {
    if (currentRoute === "register") {
      return <Register onNavigate={navigate} />;
    }
    return <Login onNavigate={navigate} />;
  }

  // Authenticated routing
  let pageContent;
  let pageTitle;

  switch (currentRoute) {
    case "accounts":
      pageTitle = "Bank Accounts";
      pageContent = <Accounts />;
      break;
    case "send-money":
      pageTitle = "Send Money";
      pageContent = <SendMoney onNavigate={navigate} />;
      break;
    case "transactions":
      pageTitle = "Passbook & Transactions";
      pageContent = (
        <Transactions
          onNavigate={navigate}
          onSelectTransaction={(id) => setSelectedTxId(id)}
        />
      );
      break;
    case "transaction-detail":
      pageTitle = "Transaction Receipt";
      pageContent = (
        <TransactionDetails
          transactionId={selectedTxId}
          onNavigate={navigate}
        />
      );
      break;
    case "dashboard":
    default:
      pageTitle = "Dashboard";
      pageContent = (
        <Dashboard
          onNavigate={navigate}
          onSelectTransaction={(id) => setSelectedTxId(id)}
        />
      );
      break;
  }

  return (
    <Layout currentRoute={currentRoute} onNavigate={navigate} title={pageTitle}>
      {pageContent}
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
