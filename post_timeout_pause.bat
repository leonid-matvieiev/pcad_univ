@echo off

chdir /d %~p0

%1

pause
exit

IF %ERRORLEVEL% NEQ 0 (
	echo.
	pause
) else (
	echo.
	timeout /t 10
)
exit

