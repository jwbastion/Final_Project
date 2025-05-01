import React, { useState } from 'react';
import '../assets/styles/survey.css';
import SurveyStep1 from './SurveyStep1';
import SurveyStep2 from './SurveyStep2';
import SurveyStep3 from './SurveyStep3';

interface LocationData {
  query: string;
  address: string;
  lat: number;
  lng: number;
}

const SurveyPage: React.FC = () => {
  const [step, setStep] = useState(1);
  const [locData, setLocData] = useState<LocationData | null>(null);
  
  const handleNextFrom1 = (data: LocationData) => {
    setLocData(data);
    setStep(2);
  };

  return (
    <div className="survey-bg">
      <div className="survey-container">
        <div className="process-bar">
          {[1,2,3].map(n => (
            <React.Fragment key={n}>
              <div className={`step ${step >= n ? 'active' : ''}`}>{n}</div>
              {n < 3 && <div className="divider" />}
            </React.Fragment>
          ))}
        </div>
        {step === 1 && <SurveyStep1 onNext={handleNextFrom1} />}
        {step === 2 && locData &&
          <SurveyStep2 data={locData} onNext={() => setStep(3)} onBack={() => setStep(1)} />}
        {step === 3 && <SurveyStep3 />}
      </div>
    </div>
  );
};

export default SurveyPage;
