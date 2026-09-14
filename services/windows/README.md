# Windows Service

KimiBridge uses Windows Task Scheduler for user-level background startup during the source-install phase.

The PowerShell installer registers a scheduled task named:

```text
KimiBridge
```

Native Windows service support can be added later if the project needs machine-level installation.
