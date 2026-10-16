# Windows Service

StudioRelay uses Windows Task Scheduler for user-level background startup during the source-install phase.

The PowerShell installer registers a scheduled task named:

```text
StudioRelay
```

(Legacy installations using `KimiBridge` remain recognized for backward compatibility).

Native Windows service support can be added later if the project needs machine-level installation.
