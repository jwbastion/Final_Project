// liveport/server.js
const express = require("express");
const cors = require("cors");
const bcrypt = require("bcrypt");
const pool = require("./db");

const app = express();
app.use(express.json());
app.use(cors());

app.post("/signup", async (req, res) => {
  const {
    name,
    username,
    password,
    gender,
    age,
    budget,
    preferred_deal_type,
    has_pet,
    prefer_elevator
  } = req.body;

  try {
    const hashed = await bcrypt.hash(password, 10);
    const result = await pool.query(
      `INSERT INTO users
      (name, username, password, gender, age, budget, preferred_deal_type, has_pet, prefer_elevator)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
      RETURNING id`,
      [name, username, hashed, gender, age, budget, preferred_deal_type, has_pet, prefer_elevator]
    );
    res.status(201).json({ success: true, userId: result.rows[0].id });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

app.post("/login", async (req, res) => {
  const { username, password } = req.body;
  try {
    const result = await pool.query("SELECT * FROM users WHERE username = $1", [username]);
    if (result.rows.length === 0) {
      return res.status(401).json({ success: false, message: "사용자 없음" });
    }

    const user = result.rows[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ success: false, message: "비밀번호 불일치" });
    }

    res.json({ success: true, userId: user.id, name: user.name });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

app.listen(5000, () => {
  console.log("서버 실행 중: http://localhost:5000");
});
