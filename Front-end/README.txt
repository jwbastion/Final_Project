[실행 전 해야할 것]
node.js 설치
vscode 폴더를 Front-end로 설정 후 터미널 창에서 'npm install react-router-dom' 실행(powershell 환경)
웹 실행하려면 터미널 창에서 'npm start' 실행

[디렉토리 구성도]
/Front-end
├── package.json
├── package-lock.json
├── README.txt
├── node_modules/ # react 셋팅 관련 모듈 폴더(건들지 않음)
├── public/            # 정적 파일 폴더
└── src/                 # 웹 실행중에 사용되는 파일 폴더
          ├── App.js   # 라우터 관리(원래는 웹 실행할 때 맨 처음에 뜨는 메인페이지를 구성하는 js파일) 
          ├── App.css
          ├── index.js 등 기타 파일들...
          └── pages/                    # 기능별 페이지 관련 파일(js, css)들은 여기에 저장
                    ├── Chatbot.js      # 챗봇 페이지
                    ├── Chatbot.css
                    ├── LoginForm.js  # 로그인 페이지
                    ├── LoginForm.css
                    ├── Signup.js       # 회원가입 페이지
                    ├── Signup.css
                    ├── Survey.js        # 설문조사 페이지
                    ├── Survey.css
                    └── 이외 페이지(를 구성하는 js, css)들도 추후 추가 예정...