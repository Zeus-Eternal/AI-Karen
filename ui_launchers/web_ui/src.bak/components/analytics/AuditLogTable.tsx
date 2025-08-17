"use client";

import { useEffect, useState } from "react";
import { AuditService, AuditLogEntry } from "@/services/auditService";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function AuditLogTable() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const service = new AuditService();
    service
      .getAuditLogs(50)
      .then(setLogs)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Audit Logs</CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {logs.length === 0 && !error ? (
          <p className="text-sm text-muted-foreground">No logs</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    {log.created_at ? new Date(log.created_at).toLocaleString() : ""}
                  </TableCell>
                  <TableCell>{log.user_id || "-"}</TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell>{log.resource_type || "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
