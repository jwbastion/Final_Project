[실행 전 해야할 것]
node.js를 최신 버전으로 설치
react 셋팅을 안 한 경우, vscode 터미널 창에서 'npx create-react-app Front-end' 실행(powershell 환경)
vscode 폴더를 Front-end로 설정 후 터미널 창에서 'npm install react-router-dom' 실행(powershell 환경)
웹 실행하려면 터미널 창에서 'npm start' 실행

[디렉토리 구성도]
/Front-end
├── package.json
├── package-lock.json
├── README.txt
├── node_modules/                        # react 셋팅 관련 모듈 폴더(건들지 않음)
├── public/                                   # 정적 파일 폴더
└── src/                                        # 웹 실행중에 사용되는 파일 폴더
    ├── App.tsx                               # 라우터 관리(원래는 웹 실행할 때 맨 처음에 뜨는 메인페이지를 구성하는 tsx파일)
    ├── App.css
    ├── README.txt                         # react 기반 웹페이지에서 pdf 추출하는 방법 소개
    ├── index.tsx 등 기타 파일들...
    ├── types/ 
    │ ├── images.d.ts
    │ └── html2pdf.d.ts                   # html2pdf 설치 이후 별도로 작성하여 저장해야 함
    ├── assets/ 
    │ ├── react.svg
    │ ├── images/                          # 웹페이지 구현에 사용되는 이미지 파일들은 여기에 저장
    │ └── styles/                            # css 파일들은 여기에 저장
    │     ├── Chatbot.css
    │     ├── login.css                     # 로그인 페이지 뿐만 아니라 회원가입 페이지에도 적용
    │     ├── MainPage.css              # 메인 페이지 관련 css
    │     ├── survey.css
    │     ├── survey-step2.css
    │     ├── survey-step3.css
    │     └── survey-step4.css
    └── pages/                               # 페이지 구현 파일(tsx)들은 여기에 저장
        ├── Chatbot.tsx                     # 챗봇 페이지
        ├── Favorite.tsx                     # 관심 목록 페이지
        ├── FavoriteModalContent.tsx # 관심 매물 상세 내용(추천 이유, 상세 매물 정보, pdf 저장 버튼 등 여기에 구현)
        ├── Home.tsx                       # 메인 페이지의 본문
        ├── Layout.tsx                      # 메인 페이지에 적용할 레이아웃(사이드바)
        ├── Login.tsx                       # 로그인 페이지
        ├── Signup.tsx                     # 회원가입 페이지
        ├── Survey.tsx                      # 이하 파일들 모두 설문조사 페이지 구현에 사용
        ├── SurveyStep1.tsx
        ├── SurveyStep2.tsx
        ├── SurveyStep3.tsx
        └── SurveyStep4.tsx