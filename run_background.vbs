Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\neeln\Projects\Ai-Thon"
WshShell.Run "cmd /c node start-servers.js", 0, False
