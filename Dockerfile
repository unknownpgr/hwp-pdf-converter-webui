FROM ubuntu:22.04

ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && apt install -y python3-pip language-pack-ko fonts-nanum-* fontconfig weasyprint
RUN pip install pyhwp six
RUN fc-cache -fv

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
