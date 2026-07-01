' JarvisOS silent launcher.
' Starts the backend (which also serves the built frontend) with NO terminal window,
' lets it manage Ollama + warm qwen3:8b, waits until it is reachable, then opens the UI
' in the default browser. Paths are derived from this script's location, so the file is
' portable and safe to commit.

Option Explicit

Dim fso, shell, scriptDir, repoRoot, backendDir, logPath, url, cmd, i

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)   ' <repo>\scripts
repoRoot  = fso.GetParentFolderName(scriptDir)                ' <repo>
backendDir = fso.BuildPath(repoRoot, "backend")
logPath = "C:\JarvisOS\jarvis.log"
url = "http://127.0.0.1:8000/"

' Returns True if the backend already answers on the port.
Function ServerUp()
    Dim h
    ServerUp = False
    On Error Resume Next
    Set h = CreateObject("MSXML2.XMLHTTP")
    h.Open "GET", url, False
    h.Send
    If Err.Number = 0 Then
        If h.Status = 200 Then ServerUp = True
    End If
    On Error GoTo 0
End Function

' Start the backend windowless only if it is not already running.
If Not ServerUp() Then
    shell.CurrentDirectory = backendDir
    cmd = "cmd /c set JARVISOS_MANAGE_OLLAMA=1 && .venv\Scripts\pythonw.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > " & logPath & " 2>&1"
    shell.Run cmd, 0, False   ' 0 = hidden window, do not wait
End If

' Wait for readiness (bind + optional Ollama spawn/health), up to ~40s.
For i = 1 To 40
    If ServerUp() Then Exit For
    WScript.Sleep 1000
Next

' Open the app in the default browser (visible).
shell.Run url, 1, False
