# 选择合适的 Python 3.9 slim 镜像，基于 Debian
FROM python:3.9-slim

# 使用 HTTPS 协议访问容器云调用证书安装
RUN apt-get update && apt-get install -y ca-certificates

# 手动添加国内镜像源，确保 apt 可以使用
RUN echo "deb http://mirrors.cloud.tencent.com/debian/ buster main" > /etc/apt/sources.list && \
    echo "deb-src http://mirrors.cloud.tencent.com/debian/ buster main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3-pip && \
    rm -rf /var/lib/apt/lists/*

# 拷贝当前项目到 /app 目录下(.dockerignore 中文件除外)
COPY . /app

# 设定当前的工作目录
WORKDIR /app

# 配置国内镜像源以加速 pip 安装
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip \
    && pip install --user -r requirements.txt

# 如果使用了本地的 wheel 文件，请确保路径和平台兼容
RUN pip install /app/wxcloudrun/utils/azure_azure_azure_cognitiveservices_speech-1.42.0-py3-none-manylinux1_x86_64.whl

# 暴露端口，容器运行时需要暴露端口以便外部访问
EXPOSE 80

# 执行启动命令，确保 CMD 只写最后一行
CMD ["python3", "manage.py", "runserver", "0.0.0.0:80"]
