import React from "react";
import { BeatLoader } from "react-spinners";
import "../../App.css";

const LoadingSpinner = ({
  size = 10,
  color = "var(--color-primary-dark)",
  loading = true,
  message = "Loading...",
}) => {
  return (
    <div className="loading-container">
      <BeatLoader
        color={color}
        loading={loading}
        size={size}
        aria-label="Loading Spinner"
        data-testid="loader"
      />
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
