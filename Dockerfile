# ✅ Dockerfile: GPT-4o 피드백 웹앱 (공유모드 전용, Conda 기반)
FROM continuumio/miniconda3

# 공유 URL 출력 위해 버퍼링 비활성화
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 생성
WORKDIR /app

# 앱 소스 복사
COPY . .

# Conda 환경 생성 (Python 3.10)
RUN conda create -n gpt4oenv python=3.10 -y

# Conda 환경 내 pip 패키지 설치
RUN /bin/bash -c "source activate gpt4oenv && pip install -r requirements.txt"

ENTRYPOINT ["bash", "-c", "source activate gpt4oenv && python \"$@\"", "--"]