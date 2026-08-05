import {
  cloneElement,
  isValidElement,
  useId,
  type ReactElement,
  type ReactNode
} from "react";

type FieldControlProps = {
  id?: string;
  required?: boolean;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean | "true" | "false";
};

export type FieldProps = {
  label: ReactNode;
  control: ReactElement<FieldControlProps>;
  hint?: ReactNode;
  error?: ReactNode;
  required?: boolean;
};

function Field({ label, control, hint, error, required }: FieldProps) {
  const generatedId = useId();
  const controlId = control.props.id ?? `${generatedId}-control`;
  const hintId = hint ? `${generatedId}-hint` : undefined;
  const errorId = error ? `${generatedId}-error` : undefined;
  const describedBy = [control.props["aria-describedby"], hintId, errorId].filter(Boolean).join(" ") || undefined;

  const linkedControl = isValidElement(control)
    ? cloneElement(control, {
        id: controlId,
        required,
        "aria-describedby": describedBy,
        "aria-invalid": error ? true : undefined
      })
    : control;

  return (
    <div className="ui-field">
      <label className="ui-field__label" htmlFor={controlId}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      {linkedControl}
      {hint && <span id={hintId} className="ui-field__hint">{hint}</span>}
      {error && <span id={errorId} className="ui-field__error">{error}</span>}
    </div>
  );
}

export default Field;
