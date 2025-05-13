# Front-end/Dockerfile

FROM node:18

# 작업 디렉토리 설정
WORKDIR /app

# package.json 및 lock 복사 후 의존성 설치
COPY package*.json ./
RUN npm install

# 소스 전체 복사
COPY . .

# Vite 개발 서버 실행 (host 0.0.0.0으로 외부 접속 허용)
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host"]