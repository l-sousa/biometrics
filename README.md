# Biometrics G5
## Biometric authentication system with Raspberry Pi 4

Initialize database:
```shell
cd backend
docker-compose up -d
```

Run application:
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 GUI/gui.py
```
