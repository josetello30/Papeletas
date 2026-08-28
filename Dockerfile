# 1. Utilizar una imagen base ligera de Python
FROM python:3.12-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el archivo de dependencias
COPY requirements.txt .

# 4. Instalar las librerías necesarias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto de tus archivos al contenedor (.py y .csv)
COPY . .

# 6. Exponer el puerto estándar de Streamlit
EXPOSE 8501

# 7. Comando para ejecutar el dashboard al encender el contenedor
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
