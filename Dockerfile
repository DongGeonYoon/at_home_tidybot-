FROM condaforge/miniforge3:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    iproute2 \
    can-utils \
    joystick \
    libusb-1.0-0 \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libsm6 \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yml /tmp/environment.yml

RUN conda env create -f /tmp/environment.yml && \
    conda clean -afy

ENV PATH="/opt/conda/envs/tidybot2/bin:${PATH}"

WORKDIR /workspace/tidybot2

COPY . .

ENV CTR_TARGET=Hardware
ENV PYTHONNOUSERSITE=1
ENV PYTHONUNBUFFERED=1

CMD ["/bin/bash"]
