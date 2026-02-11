# Dataflow Flex Template Dockerfile
FROM gcr.io/dataflow-templates-base/python312-template-launcher-base:latest

ARG WORKDIR=/dataflow/template
WORKDIR ${WORKDIR}

# Install requirements first to leverage Docker cache
COPY requirements.txt .

# Optimize layer size and clean cache
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache /tmp/*

# Copy pipeline source code and shared library
COPY . .

# Sanity check to ensure the entry point exists
RUN test -f pipeline.py

# Environment variables required by the Flex Template launcher
ENV FLEX_TEMPLATE_PYTHON_PY_FILE="${WORKDIR}/pipeline.py" \
    FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE="${WORKDIR}/requirements.txt"
