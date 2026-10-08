import { useId } from "react";

export function Input({
  label,
  error,
  hint,
  id,
  className = "",
  rightElement,
  style,
  ...props
}) {
  const generatedId = useId();
  const inputId = id || props.name || generatedId;

  return (
    <div className="form-group">
      {label && (
        <label htmlFor={inputId} className="form-label">
          {label}
        </label>
      )}
      <div style={{ position: "relative", width: "100%" }}>
        <input
          id={inputId}
          className={`form-input ${error ? "error" : ""} ${className}`.trim()}
          style={{
            ...(rightElement ? { paddingRight: "42px" } : {}),
            ...(style || {}),
          }}
          {...props}
        />
        {rightElement && (
          <div
            style={{
              position: "absolute",
              right: "12px",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          >
            {rightElement}
          </div>
        )}
      </div>
      {error && <span className="form-error">{error}</span>}
      {hint && !error && <span className="form-hint">{hint}</span>}
    </div>
  );
}
