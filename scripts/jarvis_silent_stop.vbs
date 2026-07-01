' JarvisOS stop.
' Terminates the windowless backend (pythonw/python running "uvicorn app.main").
' Ollama is intentionally left running: on Windows it is usually a shared service that
' the launcher attaches to (does not own), so JarvisOS must not kill it here.

Option Explicit

Dim wmi, procs, p, cmdLine, killed
killed = 0

Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set procs = wmi.ExecQuery("SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name='pythonw.exe' OR Name='python.exe' OR Name='cmd.exe'")

For Each p In procs
    cmdLine = ""
    If Not IsNull(p.CommandLine) Then cmdLine = LCase(p.CommandLine)
    If InStr(cmdLine, "uvicorn") > 0 And InStr(cmdLine, "app.main") > 0 Then
        On Error Resume Next
        p.Terminate()
        If Err.Number = 0 Then killed = killed + 1
        On Error GoTo 0
    End If
Next

Dim sh
Set sh = CreateObject("WScript.Shell")
If killed > 0 Then
    ' Auto-dismissing confirmation (3s).
    sh.Popup "JarvisOS stopped.", 3, "JarvisOS", 64
Else
    sh.Popup "JarvisOS was not running.", 3, "JarvisOS", 48
End If
