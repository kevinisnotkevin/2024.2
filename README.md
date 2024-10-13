# НЕОБХОДИМО СДЕЛАТЬ ДОКЕР ДОСТУПНЫМ ИЗВНЕ

```bash
sudo systemctl edit docker.service
```
- Используйте команду, чтобы открыть файл переопределения для docker.service в текстовом редакторе

```
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375
```
- Добавьте следующие строки

```bash
sudo systemctl daemon-reload
```
- Перезагрузите конфигурацию systemctl

```bash
sudo systemctl restart docker.service
```
- Перезапустить Docker
