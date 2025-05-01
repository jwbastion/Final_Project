import React, { useState } from 'react';
import SurveyStep1 from "./SurveyStep1";
import SurveyStep2 from "./SurveyStep2";
import SurveyStep3 from "./SurveyStep3";
import SurveyStep4 from "./SurveyStep4";

interface SurveyData {
  lat: number;
  lng: number;
  query: string;
  monthly: string;
  deposit: string;
  maintenance: string;
}

export default function SurveyFlow() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<Partial<SurveyData>>({});

  const handleNext = (newData: Partial<SurveyData>) => {
    setData((prev) => ({ ...prev, ...newData }));
    setStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setStep((prev) => prev - 1);
  };

  return (
    <div>
      {step === 1 && <SurveyStep1 onNext={handleNext} />}
      {step === 2 && <SurveyStep2 data={data} onNext={handleNext} onBack={handleBack} />}
      {step === 3 && <SurveyStep3 data={data} onNext={handleNext} onBack={handleBack} />}
      {step === 4 && <SurveyStep4 data={data} />}
    </div>
  );
}
