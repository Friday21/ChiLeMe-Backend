# 选择基础镜像
FROM python:3.9-slim

# 更新 apt 源，确保包含 ffmpeg
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update

# 安装 ffmpeg 及其他必要依赖
RUN apt-get install -y --no-install-recommends ffmpeg ca-certificates python3-pip && \
    rm -rf /var/lib/apt/lists/*

# 拷贝当前项目到 /app 目录
COPY . /app

# 设定当前的工作目录
WORKDIR /app

# 选用国内镜像源以提高 pip 安装速度
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple && \
    pip config set global.trusted-host mirrors.cloud.tencent.com && \
    pip install --upgrade pip && \
    pip install --user -r requirements.txt

# 安装适用于 x86_64 的 Azure 认知服务语音库
RUN pip install /app/wxcloudrun/utils/azure_cognitiveservices_speech-1.42.0-py3-none-manylinux1_x86_64.whl

# 暴露端口
EXPOSE 80

# 启动命令
CMD ["/root/.local/bin/gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "wxcloudrun.wsgi:application"]
