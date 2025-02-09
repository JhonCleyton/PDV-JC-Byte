@echo off
echo Iniciando o PDV JC Byte...
echo.

REM Obtém o endereço IP da máquina
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /r "IPv4.*[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"') do (
    set IP=%%a
    goto :break
)
:break
set IP=%IP:~1%

echo Servidor disponivel em:
echo Local: http://localhost:5000
echo Rede: http://%IP%:5000
echo.

REM Abre o navegador padrão
start http://localhost:5000

REM Inicia o servidor Flask
python app.py

pause
