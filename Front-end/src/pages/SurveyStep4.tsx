import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../assets/styles/survey-step4.css';

const SurveyStep4: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const email = localStorage.getItem("email");
    const preferred_area = localStorage.getItem("preferred_area");
    const budget = localStorage.getItem("budget");
    const monthly = localStorage.getItem("monthly");
    const maintenance_fee = localStorage.getItem("maintenance_fee");

    const submitSurvey = async () => {
      console.log("📤 보낼 설문 데이터:", { email, preferred_area, budget, monthly, maintenance_fee });

      try {
        const response = await fetch("http://localhost:5000/api/survey", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            preferred_area,
            budget: budget ? parseInt(budget) : null,
            monthly: monthly ? parseInt(monthly) : null,
            maintenance_fee: maintenance_fee ? parseInt(maintenance_fee) : null
          })
        });

        const result = await response.json();
        if (!response.ok) {
          alert(`설문 저장 실패: ${result.error || "알 수 없는 오류"}`);
        } else {
          console.log("설문 저장 성공:", result);
        }
      } catch (error) {
        console.error("설문 전송 중 오류:", error);
        alert("서버 전송 중 오류가 발생했습니다.");
      }
    };

    submitSurvey();
  }, []);

  return (
    <div className="step4-container">
      <div className="step4-card">
        <div className="step4-icon">🎉</div>
        <h3 className="step4-title">설문 제출 완료!</h3>
        <p className="step4-text">
          제출된 응답을 바탕으로 사용자의 유형을<br/>
          분석 중입니다. 잠시만 기다려 주세요.
        </p>
        <button
          type="button"
          className="step4-button"
          onClick={() => navigate('/main')}
        >
          분석결과 보러가기
        </button>
      </div>
    </div>
  );
};

export default SurveyStep4;

