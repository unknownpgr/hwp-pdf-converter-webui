# HWP to PDF Converter

한글(HWP) 파일을 PDF로 변환하는 웹 애플리케이션입니다. FastAPI를 사용하여 개발되었으며, Docker를 통해 쉽게 배포할 수 있습니다.

## 기능

- 다중 HWP 파일 동시 변환
- 변환된 PDF 파일 다운로드

## 기술 스택

- **Backend**: FastAPI, Python
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **변환 도구**: hwp5html, WeasyPrint
- **배포**: Docker, Docker Compose

## 시스템 요구사항

- Docker 및 Docker Compose
- 최소 2GB RAM
- Ubuntu 22.04 또는 호환되는 Linux 배포판

## 설치 및 실행

1. 저장소 클론:
```bash
git clone [repository-url]
cd hwp-converter
```

2. Docker Compose로 실행:
```bash
docker-compose up -d
# Note: Check docker-compose.yml for more details
```

3. 웹 브라우저에서 접속:
```
http://localhost:80
```

## API 엔드포인트
- `POST /convert`: HWP 파일을 업로드하여 PDF로 변환합니다. 여러 파일을 동시에 업로드할 수 있습니다.
  - Request: `multipart/form-data`로 HWP 파일들을 전송
  - Response: `{"files": ["<file_hash>.pdf", ...]}` 형식으로 변환된 PDF 파일명 목록 반환

- `GET /files/{filename}`: 변환된 PDF 파일을 다운로드합니다.
  - Response: PDF 파일 스트림 (`application/pdf`)

- `GET /`: 메인 페이지를 표시합니다.
  - Response: HTML 페이지

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 연락처

문제나 문의사항이 있으시면 다음 이메일로 연락해주세요:
unknownpgr@gmail.com
