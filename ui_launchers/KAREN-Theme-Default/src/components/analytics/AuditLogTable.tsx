"use client";

import React, { useEffect, useState } from "react";
import { AuditService, AuditLogEntry } from "@/services/auditService";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
export default function AuditLogTable() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const service = new AuditService();
    service
      .getAuditLogs(50)
      .then((data) => setLogs(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Card className="w-full shadow-sm border border-border">
      <CardHeader>
        <CardTitle className="text-lg font-semibold tracking-tight">
          Recent Audit Logs
        </CardTitle>
      </CardHeader>

      <CardContent className="overflow-x-auto">
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-6 w-full" />
            ))}
          </div>
        )}

        {error && (
          <p className="text-sm text-destructive mt-2">
            Error loading audit logs: {error}
          </p>
        )}

        {!loading && !error && logs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No audit logs found.
          </p>
        )}

        {!loading && !error && logs.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Resource ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} className="hover:bg-muted/40">
                  <TableCell>
                    {log.created_at
                      ? new Date(log.created_at).toLocaleString()
                      : ""}
                  </TableCell>
                  <TableCell className="font-medium">
                    {log.user_id || "—"}
                  </TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell>{log.resource_type || "—"}</TableCell>
                  <TableCell>{log.resource_id || "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
