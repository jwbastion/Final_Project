const express = require('express');
const mysql = require('mysql2');
const app = express();

app.use(express.json());

// ✅ MySQL 연결 설정
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'toor',
  database: 'practice_db'
});

// ✅ 연결 확인
db.connect(err => {
  if (err) throw err;
  console.log('✅ MySQL 연결 완료');
});

// ✅ 모든 사용자 가져오기
app.get('/users', (req, res) => {
  db.query('SELECT * FROM users', (err, results) => {
    if (err) return res.status(500).send(err);
    res.json(results);
  });
});

// ✅ 사용자 추가
app.post('/users', (req, res) => {
  const { name, email } = req.body;
  db.query(
    'INSERT INTO users (name, email) VALUES (?, ?)',
    [name, email],
    (err, result) => {
      if (err) return res.status(500).send(err);
      res.json({ id: result.insertId, name, email });
    }
  );
});

// ✅ 서버 실행
app.listen(3000, () => {
  console.log('🚀 서버 실행 중: http://localhost:3000');
});
