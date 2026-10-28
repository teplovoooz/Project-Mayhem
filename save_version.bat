@echo off
echo Сохранение рабочей версии в Git...

git init
git add .
git commit -m "v1.0 - Рабочая версия: вход на лекции через веб-интерфейс"
git tag v1.0

echo Готово! Проект сохранён как v1.0
pause
