type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  error?: string;
}

export const Input = ({className, error, ...props}:InputProps) => {
  return (
    <div className="pb-8 relative">
      <input
        {...props}
        className={`border-1 disabled:bg-gray-100 bg-white p-2 outline-none text-black hover:bg-gray-100 focus:bg-gray-100 p-2 ${className ?? ""}`}
      />
      {error && <p className=" absolute text-red-800">{error}</p>}
    </div>
  );
}