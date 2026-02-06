import { FC } from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>; 
export const Button: FC<ButtonProps> = ({ children, className, ...props }) => {
  return (
    <button
      className={`ppx-button ${className ?? ""}`}
      {...props}
    >
      {children}
    </button>
  );
};
