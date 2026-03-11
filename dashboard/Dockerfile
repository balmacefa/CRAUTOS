FROM python:3.11-slim

WORKDIR /app

# Install necessary libraries
RUN pip install --no-cache-dir dash dash-bootstrap-components plotly pandas requests gunicorn

COPY dashboard /app/dashboard

EXPOSE 8050

CMD ["gunicorn", "-b", "0.0.0.0:8050", "dashboard.app:server"]