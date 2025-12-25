"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import {
  Sun,
  Moon,
  Monitor,
  Mail,
  Lock,
  Key,
  Eye,
  EyeOff,
  Copy,
  Plus,
  Trash2,
  Check,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";
import {
  useApiKeys,
  useCreateApiKey,
  useDeleteApiKey,
  useUpdateEmail,
  useUpdatePassword,
} from "@/lib/hooks/use-settings";
import { toast } from "sonner";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user } = useAuth();
  const [mounted, setMounted] = useState(false);

  // Email state
  const [newEmail, setNewEmail] = useState("");
  const updateEmailMutation = useUpdateEmail();

  // Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const updatePasswordMutation = useUpdatePassword();

  // API Keys state
  const { data: apiKeysData, isLoading: isLoadingApiKeys } = useApiKeys();
  const createApiKeyMutation = useCreateApiKey();
  const deleteApiKeyMutation = useDeleteApiKey();
  const [newKeyName, setNewKeyName] = useState("");
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<{ id: string; key: string } | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleEmailChange = async () => {
    if (!newEmail) {
      toast.error("Please enter a new email address");
      return;
    }
    await updateEmailMutation.mutateAsync(newEmail);
    setNewEmail("");
  };

  const handlePasswordChange = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Please fill in all password fields");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    await updatePasswordMutation.mutateAsync({
      currentPassword,
      newPassword,
    });
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  const generateApiKey = async () => {
    if (!newKeyName.trim()) {
      toast.error("Please enter a name for the API key");
      return;
    }
    const result = await createApiKeyMutation.mutateAsync(newKeyName);
    setNewKeyName("");
    // Store the newly created key to show it once
    setNewlyCreatedKey({ id: result.id, key: result.key });
    setVisibleKeys(new Set(Array.from(visibleKeys).concat(result.id)));
    toast.success("API key created successfully. Make sure to copy it now!");
  };

  const handleDeleteApiKey = async (id: string) => {
    await deleteApiKeyMutation.mutateAsync(id);
    // Clear newly created key if it was deleted
    if (newlyCreatedKey?.id === id) {
      setNewlyCreatedKey(null);
    }
  };

  const toggleKeyVisibility = (id: string) => {
    const newVisibleKeys = new Set(visibleKeys);
    if (newVisibleKeys.has(id)) {
      newVisibleKeys.delete(id);
    } else {
      newVisibleKeys.add(id);
    }
    setVisibleKeys(newVisibleKeys);
  };

  const copyToClipboard = async (key: string, id: string) => {
    await navigator.clipboard.writeText(key);
    setCopiedKeyId(id);
    toast.success("API key copied to clipboard");
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  const maskKey = (keyPrefix: string) => {
    return keyPrefix + "•".repeat(32);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const themeOptions = [
    { value: "light", label: "Light", icon: Sun },
    { value: "dark", label: "Dark", icon: Moon },
    { value: "system", label: "System", icon: Monitor },
  ];

  if (!mounted) {
    return null;
  }

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Settings"
          description="Manage your account settings and preferences"
        />

        <Tabs defaultValue="appearance" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-4">
            <TabsTrigger value="appearance">Appearance</TabsTrigger>
            <TabsTrigger value="email">Email</TabsTrigger>
            <TabsTrigger value="password">Password</TabsTrigger>
            <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          </TabsList>

          {/* Theme Settings */}
          <TabsContent value="appearance">
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>
                  Customize how MagOneAI looks on your device
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>Theme</Label>
                  <div className="grid grid-cols-3 gap-3">
                    {themeOptions.map((option) => {
                      const Icon = option.icon;
                      const isSelected = theme === option.value;
                      return (
                        <button
                          key={option.value}
                          onClick={() => setTheme(option.value)}
                          className={cn(
                            "flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all hover:bg-accent",
                            isSelected
                              ? "border-primary bg-accent"
                              : "border-border"
                          )}
                        >
                          <Icon
                            className={cn(
                              "h-6 w-6",
                              isSelected
                                ? "text-primary"
                                : "text-muted-foreground"
                            )}
                          />
                          <span
                            className={cn(
                              "text-sm font-medium",
                              isSelected
                                ? "text-foreground"
                                : "text-muted-foreground"
                            )}
                          >
                            {option.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {theme === "system"
                      ? "Theme will automatically switch based on your system preferences"
                      : `Currently using ${theme} theme`}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Email Settings */}
          <TabsContent value="email">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Email Settings
                </CardTitle>
                <CardDescription>
                  Update your email address for account notifications
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Current Email</Label>
                  <div className="flex h-9 items-center rounded-md border border-input bg-muted px-3 text-sm">
                    {user?.email || "Loading..."}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-email">New Email Address</Label>
                  <Input
                    id="new-email"
                    type="email"
                    placeholder="Enter new email address"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                  />
                </div>

                <Button
                  onClick={handleEmailChange}
                  disabled={updateEmailMutation.isPending || !newEmail}
                >
                  {updateEmailMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    "Update Email"
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Password Settings */}
          <TabsContent value="password">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="h-5 w-5" />
                  Change Password
                </CardTitle>
                <CardDescription>
                  Update your password to keep your account secure
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="current-password">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="current-password"
                      type={showCurrentPassword ? "text" : "password"}
                      placeholder="Enter current password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showCurrentPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-password">New Password</Label>
                  <div className="relative">
                    <Input
                      id="new-password"
                      type={showNewPassword ? "text" : "password"}
                      placeholder="Enter new password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showNewPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Must be at least 8 characters with uppercase, lowercase, number, and special character
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <div className="relative">
                    <Input
                      id="confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <Button
                  onClick={handlePasswordChange}
                  disabled={
                    updatePasswordMutation.isPending ||
                    !currentPassword ||
                    !newPassword ||
                    !confirmPassword
                  }
                >
                  {updatePasswordMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    "Change Password"
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Keys Settings */}
          <TabsContent value="api-keys">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  API Keys
                </CardTitle>
                <CardDescription>
                  Manage your API keys for programmatic access to MagOneAI
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Create new API key */}
                <div className="flex gap-3">
                  <Input
                    placeholder="API key name (e.g., Production)"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && generateApiKey()}
                    disabled={createApiKeyMutation.isPending}
                  />
                  <Button
                    onClick={generateApiKey}
                    className="gap-2"
                    disabled={createApiKeyMutation.isPending || !newKeyName.trim()}
                  >
                    {createApiKeyMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    Create Key
                  </Button>
                </div>

                {/* API Keys List */}
                <div className="space-y-3">
                  {isLoadingApiKeys ? (
                    <>
                      <Skeleton className="h-24 w-full" />
                      <Skeleton className="h-24 w-full" />
                    </>
                  ) : apiKeysData?.api_keys.length === 0 ? (
                    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-8 text-center">
                      <Key className="h-8 w-8 text-muted-foreground" />
                      <p className="mt-2 text-sm text-muted-foreground">
                        No API keys yet. Create one to get started.
                      </p>
                    </div>
                  ) : (
                    apiKeysData?.api_keys.map((apiKey) => {
                      // Check if this is the newly created key
                      const isNewlyCreated = newlyCreatedKey?.id === apiKey.id;

                      return (
                        <div
                          key={apiKey.id}
                          className={cn(
                            "flex items-center justify-between rounded-lg border border-border bg-card p-4",
                            isNewlyCreated && "border-primary/50 bg-primary/5"
                          )}
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <p className="font-medium">{apiKey.name}</p>
                              {isNewlyCreated && (
                                <span className="rounded bg-primary/20 px-1.5 py-0.5 text-xs text-primary">
                                  New - Copy now!
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <code className="rounded bg-muted px-2 py-1 font-mono text-xs">
                                {isNewlyCreated && visibleKeys.has(apiKey.id)
                                  ? newlyCreatedKey.key
                                  : maskKey(apiKey.key_prefix)}
                              </code>
                              {isNewlyCreated && (
                                <>
                                  <button
                                    onClick={() => toggleKeyVisibility(apiKey.id)}
                                    className="text-muted-foreground hover:text-foreground"
                                  >
                                    {visibleKeys.has(apiKey.id) ? (
                                      <EyeOff className="h-4 w-4" />
                                    ) : (
                                      <Eye className="h-4 w-4" />
                                    )}
                                  </button>
                                  <button
                                    onClick={() =>
                                      copyToClipboard(newlyCreatedKey.key, apiKey.id)
                                    }
                                    className="text-muted-foreground hover:text-foreground"
                                  >
                                    {copiedKeyId === apiKey.id ? (
                                      <Check className="h-4 w-4 text-green-500" />
                                    ) : (
                                      <Copy className="h-4 w-4" />
                                    )}
                                  </button>
                                </>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Created: {formatDate(apiKey.created_at)}
                              {apiKey.last_used_at &&
                                ` • Last used: ${formatDate(apiKey.last_used_at)}`}
                            </p>
                          </div>

                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-muted-foreground hover:text-destructive"
                                disabled={deleteApiKeyMutation.isPending}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete API Key</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete &quot;{apiKey.name}
                                  &quot;? This action cannot be undone and any
                                  applications using this key will stop working.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDeleteApiKey(apiKey.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      );
                    })
                  )}
                </div>

                <div className="rounded-lg border border-border bg-muted/50 p-4">
                  <p className="text-sm text-muted-foreground">
                    <strong>Security tip:</strong> API keys are only shown once when
                    created. Store them securely. Do not share them in publicly
                    accessible areas such as GitHub or client-side code.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </PageContainer>
    </>
  );
}
