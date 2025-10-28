@echo off
echo ================================================================================
echo   AI ECONOMY PROTOCOL - LIVE AGENT TEST
echo ================================================================================
echo.
echo This will start both agents in separate windows.
echo.
echo Agent A (Provider): Data Analyst Agent - Port 8000
echo Agent B (Client):   Client Agent       - Port 8001
echo.
echo Press any key to start the agents...
pause > nul

echo.
echo Starting Agent A (Provider)...
start "Agent A - Provider" cmd /k "cd /d %~dp0 && python agent_a.py"

timeout /t 3 > nul

echo Starting Agent B (Client)...
start "Agent B - Client" cmd /k "cd /d %~dp0 && python agent_b.py"

echo.
echo ================================================================================
echo   AGENTS STARTED
echo ================================================================================
echo.
echo Two new windows have opened:
echo   - Agent A (Provider) - Waiting for service requests
echo   - Agent B (Client)   - Will discover and request services
echo.
echo Watch the agent windows for the payment flow!
echo.
echo To monitor transactions in real-time, run:
echo   python monitor_dashboard.py
echo.
echo Press any key to exit this window...
pause > nul
