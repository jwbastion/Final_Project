const express = require('express');
const cors = require('cors');
const mysql = require('mysql2');
const bcrypt = require('bcryptjs');

const app = express();
app.use(cors());
app.use(express.json());

// ✅ MySQL 연결 설정
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'toor',   // ← 본인 비밀번호로 수정
  database: 'liveport_db' // ← 본인 DB명으로 수정
});

db.connect((err) => {
  if (err) {
    console.error('MySQL 연결 실패:', err);
  } else {
    console.log('✅ MySQL 연결 성공!');
  }
});

// ✅ 회원가입 API
app.post('/signup', async (req, res) => {
  const { password, email } = req.body;
  const hashed = await bcrypt.hash(password, 10);

  const sql = 'INSERT INTO users (email, password) VALUES (?, ?)';
  db.query(sql, [email, hashed], (err, result) => {
    if (err) {
      console.error('회원가입 오류:', err);
      return res.status(500).json({ message: '회원가입 실패' });
    }
    res.json({ message: '회원가입 성공' });
  });
});

// ✅ 로그인 API
app.post('/login', async (req, res) => {
  console.log('로그인 요청 받음:', req.body);  // ← 여기 문제 아님

  const { email, password } = req.body;        // ✅ 먼저 선언되어야 함

  const sql = 'SELECT * FROM users WHERE email = ?';
  db.query(sql, [email], async (err, results) => {
    if (err) {
      console.error('DB 조회 실패:', err);
      return res.status(500).json({ message: '서버 오류' });
    }

    if (results.length === 0) {
      return res.status(401).json({ message: '존재하지 않는 계정입니다.' });
    }

    const user = results[0];

    // ✅ password 변수는 여기서 이미 선언되어 있으므로 오류 없음
    const match = await bcrypt.compare(password, user.password);
    console.log('비밀번호 일치 여부:', match);  // 🔍 여기에 문제 없도록!

    if (!match) {
      return res.status(401).json({ message: '비밀번호가 틀렸습니다.' });
    }

    res.json({ message: '로그인 성공!' });
  });
});



// ✅ 서버 실행
app.listen(3001, () => {
  console.log('🚀 서버 실행 중: http://localhost:3001');
});
