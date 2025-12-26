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
  Plus,
  Trash2,
  Loader2,
  User,
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
  useUpdateEmail,
  useUpdatePassword,
  useUpdateProfile,
  useLLMCredentials,
  useCreateLLMCredential,
  useUpdateLLMCredential,
  useDeleteLLMCredential,
} from "@/lib/hooks/use-settings";
import type { LLMCredential } from "@/lib/api/settings";
import { toast } from "sonner";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user } = useAuth();
  const [mounted, setMounted] = useState(false);

  // Profile state
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const updateProfileMutation = useUpdateProfile();

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

  // LLM Credentials state
  const { data: llmCredentialsData, isLoading: isLoadingLLMCredentials } = useLLMCredentials();
  const createLLMCredentialMutation = useCreateLLMCredential();
  const updateLLMCredentialMutation = useUpdateLLMCredential();
  const deleteLLMCredentialMutation = useDeleteLLMCredential();
  const [selectedProvider, setSelectedProvider] = useState<string>("openai");
  const [llmDisplayName, setLLMDisplayName] = useState("");
  const [llmApiKey, setLLMApiKey] = useState("");
  const [llmApiBase, setLLMApiBase] = useState("");
  const [showLLMApiKey, setShowLLMApiKey] = useState(false);
  const [editingCredential, setEditingCredential] = useState<LLMCredential | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (user?.display_name !== undefined) setDisplayName(user.display_name || "");
  }, [user?.display_name]);

  const handleProfileUpdate = async () => {
    await updateProfileMutation.mutateAsync(displayName || null);
  };

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

  // LLM Credential handlers
  const llmProviders = [
    { value: "openai", label: "OpenAI", placeholder: "sk-..." },
    { value: "anthropic", label: "Anthropic", placeholder: "sk-ant-..." },
    { value: "azure", label: "Azure OpenAI", placeholder: "Your Azure API key" },
    { value: "google", label: "Google AI", placeholder: "Your Google API key" },
    { value: "mistral", label: "Mistral AI", placeholder: "Your Mistral API key" },
    { value: "groq", label: "Groq", placeholder: "gsk_..." },
  ];

  const handleCreateLLMCredential = async () => {
    if (!llmApiKey.trim()) {
      toast.error("Please enter an API key");
      return;
    }
    const displayName = llmDisplayName.trim() ||
      llmProviders.find(p => p.value === selectedProvider)?.label || selectedProvider;

    await createLLMCredentialMutation.mutateAsync({
      provider: selectedProvider,
      display_name: displayName,
      api_key: llmApiKey,
      api_base: llmApiBase || null,
    });

    // Reset form
    setLLMDisplayName("");
    setLLMApiKey("");
    setLLMApiBase("");
    setShowLLMApiKey(false);
  };

  const handleUpdateLLMCredential = async () => {
    if (!editingCredential) return;

    await updateLLMCredentialMutation.mutateAsync({
      id: editingCredential.id,
      data: {
        display_name: llmDisplayName || undefined,
        api_key: llmApiKey || undefined,
        api_base: llmApiBase || undefined,
      },
    });

    // Reset form
    setEditingCredential(null);
    setLLMDisplayName("");
    setLLMApiKey("");
    setLLMApiBase("");
    setShowLLMApiKey(false);
  };

  const handleDeleteLLMCredential = async (id: string) => {
    await deleteLLMCredentialMutation.mutateAsync(id);
  };

  const startEditingCredential = (credential: LLMCredential) => {
    setEditingCredential(credential);
    setSelectedProvider(credential.provider);
    setLLMDisplayName(credential.display_name);
    setLLMApiBase(credential.api_base || "");
    setLLMApiKey(""); // Don't pre-fill the API key for security
  };

  const cancelEditing = () => {
    setEditingCredential(null);
    setLLMDisplayName("");
    setLLMApiKey("");
    setLLMApiBase("");
    setShowLLMApiKey(false);
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

        <Tabs defaultValue="llm-providers" className="space-y-6">
          <TabsList className="grid w-full max-w-2xl grid-cols-5">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="llm-providers">LLM Providers</TabsTrigger>
            <TabsTrigger value="appearance">Appearance</TabsTrigger>
            <TabsTrigger value="email">Email</TabsTrigger>
            <TabsTrigger value="password">Password</TabsTrigger>
          </TabsList>

          {/* Profile Settings */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profile
                </CardTitle>
                <CardDescription>Update your display name</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="display-name-profile">Display Name</Label>
                  <Input id="display-name-profile" placeholder="Your name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
                </div>
                <Button onClick={handleProfileUpdate} disabled={updateProfileMutation.isPending}>{updateProfileMutation.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Updating...</> : "Save"}</Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* LLM Providers Settings */}
          <TabsContent value="llm-providers">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  LLM Provider API Keys
                </CardTitle>
                <CardDescription>
                  Add your own API keys for LLM providers like OpenAI, Anthropic, etc.
                  These keys will be used for AI interactions in your account.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Add/Edit LLM Credential Form */}
                <div className="space-y-4 rounded-lg border border-border p-4">
                  <h4 className="font-medium">
                    {editingCredential ? "Update Credential" : "Add New Credential"}
                  </h4>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="provider">Provider</Label>
                      <select
                        id="provider"
                        value={selectedProvider}
                        onChange={(e) => setSelectedProvider(e.target.value)}
                        disabled={!!editingCredential}
                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {llmProviders.map((provider) => (
                          <option key={provider.value} value={provider.value}>
                            {provider.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="display-name">Display Name (Optional)</Label>
                      <Input
                        id="display-name"
                        placeholder={`e.g., My ${llmProviders.find(p => p.value === selectedProvider)?.label} Key`}
                        value={llmDisplayName}
                        onChange={(e) => setLLMDisplayName(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api-key">API Key</Label>
                    <div className="relative">
                      <Input
                        id="api-key"
                        type={showLLMApiKey ? "text" : "password"}
                        placeholder={llmProviders.find(p => p.value === selectedProvider)?.placeholder}
                        value={llmApiKey}
                        onChange={(e) => setLLMApiKey(e.target.value)}
                      />
                      <button
                        type="button"
                        onClick={() => setShowLLMApiKey(!showLLMApiKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showLLMApiKey ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {editingCredential && (
                      <p className="text-xs text-muted-foreground">
                        Leave empty to keep the existing API key
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api-base">Custom API Base URL (Optional)</Label>
                    <Input
                      id="api-base"
                      placeholder="https://api.example.com/v1"
                      value={llmApiBase}
                      onChange={(e) => setLLMApiBase(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Only needed for self-hosted or proxy endpoints
                    </p>
                  </div>

                  <div className="flex gap-2">
                    {editingCredential ? (
                      <>
                        <Button
                          onClick={handleUpdateLLMCredential}
                          disabled={updateLLMCredentialMutation.isPending}
                        >
                          {updateLLMCredentialMutation.isPending ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Updating...
                            </>
                          ) : (
                            "Update Credential"
                          )}
                        </Button>
                        <Button variant="outline" onClick={cancelEditing}>
                          Cancel
                        </Button>
                      </>
                    ) : (
                      <Button
                        onClick={handleCreateLLMCredential}
                        disabled={createLLMCredentialMutation.isPending || !llmApiKey.trim()}
                        className="gap-2"
                      >
                        {createLLMCredentialMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Plus className="h-4 w-4" />
                        )}
                        Add Credential
                      </Button>
                    )}
                  </div>
                </div>

                {/* LLM Credentials List */}
                <div className="space-y-3">
                  <h4 className="font-medium">Your LLM Credentials</h4>

                  {isLoadingLLMCredentials ? (
                    <>
                      <Skeleton className="h-20 w-full" />
                      <Skeleton className="h-20 w-full" />
                    </>
                  ) : llmCredentialsData?.credentials.length === 0 ? (
                    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-8 text-center">
                      <Key className="h-8 w-8 text-muted-foreground" />
                      <p className="mt-2 text-sm text-muted-foreground">
                        No LLM credentials yet. Add your API keys to get started.
                      </p>
                    </div>
                  ) : (
                    llmCredentialsData?.credentials.map((credential) => (
                      <div
                        key={credential.id}
                        className={cn(
                          "flex items-center justify-between rounded-lg border border-border bg-card p-4",
                          !credential.is_active && "opacity-60"
                        )}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{credential.display_name}</p>
                            <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">
                              {llmProviders.find(p => p.value === credential.provider)?.label || credential.provider}
                            </span>
                            {!credential.is_active && (
                              <span className="rounded bg-yellow-500/20 px-2 py-0.5 text-xs text-yellow-600 dark:text-yellow-400">
                                Inactive
                              </span>
                            )}
                          </div>
                          <code className="rounded bg-muted px-2 py-1 font-mono text-xs">
                            {credential.api_key_preview}
                          </code>
                          <p className="text-xs text-muted-foreground">
                            Added: {formatDate(credential.created_at)}
                            {credential.last_used_at &&
                              ` • Last used: ${formatDate(credential.last_used_at)}`}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => startEditingCredential(credential)}
                            className="text-muted-foreground hover:text-foreground"
                          >
                            <Key className="h-4 w-4" />
                          </Button>

                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-muted-foreground hover:text-destructive"
                                disabled={deleteLLMCredentialMutation.isPending}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete LLM Credential</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete the {credential.display_name} credential?
                                  This action cannot be undone and any agents using this credential will
                                  need to be reconfigured.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDeleteLLMCredential(credential.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="rounded-lg border border-border bg-muted/50 p-4">
                  <p className="text-sm text-muted-foreground">
                    <strong>Security note:</strong> Your API keys are encrypted and stored securely.
                    We never share or log your API keys. You can delete or update them at any time.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

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
        </Tabs>
      </PageContainer>
    </>
  );
}
