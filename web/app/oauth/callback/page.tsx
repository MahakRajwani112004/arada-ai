"use client";

import { Suspense, useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, XCircle, Loader2, Calendar, Mail, HardDrive, RefreshCw, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCreateServer, useUpdateServerCredentials } from "@/lib/hooks/use-mcp";
import { useAuth } from "@/lib/auth";

// Google services
const googleServiceConfig: Record<string, { name: string; icon: React.ReactNode; template: string }> = {
  calendar: {
    name: "Google Calendar",
    icon: <Calendar className="h-8 w-8" />,
    template: "google-calendar",
  },
  gmail: {
    name: "Gmail",
    icon: <Mail className="h-8 w-8" />,
    template: "gmail",
  },
  drive: {
    name: "Google Drive",
    icon: <HardDrive className="h-8 w-8" />,
    template: "google-drive",
  },
};

// Microsoft services
const microsoftServiceConfig: Record<string, { name: string; icon: React.ReactNode; template: string }> = {
  calendar: {
    name: "Outlook Calendar",
    icon: <Calendar className="h-8 w-8" />,
    template: "outlook-calendar",
  },
  email: {
    name: "Outlook Email",
    icon: <Mail className="h-8 w-8" />,
    template: "outlook-email",
  },
};

type CallbackState = "loading" | "not_authenticated" | "connecting" | "reconnecting" | "success" | "error";

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const createServer = useCreateServer();
  const updateCredentials = useUpdateServerCredentials();
  const hasRun = useRef(false);
  const { isAuthenticated, accessToken, hasHydrated } = useAuth();

  // Debug: Log on mount to verify this component is being used
  useEffect(() => {
    console.log("[OAuth Callback Page] Component mounted - this is the UNPROTECTED version");
    console.log("[OAuth Callback Page] URL:", window.location.href);
    console.log("[OAuth Callback Page] Search params:", searchParams.toString());
  }, [searchParams]);

  const [state, setState] = useState<CallbackState>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [isReconnect, setIsReconnect] = useState(false);

  // Try to get params from URL first, then fall back to sessionStorage
  const urlTokenRef = searchParams.get("token_ref");
  const urlService = searchParams.get("service");
  const urlError = searchParams.get("error");
  const urlServerId = searchParams.get("server_id");
  const urlReconnect = searchParams.get("reconnect");
  const urlProvider = searchParams.get("provider");

  // Restore from sessionStorage if URL params are missing (after login redirect)
  const savedParams = typeof window !== "undefined"
    ? sessionStorage.getItem("oauth_callback_params")
    : null;
  const parsedSavedParams = savedParams ? JSON.parse(savedParams) : {};

  const tokenRef = urlTokenRef || parsedSavedParams.token_ref;
  const service = urlService || parsedSavedParams.service || "calendar";
  const error = urlError || parsedSavedParams.error;
  const serverId = urlServerId || parsedSavedParams.server_id;
  const reconnect = (urlReconnect || parsedSavedParams.reconnect) === "true";
  const provider = urlProvider || parsedSavedParams.provider || "google";

  // Get config based on provider
  const isMicrosoft = provider === "microsoft";
  const serviceConfigMap = isMicrosoft ? microsoftServiceConfig : googleServiceConfig;
  const defaultConfig = isMicrosoft ? microsoftServiceConfig.calendar : googleServiceConfig.calendar;
  const config = serviceConfigMap[service] || defaultConfig;

  useEffect(() => {
    if (hasRun.current) return;

    // Wait for auth store to hydrate from localStorage
    if (!hasHydrated) {
      return;
    }

    // Check authentication after hydration
    if (!isAuthenticated && !accessToken) {
      setState("not_authenticated");
      return;
    }

    hasRun.current = true;
    setIsReconnect(reconnect);

    async function handleCallback() {
      // Handle error from OAuth
      if (error) {
        setState("error");
        setErrorMessage(error);
        return;
      }

      // No token ref means something went wrong
      if (!tokenRef) {
        setState("error");
        setErrorMessage("No authorization token received");
        return;
      }

      // Clear stored params since we're processing now
      sessionStorage.removeItem("oauth_callback_params");

      // Handle reconnection flow
      if (reconnect && serverId) {
        setState("reconnecting");
        try {
          await updateCredentials.mutateAsync({
            serverId,
            oauthTokenRef: tokenRef,
          });
          setState("success");

          // Auto-redirect after success
          setTimeout(() => {
            router.push("/integrations");
          }, 2000);
        } catch (err) {
          setState("error");
          setErrorMessage(err instanceof Error ? err.message : "Failed to reconnect service");
        }
        return;
      }

      // Create new MCP server with the OAuth token
      setState("connecting");
      try {
        // Get server name from localStorage (set by integrations page)
        const storedName = localStorage.getItem("oauth_server_name");
        const serverName = storedName || `My ${config.name}`;

        // Clear the stored name
        localStorage.removeItem("oauth_server_name");

        await createServer.mutateAsync({
          template: config.template,
          name: serverName,
          credentials: {},
          oauth_token_ref: tokenRef,
        });
        setState("success");

        // Auto-redirect after success
        setTimeout(() => {
          router.push("/integrations");
        }, 2000);
      } catch (err) {
        setState("error");
        setErrorMessage(err instanceof Error ? err.message : "Failed to connect service");
      }
    }

    handleCallback();
  }, [tokenRef, error, config, createServer, updateCredentials, router, reconnect, serverId, isAuthenticated, accessToken, hasHydrated]);

  const handleLogin = () => {
    // Save OAuth params to sessionStorage before redirecting to login
    const paramsToSave = {
      token_ref: tokenRef,
      service: service,
      error: error,
      server_id: serverId,
      reconnect: reconnect ? "true" : undefined,
      provider: provider,
    };
    sessionStorage.setItem("oauth_callback_params", JSON.stringify(paramsToSave));

    router.push(`/login?redirect=${encodeURIComponent("/oauth/callback")}`);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="mx-auto max-w-md px-4 text-center">
        {state === "loading" && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
            <h1 className="mt-6 text-xl font-semibold">Processing...</h1>
            <p className="mt-2 text-muted-foreground">
              Please wait while we complete the authorization.
            </p>
          </>
        )}

        {state === "not_authenticated" && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-orange-500/10 text-orange-400">
              <LogIn className="h-8 w-8" />
            </div>
            <h1 className="mt-6 text-xl font-semibold">Login Required</h1>
            <p className="mt-2 text-muted-foreground">
              Please log in to complete the {config.name} connection.
            </p>
            <Button className="mt-6" onClick={handleLogin}>
              Log In to Continue
            </Button>
          </>
        )}

        {state === "connecting" && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/10 text-blue-400">
              {config.icon}
            </div>
            <h1 className="mt-6 text-xl font-semibold">Connecting {config.name}...</h1>
            <p className="mt-2 text-muted-foreground">
              Setting up your integration. This will only take a moment.
            </p>
            <div className="mt-4 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          </>
        )}

        {state === "reconnecting" && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-orange-500/10 text-orange-400">
              <RefreshCw className="h-8 w-8" />
            </div>
            <h1 className="mt-6 text-xl font-semibold">Reconnecting {config.name}...</h1>
            <p className="mt-2 text-muted-foreground">
              Updating your credentials. This will only take a moment.
            </p>
            <div className="mt-4 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          </>
        )}

        {state === "success" && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
              <CheckCircle2 className="h-8 w-8 text-success" />
            </div>
            <h1 className="mt-6 text-xl font-semibold">
              {isReconnect ? "Reconnected!" : "Connected!"}
            </h1>
            <p className="mt-2 text-muted-foreground">
              {isReconnect
                ? `${config.name} credentials have been updated successfully.`
                : `${config.name} is now connected. Your agents can access your ${service}.`}
            </p>
            <p className="mt-4 text-sm text-muted-foreground">
              Redirecting to integrations...
            </p>
            <Button className="mt-4" onClick={() => router.push("/integrations")}>
              Go to Integrations
            </Button>
          </>
        )}

        {state === "error" && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
              <XCircle className="h-8 w-8 text-destructive" />
            </div>
            <h1 className="mt-6 text-xl font-semibold">Connection Failed</h1>
            <p className="mt-2 text-muted-foreground">{errorMessage}</p>
            <div className="mt-6 flex justify-center gap-3">
              <Button variant="outline" onClick={() => router.push("/integrations")}>
                Back to Integrations
              </Button>
              <Button onClick={() => window.location.reload()}>Try Again</Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="mx-auto max-w-md px-4 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
        <h1 className="mt-6 text-xl font-semibold">Processing...</h1>
        <p className="mt-2 text-muted-foreground">
          Please wait while we complete the authorization.
        </p>
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <OAuthCallbackContent />
    </Suspense>
  );
}
