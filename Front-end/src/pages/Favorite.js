import React from 'react';

export default function Favorite() {
  return (
    <section className="content">
      {/* 관심 매물(예시) */}
      <div className="card-list">
        <div className="card">
          <div className="image-placeholder">[매물사진]</div>
          <h3>강남 원룸</h3>
          <p>월세 65 / 보증금 1000</p>
          <p>강남역 도보 5분</p>
        </div>

        <div className="card">
          <div className="image-placeholder">[매물사진]</div>
          <h3>건대입구 투룸</h3>
          <p>월세 90 / 보증금 2000</p>
          <p>건대입구역 도보 3분</p>
        </div>
      </div>
    </section>
  );
}
