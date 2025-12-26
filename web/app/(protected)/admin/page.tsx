"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Shield,
  Users,
  UserCheck,
  UserX,
  Pencil,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import { useAuth } from "@/lib/auth";
import { useUsers, useToggleUserStatus } from "@/lib/hooks/use-admin";
import { UserEditDialog } from "@/components/admin/user-edit-dialog";
import type { AdminUser } from "@/lib/api/admin";

export default function AdminPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const limit = 20;
  const { data, isLoading, error } = useUsers(page, limit);
  const toggleStatusMutation = useToggleUserStatus();

  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);

  // Redirect non-superusers
  if (user && !user.is_superuser) {
    router.push("/");
    return null;
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleToggleStatus = async (userId: string, currentStatus: boolean) => {
    await toggleStatusMutation.mutateAsync({
      userId,
      isActive: !currentStatus,
    });
  };

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Admin Dashboard"
          description="Manage users and system settings"
        />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Management
            </CardTitle>
            <CardDescription>
              View and manage all users in the system
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-destructive">
                  Failed to load users. Please try again.
                </p>
              </div>
            ) : data?.users.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Users className="h-8 w-8 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  No users found.
                </p>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Display Name</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Last Login</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data?.users.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.email}</TableCell>
                        <TableCell>{u.display_name || "-"}</TableCell>
                        <TableCell>
                          {u.is_active ? (
                            <Badge variant="default" className="bg-green-500/20 text-green-600 hover:bg-green-500/20">
                              <UserCheck className="mr-1 h-3 w-3" />
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="bg-red-500/20 text-red-600">
                              <UserX className="mr-1 h-3 w-3" />
                              Inactive
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {u.is_superuser ? (
                            <Badge variant="default" className="bg-purple-500/20 text-purple-600 hover:bg-purple-500/20">
                              <Shield className="mr-1 h-3 w-3" />
                              Admin
                            </Badge>
                          ) : (
                            <Badge variant="outline">User</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDateTime(u.last_login_at)}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDate(u.created_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setEditingUser(u)}
                              title="Edit user"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>

                            {/* Don't allow deactivating yourself */}
                            {u.id !== user?.id && (
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    title={u.is_active ? "Deactivate user" : "Activate user"}
                                    disabled={toggleStatusMutation.isPending}
                                  >
                                    {u.is_active ? (
                                      <UserX className="h-4 w-4 text-destructive" />
                                    ) : (
                                      <UserCheck className="h-4 w-4 text-green-600" />
                                    )}
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>
                                      {u.is_active ? "Deactivate" : "Activate"} User
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                      {u.is_active
                                        ? `Are you sure you want to deactivate ${u.email}? They will no longer be able to log in.`
                                        : `Are you sure you want to activate ${u.email}? They will be able to log in again.`}
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => handleToggleStatus(u.id, u.is_active)}
                                      className={
                                        u.is_active
                                          ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                          : ""
                                      }
                                    >
                                      {u.is_active ? "Deactivate" : "Activate"}
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-4 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Showing {(page - 1) * limit + 1} to{" "}
                      {Math.min(page * limit, data?.total || 0)} of {data?.total}{" "}
                      users
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        Page {page} of {totalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </PageContainer>

      {/* Edit User Dialog */}
      <UserEditDialog
        user={editingUser}
        open={!!editingUser}
        onOpenChange={(open) => !open && setEditingUser(null)}
      />
    </>
  );
}
