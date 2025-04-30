const express = require("express");
const app = express();
const cors = require("cors");
const bcrypt = require("bcrypt");
const pool = require("./db");  // PostgreSQL 연결

// 미들웨어
app.use(express.json());
app.use(cors());

// 회원가입 API
app.post("/signup", async (req, res) => {
  const { email, password } = req.body;

  try {
    const hashed = await bcrypt.hash(password, 10);
    const result = await pool.query(
      `INSERT INTO users (email, password) VALUES ($1, $2) RETURNING id`,
      [email, hashed]
    );
    res.status(201).json({ success: true, userId: result.rows[0].id });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

app.post("/login", async (req, res) => {
  const { email, password } = req.body;

  try {
    const result = await pool.query("SELECT * FROM users WHERE email = $1", [email]);

    if (result.rows.length === 0) {
      return res.status(401).json({ success: false, message: "사용자 없음" });
    }

    const user = result.rows[0];
    const isMatch = await bcrypt.compare(password, user.password);

    if (!isMatch) {
      return res.status(401).json({ success: false, message: "비밀번호 불일치" });
    }

    res.json({ success: true, userId: user.id, email: user.email });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});


// 서버 시작
app.listen(5000, () => {
  console.log("서버 실행 중: http://localhost:5000");
});
