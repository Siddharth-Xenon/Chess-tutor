cp example.env .env

uvicorn app.main:app --reload --host localhost --port 8080

openssl genrsa -des3 -out private.pem 2048
openssl rsa -in private.pem -outform PEM -pubout -out public.pem
