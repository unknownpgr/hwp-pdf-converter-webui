# HWP to PDF Converter

한글(HWP) 파일을 PDF로 변환하는 웹 애플리케이션입니다. FastAPI를 사용하여 개발되었으며, Docker를 통해 쉽게 배포할 수 있습니다.

## 기능

- 다중 HWP 파일 동시 변환
- 실시간 변환 상태 확인
- 변환된 PDF 파일 다운로드
- 모던하고 반응형 웹 인터페이스

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

## 사용 방법

1. 웹 인터페이스에서 "파일 선택" 버튼을 클릭하여 HWP 파일을 선택합니다.
2. "변환하기" 버튼을 클릭하여 변환을 시작합니다.
3. 변환 상태를 실시간으로 확인할 수 있습니다.
4. 변환이 완료되면 PDF 파일을 다운로드할 수 있습니다.

## API 엔드포인트

- `POST /convert`: HWP 파일 업로드 및 변환 시작
- `GET /conversion-status/{session_id}`: 변환 상태 확인
- `GET /files/{session_id}`: 변환된 파일 목록 조회
- `GET /files/{session_id}/{filename}`: PDF 파일 다운로드

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 연락처

문제나 문의사항이 있으시면 다음 이메일로 연락해주세요:
unknownpgr@gmail.com
