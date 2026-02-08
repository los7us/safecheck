"use client";

import { useState, useEffect } from "react";

export function ConsentBanner() {
  const [show, setShow] = useState(false);
  
  useEffect(() => {
    // Check localStorage on mount
    const consent = localStorage.getItem("privacy-consent");
    if (consent !== "true") {
      setShow(true);
    }
  }, []);
  
  const handleAccept = () => {
    localStorage.setItem("privacy-consent", "true");
    setShow(false);
  };
  
  if (!show) return null;
  
  return (
    <div className="fixed bottom-0 inset-x-0 bg-gray-900 text-white p-4 z-50 border-t border-gray-700 shadow-xl">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-sm text-gray-300 text-center sm:text-left">
          We use Google Gemini AI to analyze content. By using this service, 
          you agree to our{" "}
          <a href="/privacy" className="underline hover:text-white">Privacy Policy</a> and 
          Google's{" "}
          <a href="https://ai.google.dev/terms" className="underline hover:text-white" target="_blank" rel="noopener noreferrer">
            Terms of Service
          </a>.
        </p>
        <button
          onClick={handleAccept}
          className="px-6 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap font-medium text-sm"
        >
          Accept & Continue
        </button>
      </div>
    </div>
  );
}
