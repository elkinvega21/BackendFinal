# Usar una imagen base de Python oficial (versión slim para menor tamaño)
FROM python:3.11-slim-buster

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requisitos e instalar las dependencias
# Se copia solo requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto en el que se ejecutará la aplicación FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación usando Uvicorn
# NOTA: No usamos --reload en Docker para producción, y para desarrollo es menos necesario
# porque los cambios en el código requieren reconstruir la imagen o usar volúmenes.
# El 0.0.0.0 es necesario para que sea accesible desde fuera del contenedor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]