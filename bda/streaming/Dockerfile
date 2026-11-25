FROM bitnami/spark:3.5.3

USER root
RUN python3 -m pip install --no-cache-dir \
    numpy==2.1.3 \
    pandas==2.2.3 \
    scikit-learn==1.6.1 \
    joblib==1.4.2 \
    pymongo==4.10.1 \
    PyYAML==6.0.2
USER 1001

WORKDIR /app
ENV PYTHONPATH=/app
